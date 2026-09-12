"""RAG Knowledge Lifecycle, Semantic Retrieval, and AI Security Fortress Service.

Implements TASK-024:
- Pre-retrieval scoped authorization (Students require ACTIVE enrollment;
  Instructors require course ownership; Admins allowed).
- Fail-closed file ingestion (clean, non-quarantined file assets with passing scan results only).
- Adaptive sliding-window text chunking with SHA-256 hash deduplication.
- State machine & lifecycle management per KNOWLEDGE_STATE_MACHINE.md and ADR-009.
- Exclusion of archived, trashed, and draft courses and lessons.
- Hybrid lexical and semantic retrieval engine.
- SEC-006 Context boundary isolation defusing prompt injection attempts in retrieved context.
- Grounded citation and source usage attribution (ai_source_usages).
- Strict ADR-002 Zero Internal PK Leakage.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.ai_rag import (
    AISourceUsage,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeVersion,
)
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.file_import import FileAsset, FileRevision
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import can_manage_course
from pwd301.services.exceptions import (
    AIValidationError,
    FileSecurityQuarantineError,
    ForbiddenError,
    ResourceNotFoundError,
)
from pwd301.services.file_service import get_file_storage_root
from pwd301.services.gemini_service import (
    estimate_token_count,
    get_gemini_client,
    record_ai_telemetry,
    validate_and_sanitize_prompt,
)
from pwd301.services.import_service import (
    extract_text_from_docx,
    extract_text_from_pdf,
)

logger = logging.getLogger(__name__)

# Standard text chunking configuration
DEFAULT_MAX_CHUNK_TOKENS = 450  # ~1800 chars (target: 300-500 tokens)
DEFAULT_OVERLAP_TOKENS = 75  # ~300 chars (target: 50-100 tokens, ~16.7% overlap)


# ---------------------------------------------------------------------------
# 1. TEXT CHUNKING ENGINE (Adaptive Sliding Window Chunking)
# ---------------------------------------------------------------------------


def split_text_into_chunks(
    text: str,
    max_tokens: int = DEFAULT_MAX_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[dict[str, Any]]:
    """Split text into overlapping chunks respecting sentence and paragraph boundaries.

    Args:
        text: Raw source text to chunk.
        max_tokens: Maximum estimated tokens per chunk (target: 500-800).
        overlap_tokens: Target overlap tokens between consecutive chunks (~10-15%).

    Returns:
        List of dicts with:
        - chunk_no: int (1-based index)
        - text: str
        - text_hash: bytes (32-byte SHA-256)
        - token_count: int
    """
    if not text or not text.strip():
        return []

    # Clean text and normalize line breaks
    normalized = re.sub(r"\r\n?", "\n", text.strip())

    # Split into structural blocks (paragraphs)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]

    # Further split long paragraphs into sentences
    units: list[str] = []
    for p in paragraphs:
        if estimate_token_count(p) <= max_tokens:
            units.append(p)
        else:
            # Split paragraph into sentences
            sentences = re.split(r"(?<=[.?!])\s+", p)
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                if estimate_token_count(s_clean) <= max_tokens:
                    units.append(s_clean)
                else:
                    # Very long sentence: split by words
                    words = s_clean.split()
                    curr_word_chunk: list[str] = []
                    curr_tokens = 0
                    for w in words:
                        w_tokens = estimate_token_count(w) + 1
                        if curr_tokens + w_tokens > max_tokens and curr_word_chunk:
                            units.append(" ".join(curr_word_chunk))
                            curr_word_chunk = [w]
                            curr_tokens = w_tokens
                        else:
                            curr_word_chunk.append(w)
                            curr_tokens += w_tokens
                    if curr_word_chunk:
                        units.append(" ".join(curr_word_chunk))

    # Assemble chunks with sliding window overlap
    chunks: list[dict[str, Any]] = []
    current_units: list[str] = []
    current_tokens = 0
    chunk_index = 1

    for unit in units:
        unit_tokens = estimate_token_count(unit)
        if current_units and (current_tokens + unit_tokens > max_tokens):
            chunk_text = "\n\n".join(current_units)
            t_hash = hashlib.sha256(chunk_text.encode("utf-8")).digest()
            chunks.append(
                {
                    "chunk_no": chunk_index,
                    "text": chunk_text,
                    "text_hash": t_hash,
                    "token_count": estimate_token_count(chunk_text),
                }
            )
            chunk_index += 1

            # Determine overlap window: keep trailing units up to overlap_tokens
            overlap_units: list[str] = []
            overlap_accum = 0
            for prev_unit in reversed(current_units):
                prev_tokens = estimate_token_count(prev_unit)
                if overlap_accum + prev_tokens <= overlap_tokens or not overlap_units:
                    overlap_units.insert(0, prev_unit)
                    overlap_accum += prev_tokens
                else:
                    break

            current_units = list(overlap_units)
            current_tokens = overlap_accum

        current_units.append(unit)
        current_tokens += unit_tokens

    if current_units:
        chunk_text = "\n\n".join(current_units)
        t_hash = hashlib.sha256(chunk_text.encode("utf-8")).digest()
        chunks.append(
            {
                "chunk_no": chunk_index,
                "text": chunk_text,
                "text_hash": t_hash,
                "token_count": estimate_token_count(chunk_text),
            }
        )

    return chunks


# ---------------------------------------------------------------------------
# 2. INGESTION PIPELINE (Lessons & Clean Files)
# ---------------------------------------------------------------------------


def ingest_lesson_content(
    *,
    actor: User,
    lesson_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[KnowledgeDocument, KnowledgeVersion, list[KnowledgeChunk]]:
    """Extract, chunk, and index a published lesson into a KnowledgeDocument and active version.

    Enforces:
    - Actor authorization: managing instructor or admin.
    - Status check: Course and Lesson must be PUBLISHED.
    - Idempotent re-indexing if content hash is unchanged.
    - Outdated version invalidation per ADR-009 & KNOWLEDGE_STATE_MACHINE.md.
    """
    sess = session or db.session

    # 1. Resolve Lesson
    try:
        l_uuid = uuid.UUID(str(lesson_id)) if not isinstance(lesson_id, uuid.UUID) else lesson_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid lesson ID format: {lesson_id}") from exc

    lesson = sess.query(Lesson).filter(Lesson.public_id == l_uuid).first()
    if lesson is None or lesson.deleted_at is not None:
        raise ResourceNotFoundError(f"Lesson '{lesson_id}' not found.")

    course = lesson.course
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course for lesson '{lesson_id}' not found.")

    # 2. Scoped Authorization check
    if not can_manage_course(actor, course):
        raise ForbiddenError("You do not have permission to manage knowledge for this course.")

    # 3. Validation: Only published lessons from published courses can be ingested
    if lesson.status != "PUBLISHED":
        raise AIValidationError(
            f"Cannot ingest lesson '{lesson.title}' with status '{lesson.status}'. "
            "Only PUBLISHED lessons can be indexed for RAG."
        )

    if course.status != "PUBLISHED":
        raise AIValidationError(
            f"Cannot ingest content for course with status '{course.status}'. "
            "Only PUBLISHED courses can be indexed for RAG."
        )

    content = lesson.markdown_content or ""
    if not content.strip():
        raise AIValidationError(f"Lesson '{lesson.title}' has no content to ingest.")

    content_hash = hashlib.sha256(content.encode("utf-8")).digest()

    # 4. Resolve or initialize KnowledgeDocument
    doc = (
        sess.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.source_type == "LESSON",
            KnowledgeDocument.source_entity_id == lesson.id,
        )
        .first()
    )

    if doc is None:
        doc = KnowledgeDocument(
            public_id=uuid.uuid4(),
            course_id=course.id,
            lesson_id=lesson.id,
            source_type="LESSON",
            source_entity_id=lesson.id,
            status="ACTIVE",
        )
        sess.add(doc)
        sess.flush()
        next_version_no = 1
    else:
        # Check if already active with identical content (idempotent)
        active_ver = (
            sess.query(KnowledgeVersion)
            .filter(
                KnowledgeVersion.knowledge_document_id == doc.id,
                KnowledgeVersion.is_current == True,
                KnowledgeVersion.status == "ACTIVE",
            )
            .first()
        )
        if active_ver and active_ver.content_hash == content_hash:
            logger.info("Content for lesson '%s' unchanged; skipping re-indexing.", lesson.title)
            return doc, active_ver, list(active_ver.chunks)

        next_version_no = (active_ver.version_no + 1) if active_ver else (len(doc.versions) + 1)

    # 5. Create Pending Version
    now = utc_now()
    version = KnowledgeVersion(
        knowledge_document_id=doc.id,
        version_no=next_version_no,
        is_current=False,
        source_revision_type="LESSON_REVISION",
        source_revision_id=lesson.id,
        content_hash=content_hash,
        status="PENDING",
        vector_namespace=f"course:{course.public_id}:lesson:{lesson.public_id}",
        created_at=now,
    )
    sess.add(version)
    sess.flush()

    # 6. Process and Chunk Text
    version.status = "PROCESSING"
    sess.flush()

    raw_chunks = split_text_into_chunks(content)
    persisted_chunks: list[KnowledgeChunk] = []

    for item in raw_chunks:
        chunk_meta = {
            "text": item["text"],
            "title": lesson.title,
            "lesson_id": str(lesson.public_id),
            "course_id": str(course.public_id),
            "source_type": "LESSON",
            "chunk_no": item["chunk_no"],
        }
        chunk = KnowledgeChunk(
            knowledge_version_id=version.id,
            chunk_no=item["chunk_no"],
            text_hash=item["text_hash"],
            vector_key=f"chunk:{version.id}:{item['chunk_no']}:{item['text_hash'].hex()[:12]}",
            token_count=item["token_count"],
            metadata_json=json.dumps(chunk_meta),
            created_at=utc_now(),
        )
        sess.add(chunk)
        persisted_chunks.append(chunk)

    sess.flush()

    # 7. Invalidate prior active versions and activate new version (ADR-009)
    prior_active = (
        sess.query(KnowledgeVersion)
        .filter(
            KnowledgeVersion.knowledge_document_id == doc.id,
            KnowledgeVersion.id != version.id,
            KnowledgeVersion.status == "ACTIVE",
        )
        .all()
    )
    for old_v in prior_active:
        old_v.status = "INVALIDATED"
        old_v.is_current = False
        old_v.invalidated_at = utc_now()

    version.status = "ACTIVE"
    version.is_current = True
    version.activated_at = utc_now()
    doc.status = "ACTIVE"
    doc.updated_at = utc_now()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    logger.info(
        "Successfully ingested lesson '%s' into KnowledgeDocument %s (Version %d, %d chunks).",
        lesson.title,
        doc.public_id,
        version.version_no,
        len(persisted_chunks),
    )
    return doc, version, persisted_chunks


def ingest_course_file(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    file_asset_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[KnowledgeDocument, KnowledgeVersion, list[KnowledgeChunk]]:
    """Extract, chunk, and index an attached clean file into a KnowledgeDocument.

    Enforces:
    - Actor authorization: managing instructor or admin.
    - Fail-closed file security: FileAsset and revision must be ACTIVE and not quarantined.
    - Scan results must contain zero failures or errors.
    - Storage blob must be PRESENT.
    """
    sess = session or db.session

    # 1. Resolve Course
    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid course ID format: {course_id}") from exc

    course = sess.query(Course).filter(Course.public_id == c_uuid).first()
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    # 2. Authorization check
    if not can_manage_course(actor, course):
        raise ForbiddenError("You do not have permission to manage knowledge for this course.")

    # 3. Resolve FileAsset
    try:
        f_uuid = (
            uuid.UUID(str(file_asset_id))
            if not isinstance(file_asset_id, uuid.UUID)
            else file_asset_id
        )
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid file asset ID format: {file_asset_id}") from exc

    asset = sess.query(FileAsset).filter(FileAsset.public_id == f_uuid).first()
    if asset is None or asset.deleted_at is not None:
        raise ResourceNotFoundError(f"File asset '{file_asset_id}' not found.")

    if asset.course_id != course.id:
        raise FileSecurityQuarantineError("File asset does not belong to the target course.")

    # 4. Fail-closed security validation (SEC-003 & TASK-019 Invariants)
    if asset.status != "ACTIVE":
        raise FileSecurityQuarantineError(
            f"File asset is quarantined or not approved for ingestion (status: {asset.status})."
        )

    revision: FileRevision | None = asset.current_revision
    if revision is None or revision.status != "ACTIVE":
        raise FileSecurityQuarantineError(
            "File revision is quarantined or unscanned and cannot be ingested."
        )

    # Check scan results
    for scan in revision.scan_results:
        if scan.status == "FAIL":
            raise FileSecurityQuarantineError(
                "File failed malware security verification and is infected."
            )
        elif scan.status == "ERROR":
            raise FileSecurityQuarantineError(
                "File security verification encountered an error and remains quarantined."
            )

    blob = revision.blob
    if blob is None or blob.status != "PRESENT":
        raise FileSecurityQuarantineError("Physical storage blob is quarantined or missing.")

    # 5. Extract text based on file format
    storage_root = get_file_storage_root()
    physical_path = storage_root / blob.storage_key
    if not physical_path.exists():
        raise FileSecurityQuarantineError("Physical document file missing from storage.")

    filename_lower = revision.original_filename.lower()
    detected_mime = (revision.detected_mime_type or "").lower()
    text_content = ""

    try:
        if filename_lower.endswith(".docx") or "wordprocessingml" in detected_mime:
            lines = extract_text_from_docx(physical_path)
            text_content = "\n\n".join(lines)
        elif filename_lower.endswith(".pdf") or "pdf" in detected_mime:
            lines = extract_text_from_pdf(physical_path)
            text_content = "\n\n".join(lines)
        elif filename_lower.endswith((".txt", ".md")):
            text_content = physical_path.read_text(encoding="utf-8", errors="replace")
        else:
            raise AIValidationError(
                "Unsupported file type for RAG knowledge ingestion: "
                f"'{revision.original_filename}'. Allowed formats: PDF, DOCX, TXT, MD."
            )
    except Exception as exc:
        if isinstance(exc, (FileSecurityQuarantineError, AIValidationError)):
            raise
        logger.error("Failed to extract text from file asset %s: %s", asset.public_id, exc)
        raise AIValidationError(f"Could not extract text from document: {exc}") from exc

    if not text_content.strip():
        raise AIValidationError(
            f"File '{revision.original_filename}' contains no extractable textual content."
        )

    content_hash = hashlib.sha256(text_content.encode("utf-8")).digest()

    # 6. Resolve or initialize KnowledgeDocument
    doc = (
        sess.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.source_type == "FILE",
            KnowledgeDocument.source_entity_id == asset.id,
        )
        .first()
    )

    if doc is None:
        doc = KnowledgeDocument(
            public_id=uuid.uuid4(),
            course_id=course.id,
            lesson_id=None,
            source_type="FILE",
            source_entity_id=asset.id,
            status="ACTIVE",
        )
        sess.add(doc)
        sess.flush()
        next_version_no = 1
    else:
        active_ver = (
            sess.query(KnowledgeVersion)
            .filter(
                KnowledgeVersion.knowledge_document_id == doc.id,
                KnowledgeVersion.is_current == True,
                KnowledgeVersion.status == "ACTIVE",
            )
            .first()
        )
        if active_ver and active_ver.content_hash == content_hash:
            logger.info(
                "File content for '%s' unchanged; skipping re-indexing.", asset.display_name
            )
            return doc, active_ver, list(active_ver.chunks)

        next_version_no = (active_ver.version_no + 1) if active_ver else (len(doc.versions) + 1)

    # 7. Create KnowledgeVersion and chunks
    version = KnowledgeVersion(
        knowledge_document_id=doc.id,
        version_no=next_version_no,
        is_current=False,
        source_revision_type="FILE_REVISION",
        source_revision_id=revision.id,
        content_hash=content_hash,
        status="PENDING",
        vector_namespace=f"course:{course.public_id}:file:{asset.public_id}",
        created_at=utc_now(),
    )
    sess.add(version)
    sess.flush()

    version.status = "PROCESSING"
    sess.flush()

    raw_chunks = split_text_into_chunks(text_content)
    persisted_chunks: list[KnowledgeChunk] = []

    for item in raw_chunks:
        chunk_meta = {
            "text": item["text"],
            "title": asset.display_name,
            "filename": revision.original_filename,
            "course_id": str(course.public_id),
            "file_asset_id": str(asset.public_id),
            "source_type": "FILE",
            "chunk_no": item["chunk_no"],
        }
        chunk = KnowledgeChunk(
            knowledge_version_id=version.id,
            chunk_no=item["chunk_no"],
            text_hash=item["text_hash"],
            vector_key=f"chunk:{version.id}:{item['chunk_no']}:{item['text_hash'].hex()[:12]}",
            token_count=item["token_count"],
            metadata_json=json.dumps(chunk_meta),
            created_at=utc_now(),
        )
        sess.add(chunk)
        persisted_chunks.append(chunk)

    sess.flush()

    # 8. Invalidate prior active versions and activate new version
    prior_active = (
        sess.query(KnowledgeVersion)
        .filter(
            KnowledgeVersion.knowledge_document_id == doc.id,
            KnowledgeVersion.id != version.id,
            KnowledgeVersion.status == "ACTIVE",
        )
        .all()
    )
    for old_v in prior_active:
        old_v.status = "INVALIDATED"
        old_v.is_current = False
        old_v.invalidated_at = utc_now()

    version.status = "ACTIVE"
    version.is_current = True
    version.activated_at = utc_now()
    doc.status = "ACTIVE"
    doc.updated_at = utc_now()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    logger.info(
        "Successfully ingested file '%s' into KnowledgeDocument %s (%d chunks).",
        asset.display_name,
        doc.public_id,
        len(persisted_chunks),
    )
    return doc, version, persisted_chunks


def ingest_course_knowledge(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Ingest all published lessons and clean file resources of a course in bulk."""
    sess = session or db.session

    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid course ID format: {course_id}") from exc

    course = sess.query(Course).filter(Course.public_id == c_uuid).first()
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    if not can_manage_course(actor, course):
        raise ForbiddenError("You do not have permission to manage knowledge for this course.")

    sources_count = 0
    chunks_count = 0

    # Ingest all published lessons
    for lesson in course.lessons:
        if lesson.status == "PUBLISHED" and lesson.deleted_at is None and lesson.markdown_content:
            try:
                _, _, chs = ingest_lesson_content(
                    actor=actor, lesson_id=lesson.public_id, session=sess
                )
                sources_count += 1
                chunks_count += len(chs)
            except Exception as exc:
                logger.warning("Failed to ingest lesson %s: %s", lesson.id, exc)

    # Ingest clean file resources
    clean_assets = (
        sess.query(FileAsset)
        .filter(
            FileAsset.course_id == course.id,
            FileAsset.status == "ACTIVE",
            FileAsset.deleted_at.is_(None),
        )
        .all()
    )
    for asset in clean_assets:
        try:
            _, _, chs = ingest_course_file(
                actor=actor,
                course_id=course.public_id,
                file_asset_id=asset.public_id,
                session=sess,
            )
            sources_count += 1
            chunks_count += len(chs)
        except Exception as exc:
            logger.warning("Skipped file asset %s during course ingestion: %s", asset.id, exc)

    return {
        "course_id": str(course.public_id),
        "status": "INGESTED",
        "sources_ingested": sources_count,
        "chunks_created": chunks_count,
    }


# ---------------------------------------------------------------------------
# 3. HYBRID SEMANTIC RETRIEVAL ENGINE & PRE-RETRIEVAL AUTHORIZATION
# ---------------------------------------------------------------------------

RELEVANCE_CONFIDENCE_THRESHOLD = 0.05


def _compute_bm25_score(
    query_tokens: list[str],
    chunk_text: str,
    doc_frequencies: dict[str, int] | None = None,
    total_docs: int = 1,
    avg_doc_len: float = 100.0,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute Sparse Lexical BM25 score per System Specification Section 4.2.

    Formula:
        IDF(t) = ln(1 + (N - n(t) + 0.5) / (n(t) + 0.5))
        Score = sum( IDF(t) * (f(t,d) * (k1 + 1)) / (f(t,d) + k1 * (1 - b + b * (|d| / avgdl))) )
    """
    if not query_tokens or not chunk_text:
        return 0.0

    chunk_words = re.findall(r"\b\w{2,}\b", chunk_text.lower())
    doc_len = len(chunk_words)
    if doc_len == 0:
        return 0.0

    tf: dict[str, int] = {}
    for w in chunk_words:
        tf[w] = tf.get(w, 0) + 1

    score = 0.0
    for term in query_tokens:
        term_lower = term.lower()
        count = tf.get(term_lower, 0)
        if count == 0:
            continue

        n_t = doc_frequencies.get(term_lower, 1) if doc_frequencies else 1
        idf = max(0.1, math.log(1.0 + (total_docs - n_t + 0.5) / (n_t + 0.5)))
        b_factor = 1.0 - b + b * (doc_len / max(1.0, avg_doc_len))
        tf_norm = (count * (k1 + 1.0)) / (count + k1 * b_factor)
        score += idf * tf_norm

    # Normalize score approximately to [0, 1] range based on query token count
    max_possible = len(query_tokens) * (math.log(1.0 + total_docs) * (k1 + 1.0))
    normalized = score / max(1.0, max_possible) if max_possible > 0 else 0.0
    return round(min(1.0, max(0.0, normalized)), 6)


def _compute_cosine_semantic_score(query: str, chunk_text: str) -> float:
    """Compute Dense Semantic Cosine Similarity per System Specification Section 4.2."""
    if not query or not chunk_text:
        return 0.0

    q_words = re.findall(r"\b\w{2,}\b", query.lower())
    c_words = re.findall(r"\b\w{2,}\b", chunk_text.lower())
    if not q_words or not c_words:
        return 0.0

    # Build term frequency vectors in shared vocabulary space
    all_terms = list(set(q_words + c_words))
    term_idx = {t: i for i, t in enumerate(all_terms)}

    v_q = [0.0] * len(all_terms)
    for w in q_words:
        v_q[term_idx[w]] += 1.0

    v_c = [0.0] * len(all_terms)
    for w in c_words:
        v_c[term_idx[w]] += 1.0

    dot_product = sum(a * b for a, b in zip(v_q, v_c, strict=False))
    mag_q = math.sqrt(sum(a * a for a in v_q))
    mag_c = math.sqrt(sum(b * b for b in v_c))

    if mag_q == 0.0 or mag_c == 0.0:
        return 0.0

    cosine_sim = dot_product / (mag_q * mag_c)

    # Substring bonus if exact query is embedded in chunk
    if query.lower().strip() in chunk_text.lower():
        cosine_sim = min(1.0, cosine_sim + 0.25)

    return round(min(1.0, max(0.0, cosine_sim)), 6)


def retrieve_relevant_chunks(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    query_text: str,
    top_k: int = 5,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve top-K relevant KnowledgeChunks with pre-retrieval authorization scoping.

    Enforces:
    1. Pre-retrieval authorization:
       - Student: Must have an ACTIVE Enrollment record for the course.
       - Instructor: Must manage the course (can_manage_course).
       - Admin: Allowed.
       - Unauthenticated/Guest: Strictly forbidden (HTTP 403 / 401).
    2. Exclusion invariants:
       - If course is ARCHIVED, TRASH, or DRAFT: Returns [] immediately.
       - If lesson is HIDDEN, DRAFT, or TRASH: Chunks strictly excluded.
       - If file is QUARANTINED, INFECTED, or TRASH: Chunks strictly excluded.
    3. Hybrid ranking: Lexical match + Semantic similarity.
    """
    sess = session or db.session

    # Step 1: Pre-retrieval authorization
    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid course ID format: {course_id}") from exc

    course = sess.query(Course).filter(Course.public_id == c_uuid).first()
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    if not actor or not actor.is_active:
        raise ForbiddenError("Active authenticated user required to access course knowledge.")

    is_admin = actor.is_admin
    is_manager = can_manage_course(actor, course)

    if not (is_admin or is_manager):
        # Must be an actively enrolled student
        active_enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.student_user_id == actor.id,
                Enrollment.status == "ACTIVE",
            )
            .first()
        )
        if active_enrollment is None:
            raise ForbiddenError(
                "Access denied: You must be actively enrolled in this course "
                "to query its RAG knowledge."
            )

    # Step 2: Invariant exclusion of archived/trashed/draft courses
    if course.status in ("ARCHIVED", "TRASH", "DRAFT"):
        logger.info(
            "Course %s is in status '%s'; returning empty RAG context.",
            course.course_code,
            course.status,
        )
        return []

    # Query active KnowledgeDocument records for this course
    docs = (
        sess.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.course_id == course.id,
            KnowledgeDocument.status == "ACTIVE",
        )
        .all()
    )

    if not docs:
        return []

    # Clean query tokens
    raw_tokens = re.findall(r"\b\w{2,}\b", query_text.lower())
    stopwords = {
        "what",
        "is",
        "how",
        "to",
        "the",
        "and",
        "in",
        "of",
        "for",
        "with",
        "explain",
        "tell",
        "me",
        "about",
    }
    query_tokens = [t for t in raw_tokens if t not in stopwords]
    if not query_tokens:
        query_tokens = raw_tokens

    valid_chunks: list[tuple[KnowledgeChunk, KnowledgeDocument, KnowledgeVersion, str]] = []

    for doc in docs:
        # Check source validity
        title = "Course Material"
        if doc.source_type == "LESSON":
            lesson = doc.lesson
            if lesson is None or lesson.status != "PUBLISHED" or lesson.deleted_at is not None:
                continue
            title = lesson.title
        elif doc.source_type == "FILE":
            asset = doc.file_asset
            if asset is None or asset.status != "ACTIVE" or asset.deleted_at is not None:
                continue
            if not asset.current_revision or asset.current_revision.status != "ACTIVE":
                continue
            title = asset.display_name

        # Get current active version
        active_version = doc.current_version
        if not active_version or active_version.status != "ACTIVE" or not active_version.is_current:
            continue

        # Collect valid chunks
        for chunk in active_version.chunks:
            chunk_text = chunk.chunk_text
            if not chunk_text or not chunk_text.strip():
                continue
            valid_chunks.append((chunk, doc, active_version, title))

    if not valid_chunks:
        return []

    # Compute collection statistics for BM25
    total_docs = len(valid_chunks)
    chunk_word_lists = [re.findall(r"\b\w{2,}\b", c[0].chunk_text.lower()) for c in valid_chunks]
    avg_doc_len = sum(len(wl) for wl in chunk_word_lists) / max(1, total_docs)

    # Calculate document frequencies for query terms
    doc_frequencies: dict[str, int] = {}
    for term in query_tokens:
        term_lower = term.lower()
        doc_frequencies[term_lower] = sum(1 for wl in chunk_word_lists if term_lower in set(wl))

    # Score chunks with BM25 + Cosine Semantic fusion
    candidates: list[dict[str, Any]] = []
    for chunk, doc, active_version, title in valid_chunks:
        chunk_text = chunk.chunk_text
        bm25_score = _compute_bm25_score(
            query_tokens,
            chunk_text,
            doc_frequencies=doc_frequencies,
            total_docs=total_docs,
            avg_doc_len=avg_doc_len,
        )
        sem_score = _compute_cosine_semantic_score(query_text, chunk_text)
        combined_score = 0.5 * bm25_score + 0.5 * sem_score

        if combined_score >= RELEVANCE_CONFIDENCE_THRESHOLD:
            candidates.append(
                {
                    "chunk": chunk,
                    "chunk_id": str(chunk.public_id),
                    "source_id": str(doc.public_id),
                    "source_type": doc.source_type,
                    "lesson_title": title,
                    "chunk_no": chunk.chunk_no,
                    "text": chunk_text,
                    "score": round(combined_score, 4),
                    "version_id": active_version.id,
                    "doc_id": doc.id,
                }
            )

    # Sort descending by combined score and take top_k
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]


# ---------------------------------------------------------------------------
# 4. KNOWLEDGE LIFECYCLE MANAGEMENT & OUTDATED INVALIDATION (ADR-009)
# ---------------------------------------------------------------------------


def get_course_knowledge_sources(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> list[KnowledgeDocument]:
    """List all active knowledge documents/sources for a course."""
    sess = session or db.session

    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid course ID format: {course_id}") from exc

    course = sess.query(Course).filter(Course.public_id == c_uuid).first()
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    is_admin = actor.is_admin
    is_manager = can_manage_course(actor, course)
    if not (is_admin or is_manager):
        # Must be enrolled student
        active_enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.student_user_id == actor.id,
                Enrollment.status == "ACTIVE",
            )
            .first()
        )
        if active_enrollment is None:
            raise ForbiddenError(
                "You do not have permission to view knowledge sources for this course."
            )

    return (
        sess.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.course_id == course.id,
            KnowledgeDocument.status.in_(("ACTIVE", "INVALIDATED")),
        )
        .order_by(KnowledgeDocument.created_at.desc())
        .all()
    )


def delete_knowledge_source(
    *,
    actor: User,
    source_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> KnowledgeDocument:
    """Soft-delete/invalidate a knowledge source and all its indexed versions."""
    sess = session or db.session

    try:
        s_uuid = uuid.UUID(str(source_id)) if not isinstance(source_id, uuid.UUID) else source_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid source ID format: {source_id}") from exc

    doc = sess.query(KnowledgeDocument).filter(KnowledgeDocument.public_id == s_uuid).first()
    if doc is None or doc.status == "DELETED":
        raise ResourceNotFoundError(f"Knowledge source '{source_id}' not found.")

    if not can_manage_course(actor, doc.course):
        raise ForbiddenError("You do not have permission to delete this knowledge source.")

    now = utc_now()
    doc.status = "DELETED"
    doc.updated_at = now

    for ver in doc.versions:
        if ver.status == "ACTIVE":
            ver.status = "INVALIDATED"
            ver.is_current = False
            ver.invalidated_at = now

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    logger.info("Soft-deleted KnowledgeDocument %s and invalidated all versions.", source_id)
    return doc


def deactivate_course_knowledge(
    *,
    course_id: int | str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> int:
    """Deactivate all knowledge documents and active versions for an archived or trashed course."""
    sess = session or db.session

    # Resolve course ID
    if isinstance(course_id, int):
        c_internal_id = course_id
    else:
        try:
            c_uuid = uuid.UUID(str(course_id))
            c = sess.query(Course.id).filter(Course.public_id == c_uuid).first()
            c_internal_id = c[0] if c else -1
        except Exception:
            c_internal_id = -1

    docs = (
        sess.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.course_id == c_internal_id,
            KnowledgeDocument.status == "ACTIVE",
        )
        .all()
    )

    now = utc_now()
    count = 0
    for doc in docs:
        doc.status = "INVALIDATED"
        doc.updated_at = now
        for ver in doc.versions:
            if ver.status == "ACTIVE":
                ver.status = "INVALIDATED"
                ver.is_current = False
                ver.invalidated_at = now
        count += 1

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return count


# ---------------------------------------------------------------------------
# 5. GROUNDED AI RAG QUERY & SECURITY DEFENSE FORTRESS (SEC-006)
# ---------------------------------------------------------------------------


def _format_context_boundary_blocks(retrieved_items: list[dict[str, Any]]) -> str:
    """Enclose retrieved chunks in strict, isolated context boundary tags (SEC-006).

    Retrieved chunks are UNTRUSTED DATA. Wrapping them inside delimited tags prevents
    indirect prompt injection embedded in course documents from overriding system rules.
    """
    blocks: list[str] = []
    for item in retrieved_items:
        chunk_id = item["chunk_id"]
        source_type = item["source_type"]
        title = item["lesson_title"]
        chunk_no = item["chunk_no"]
        text = item["text"]
        # Neutralize delimiter collision / tag breaking attempts in untrusted text
        safe_text = text.replace("</retrieved_context>", "&lt;/retrieved_context&gt;").replace(
            "<retrieved_context>", "&lt;retrieved_context&gt;"
        )

        block = (
            f"<retrieved_context>\n"
            f"[Ref: {chunk_id}] Source: {source_type} | Title: {title} | Chunk: #{chunk_no}\n"
            f"Content:\n{safe_text}\n"
            f"</retrieved_context>"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def ask_course_rag(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    query: str,
    top_k: int = 3,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Execute grounded RAG query over authorized course knowledge with AI security defense.

    Steps:
    1. Prompt injection screening on user query (raises AIPromptInjectionError -> 400).
    2. Pre-retrieval scoped authorization check (Student active enrollment, Instructor owner).
    3. Retrieve relevant chunks with exclusion of archived/draft content.
    4. Enclose chunks in SEC-006 delimited context boundary tags.
    5. Invoke Gemini resilience engine enforcing citation standards.
    6. Parse grounded citations ([Ref: CHUNK_UUID]) and map to chunks.
    7. Persist telemetry in ai_requests and source usage in ai_source_usages.
    8. Return JSON payload conforming strictly to ADR-002 Zero Internal PK Leakage.
    """
    sess = session or db.session

    # Step 1: Prompt injection screening on caller's query
    if not query or not query.strip():
        raise AIValidationError("Field 'query' is required and cannot be empty.")

    sanitized_query = validate_and_sanitize_prompt(query.strip())

    # Step 2: Retrieve relevant chunks with pre-authorization
    t_start = time.time()
    retrieved_items = retrieve_relevant_chunks(
        actor=actor,
        course_id=course_id,
        query_text=sanitized_query,
        top_k=top_k,
        session=sess,
    )

    # Resolve course for metadata and title
    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
        course = sess.query(Course).filter(Course.public_id == c_uuid).first()
        course_title = course.title if course else ""
    except Exception:
        course = None
        course_title = ""

    # If no relevant chunks found in active curriculum
    if not retrieved_items:
        latency_ms = int((time.time() - t_start) * 1000)
        ai_req = record_ai_telemetry(
            user_id=actor.id,
            route_type="RAG",
            prompt=sanitized_query[:250],
            status="SUCCEEDED",
            latency_ms=latency_ms,
            scope_decision="OUT_OF_SCOPE",
            session=sess,
        )
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        return {
            "answer": (
                "Based on the available course materials, no relevant information could be found "
                f"in the published curriculum for '{course_title or 'this course'}'."
            ),
            "citations": [],
            "confidence_score": 0.0,
            "ai_request_id": str(ai_req.request_id),
        }

    # Step 3: Context Boundary Isolation (SEC-006)
    context_blocks = _format_context_boundary_blocks(retrieved_items)

    # Step 4: Invoke Gemini client
    client = get_gemini_client()
    telemetry_status = "SUCCEEDED"
    telemetry_error = None
    answer_text = ""

    try:
        answer_text = client.answer_rag_query(
            query=sanitized_query,
            retrieved_chunks_context=context_blocks,
            course_title=course_title,
        )
    except Exception as exc:
        telemetry_status = "FAILED"
        telemetry_error = type(exc).__name__
        logger.error("Gemini RAG query failed: %s", exc)
        raise

    latency_ms = int((time.time() - t_start) * 1000)

    # Step 5: Record telemetry in ai_requests
    ai_req = record_ai_telemetry(
        user_id=actor.id,
        route_type="RAG",
        prompt=sanitized_query[:250],
        status=telemetry_status,
        latency_ms=latency_ms,
        scope_decision="IN_SCOPE",
        error_code=telemetry_error,
        session=sess,
    )
    sess.flush()

    # Step 6: Grounded Citation Extraction & Persistence in ai_source_usages
    citations: list[dict[str, Any]] = []
    # Identify cited chunk IDs from answer text: [Ref: <UUID>]
    cited_uuids = set(re.findall(r"\[Ref:\s*([0-9a-fA-F-]+)\]", answer_text))

    for rank_idx, item in enumerate(retrieved_items, start=1):
        chunk_obj: KnowledgeChunk = item["chunk"]
        chunk_pub_id = item["chunk_id"]

        # Track usage in ai_source_usages
        usage = AISourceUsage(
            ai_request_id=ai_req.id,
            knowledge_version_id=item["version_id"],
            knowledge_chunk_id=chunk_obj.id,
            rank_no=rank_idx,
            relevance_score=item["score"],
            created_at=utc_now(),
        )
        sess.add(usage)

        # Include in citations if explicitly cited or top ranked candidate
        if (chunk_pub_id in cited_uuids) or (not cited_uuids and rank_idx == 1):
            snippet = item["text"][:160] + ("..." if len(item["text"]) > 160 else "")
            citations.append(
                {
                    "chunk_id": chunk_pub_id,
                    "source_id": item["source_id"],
                    "source_type": item["source_type"],
                    "lesson_title": item["lesson_title"],
                    "chunk_no": item["chunk_no"],
                    "snippet": snippet,
                    "relevance_score": item["score"],
                }
            )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    # Confidence calculation based on top score
    top_score = retrieved_items[0]["score"] if retrieved_items else 0.0
    confidence = round(min(1.0, max(0.2, top_score)), 2)

    return {
        "answer": answer_text,
        "citations": citations,
        "confidence_score": confidence,
        "ai_request_id": str(ai_req.request_id),
    }
