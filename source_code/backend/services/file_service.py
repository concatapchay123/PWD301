"""File storage and authorization service for PWD301.

Implements:
- Physical Blob and Logical Asset separation (ADR-008).
- SHA-256 Content-hash deduplication (Algorithm 12).
- Zero PK leakage and public UUIDv4/v5 boundaries (ADR-002).
- Strict upload size constraints (video < 1 GB, images <= 10 MB,
  PDF/DOCX <= 50 MB, PPTX <= 100 MB).
- Fail-closed download security and zero-trust IDOR prevention.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import mimetypes
import os
import re
import shutil
import time
import uuid
import zipfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from pathlib import Path
from typing import IO, Any, BinaryIO

import sqlalchemy as sa
from flask import current_app
from sqlalchemy.orm import Session, scoped_session

from backend.extensions import db
from backend.models.course import Course, CourseChangeRequest, Enrollment, LearningUnit, Lesson
from backend.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from backend.models.identity import User
from backend.models.notification_audit import AuditEvent
from backend.models.types import utc_now
from backend.services.authorization_service import (
    _resolve_lesson,
    require_course_manager,
)
from backend.services.exceptions import (
    ConflictError,
    FileAccessDeniedError,
    FileAssetNotFoundError,
    FileInfectedError,
    FileSecurityQuarantineError,
    FileSizeLimitExceededError,
    FileStorageError,
    FileValidationError,
    ResourceNotFoundError,
)
from backend.services.scanner_service import (
    scan_blob_file,
    scan_file_all_engines,
)
from backend.services.storage_adapter import (
    create_download_url,
    download_blob_from_cloud,
    is_cloud_storage_enabled,
    upload_blob_to_cloud,
)

# Dangerous executable extensions strictly forbidden per security architecture
DANGEROUS_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".exe",
        ".bat",
        ".cmd",
        ".sh",
        ".bash",
        ".php",
        ".py",
        ".pyw",
        ".pl",
        ".cgi",
        ".jar",
        ".vbs",
        ".js",
        ".vbe",
        ".wsf",
        ".wsh",
        ".msi",
        ".scr",
        ".com",
        ".pif",
        ".hta",
        ".cpl",
        ".msc",
        # Macro-enabled Office forbidden per Business Rule 11
        ".docm",
        ".xlsm",
        ".pptm",
        ".dotm",
        ".xltm",
        ".potm",
    }
)

# Forbidden archive extensions strictly blocked per non-archive attachment policy
FORBIDDEN_ARCHIVE_EXTENSIONS: frozenset[str] = frozenset(
    {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"}
)

FORBIDDEN_ARCHIVE_MESSAGE: str = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)

# Allowed non-archive document, CAD, and 3D model formats
ALLOWED_DOCUMENT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".pptx",
        ".ppt",
        ".txt",
        ".dwg",
        ".dxf",
        ".obj",
        ".fbx",
        ".stl",
        ".blend",
        ".step",
        ".stp",
        ".gltf",
        ".glb",
    }
)

MAX_PPTX_BYTES: int = 50_000_000  # 50 MB
MAX_DOCUMENT_BYTES: int = 50_000_000  # 50 MB
MAX_ATTACHMENT_BYTES: int = 50_000_000  # 50 MB


def _file_rejection_event_key(revision: FileRevision, recipient_user_id: int) -> uuid.UUID:
    """Return one retry key for a rejected file revision notification."""
    if revision.id is None:
        raise RuntimeError("File rejection notification key requires a persisted revision.")
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"pwd301:file-rejected:{revision.id}:{recipient_user_id}",
    )


IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"}
)

VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v", ".wmv", ".flv"}
)


class LimitingStream:
    """Wraps an incoming binary stream to enforce an absolute byte ceiling during reading.

    If the accumulated bytes read reach or exceed max_bytes, reading is immediately aborted
    and FileSizeLimitExceededError is raised (yielding HTTP 413).
    """

    def __init__(self, stream: Any, max_bytes: int = 1_000_000_000) -> None:
        self._stream = stream
        self._max_bytes = max_bytes
        self._bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._stream.read(size)
        if chunk:
            self._bytes_read += len(chunk)
            if self._bytes_read >= self._max_bytes:
                raise FileSizeLimitExceededError(
                    f"File stream exceeded maximum limit of {self._max_bytes} bytes."
                )
        return chunk


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection attacks.

    Extracts basename only, removes null bytes, slashes, and hazardous characters,
    and strips leading/trailing dots and spaces.
    """
    if not filename:
        return "unnamed_file"

    # Normalize backslashes and get basename
    cleaned = os.path.basename(filename.replace("\\", "/"))

    # Remove null bytes and non-printable characters
    cleaned = "".join(c for c in cleaned if c.isprintable() and c not in '<>:"/\\|?*;\x00')

    # Remove any traversal patterns remaining
    cleaned = re.sub(r"\.\.+", ".", cleaned)

    # Strip whitespace and dots from ends
    cleaned = cleaned.strip(". ")

    return cleaned or "unnamed_file"


def get_file_storage_root() -> Path:
    """Resolve the root path for permanent physical file storage."""
    raw = current_app.config.get("FILE_STORAGE_ROOT", "./storage")
    path = Path(raw).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_quarantine_root() -> Path:
    """Resolve the root path for temporary quarantine uploads."""
    raw = current_app.config.get("FILE_QUARANTINE_ROOT", "./quarantine")
    path = Path(raw).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_infected_root() -> Path:
    """Resolve the isolated quarantine root for infected files."""
    root = get_file_quarantine_root() / "infected"
    root.mkdir(parents=True, exist_ok=True)
    return root


def validate_file_metadata(filename: str, declared_mime: str | None = None) -> None:
    """Validate file metadata against forbidden executable extensions and archives."""
    clean_lower = filename.lower()
    ext = Path(clean_lower).suffix
    if ext in FORBIDDEN_ARCHIVE_EXTENSIONS or any(
        clean_lower.endswith(arch_ext) for arch_ext in FORBIDDEN_ARCHIVE_EXTENSIONS
    ):
        raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)
    if ext in DANGEROUS_EXTENSIONS:
        raise FileValidationError(f"File extension '{ext}' is forbidden for security.")


def check_file_size_limit(size_bytes: int, filename: str) -> None:
    """Check file size strictly against configured category limits.

    Non-negotiable invariants:
    - Video files must be strictly < 1 GB (1,000,000,000 bytes).
    - Document and lesson attachments (Word, PDF, Excel, PowerPoint, Text, CAD, 3D) <= 50 MB (50,000,000 bytes).
    """
    if size_bytes <= 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    ext = Path(filename).suffix.lower()

    # Video check: strictly < 1 GB (1,000,000,000 bytes)
    max_video_exclusive = current_app.config.get("MAX_VIDEO_BYTES_EXCLUSIVE", 1_000_000_000)
    if ext in VIDEO_EXTENSIONS and size_bytes >= max_video_exclusive:
        raise FileSizeLimitExceededError(
            f"Video file exceeds maximum allowed limit of {max_video_exclusive} bytes "
            "(strictly < 1 GB)."
        )

    # Platform-wide exclusive upper ceiling
    if size_bytes >= max_video_exclusive:
        raise FileSizeLimitExceededError(
            f"File exceeds maximum platform limit of {max_video_exclusive} bytes."
        )

    # Image limit: 10 MB (10,000,000 bytes)
    max_image = current_app.config.get("MAX_IMAGE_BYTES", 10_000_000)
    if ext in IMAGE_EXTENSIONS and size_bytes > max_image:
        raise FileSizeLimitExceededError(
            f"Image file exceeds maximum allowed size of {max_image} bytes."
        )

    # PDF limit: 50 MB
    max_pdf = current_app.config.get("MAX_PDF_BYTES", 50_000_000)
    if ext == ".pdf" and size_bytes > max_pdf:
        raise FileSizeLimitExceededError(
            f"PDF file exceeds maximum allowed size of {max_pdf} bytes."
        )

    # DOCX limit: 50 MB
    max_docx = current_app.config.get("MAX_DOCX_BYTES", 50_000_000)
    if ext in {".docx", ".doc"} and size_bytes > max_docx:
        raise FileSizeLimitExceededError(
            f"DOCX file exceeds maximum allowed size of {max_docx} bytes."
        )

    # PPTX limit: 50 MB
    max_pptx = current_app.config.get("MAX_PPTX_BYTES", 50_000_000)
    if ext in {".pptx", ".ppt"} and size_bytes > max_pptx:
        raise FileSizeLimitExceededError(
            f"PPTX file exceeds maximum allowed size of {max_pptx} bytes."
        )

    # Strict 50MB ceiling across all document, CAD, 3D, and non-video attachments
    max_attachment = current_app.config.get(
        "MAX_ATTACHMENT_BYTES",
        current_app.config.get("MAX_DOCUMENT_BYTES", 50_000_000),
    )
    if ext in ALLOWED_DOCUMENT_EXTENSIONS and size_bytes > max_attachment:
        raise FileSizeLimitExceededError(
            f"Document/attachment file exceeds maximum allowed size of {max_attachment} bytes (50 MB)."
        )
    if ext not in VIDEO_EXTENSIONS and ext not in IMAGE_EXTENSIONS and size_bytes > max_attachment:
        raise FileSizeLimitExceededError(
            f"Attachment file exceeds maximum allowed size of {max_attachment} bytes (50 MB)."
        )


def detect_mime_type(header_bytes: bytes, filename: str, declared_mime: str | None = None) -> str:
    """Detect MIME type combining magic byte signatures and filename extension."""
    ext = Path(filename).suffix.lower()

    # Magic bytes check
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header_bytes.startswith(b"GIF87a") or header_bytes.startswith(b"GIF89a"):
        return "image/gif"
    if header_bytes.startswith(b"%PDF-"):
        return "application/pdf"
    if header_bytes.startswith(b"PK\x03\x04"):
        if ext == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if ext == ".pptx":
            return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        if ext == ".xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if (
        header_bytes.startswith(b"RIFF")
        and len(header_bytes) >= 12
        and header_bytes[8:12] == b"WEBP"
    ):
        return "image/webp"

    # CAD & 3D magic bytes and extension mapping
    if header_bytes.startswith(b"AC10") or ext == ".dwg":
        return "application/acad"
    if (
        header_bytes.startswith(b"SECTION")
        or header_bytes.startswith(b"0\nSECTION")
        or header_bytes.startswith(b"0\r\nSECTION")
        or ext == ".dxf"
    ):
        return "application/dxf"
    if header_bytes.startswith(b"BLENDER") or ext == ".blend":
        return "application/x-blender"
    if header_bytes.startswith(b"glTF") or ext == ".glb":
        return "model/gltf-binary"
    if (
        header_bytes.startswith(b"Kaydara FBX Binary  \x00")
        or header_bytes.startswith(b"; FBX")
        or ext == ".fbx"
    ):
        return "application/octet-stream"
    if header_bytes.startswith(b"solid") or ext == ".stl":
        return "model/stl"
    if b"ISO-10303-21" in header_bytes[:512] or ext in {".step", ".stp"}:
        return "application/step"
    if ext == ".gltf":
        return "model/gltf+json"
    if ext == ".obj":
        return "model/obj"
    if ext == ".txt":
        return "text/plain"
    if ext == ".doc":
        return "application/msword"
    if ext == ".xls":
        return "application/vnd.ms-excel"
    if ext == ".ppt":
        return "application/vnd.ms-powerpoint"

    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        return guessed

    if declared_mime and declared_mime not in {"application/octet-stream", ""}:
        return declared_mime

    return "application/octet-stream"


def check_archive_rejection(header_bytes: bytes, filename: str, file_path: Path) -> None:
    """Inspect file extension and magic byte signatures to block forbidden archives.

    Differentiates generic zip archives from valid OOXML (docx, xlsx, pptx).
    Raises FileValidationError with exact Vietnamese message on forbidden archives.
    """
    clean_lower = filename.lower()
    ext = Path(clean_lower).suffix

    # 1. Extension check
    if ext in FORBIDDEN_ARCHIVE_EXTENSIONS or any(
        clean_lower.endswith(arch_ext) for arch_ext in FORBIDDEN_ARCHIVE_EXTENSIONS
    ):
        raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)

    # 2. Non-ZIP archive magic bytes
    if (
        header_bytes.startswith((b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00"))
        or header_bytes.startswith(b"7z\xbc\xaf\x27\x1c")
        or header_bytes.startswith(b"\x1f\x8b")
        or header_bytes.startswith(b"BZh")
        or header_bytes.startswith(b"\xfd7zXZ\x00")
        or (len(header_bytes) >= 262 and header_bytes[257:262] == b"ustar")
        or (len(header_bytes) >= 32773 and header_bytes[32768:32773] == b"CD001")
    ):
        raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)

    # 3. ZIP magic bytes (PK\x03\x04, PK\x05\x06, PK\x07\x08)
    if header_bytes.startswith((b"PK\x05\x06", b"PK\x07\x08")):
        raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)

    if header_bytes.startswith(b"PK\x03\x04"):
        if ext not in {".docx", ".xlsx", ".pptx"}:
            raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)
        # Check genuine OOXML contents
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                names = set(zf.namelist())
                is_ooxml = "[Content_Types].xml" in names and (
                    (ext == ".docx" and any(n.startswith("word/") for n in names))
                    or (ext == ".xlsx" and any(n.startswith("xl/") for n in names))
                    or (ext == ".pptx" and any(n.startswith("ppt/") for n in names))
                )
                if not is_ooxml:
                    raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)
        except zipfile.BadZipFile as err:
            raise FileValidationError("Document archive is corrupted or has invalid ZIP structure.") from err
        except FileValidationError:
            raise
        except Exception as err:
            raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE) from err


def _resolve_file_asset(
    asset_or_id: FileAsset | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset | None:
    """Resolve a FileAsset instance by model, public UUID, internal PK, or LessonResource ID."""
    if isinstance(asset_or_id, FileAsset):
        return asset_or_id

    sess = session if session is not None else db.session
    if isinstance(asset_or_id, int):
        fa = sess.get(FileAsset, asset_or_id)
        if fa is not None:
            return fa
        res = sess.get(LessonResource, asset_or_id)
        if res is not None and res.file_asset is not None:
            return res.file_asset
        return None

    if isinstance(asset_or_id, uuid.UUID):
        fa = sess.query(FileAsset).filter(FileAsset.public_id == asset_or_id).first()
        if fa is not None:
            return fa
        for lr in sess.query(LessonResource).all():
            if lr.public_id == asset_or_id and lr.file_asset is not None:
                return lr.file_asset
        return None

    if isinstance(asset_or_id, str):
        try:
            val_uuid = uuid.UUID(asset_or_id)
            fa = sess.query(FileAsset).filter(FileAsset.public_id == val_uuid).first()
            if fa is not None:
                return fa
            for lr in sess.query(LessonResource).all():
                if lr.public_id == val_uuid and lr.file_asset is not None:
                    return lr.file_asset
        except ValueError:
            pass
        if asset_or_id.isdigit():
            fa = sess.get(FileAsset, int(asset_or_id))
            if fa is not None:
                return fa
            res = sess.get(LessonResource, int(asset_or_id))
            if res is not None and res.file_asset is not None:
                return res.file_asset

    return None


@contextmanager
def filesystem_lease(lock_path: Path, timeout_seconds: float = 30) -> Iterator[None]:
    """Cross-process lease reused by volume budgets and HLS generation."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"1")
            lock.flush()
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                lock.seek(0)
                if os.name == "nt":
                    msvcrt = importlib.import_module("msvcrt")
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl = importlib.import_module("fcntl")
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise FileStorageError(
                        "Temporary file processing is busy; retry shortly."
                    ) from None
                time.sleep(0.05)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt = importlib.import_module("msvcrt")
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl = importlib.import_module("fcntl")
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def with_storage_budget(function: Callable[..., Any]) -> Callable[..., Any]:
    """Serialize temporary budget decisions across processes sharing the storage volume."""

    @wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> Any:
        with filesystem_lease(get_file_storage_root() / ".budget.lock"):
            return function(*args, **kwargs)

    return guarded


def _ensure_file_asset_authoring(actor: User, asset: FileAsset, sess: Any) -> None:
    from backend.models.file_import import QuestionRevisionResource
    from backend.models.question_bank import Question, QuestionRevision
    from backend.services.course_workflow_service import ensure_course_authoring, should_stage

    course = ensure_course_authoring(actor, asset.course_id, session=sess)
    if not should_stage(actor, course, sess):
        return
    lesson_reference = (
        sess.query(LessonResource.id)
        .join(Lesson, Lesson.id == LessonResource.lesson_id)
        .filter(
            LessonResource.file_asset_id == asset.id,
            Lesson.status.in_(("ACTIVE", "PUBLISHED", "HIDDEN", "HISTORICAL")),
        )
        .first()
    )
    question_reference = (
        sess.query(QuestionRevisionResource.id)
        .join(
            QuestionRevision, QuestionRevision.id == QuestionRevisionResource.question_revision_id
        )
        .join(Question, Question.id == QuestionRevision.question_id)
        .filter(
            QuestionRevisionResource.file_asset_id == asset.id,
            sa.or_(
                Question.status != "DRAFT",
                QuestionRevision.was_student_exposed == sa.true(),
                QuestionRevision.was_used_for_grading == sa.true(),
            ),
        )
        .first()
    )
    held, approved = _course_file_memberships(course, sess)
    identifier = str(asset.public_id)
    draft_reference = (
        sess.query(LessonResource.id)
        .join(Lesson, Lesson.id == LessonResource.lesson_id)
        .filter(
            LessonResource.file_asset_id == asset.id,
            Lesson.status.in_(("DRAFT", "PENDING_APPROVAL")),
            Lesson.change_request_id.is_not(None),
        )
        .first()
        or sess.query(QuestionRevisionResource.id)
        .join(
            QuestionRevision, QuestionRevision.id == QuestionRevisionResource.question_revision_id
        )
        .join(Question, Question.id == QuestionRevision.question_id)
        .filter(
            QuestionRevisionResource.file_asset_id == asset.id,
            Question.status == "DRAFT",
            QuestionRevision.was_student_exposed == sa.false(),
            QuestionRevision.was_used_for_grading == sa.false(),
        )
        .first()
    )
    legacy_baseline = (
        asset.asset_type == "RESOURCE" and identifier not in held and not draft_reference
    )
    if (
        course.thumbnail_file_asset_id == asset.id
        or lesson_reference
        or question_reference
        or identifier in approved
        or legacy_baseline
    ):
        raise ConflictError(
            "Tệp đang được nội dung đã duyệt sử dụng. Hãy tải một tệp mới và thay thế "
            "hoặc gỡ liên kết trong bản nháp khóa học để gửi duyệt."
        )


@with_storage_budget
def store_file_stream(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    file_stream: IO[bytes] | BinaryIO | LimitingStream,
    filename: str,
    content_type: str | None = None,
    asset_type: str = "RESOURCE",
    title: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Store an uploaded file stream following Algorithm 12 Deduplication.

    1. Enforces course management authorization.
    2. Validates filename and extension security.
    3. Streams content to quarantine while computing SHA-256 and checking size limits.
    4. If hash exists in file_blobs: increments reference_count, reuses blob, deletes temp file.
    5. If hash is new: moves to hierarchical path (storage/blobs/ab/cd/<hash>), creates FileBlob.
    6. Creates FileAsset and FileRevision 1 in ACTIVE state, records passing FileScanResult.
    7. Rollback retains content-addressed files for conservative orphan reconciliation.
    """
    sess = session if session is not None else db.session
    from backend.services.course_workflow_service import ensure_course_authoring

    course = ensure_course_authoring(actor, course_id, session=sess)

    clean_filename = sanitize_filename(filename)
    validate_file_metadata(clean_filename, content_type)
    ext = Path(clean_filename).suffix.lower()

    quarantine_root = get_file_quarantine_root()
    reserve_storage_space(quarantine_root, 0)
    temp_filename = f"upload_{uuid.uuid4().hex}{ext}"
    temp_path = quarantine_root / temp_filename

    hasher = hashlib.sha256()
    total_size = 0
    header_bytes = b""
    max_video_exclusive = current_app.config.get("MAX_VIDEO_BYTES_EXCLUSIVE", 1_000_000_000)
    max_attachment_bytes = current_app.config.get(
        "MAX_ATTACHMENT_BYTES",
        current_app.config.get("MAX_DOCUMENT_BYTES", 50_000_000),
    )
    stream_limit = (
        max_video_exclusive
        if ext in VIDEO_EXTENSIONS
        else max_attachment_bytes + 1
    )
    stream_to_read: Any = (
        file_stream
        if isinstance(file_stream, LimitingStream)
        else LimitingStream(file_stream, max_bytes=stream_limit)
    )
    newly_created_dest: Path | None = None

    try:
        # Stream into quarantine temp file
        with open(temp_path, "wb") as f_out:
            while True:
                chunk = stream_to_read.read(64 * 1024)
                if not chunk:
                    break
                if not header_bytes:
                    header_bytes = chunk[:512]
                total_size += len(chunk)

                # Early check during streaming to avoid disk exhaustion
                ceiling = max_video_exclusive if ext in VIDEO_EXTENSIONS else max_attachment_bytes
                if (ext in VIDEO_EXTENSIONS and total_size >= ceiling) or (
                    ext not in VIDEO_EXTENSIONS and total_size > ceiling
                ):
                    raise FileSizeLimitExceededError(
                        f"File stream exceeded maximum limit of {ceiling} bytes."
                    )

                reserve_storage_space(quarantine_root, len(chunk))
                hasher.update(chunk)
                f_out.write(chunk)

        # Inspect extension and magic bytes for forbidden archives
        check_archive_rejection(header_bytes, clean_filename, temp_path)

        # Validate total size strictly
        check_file_size_limit(total_size, clean_filename)
        detected_mime = detect_mime_type(header_bytes, clean_filename, content_type)

        digest_bytes = hasher.digest()
        hex_hash = hasher.hexdigest()

        # Multi-engine malware scanning while quarantined (single-pass)
        now = utc_now()
        scan_verdicts = scan_file_all_engines(temp_path, declared_filename=clean_filename)
        main_verdict = scan_blob_file(temp_path, declared_filename=clean_filename)
        if main_verdict.status != "PASS" and not any(
            v.status == main_verdict.status for v in scan_verdicts
        ):
            scan_verdicts.insert(0, main_verdict)

        for v in scan_verdicts:
            if v.signature_name == "Forbidden-Archive-Format":
                raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)

        valid_asset_types = {
            "RESOURCE",
            "QUESTION_IMAGE",
            "COURSE_IMAGE",
            "IMPORT_SOURCE",
            "EXPORT",
            "OTHER",
        }
        chosen_type = (
            asset_type.upper()
            if asset_type and asset_type.upper() in valid_asset_types
            else "RESOURCE"
        )

        blob: FileBlob | None = None

        if (
            main_verdict.status == "PASS"
            and scan_verdicts
            and all(v.status == "PASS" for v in scan_verdicts)
        ):
            # Algorithm 12 Deduplication lookup for clean files
            blob = sess.query(FileBlob).filter(FileBlob.sha256 == digest_bytes).first()
            if blob is not None and blob.status == "PRESENT":
                # Reuse existing clean blob
                blob.reference_count += 1
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
            else:
                # Promote to permanent hierarchical storage path
                storage_root = get_file_storage_root()
                ab = hex_hash[:2]
                cd = hex_hash[2:4]
                dest_dir = storage_root / "blobs" / ab / cd
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / hex_hash

                if temp_path.exists():
                    if dest_path.exists():
                        temp_path.unlink(missing_ok=True)
                    else:
                        try:
                            os.replace(temp_path, dest_path)
                        except OSError:
                            shutil.copy2(temp_path, dest_path)
                            temp_path.unlink(missing_ok=True)
                newly_created_dest = dest_path

                storage_key = f"blobs/{ab}/{cd}/{hex_hash}"
                cloud = is_cloud_storage_enabled() and not detected_mime.startswith("video/")
                if cloud and not upload_blob_to_cloud(dest_path, storage_key):
                    raise FileStorageError("Cloud upload could not be verified.")
                blob = FileBlob(
                    sha256=digest_bytes,
                    size_bytes=total_size,
                    detected_mime_type=detected_mime,
                    storage_key=storage_key,
                    storage_backend="s3" if cloud else "local",
                    cloud_verified_at=now if cloud else None,
                    status="PRESENT",
                    reference_count=1,
                )
                sess.add(blob)
                sess.flush()

            asset = FileAsset(
                course_id=course.id,
                created_by_user_id=actor.id,
                asset_type=chosen_type,
                display_name=title or clean_filename,
                status="ACTIVE",
            )
            sess.add(asset)
            sess.flush()

            revision = FileRevision(
                file_asset_id=asset.id,
                revision_no=1,
                is_current=True,
                blob_id=blob.id,
                original_filename=clean_filename,
                declared_mime_type=content_type or detected_mime,
                detected_mime_type=detected_mime,
                size_bytes=total_size,
                status="ACTIVE",
                uploaded_by_user_id=actor.id,
                security_checks_completed_at=now,
                activated_at=now,
            )
            sess.add(revision)
            sess.flush()

            # Record scan results
            for v in scan_verdicts:
                sess.add(
                    FileScanResult(
                        file_revision_id=revision.id,
                        scan_type="MALWARE",
                        engine=v.engine_name,
                        engine_version=v.engine_version,
                        status=v.status,
                        details_json=v.details_json,
                        started_at=now,
                        completed_at=now,
                    )
                )

            sess.add(
                FileScanResult(
                    file_revision_id=revision.id,
                    scan_type="FILE_VALIDATION",
                    engine="builtin_validator",
                    engine_version="1.0",
                    status="PASS",
                    details_json=None,
                    started_at=now,
                    completed_at=now,
                )
            )
            _stage_uploaded_file(actor, course, asset, sess)
            sess.commit()
            if newly_created_dest is not None and blob.storage_backend == "s3":
                newly_created_dest.unlink(missing_ok=True)
            return asset

        elif main_verdict.status == "FAIL":
            # Isolate infected file to quarantine/infected/
            infected_dir = get_file_infected_root()
            infected_path = infected_dir / hex_hash
            if temp_path.exists():
                os.replace(temp_path, infected_path)
            newly_created_dest = infected_path

            asset = FileAsset(
                course_id=course.id,
                created_by_user_id=actor.id,
                asset_type=chosen_type,
                display_name=title or clean_filename,
                status="PENDING",
            )
            sess.add(asset)
            sess.flush()

            sig_desc = main_verdict.signature_name or "Malware detected"
            revision = FileRevision(
                file_asset_id=asset.id,
                revision_no=1,
                is_current=False,
                blob_id=None,
                original_filename=clean_filename,
                declared_mime_type=content_type or detected_mime,
                detected_mime_type=detected_mime,
                size_bytes=total_size,
                status="REJECTED",
                quarantine_key=f"infected/{hex_hash}",
                rejection_reason=f"Infected: {sig_desc}",
                uploaded_by_user_id=actor.id,
                security_checks_completed_at=now,
            )
            sess.add(revision)
            sess.flush()

            for v in scan_verdicts:
                sess.add(
                    FileScanResult(
                        file_revision_id=revision.id,
                        scan_type="MALWARE",
                        engine=v.engine_name,
                        engine_version=v.engine_version,
                        status=v.status,
                        details_json=v.details_json,
                        started_at=now,
                        completed_at=now,
                    )
                )

            try:
                from backend.services.notification_service import dispatch_notification

                dispatch_notification(
                    recipient_user=actor.id,
                    event_type="FILE_REJECTED",
                    title="Tệp tải lên bị từ chối do nhiễm mã độc",
                    body=(
                        f"Tệp '{clean_filename}' đã bị từ chối và cách ly "
                        f"vì phát hiện mã độc ({sig_desc})."
                    ),
                    category="SECURITY",
                    target_role="INSTRUCTOR",
                    event_key=_file_rejection_event_key(revision, actor.id),
                    session=sess,
                )
            except Exception:
                pass

            _stage_uploaded_file(actor, course, asset, sess)
            sess.commit()
            return asset

        else:
            # Scanner error or timeout: fail-closed quarantine
            asset = FileAsset(
                course_id=course.id,
                created_by_user_id=actor.id,
                asset_type=chosen_type,
                display_name=title or clean_filename,
                status="PENDING",
            )
            sess.add(asset)
            sess.flush()

            revision = FileRevision(
                file_asset_id=asset.id,
                revision_no=1,
                is_current=False,
                blob_id=None,
                original_filename=clean_filename,
                declared_mime_type=content_type or detected_mime,
                detected_mime_type=detected_mime,
                size_bytes=total_size,
                status="QUARANTINED",
                quarantine_key=f"quarantine/{temp_filename}",
                rejection_reason=f"Scanner error: {main_verdict.details or 'Unavailable'}",
                uploaded_by_user_id=actor.id,
                security_checks_completed_at=now,
            )
            sess.add(revision)
            sess.flush()

            for v in scan_verdicts:
                sess.add(
                    FileScanResult(
                        file_revision_id=revision.id,
                        scan_type="MALWARE",
                        engine=v.engine_name,
                        engine_version=v.engine_version,
                        status=v.status,
                        details_json=v.details_json,
                        started_at=now,
                        completed_at=now,
                    )
                )

            sess.flush()
            from backend.services.background_job_service import enqueue_background_job

            enqueue_background_job(
                job_type="FILE_SCAN",
                payload={"asset_id": asset.id, "user_id": actor.id},
                run_async=True,
                session=sess,
            )

            _stage_uploaded_file(actor, course, asset, sess)
            sess.commit()
            return asset

    except Exception:
        sess.rollback()
        # Clean up temporary quarantine file
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        # A concurrent transaction may reference this content-addressed path.
        # Retain it until conservative reconciliation; never erase a shared blob on rollback.
        raise


@with_storage_budget
def add_file_revision(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    file_stream: IO[bytes] | BinaryIO | LimitingStream,
    filename: str,
    content_type: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> FileRevision:
    """Upload a new revision for an existing FileAsset."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    _ensure_file_asset_authoring(actor, asset, sess)

    if asset.status in ("TRASH", "DELETED"):
        raise FileValidationError("Cannot add revision to a trashed or deleted file asset.")

    clean_filename = sanitize_filename(filename)
    validate_file_metadata(clean_filename, content_type)
    ext = Path(clean_filename).suffix.lower()

    quarantine_root = get_file_quarantine_root()
    reserve_storage_space(quarantine_root, 0)
    temp_filename = f"rev_{uuid.uuid4().hex}{ext}"
    temp_path = quarantine_root / temp_filename

    hasher = hashlib.sha256()
    total_size = 0
    header_bytes = b""
    max_video_exclusive = current_app.config.get("MAX_VIDEO_BYTES_EXCLUSIVE", 1_000_000_000)
    max_attachment_bytes = current_app.config.get(
        "MAX_ATTACHMENT_BYTES",
        current_app.config.get("MAX_DOCUMENT_BYTES", 50_000_000),
    )
    stream_limit = (
        max_video_exclusive
        if ext in VIDEO_EXTENSIONS
        else max_attachment_bytes + 1
    )
    stream_to_read: Any = (
        file_stream
        if isinstance(file_stream, LimitingStream)
        else LimitingStream(file_stream, max_bytes=stream_limit)
    )
    newly_created_dest: Path | None = None

    try:
        with open(temp_path, "wb") as f_out:
            while True:
                chunk = stream_to_read.read(64 * 1024)
                if not chunk:
                    break
                if not header_bytes:
                    header_bytes = chunk[:512]
                total_size += len(chunk)

                ceiling = max_video_exclusive if ext in VIDEO_EXTENSIONS else max_attachment_bytes
                if (ext in VIDEO_EXTENSIONS and total_size >= ceiling) or (
                    ext not in VIDEO_EXTENSIONS and total_size > ceiling
                ):
                    raise FileSizeLimitExceededError(
                        f"File size exceeded maximum limit of {ceiling} bytes."
                    )

                reserve_storage_space(quarantine_root, len(chunk))
                hasher.update(chunk)
                f_out.write(chunk)

        check_archive_rejection(header_bytes, clean_filename, temp_path)
        check_file_size_limit(total_size, clean_filename)
        detected_mime = detect_mime_type(header_bytes, clean_filename, content_type)

        digest_bytes = hasher.digest()
        hex_hash = hasher.hexdigest()

        # Multi-engine malware scanning while quarantined
        now = utc_now()
        scan_verdicts = scan_file_all_engines(temp_path, declared_filename=clean_filename)
        main_verdict = scan_blob_file(temp_path, declared_filename=clean_filename)

        for v in scan_verdicts:
            if v.signature_name == "Forbidden-Archive-Format":
                raise FileValidationError(FORBIDDEN_ARCHIVE_MESSAGE)

        existing_revisions = (
            sess.query(FileRevision).filter(FileRevision.file_asset_id == asset.id).all()
        )
        max_rev = max([r.revision_no for r in existing_revisions], default=0)

        if (
            main_verdict.status == "PASS"
            and scan_verdicts
            and all(v.status == "PASS" for v in scan_verdicts)
        ):
            # Deduplication lookup for clean revision
            blob = sess.query(FileBlob).filter(FileBlob.sha256 == digest_bytes).first()
            if blob is not None and blob.status == "PRESENT":
                blob.reference_count += 1
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
            else:
                storage_root = get_file_storage_root()
                ab = hex_hash[:2]
                cd = hex_hash[2:4]
                dest_dir = storage_root / "blobs" / ab / cd
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / hex_hash

                if temp_path.exists():
                    os.replace(temp_path, dest_path)
                newly_created_dest = dest_path

                storage_key = f"blobs/{ab}/{cd}/{hex_hash}"
                cloud = is_cloud_storage_enabled() and not detected_mime.startswith("video/")
                if cloud and not upload_blob_to_cloud(dest_path, storage_key):
                    raise FileStorageError("Cloud upload could not be verified.")
                blob = FileBlob(
                    sha256=digest_bytes,
                    size_bytes=total_size,
                    detected_mime_type=detected_mime,
                    storage_key=storage_key,
                    storage_backend="s3" if cloud else "local",
                    cloud_verified_at=now if cloud else None,
                    status="PRESENT",
                    reference_count=1,
                )
                sess.add(blob)
                sess.flush()

            # Mark all existing active revisions for this asset as replaced
            for rev in existing_revisions:
                if rev.is_current:
                    rev.is_current = False
                    rev.replaced_at = now
                    rev.status = "REPLACED"
                    rev.recovery_until = now + timedelta(days=30)

            # Create new active revision
            new_rev = FileRevision(
                file_asset_id=asset.id,
                revision_no=max_rev + 1,
                is_current=True,
                blob_id=blob.id,
                original_filename=clean_filename,
                declared_mime_type=content_type or detected_mime,
                detected_mime_type=detected_mime,
                size_bytes=total_size,
                status="ACTIVE",
                uploaded_by_user_id=actor.id,
                security_checks_completed_at=now,
                activated_at=now,
            )
            sess.add(new_rev)
            sess.flush()

            asset.display_name = clean_filename
            asset.updated_at = now

            for v in scan_verdicts:
                sess.add(
                    FileScanResult(
                        file_revision_id=new_rev.id,
                        scan_type="MALWARE",
                        engine=v.engine_name,
                        engine_version=v.engine_version,
                        status=v.status,
                        details_json=v.details_json,
                        started_at=now,
                        completed_at=now,
                    )
                )

            sess.add(
                FileScanResult(
                    file_revision_id=new_rev.id,
                    scan_type="FILE_VALIDATION",
                    engine="builtin_validator",
                    engine_version="1.0",
                    status="PASS",
                    details_json=None,
                    started_at=now,
                    completed_at=now,
                )
            )
            sess.commit()
            if newly_created_dest is not None and blob.storage_backend == "s3":
                newly_created_dest.unlink(missing_ok=True)
            return new_rev

        elif main_verdict.status == "FAIL":
            # Isolate infected revision to quarantine/infected/
            infected_dir = get_file_infected_root()
            infected_path = infected_dir / hex_hash
            if temp_path.exists():
                os.replace(temp_path, infected_path)
            newly_created_dest = infected_path

            sig_desc = main_verdict.signature_name or "Malware detected"
            new_rev = FileRevision(
                file_asset_id=asset.id,
                revision_no=max_rev + 1,
                is_current=False,
                blob_id=None,
                original_filename=clean_filename,
                declared_mime_type=content_type or detected_mime,
                detected_mime_type=detected_mime,
                size_bytes=total_size,
                status="REJECTED",
                quarantine_key=f"infected/{hex_hash}",
                rejection_reason=f"Infected: {sig_desc}",
                uploaded_by_user_id=actor.id,
                security_checks_completed_at=now,
            )
            sess.add(new_rev)
            sess.flush()

            for v in scan_verdicts:
                sess.add(
                    FileScanResult(
                        file_revision_id=new_rev.id,
                        scan_type="MALWARE",
                        engine=v.engine_name,
                        engine_version=v.engine_version,
                        status=v.status,
                        details_json=v.details_json,
                        started_at=now,
                        completed_at=now,
                    )
                )
            try:
                from backend.services.notification_service import dispatch_notification

                dispatch_notification(
                    recipient_user=actor.id,
                    event_type="FILE_REJECTED",
                    title="Phiên bản tệp bị từ chối do nhiễm mã độc",
                    body=(
                        f"Phiên bản mới của tệp '{clean_filename}' đã bị từ chối "
                        f"vì phát hiện mã độc ({sig_desc})."
                    ),
                    category="SECURITY",
                    force_email=True,
                    target_role="INSTRUCTOR",
                    event_key=_file_rejection_event_key(new_rev, actor.id),
                    session=sess,
                )
            except Exception:
                pass

            sess.commit()
            return new_rev

        else:
            # Scanner error: keep in quarantine
            new_rev = FileRevision(
                file_asset_id=asset.id,
                revision_no=max_rev + 1,
                is_current=False,
                blob_id=None,
                original_filename=clean_filename,
                declared_mime_type=content_type or detected_mime,
                detected_mime_type=detected_mime,
                size_bytes=total_size,
                status="QUARANTINED",
                quarantine_key=f"quarantine/{temp_filename}",
                rejection_reason=f"Scanner error: {main_verdict.details or 'Unavailable'}",
                uploaded_by_user_id=actor.id,
                security_checks_completed_at=now,
            )
            sess.add(new_rev)
            sess.flush()

            for v in scan_verdicts:
                sess.add(
                    FileScanResult(
                        file_revision_id=new_rev.id,
                        scan_type="MALWARE",
                        engine=v.engine_name,
                        engine_version=v.engine_version,
                        status=v.status,
                        details_json=v.details_json,
                        started_at=now,
                        completed_at=now,
                    )
                )

            sess.flush()
            from backend.services.background_job_service import enqueue_background_job

            enqueue_background_job(
                job_type="FILE_SCAN",
                payload={"asset_id": asset.id, "user_id": actor.id},
                run_async=False,
                session=sess,
            )

            sess.commit()
            return new_rev

    except Exception:
        sess.rollback()
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        # Retain content-addressed evidence; another transaction may share it.
        raise


def trash_file_asset(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Soft-delete a logical FileAsset to TRASH status."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    _ensure_file_asset_authoring(actor, asset, sess)

    now = utc_now()
    asset.status = "TRASH"
    asset.deleted_at = now
    asset.deleted_by_user_id = actor.id
    asset.restore_until = now + timedelta(days=30)
    asset.updated_at = now

    try:
        _stage_uploaded_file(actor, asset.course, asset, sess)
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return asset


def restore_file_asset(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Restore a soft-deleted FileAsset from TRASH to ACTIVE status."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    _ensure_file_asset_authoring(actor, asset, sess)

    now = utc_now()
    asset.status = "ACTIVE"
    asset.deleted_at = None
    asset.deleted_by_user_id = None
    asset.restore_until = None
    asset.updated_at = now

    try:
        _stage_uploaded_file(actor, asset.course, asset, sess)
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return asset


def _stage_uploaded_file(actor, course, asset, session):
    from backend.services.course_workflow_service import (
        payload_for,
        should_stage,
        working_changeset,
        write_payload,
    )

    if not should_stage(actor, course, session):
        return
    record = working_changeset(actor, course, session)
    payload = payload_for(record)
    identifier = str(asset.public_id)
    uploaded = set(payload.get("uploaded_file_assets") or [])
    uploaded.add(identifier)
    payload["uploaded_file_assets"] = sorted(uploaded)
    accepted = set(payload.get("new_file_assets") or [])
    revision = (
        session.query(FileRevision).filter_by(file_asset_id=asset.id, is_current=True).first()
    )
    scans = latest_file_scan_results(revision) if revision is not None else []
    eligible = (
        asset.status == "ACTIVE"
        and asset.deleted_at is None
        and revision is not None
        and revision.status == "ACTIVE"
        and revision.blob is not None
        and revision.blob.status == "PRESENT"
        and bool(scans)
        and all(scan.status == "PASS" for scan in scans)
        and any(scan.scan_type == "MALWARE" for scan in scans)
    )
    if eligible:
        accepted.add(identifier)
    else:
        accepted.discard(identifier)
    payload["new_file_assets"] = sorted(accepted)
    write_payload(record, payload, session)


def _course_file_memberships(course, session) -> tuple[set[str], set[str]]:
    from backend.services.course_workflow_service import payload_for

    held: set[str] = set()
    approved: set[str] = set()
    for record in (
        session.query(CourseChangeRequest)
        .filter_by(course_id=course.id, change_type="COURSE_VERSION_CHANGESET")
        .all()
    ):
        payload = payload_for(record)
        accepted = set(payload.get("new_file_assets") or [])
        held.update(accepted)
        held.update(payload.get("uploaded_file_assets") or [])
        if record.status in ("APPROVED", "APPLIED"):
            approved.update(accepted)
    return held, approved


def unapproved_course_asset_ids(course, session=None) -> set[str]:
    """Draft and discarded uploads stay private until an exact aggregate approves them."""
    from backend.models.file_import import QuestionRevisionResource
    from backend.models.question_bank import Question, QuestionRevision

    sess = session if session is not None else db.session
    held, released = _course_file_memberships(course, sess)
    blocked = held - released
    if not blocked:
        return blocked
    assets = sess.query(FileAsset).filter(FileAsset.course_id == course.id).all()
    by_id = {asset.id: str(asset.public_id) for asset in assets if str(asset.public_id) in blocked}
    live_ids = {
        row[0]
        for row in sess.query(LessonResource.file_asset_id)
        .join(Lesson, Lesson.id == LessonResource.lesson_id)
        .filter(
            LessonResource.file_asset_id.in_(by_id),
            Lesson.status == "PUBLISHED",
            Lesson.deleted_at.is_(None),
            Lesson.change_request_id.is_(None),
        )
        .all()
    }
    live_ids.update(
        row[0]
        for row in sess.query(QuestionRevisionResource.file_asset_id)
        .join(
            QuestionRevision, QuestionRevision.id == QuestionRevisionResource.question_revision_id
        )
        .join(Question, Question.id == QuestionRevision.question_id)
        .filter(
            QuestionRevisionResource.file_asset_id.in_(by_id),
            Question.course_id == course.id,
            Question.status == "ACTIVE",
            Question.change_request_id.is_(None),
            QuestionRevision.is_current == sa.true(),
        )
        .all()
    )
    live_ids.add(course.thumbnail_file_asset_id)
    return blocked - {by_id[identifier] for identifier in live_ids if identifier in by_id}


def latest_file_scan_results(revision: FileRevision) -> list[FileScanResult]:
    """Current verdict per engine/type; historical records remain append-only."""
    return revision.current_scan_results


def authorize_file_download(
    actor: User | None,
    asset_id: FileAsset | int | uuid.UUID | str,
    revision_no: int | None = None,
    session: Session | scoped_session[Any] | None = None,
    public_course_thumbnail: bool = False,
) -> tuple[FileAsset, FileBlob, FileRevision]:
    """Authorize access and retrieve physical file path for streaming/download.

    Enforces Zero-Trust & Fail-Closed rules:
    - Actor must be active and authenticated.
    - Admin has platform-wide access.
    - Managing Instructor has access to all files within their course.
    - Enrolled Student must have ACTIVE enrollment, course must be PUBLISHED,
      and any lesson to which the asset is attached must be PUBLISHED.
    - External instructors or unenrolled students are rejected with 403 Forbidden.
    - FileAsset must be ACTIVE (not TRASH or DELETED).
    - Requested or Current FileRevision must be ACTIVE and have passing scan results.
    - FileBlob must be PRESENT and physically present on disk.
    """
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    if not public_course_thumbnail and (actor is None or not actor.is_active):
        raise FileAccessDeniedError("Authentication required to download this file.")

    course = sess.get(Course, asset.course_id)
    if course is None:
        raise FileAssetNotFoundError("Parent course not found.")

    # Ma trận phân quyền Zero-Trust
    if public_course_thumbnail:
        from backend.services.course_service import get_course_thumbnail_asset

        cover = get_course_thumbnail_asset(course, session=sess)
        is_authorized = bool(
            course.status == "PUBLISHED"
            and course.deleted_at is None
            and cover is not None
            and cover.id == asset.id
        )
    elif actor is not None and (
        actor.is_admin or (actor.has_role("INSTRUCTOR") and course.owner_instructor_id == actor.id)
    ):
        is_authorized = True
    elif actor is not None and actor.has_role("STUDENT"):
        # 1. Khóa học phải ở trạng thái PUBLISHED
        if course.status != "PUBLISHED":
            raise FileAccessDeniedError("Cannot download files from an unpublished course.")

        # 2. Học viên có Enrollment ACTIVE hoặc COMPLETED trong khóa học
        enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.student_user_id == actor.id,
                Enrollment.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .first()
        )
        if enrollment is None:
            raise FileAccessDeniedError("You are not actively enrolled in this course.")
        if str(asset.public_id) in unapproved_course_asset_ids(course, sess):
            raise FileAccessDeniedError("Tệp nằm trong bản nháp chưa được phê duyệt.")

        # 3. Nếu tệp gắn với Lesson, bài học đó phải ở trạng thái PUBLISHED
        lesson_resources = (
            sess.query(LessonResource).filter(LessonResource.file_asset_id == asset.id).all()
        )
        if lesson_resources:
            attached_lessons = [sess.get(Lesson, lr.lesson_id) for lr in lesson_resources]
            published_lessons = [
                les for les in attached_lessons if les is not None and les.status == "PUBLISHED"
            ]
            if not published_lessons:
                raise FileAccessDeniedError(
                    "The lesson containing this resource is not yet published."
                )

        is_authorized = True
    else:
        is_authorized = False

    if not is_authorized:
        raise FileAccessDeniedError("You do not have permission to access this file.")

    # Fail-Closed Security Checks: resolve target revision first
    if revision_no is not None:
        revision = (
            sess.query(FileRevision)
            .filter(
                FileRevision.file_asset_id == asset.id,
                FileRevision.revision_no == revision_no,
            )
            .first()
        )
        if revision is None:
            raise FileAssetNotFoundError(f"Revision {revision_no} not found for this asset.")
    else:
        revision = asset.current_revision
        if revision is None:
            # Fallback to the latest revision (even if quarantined/rejected)
            revision = (
                sess.query(FileRevision)
                .filter(FileRevision.file_asset_id == asset.id)
                .order_by(FileRevision.revision_no.desc())
                .first()
            )

    # If revision is quarantined, rejected, or infected, fail-closed with 403 FILE_QUARANTINED
    if revision is not None:
        if revision.status == "REJECTED":
            raise FileInfectedError("File revision is rejected due to malware detection.")
        if revision.status == "QUARANTINED":
            raise FileSecurityQuarantineError(
                "File revision is quarantined pending security clearance."
            )
        for scan in latest_file_scan_results(revision):
            if scan.status == "FAIL":
                raise FileInfectedError("File security verification detected malware.")
            elif scan.status == "ERROR":
                raise FileSecurityQuarantineError("File security verification error.")

    if asset.status == "TRASH":
        raise FileAccessDeniedError("File asset is in trash and cannot be accessed.")

    if asset.status != "ACTIVE":
        raise FileSecurityQuarantineError(f"File asset is not accessible (status: {asset.status}).")

    if revision is None or revision.status not in ("ACTIVE", "REPLACED"):
        raise FileSecurityQuarantineError(
            "File revision is quarantined or not approved for access."
        )

    blob = revision.blob
    if blob is None or blob.status != "PRESENT":
        raise FileSecurityQuarantineError("Physical storage blob is quarantined or missing.")

    if not revision.scan_results or not any(
        scan.status == "PASS" and scan.scan_type == "MALWARE"
        for scan in latest_file_scan_results(revision)
    ):
        raise FileSecurityQuarantineError("File has no passing malware scan.")
    return asset, blob, revision


def get_file_for_download(
    actor: User | None,
    asset_id: FileAsset | int | uuid.UUID | str,
    revision_no: int | None = None,
    session: Session | scoped_session[Any] | None = None,
    public_course_thumbnail: bool = False,
) -> tuple[FileAsset, FileBlob, Path]:
    asset, blob, revision = authorize_file_download(
        actor, asset_id, revision_no, session, public_course_thumbnail
    )
    sess = session if session is not None else db.session
    course = sess.get(Course, asset.course_id)
    manager = actor is not None and (
        actor.has_admin_permission("COURSE_REVIEW")
        or (
            actor.has_role("INSTRUCTOR")
            and course is not None
            and course.owner_instructor_id == actor.id
        )
    )
    if (asset.is_video or blob.detected_mime_type.startswith("video/")) and not manager:
        raise FileAccessDeniedError("Learners must use protected video playback.")
    return asset, blob, materialize_authorized_blob(blob)


@with_storage_budget
def materialize_authorized_blob(blob: FileBlob) -> Path:
    """Internal bytes resolution: callers must authorize the asset before invocation."""
    if blob.status != "PRESENT" or (
        blob.storage_backend == "s3" and blob.cloud_verified_at is None
    ):
        raise FileSecurityQuarantineError("Blob is not available for protected processing.")
    storage_root = get_file_storage_root().resolve()
    if blob.storage_backend == "s3":
        storage_root = storage_root / "cache"
        storage_root.mkdir(parents=True, exist_ok=True)
        cleanup_storage_cache()
    physical_path = (storage_root / blob.storage_key).resolve()
    if not physical_path.is_relative_to(storage_root):
        raise FileAccessDeniedError("Physical file path escapes designated storage root.")
    if not physical_path.is_file():
        if blob.storage_backend != "s3":
            raise FileStorageError("Physical file blob not found on disk.")
        reserve_storage_space(storage_root, blob.size_bytes, cache=True)
        if not download_blob_from_cloud(blob.storage_key, physical_path):
            raise FileStorageError("Cloud blob is unavailable.")
        digest = hashlib.sha256()
        with physical_path.open("rb") as source:
            while chunk := source.read(64 * 1024):
                digest.update(chunk)
        if physical_path.stat().st_size != blob.size_bytes or digest.hexdigest() != blob.sha256_hex:
            physical_path.unlink(missing_ok=True)
            raise FileStorageError("Cloud blob integrity verification failed.")
    if blob.storage_backend == "s3":
        physical_path.touch()
    return physical_path


def get_file_download_ticket(
    actor: User | None,
    asset_id: FileAsset | int | uuid.UUID | str,
    revision_no: int | None = None,
    disposition: str = "attachment",
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    asset, blob, revision = authorize_file_download(actor, asset_id, revision_no, session)
    if asset.is_video or blob.detected_mime_type.startswith("video/"):
        raise FileAccessDeniedError("Raw lesson video download tickets are not allowed.")
    if disposition not in ("inline", "attachment"):
        raise FileValidationError("Invalid download disposition.")
    filename = sanitize_filename(revision.original_filename)
    if blob.storage_backend == "s3":
        if blob.cloud_verified_at is None:
            raise FileStorageError("Cloud blob has not been verified.")
        return {
            "url": create_download_url(
                blob.storage_key, filename, blob.detected_mime_type, disposition
            ),
            "expires_in": 60,
        }
    from urllib.parse import urlencode

    params = {"disposition": disposition}
    if revision_no is not None:
        params["version"] = str(revision_no)
    return {"url": f"/api/files/{asset.public_id}/download?{urlencode(params)}", "expires_in": None}


def reserve_storage_space(root: Path, incoming_size: int, cache: bool = False) -> None:
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    used = sum(
        path.stat().st_size for path in root.rglob("*") if path.is_file() and not path.is_symlink()
    )
    limit = int(
        current_app.config.get(
            "STORAGE_CACHE_MAX_BYTES" if cache else "FILE_QUARANTINE_MAX_BYTES",
            1024**3 if cache else 2 * 1024**3,
        )
    )
    if used + incoming_size > limit:
        raise FileStorageError("Temporary storage quota exceeded.")
    if shutil.disk_usage(root).free - incoming_size < int(
        current_app.config.get("FILE_MIN_FREE_BYTES", 1024**3)
    ):
        raise FileStorageError("Insufficient free disk space for safe file processing.")


def cleanup_storage_cache() -> int:
    import time

    root = (get_file_storage_root() / "cache").resolve()
    if not root.exists():
        return 0
    cutoff = time.time() - int(current_app.config.get("STORAGE_CACHE_TTL_SECONDS", 3600))
    removed = 0
    for path in root.rglob("*"):
        if (
            path.is_file()
            and not path.is_symlink()
            and path.resolve().is_relative_to(root)
            and path.stat().st_mtime < cutoff
        ):
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def _resource_authoring_target(actor: User, lesson: Lesson, course: Course, sess: Any) -> Lesson:
    from backend.services.course_workflow_service import should_stage, working_changeset
    from backend.services.lesson_service import update_lesson

    if not should_stage(actor, course, sess):
        return lesson
    target = update_lesson(actor, lesson.id, {}, session=sess)
    draft = working_changeset(actor, course, sess)
    if target.change_request_id not in (None, draft.id):
        raise FileValidationError("Lesson does not belong to the editable course draft.")
    target.change_request_id = draft.id
    sess.flush()
    return target


def attach_resource_to_lesson(
    actor: User,
    lesson_id: Lesson | int | uuid.UUID | str,
    asset_id: FileAsset | int | uuid.UUID | str,
    is_downloadable: bool = True,
    label: str | None = None,
    session: Session | scoped_session[Any] | None = None,
    commit: bool = True,
) -> LessonResource:
    """Attach a FileAsset to a Lesson as a learning resource."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise ResourceNotFoundError("Lesson not found.")

    from backend.services.course_workflow_service import ensure_course_authoring

    course = ensure_course_authoring(actor, lesson.course_id, session=sess)

    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    # Invariant: file_asset.course_id phải cùng lesson.course_id
    if asset.course_id != lesson.course_id:
        raise FileValidationError("File asset belongs to a different course than the lesson.")
    if asset.asset_type != "RESOURCE":
        raise FileValidationError("Only learning resources can be attached to a lesson.")
    lesson = _resource_authoring_target(actor, lesson, course, sess)

    existing = (
        sess.query(LessonResource)
        .filter(
            LessonResource.lesson_id == lesson.id,
            LessonResource.file_asset_id == asset.id,
        )
        .first()
    )
    if existing is not None:
        if label:
            existing.label = label
        if commit:
            try:
                sess.commit()
            except Exception:
                sess.rollback()
                raise
        else:
            sess.flush()
        return existing

    if lesson.learning_unit is not None:
        from backend.services.exceptions import LessonValidationError
        from backend.services.lesson_service import validate_lesson_media_limits

        try:
            unit = (
                sess.query(LearningUnit)
                .filter(LearningUnit.id == lesson.learning_unit_id)
                .with_hint(LearningUnit, "WITH (UPDLOCK, HOLDLOCK)", dialect_name="mssql")
                .with_for_update()
                .one()
            )
            sess.expire(unit, ["lessons"])
            validate_lesson_media_limits(
                unit,
                lesson,
                lesson.markdown_content,
                added_uploaded_video=1 if asset.is_video else 0,
                added_documents=0 if asset.is_video else 1,
            )
        except LessonValidationError as exc:
            raise FileValidationError(str(exc)) from exc

    max_pos = (
        sess.query(sa.func.max(LessonResource.position))
        .filter(LessonResource.lesson_id == lesson.id)
        .scalar()
        or 0
    )

    resource = LessonResource(
        lesson_id=lesson.id,
        file_asset_id=asset.id,
        position=max_pos + 1,
        label=label or asset.display_name,
        is_required=False,
    )
    sess.add(resource)
    try:
        if commit:
            sess.commit()
        else:
            sess.flush()
    except Exception:
        sess.rollback()
        raise

    return resource


def detach_resource_from_lesson(
    actor: User,
    lesson_id: Lesson | int | uuid.UUID | str,
    resource_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
    commit: bool = True,
) -> bool:
    """Detach a learning resource link from a Lesson."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise ResourceNotFoundError("Lesson not found.")

    from backend.services.course_workflow_service import ensure_course_authoring

    course = ensure_course_authoring(actor, lesson.course_id, session=sess)

    # Resolve resource by synthetic public_id, internal id, or asset public_id
    res: LessonResource | None = None
    all_resources = sess.query(LessonResource).filter(LessonResource.lesson_id == lesson.id).all()

    target_str = str(resource_id)
    for r in all_resources:
        if str(r.public_id) == target_str or str(r.id) == target_str:
            res = r
            break
        if r.file_asset and str(r.file_asset.public_id) == target_str:
            res = r
            break

    if res is None:
        raise ResourceNotFoundError("Lesson resource link not found.")

    target = _resource_authoring_target(actor, lesson, course, sess)
    if target.id != lesson.id:
        res = (
            sess.query(LessonResource)
            .filter_by(lesson_id=target.id, file_asset_id=res.file_asset_id)
            .first()
        )
        if res is None:
            raise ResourceNotFoundError("Lesson resource link is already absent from the draft.")

    fa_id = res.file_asset_id
    sess.delete(res)
    sess.flush()

    from backend.models.course import Lesson

    other_ref = (
        sess.query(LessonResource)
        .join(Lesson, LessonResource.lesson_id == Lesson.id)
        .filter(
            LessonResource.file_asset_id == fa_id,
            Lesson.deleted_at.is_(None),
            Lesson.status.notin_(("TRASH", "HISTORICAL")),
        )
        .first()
    )
    if not other_ref:
        fa = sess.get(FileAsset, fa_id)
        if fa and fa.asset_type not in ("COURSE_IMAGE", "QUESTION_IMAGE", "IMPORT_SOURCE"):
            fa.status = "TRASH"
            fa.deleted_at = utc_now()
            fa.deleted_by_user_id = actor.id
            fa.restore_until = utc_now() + timedelta(days=30)

    try:
        if commit:
            sess.commit()
        else:
            sess.flush()
    except Exception:
        sess.rollback()
        raise
    return True


def list_course_files(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    status: str | None = "ACTIVE",
    session: Session | scoped_session[Any] | None = None,
) -> list[FileAsset]:
    """List FileAssets belonging to a course for authorized instructors or admin."""
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    query = sess.query(FileAsset).filter(FileAsset.course_id == course.id)
    query = query.filter(FileAsset.deleted_at.is_(None))
    if status:
        query = query.filter(FileAsset.status == status)
    else:
        query = query.filter(FileAsset.status != "DELETED")

    return query.order_by(FileAsset.created_at.desc()).all()


def get_file_scan_history(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve security scan history for a FileAsset conforming to ADR-002."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    require_course_manager(actor, asset.course_id, session=sess)

    results: list[dict[str, Any]] = []
    revisions = (
        sess.query(FileRevision)
        .filter(FileRevision.file_asset_id == asset.id)
        .order_by(FileRevision.revision_no.desc())
        .all()
    )
    for rev in revisions:
        scans = (
            sess.query(FileScanResult)
            .filter(FileScanResult.file_revision_id == rev.id)
            .order_by(FileScanResult.created_at.desc())
            .all()
        )
        for scan in scans:
            sig_name: str | None = None
            details_str: str | None = None
            if scan.details_json:
                try:
                    parsed = json.loads(scan.details_json)
                    sig_name = parsed.get("signature_name")
                    details_str = parsed.get("details")
                except Exception:
                    pass

            scan_synthetic_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"backend.file_scan.{scan.id}")
            scan_time = scan.completed_at or scan.created_at
            results.append(
                {
                    "scan_id": str(scan_synthetic_uuid),
                    "revision_no": rev.revision_no,
                    "scan_type": scan.scan_type,
                    "engine": scan.engine,
                    "engine_version": scan.engine_version,
                    "status": scan.status,
                    "signature_name": sig_name,
                    "details": details_str,
                    "details_json": scan.details_json,
                    "scanned_at": scan_time.isoformat() if scan_time else None,
                    "created_at": scan.created_at.isoformat() if scan.created_at else None,
                }
            )
    return results


def _prepare_rescan_copy(source: Path, destination: Path, size_bytes: int) -> None:
    """Publish complete scanned bytes without consuming the rollback source."""
    reserve_storage_space(destination.parent, size_bytes)
    prepared = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        shutil.copyfile(source, prepared)
        os.replace(prepared, destination)
    finally:
        prepared.unlink(missing_ok=True)


def rescan_file_asset(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Rescan a FileAsset's physical bytes on-demand and update lifecycle status."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    require_course_manager(actor, asset.course_id, session=sess)

    revision = (
        sess.query(FileRevision)
        .filter(FileRevision.file_asset_id == asset.id)
        .order_by(FileRevision.revision_no.desc())
        .first()
    )
    if revision is None:
        raise FileValidationError("File asset has no revisions to rescan.")

    target_path: Path | None = None
    if revision.blob and revision.blob.status == "PRESENT":
        storage_root = get_file_storage_root()
        target_path = storage_root / revision.blob.storage_key
    elif revision.quarantine_key:
        if revision.quarantine_key.startswith("infected/"):
            target_path = get_file_infected_root() / Path(revision.quarantine_key).name
        elif revision.quarantine_key.startswith("quarantine/"):
            target_path = get_file_quarantine_root() / Path(revision.quarantine_key).name
        else:
            target_path = get_file_quarantine_root() / revision.quarantine_key

    if revision.blob and revision.blob.storage_backend == "s3":
        _, _, target_path = get_file_for_download(actor, asset, revision.revision_no, session=sess)
    if target_path is None or not target_path.exists():
        raise FileStorageError("Physical file for rescan could not be located on disk.")

    now = utc_now()
    scan_verdicts = scan_file_all_engines(target_path)
    main_verdict = scan_blob_file(target_path)

    for v in scan_verdicts:
        sess.add(
            FileScanResult(
                file_revision_id=revision.id,
                scan_type="MALWARE",
                engine=v.engine_name,
                engine_version=v.engine_version,
                status=v.status,
                details_json=v.details_json,
                started_at=now,
                completed_at=now,
            )
        )

    source_cleanup: Path | None = None
    source_isolated = any(
        target_path.resolve().is_relative_to(root.resolve())
        for root in (get_file_quarantine_root(), get_file_infected_root())
    )
    if (
        main_verdict.status == "PASS"
        and scan_verdicts
        and all(v.status == "PASS" for v in scan_verdicts)
    ):
        hasher = hashlib.sha256()
        with open(target_path, "rb") as f:
            while True:
                chunk = f.read(64 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        digest_bytes = hasher.digest()
        hex_hash = hasher.hexdigest()

        blob = sess.query(FileBlob).filter(FileBlob.sha256 == digest_bytes).first()
        if blob is None:
            storage_root = get_file_storage_root()
            ab = hex_hash[:2]
            cd = hex_hash[2:4]
            dest_dir = storage_root / "blobs" / ab / cd
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / hex_hash
            if target_path != dest_path:
                _prepare_rescan_copy(target_path, dest_path, revision.size_bytes)
                source_cleanup = target_path
            blob = FileBlob(
                sha256=digest_bytes,
                size_bytes=revision.size_bytes,
                detected_mime_type=revision.detected_mime_type or "application/octet-stream",
                storage_key=f"blobs/{ab}/{cd}/{hex_hash}",
                status="PRESENT",
                reference_count=1,
            )
            sess.add(blob)
            sess.flush()
        else:
            if revision.blob_id != blob.id:
                blob.reference_count += 1
            if target_path.exists() and source_isolated:
                source_cleanup = target_path

        for rev in asset.revisions:
            if rev.id != revision.id and (rev.is_current or rev.status == "ACTIVE"):
                rev.is_current = False
                rev.status = "REPLACED"
                rev.replaced_at = now

        revision.blob_id = blob.id
        revision.status = "ACTIVE"
        revision.is_current = True
        revision.rejection_reason = None
        revision.security_checks_completed_at = now
        revision.activated_at = now
        asset.status = "ACTIVE"

    elif main_verdict.status == "FAIL":
        infected_dir = get_file_infected_root()
        if target_path.parent.resolve() != infected_dir.resolve():
            hasher = hashlib.sha256()
            with open(target_path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
            hex_hash = hasher.hexdigest()
            infected_path = infected_dir / hex_hash
            if target_path != infected_path:
                if source_isolated:
                    _prepare_rescan_copy(target_path, infected_path, revision.size_bytes)
                    source_cleanup = target_path
                else:
                    # Preserve immediate fail-closed removal of an infected shared live blob.
                    os.replace(target_path, infected_path)
            revision.quarantine_key = f"infected/{hex_hash}"

        revision.status = "REJECTED"
        revision.is_current = False
        sig_desc = main_verdict.signature_name or "Threat detected"
        revision.rejection_reason = f"Malware detected: {sig_desc}"
        has_active = (
            sess.query(FileRevision)
            .filter(
                FileRevision.file_asset_id == asset.id,
                FileRevision.status == "ACTIVE",
                FileRevision.id != revision.id,
            )
            .count()
            > 0
        )
        if not has_active:
            asset.status = "PENDING"

    else:
        revision.status = "QUARANTINED"
        revision.is_current = False
        revision.rejection_reason = f"Scanner error: {main_verdict.details or 'Unavailable'}"
        has_active = (
            sess.query(FileRevision)
            .filter(
                FileRevision.file_asset_id == asset.id,
                FileRevision.status == "ACTIVE",
                FileRevision.id != revision.id,
            )
            .count()
            > 0
        )
        if not has_active:
            asset.status = "PENDING"

    cloud_source = None
    if (
        revision.status == "ACTIVE"
        and revision.blob is not None
        and is_cloud_storage_enabled()
        and not revision.blob.detected_mime_type.startswith("video/")
    ):
        cloud_blob = revision.blob
        cloud_source = (
            target_path
            if cloud_blob.storage_backend == "s3"
            else get_file_storage_root() / cloud_blob.storage_key
        )
        if not upload_blob_to_cloud(cloud_source, cloud_blob.storage_key):
            sess.rollback()
            raise FileStorageError("Rescanned cloud upload could not be verified.")
        cloud_blob.storage_backend = "s3"
        cloud_blob.cloud_verified_at = now

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    if source_cleanup is not None:
        source_cleanup.unlink(missing_ok=True)
    if cloud_source is not None:
        cloud_source.unlink(missing_ok=True)
    return asset


def quarantine_override(
    admin_actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    reason: str,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    sess = session if session is not None else db.session
    if not (admin_actor.is_admin and getattr(admin_actor, "is_primary_admin", False)):
        raise FileAccessDeniedError(
            "Chỉ Quản trị viên cấp cao (Primary Admin) mới có quyền "
            "giải phóng tệp khỏi diện kiểm dịch."
        )

    clean_reason = (reason or "").strip()
    if not clean_reason or len(clean_reason) < 5:
        raise FileValidationError(
            "Justification reason is required for quarantine override: "
            "Lý do giải phóng tệp kiểm dịch kiểm toán bắt buộc tối thiểu 5 ký tự."
        )

    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    revision = (
        sess.query(FileRevision)
        .filter(FileRevision.file_asset_id == asset.id)
        .order_by(FileRevision.revision_no.desc())
        .first()
    )
    if revision is None:
        raise FileValidationError("File asset has no revisions to override.")

    target_path: Path | None = None
    if revision.blob and revision.blob.status == "PRESENT":
        storage_root = get_file_storage_root()
        target_path = storage_root / revision.blob.storage_key
    elif revision.quarantine_key:
        if revision.quarantine_key.startswith("infected/"):
            target_path = get_file_infected_root() / Path(revision.quarantine_key).name
        elif revision.quarantine_key.startswith("quarantine/"):
            target_path = get_file_quarantine_root() / Path(revision.quarantine_key).name
        else:
            target_path = get_file_quarantine_root() / revision.quarantine_key

    if target_path is None or not target_path.exists():
        raise FileStorageError("Physical file could not be located on disk for override.")

    now = utc_now()
    hasher = hashlib.sha256()
    with open(target_path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    digest_bytes = hasher.digest()
    hex_hash = hasher.hexdigest()

    storage_root = get_file_storage_root()
    ab = hex_hash[:2]
    cd = hex_hash[2:4]
    dest_dir = storage_root / "blobs" / ab / cd
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / hex_hash

    if target_path != dest_path:
        os.replace(target_path, dest_path)

    blob = sess.query(FileBlob).filter(FileBlob.sha256 == digest_bytes).first()
    if blob is None:
        blob = FileBlob(
            sha256=digest_bytes,
            size_bytes=revision.size_bytes,
            detected_mime_type=revision.detected_mime_type or "application/octet-stream",
            storage_key=f"blobs/{ab}/{cd}/{hex_hash}",
            status="PRESENT",
            reference_count=1,
        )
        sess.add(blob)
        sess.flush()
    else:
        if revision.blob_id != blob.id:
            blob.reference_count += 1

    before_state = {
        "asset_status": asset.status,
        "revision_status": revision.status,
    }

    for rev in asset.revisions:
        if rev.id != revision.id and (rev.is_current or rev.status == "ACTIVE"):
            rev.is_current = False
            rev.status = "REPLACED"
            rev.replaced_at = now

    revision.blob_id = blob.id
    revision.status = "ACTIVE"
    revision.is_current = True
    revision.rejection_reason = None
    revision.security_checks_completed_at = now
    revision.activated_at = now
    asset.status = "ACTIVE"
    asset.updated_at = now

    after_state = {
        "asset_status": "ACTIVE",
        "revision_status": "ACTIVE",
    }

    scan_result = FileScanResult(
        file_revision_id=revision.id,
        scan_type="CONTENT_SECURITY",
        engine="admin_override",
        engine_version="1.0",
        status="PASS",
        details_json=json.dumps(
            {
                "override_by": str(admin_actor.public_id),
                "reason": clean_reason,
            },
            ensure_ascii=False,
        ),
        started_at=now,
        completed_at=now,
    )
    sess.add(scan_result)

    audit_entry = AuditEvent(
        actor_user_id=admin_actor.id,
        actor_roles_snapshot="ADMIN",
        action="QUARANTINE_OVERRIDE",
        target_type="FILE_ASSET",
        target_id=asset.id,
        reason=clean_reason,
        before_json=json.dumps(before_state),
        after_json=json.dumps(after_state),
        performed_as_admin=True,
        created_at=now,
    )
    sess.add(audit_entry)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return asset


# ==============================================================================
# ADR-002 Compliant Serializers (Zero Internal PK or Storage Key Leakage)
# ==============================================================================


def _serialize_file_asset(asset: FileAsset) -> dict[str, Any]:
    """Serialize FileAsset exposing only public UUIDs and safe metadata."""
    cur_rev = asset.current_revision or (asset.revisions[-1] if asset.revisions else None)
    effective_status = asset.status
    scan_status = getattr(asset, "virus_scan_status", "CLEAN")
    if asset.status in ("TRASH", "DELETED") or asset.deleted_at is not None:
        effective_status = "TRASH"
    elif cur_rev:
        if cur_rev.status == "REJECTED":
            effective_status = "INFECTED"
            scan_status = "INFECTED"
        elif cur_rev.status == "QUARANTINED":
            effective_status = "QUARANTINED"
            scan_status = "SCANNING"
        elif cur_rev.status == "ACTIVE":
            effective_status = "ACTIVE"
            scan_status = "CLEAN"

    return {
        "asset_id": str(asset.public_id),
        "course_id": str(asset.course.public_id) if asset.course else None,
        "title": asset.display_name,
        "display_name": asset.display_name,
        "filename": cur_rev.original_filename if cur_rev else asset.display_name,
        "original_filename": cur_rev.original_filename if cur_rev else asset.display_name,
        "byte_size": cur_rev.size_bytes if cur_rev else 0,
        "mime_type": (
            cur_rev.detected_mime_type or cur_rev.declared_mime_type
            if cur_rev
            else "application/octet-stream"
        ),
        "content_type": (
            cur_rev.detected_mime_type or cur_rev.declared_mime_type
            if cur_rev
            else "application/octet-stream"
        ),
        "status": effective_status,
        "asset_status": asset.status,
        "revision_status": cur_rev.status if cur_rev else asset.status,
        "virus_scan_status": scan_status,
        "current_version": cur_rev.revision_no if cur_rev else 1,
        "revision_no": cur_rev.revision_no if cur_rev else 1,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        "revisions": [
            {
                "revision_id": str(r.public_id),
                "version": r.revision_no,
                "revision_no": r.revision_no,
                "byte_size": r.size_bytes,
                "size_bytes": r.size_bytes,
                "detected_mime_type": r.detected_mime_type,
                "status": r.status,
                "created_at": r.activated_at.isoformat() if r.activated_at else None,
            }
            for r in (asset.revisions or [])
        ],
    }


def _serialize_lesson_resource(res: LessonResource) -> dict[str, Any]:
    """Serialize LessonResource with synthetic public UUIDv5 per ADR-002."""
    fa = res.file_asset
    file_asset_id = str(fa.public_id) if fa and hasattr(fa, "public_id") else None
    course_id = (
        str(fa.course.public_id)
        if fa and getattr(fa, "course", None) and hasattr(fa.course, "public_id")
        else (str(res.lesson.course.public_id) if res.lesson and res.lesson.course else "")
    )
    download_url = (
        f"/student/courses/{course_id}/files/{str(res.public_id)}/download"
        if course_id
        else f"/student/files/{file_asset_id}/download"
    )
    serialized_fa = _serialize_file_asset(fa) if fa else None
    orig_filename = (
        (serialized_fa.get("original_filename") or serialized_fa.get("filename") or res.label)
        if serialized_fa
        else (res.label or "Tài liệu bài học")
    )
    byte_sz = serialized_fa.get("byte_size", 0) if serialized_fa else 0
    mime = (
        serialized_fa.get("mime_type", "application/octet-stream")
        if serialized_fa
        else "application/octet-stream"
    )

    stream_url = f"/api/files/{file_asset_id}/stream" if file_asset_id else ""

    return {
        "resource_id": str(res.public_id),
        "asset_id": file_asset_id,
        "lesson_id": str(res.lesson.public_id) if res.lesson else None,
        "title": res.label or (fa.display_name if fa else orig_filename),
        "label": res.label,
        "filename": orig_filename,
        "byte_size": byte_sz,
        "mime_type": mime,
        "download_url": download_url,
        "file_url": stream_url,
        "stream_url": stream_url,
        "file_asset": serialized_fa,
        "position": res.position,
        "is_required": res.is_required,
        "created_at": res.created_at.isoformat() if res.created_at else None,
    }
