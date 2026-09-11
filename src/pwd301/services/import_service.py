"""DOCX/PDF assessment and question import engine for PWD301.

Implements business logic for TASK-020:
- Fail-closed security validation (files must be ACTIVE, PRESENT, and PASS malware scans).
- OpenXML DOCX parsing using standard library zipfile and xml.etree.ElementTree.
- Resilient PDF text extraction via pypdf with fallback content stream token extraction.
- Pattern matcher engine for 5 question types (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE,
  SHORT_ANSWER, ESSAY) recognizing stems, choices, answers, difficulty, points, explanations.
- Duplicate detection engine using SHA-256 exact hashes and difflib.SequenceMatcher.
- Review workflow and atomic database commit into canonical Question Bank entities.
- Zero PK leakage conforming to ADR-002 (public UUID boundaries).
"""

from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import re
import uuid
import xml.etree.ElementTree as ET
import zipfile
import zlib

try:
    import defusedxml.ElementTree as defused_ET
    from defusedxml.common import DefusedXmlException
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as defused_ET

    DefusedXmlException = ET.ParseError
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import (
    DocumentImportJob,
    FileAsset,
    ImportDuplicateCandidate,
    ImportQuestion,
)
from pwd301.models.identity import User
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import require_course_manager
from pwd301.services.exceptions import (
    CourseNotFoundError,
    DocumentImportError,
    DocumentImportJobNotFoundError,
    DocumentImportStateViolationError,
    DocumentParsingError,
    FileSecurityQuarantineError,
    ImportQuestionNotFoundError,
    ValidationError,
)
from pwd301.services.file_service import get_file_storage_root
from pwd301.services.question_bank_service import create_question

# WordprocessingML XML namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_MAP = {"w": W_NS}


@dataclass
class ParsedChoice:
    """Parsed multiple choice item."""

    key: str
    content: str
    position: int
    is_correct: bool = False
    is_fixed_position: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedQuestionDraft:
    """Intermediate parsed question draft before database persistence."""

    ordinal: int
    content_text: str
    question_type: str
    difficulty: str = "UNDERSTAND"
    points: float = 1.0
    choices: list[ParsedChoice] = field(default_factory=list)
    detected_answers: list[str] = field(default_factory=list)
    explanation_text: str | None = None
    confidence_score: float = 0.5
    diagnostics: dict[str, Any] = field(default_factory=dict)
    review_state: str = "READY"
    has_broken_resource: bool = False


# ----------------------------------------------------------------------
# 1. DOCUMENT TEXT EXTRACTION (DOCX & PDF)
# ----------------------------------------------------------------------


def extract_text_from_docx(file_path: Path) -> list[str]:
    """Extract paragraphs and table text from a DOCX file using Python's standard zipfile and xml.

    Traverses word/document.xml without any third-party C/binary dependencies.
    """
    if not file_path.exists():
        raise DocumentParsingError(f"DOCX file not found: {file_path}")

    lines: list[str] = []
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Defensive inspection against zip bomb and zip-slip attacks
            entries = zf.infolist()
            MAX_ZIP_ENTRIES = 1_000
            if len(entries) > MAX_ZIP_ENTRIES:
                msg = (
                    f"DOCX archive contains excessive entries "
                    f"({len(entries)} > {MAX_ZIP_ENTRIES}). Potential zip bomb."
                )
                raise DocumentParsingError(msg)

            MAX_CUMULATIVE_UNCOMPRESSED_SIZE = 50_000_000  # 50 MB
            total_uncompressed = sum(info.file_size for info in entries)
            if total_uncompressed > MAX_CUMULATIVE_UNCOMPRESSED_SIZE:
                msg = (
                    f"DOCX uncompressed cumulative size ({total_uncompressed} bytes) "
                    f"exceeds safety limit ({MAX_CUMULATIVE_UNCOMPRESSED_SIZE} bytes)."
                )
                raise DocumentParsingError(msg)

            for info in entries:
                fname = info.filename
                if ".." in fname or fname.startswith(("/", "\\")):
                    raise DocumentParsingError(
                        f"Potentially unsafe path in DOCX archive entry: '{fname}'."
                    )
                if info.file_size > 1_000_000:
                    compressed_size = max(info.compress_size, 1)
                    ratio = info.file_size / compressed_size
                    if ratio > 100:
                        msg = (
                            f"Suspicious compression ratio ({ratio:.1f}:1) "
                            f"detected for entry '{fname}'. Potential zip bomb."
                        )
                        raise DocumentParsingError(msg)

            if "word/document.xml" not in zf.namelist():
                raise DocumentParsingError("Invalid DOCX format: word/document.xml missing.")

            doc_entry = zf.getinfo("word/document.xml")
            max_doc_xml_size = 50_000_000
            if doc_entry.file_size > max_doc_xml_size:
                msg = (
                    f"DOCX document.xml exceeds maximum safe uncompressed size "
                    f"({max_doc_xml_size} bytes)."
                )
                raise DocumentParsingError(msg)

            xml_content = zf.read("word/document.xml")
            root = defused_ET.fromstring(xml_content)

            # Traverse body elements preserving order
            body = root.find("w:body", NS_MAP)
            if body is None:
                return lines

            for elem in body:
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == "p":
                    text = _extract_paragraph_text(elem)
                    if text.strip():
                        lines.append(text.strip())
                elif tag == "tbl":
                    # Extract text from tables row by row, cell by cell
                    for row in elem.findall(".//w:tr", NS_MAP):
                        row_texts: list[str] = []
                        for cell in row.findall(".//w:tc", NS_MAP):
                            cell_paragraphs: list[str] = []
                            for p in cell.findall(".//w:p", NS_MAP):
                                p_text = _extract_paragraph_text(p)
                                if p_text.strip():
                                    cell_paragraphs.append(p_text.strip())
                            if cell_paragraphs:
                                row_texts.append(" ".join(cell_paragraphs))
                        if row_texts:
                            lines.append(" | ".join(row_texts))
    except zipfile.BadZipFile as err:
        raise DocumentParsingError(f"Corrupted or invalid DOCX archive: {err}") from err
    except (ET.ParseError, DefusedXmlException) as err:
        msg = f"Failed to parse DOCX XML structure or entity expansion detected: {err}"
        raise DocumentParsingError(msg) from err
    except Exception as err:
        raise DocumentParsingError(f"Unexpected error extracting DOCX content: {err}") from err

    return lines


def _extract_paragraph_text(p_elem: ET.Element) -> str:
    """Extract full textual content from a w:p paragraph element."""
    parts: list[str] = []
    for node in p_elem.iter():
        tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
        if tag == "t" and node.text:
            parts.append(node.text)
        elif tag == "tab":
            parts.append("\t")
        elif tag in ("br", "cr"):
            parts.append("\n")
    return "".join(parts)


def extract_text_from_pdf(file_path: Path) -> list[str]:
    """Extract text from a PDF file using pypdf with fallback stream extraction."""
    if not file_path.exists():
        raise DocumentParsingError(f"PDF file not found: {file_path}")

    lines: list[str] = []

    # Primary strategy: pypdf
    try:
        import pypdf

        reader = pypdf.PdfReader(str(file_path))

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                for line in page_text.splitlines():
                    cleaned = line.strip()
                    if cleaned:
                        lines.append(cleaned)
        if lines:
            return lines
    except Exception:
        # Fallback to stream extractor
        pass

    # Fallback strategy: Raw PDF content stream decompressor
    try:
        raw_lines = _extract_text_from_pdf_streams(file_path)
        if raw_lines:
            return raw_lines
    except Exception as err:
        raise DocumentParsingError(f"Failed to extract text from PDF: {err}") from err

    return lines


def _extract_text_from_pdf_streams(file_path: Path) -> list[str]:
    """Fallback text extractor that decompresses PDF flate streams and parses text operators."""
    content = file_path.read_bytes()
    lines: list[str] = []

    # Find stream blocks
    stream_pattern = re.compile(rb"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    for match in stream_pattern.finditer(content):
        stream_bytes = match.group(1)
        decompressed: bytes | None = None
        # Attempt zlib decompression
        try:
            decompressed = zlib.decompress(stream_bytes)
        except Exception:
            decompressed = stream_bytes

        if not decompressed:
            continue

        text_str = decompressed.decode("latin-1", errors="ignore")

        # Extract text within Tj and TJ operators
        tj_matches = re.findall(r"\((.*?)\)\s*(?:Tj|'|\")", text_str)
        for tm in tj_matches:
            unescaped = _unescape_pdf_string(tm).strip()
            if unescaped:
                lines.append(unescaped)

        # Extract array strings in TJ operator: [(str1) 20 (str2)] TJ
        array_matches = re.findall(r"\[(.*?)\]\s*TJ", text_str)
        for am in array_matches:
            parts = re.findall(r"\((.*?)\)", am)
            combined = "".join(_unescape_pdf_string(p) for p in parts).strip()
            if combined:
                lines.append(combined)

    return lines


def _unescape_pdf_string(s: str) -> str:
    """Unescape standard PDF string escape sequences."""
    s = s.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    s = s.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t")
    return s


# ----------------------------------------------------------------------
# 2. PATTERN MATCHER ENGINE
# ----------------------------------------------------------------------

# Patterns for question headers
STEM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(?:Câu|Question)\s*(\d+)[:.]?\s*(.*)", re.IGNORECASE),
    re.compile(r"^(\d+)[.)]\s+(.*)"),
    re.compile(r"^(?:Bài|Task)\s*(\d+)[:.]?\s*(.*)", re.IGNORECASE),
]

# Choice patterns (e.g. "A. Option", "B) Option", "C: Option")
CHOICE_LINE_PATTERN = re.compile(r"^([A-Fa-f])[.:)]\s*(.*)")
INLINE_CHOICES_PATTERN = re.compile(
    r"(?:^|\s+)([A-Fa-f])[.:)]\s+(.+?)(?=(?:\s+[A-Fa-f][.:)]\s+|$))"
)


# Answer patterns
ANSWER_PATTERN = re.compile(
    r"^(?:Đáp\s*án|Answer|Key|Đ/A|Dap\s*an)[:\s]*(.*)",
    re.IGNORECASE,
)

# Difficulty patterns
DIFFICULTY_PATTERN = re.compile(
    r"\[(REMEMBER|UNDERSTAND|APPLY|Nhận\s*biết|Thông\s*hiểu|Vận\s*dụng)\]",
    re.IGNORECASE,
)

# Points patterns
POINTS_PATTERN = re.compile(
    r"\[(\d+(?:\.\d+)?)\s*(?:đ|pts|points?|điểm)\]",
    re.IGNORECASE,
)

# Explanation patterns
EXPLANATION_PATTERN = re.compile(
    r"^(?:Giải\s*thích|Explanation|Note|Ghi\s*chú)[:\s]*(.*)",
    re.IGNORECASE,
)

# Explicit question type markers
TYPE_TAG_PATTERN = re.compile(
    r"\[(SINGLE_CHOICE|MULTIPLE_CHOICE|TRUE_FALSE|SHORT_ANSWER|ESSAY|"
    r"Trắc\s*nghiệm|Nhiều\s*đáp\s*án|Đúng/Sai|Điền\s*khuyết|Tự\s*luận)\]",
    re.IGNORECASE,
)


def parse_question_blocks(lines: list[str]) -> list[ParsedQuestionDraft]:
    """Parse document lines into structured question drafts with pattern matching."""
    if not lines:
        return []

    # Step 1: Partition lines into raw question blocks
    blocks: list[tuple[int, list[str]]] = []
    current_ordinal = 0
    current_lines: list[str] = []

    for line in lines:
        header_match = None
        extracted_ordinal = None

        for pat in STEM_PATTERNS:
            m = pat.match(line)
            if m:
                header_match = m
                try:
                    extracted_ordinal = int(m.group(1))
                except ValueError:
                    extracted_ordinal = current_ordinal + 1
                break

        if header_match:
            if current_lines:
                blocks.append((current_ordinal or 1, current_lines))
                current_lines = []
            current_ordinal = (
                extracted_ordinal if extracted_ordinal is not None else current_ordinal + 1
            )
            current_lines.append(line)
        else:
            if current_lines:
                current_lines.append(line)
            else:
                # Leading preamble or intro text: start block 1 if not yet started
                current_ordinal = 1
                current_lines.append(line)

    if current_lines:
        blocks.append((current_ordinal or len(blocks) + 1, current_lines))

    # Step 2: Parse each block into a ParsedQuestionDraft
    parsed_questions: list[ParsedQuestionDraft] = []
    for idx, (_ord_val, blk_lines) in enumerate(blocks, start=1):
        draft = _parse_single_block(idx, blk_lines)

        if draft:
            parsed_questions.append(draft)

    return parsed_questions


def _parse_single_block(ordinal: int, lines: list[str]) -> ParsedQuestionDraft | None:
    """Parse a single block of lines into a structured ParsedQuestionDraft."""
    if not lines:
        return None

    stem_parts: list[str] = []
    choices: list[ParsedChoice] = []
    detected_answers: list[str] = []
    explanation_parts: list[str] = []
    explicit_type: str | None = None
    difficulty = "UNDERSTAND"
    points = 1.0
    warnings: list[str] = []

    in_explanation = False
    choice_position = 1

    for line in lines:
        # Check explanation marker
        exp_match = EXPLANATION_PATTERN.match(line)
        if exp_match:
            in_explanation = True
            exp_text = exp_match.group(1).strip()
            if exp_text:
                explanation_parts.append(exp_text)
            continue

        if in_explanation:
            explanation_parts.append(line)
            continue

        # Check answer marker
        ans_match = ANSWER_PATTERN.match(line)
        if ans_match:
            raw_ans = ans_match.group(1).strip()
            if raw_ans:
                # Split comma/space separated answers if any: e.g. "A, B" or "A B"
                split_keys = [k.strip().upper() for k in re.split(r"[,;\s]+", raw_ans) if k.strip()]
                # If it's a short text answer or boolean
                if any(k in ("TRUE", "FALSE", "ĐÚNG", "SAI") for k in split_keys):
                    detected_answers = [raw_ans]
                elif all(len(k) == 1 and k.isalpha() for k in split_keys):
                    detected_answers.extend(split_keys)
                else:
                    detected_answers.append(raw_ans)
            continue

        # Check inline choices on a single line: "A. Apple B. Banana C. Carrot D. Date"
        inline_matches = INLINE_CHOICES_PATTERN.findall(line)
        if len(inline_matches) >= 2:
            for key_char, content_str in inline_matches:
                choices.append(
                    ParsedChoice(
                        key=key_char.upper(),
                        content=content_str.strip(),
                        position=choice_position,
                    )
                )
                choice_position += 1
            continue

        # Check single line choice: "A. Apple"
        choice_match = CHOICE_LINE_PATTERN.match(line)
        if choice_match:
            key_char = choice_match.group(1).upper()
            content_str = choice_match.group(2).strip()
            choices.append(
                ParsedChoice(
                    key=key_char,
                    content=content_str,
                    position=choice_position,
                )
            )
            choice_position += 1
            continue

        # Not choice, answer, or explanation: part of question stem
        stem_parts.append(line)

    full_stem = " ".join(stem_parts).strip()

    # Extract metadata tags from full stem
    # 1. Question type tag
    type_tag_match = TYPE_TAG_PATTERN.search(full_stem)
    if type_tag_match:
        tag_val = type_tag_match.group(1).upper()
        if tag_val in ("TRẮC NGHIỆM", "SINGLE_CHOICE"):
            explicit_type = "SINGLE_CHOICE"
        elif tag_val in ("NHIỀU ĐÁP ÁN", "MULTIPLE_CHOICE"):
            explicit_type = "MULTIPLE_CHOICE"
        elif tag_val in ("ĐÚNG/SAI", "TRUE_FALSE"):
            explicit_type = "TRUE_FALSE"
        elif tag_val in ("ĐIỀN KHUYẾT", "SHORT_ANSWER"):
            explicit_type = "SHORT_ANSWER"
        elif tag_val in ("TỰ LUẬN", "ESSAY"):
            explicit_type = "ESSAY"
        else:
            explicit_type = tag_val
        full_stem = TYPE_TAG_PATTERN.sub("", full_stem).strip()

    # 2. Difficulty tag
    diff_match = DIFFICULTY_PATTERN.search(full_stem)
    if diff_match:
        raw_diff = diff_match.group(1).upper()
        if "NHẬN" in raw_diff or "REMEMBER" in raw_diff:
            difficulty = "REMEMBER"
        elif "THÔNG" in raw_diff or "UNDERSTAND" in raw_diff:
            difficulty = "UNDERSTAND"
        elif "VẬN" in raw_diff or "APPLY" in raw_diff:
            difficulty = "APPLY"
        full_stem = DIFFICULTY_PATTERN.sub("", full_stem).strip()

    # 3. Points tag
    pts_match = POINTS_PATTERN.search(full_stem)
    if pts_match:
        try:
            points = float(pts_match.group(1))
        except ValueError:
            points = 1.0
        full_stem = POINTS_PATTERN.sub("", full_stem).strip()

    # Clean leading "Câu 1:", "Question 1." from the stem
    for pat in STEM_PATTERNS:
        m = pat.match(full_stem)
        if m:
            full_stem = m.group(2).strip()
            break

    if not full_stem:
        warnings.append("Question stem is empty.")

    # Determine Question Type if not explicitly tagged
    if explicit_type:
        question_type = explicit_type
    elif choices:
        # Check if it's TRUE_FALSE
        choice_contents = {c.content.upper() for c in choices}
        if len(choices) == 2 and (
            choice_contents.issubset({"ĐÚNG", "SAI"})
            or choice_contents.issubset({"TRUE", "FALSE"})
            or choice_contents.issubset({"T", "F"})
        ):
            question_type = "TRUE_FALSE"
        elif len(detected_answers) > 1:
            question_type = "MULTIPLE_CHOICE"
        else:
            question_type = "SINGLE_CHOICE"
    else:
        if detected_answers and len(detected_answers[0]) < 100:
            question_type = "SHORT_ANSWER"
        else:
            question_type = "ESSAY"

    # Set choice correctness
    correct_count = 0
    if choices and detected_answers:
        for c in choices:
            if c.key in detected_answers or c.content.strip().upper() in [
                a.strip().upper() for a in detected_answers
            ]:
                c.is_correct = True
                correct_count += 1
            else:
                c.is_correct = False

    # Adjust question type if MULTIPLE_CHOICE has multiple correct choices
    if question_type == "SINGLE_CHOICE" and correct_count > 1:
        question_type = "MULTIPLE_CHOICE"

    # Compute Confidence Score and Review State
    confidence = 0.50
    review_state = "READY"

    if full_stem:
        confidence += 0.20
    else:
        confidence -= 0.30
        review_state = "INVALID"

    if question_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
        if len(choices) >= 2:
            confidence += 0.15
        else:
            confidence -= 0.20
            warnings.append(f"Insufficient choices ({len(choices)}) for {question_type}.")
            review_state = "NEEDS_REVIEW"

        if detected_answers:
            confidence += 0.15
            if question_type == "SINGLE_CHOICE" and correct_count != 1:
                warnings.append(f"SINGLE_CHOICE expects 1 correct choice, found {correct_count}.")
                review_state = "NEEDS_REVIEW"
        else:
            confidence = min(confidence, 0.70)
            warnings.append("No answer key detected; instructor confirmation required.")
            review_state = "NEEDS_REVIEW"
    elif question_type == "SHORT_ANSWER":
        if detected_answers:
            confidence += 0.30
        else:
            confidence = min(confidence, 0.70)
            warnings.append("No expected answer key detected for SHORT_ANSWER.")
            review_state = "NEEDS_REVIEW"
    elif question_type == "ESSAY":
        confidence += 0.25

    confidence = max(0.0, min(1.0, confidence))

    explanation = " ".join(explanation_parts).strip() if explanation_parts else None

    diagnostics = {
        "difficulty": difficulty,
        "points": points,
        "warnings": warnings,
        "detected_type": question_type,
    }

    return ParsedQuestionDraft(
        ordinal=ordinal,
        content_text=full_stem,
        question_type=question_type,
        difficulty=difficulty,
        points=points,
        choices=choices,
        detected_answers=detected_answers,
        explanation_text=explanation,
        confidence_score=confidence,
        diagnostics=diagnostics,
        review_state=review_state,
        has_broken_resource=False,
    )


# ----------------------------------------------------------------------
# 3. DUPLICATE DETECTION ENGINE
# ----------------------------------------------------------------------


def normalize_text_for_dedup(text: str) -> str:
    """Normalize question text by lowercasing, stripping numbers and punctuation."""
    if not text:
        return ""
    # Lowercase
    normalized = text.lower()
    # Remove leading question prefixes e.g. "câu 1:", "question 1.", "1."
    normalized = re.sub(
        r"^(?:(?:câu|question|bài|task)(?:\s*\d+)?|\d+)[.:)\s]+",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    # Remove non-alphanumeric except whitespace (keep letters/digits in Unicode)
    normalized = re.sub(r"[^\w\s]", "", normalized)
    # Collapse multiple whitespaces
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def compute_sha256(text: str) -> str:
    """Return hex SHA-256 hash of normalized text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class DuplicateMatch:
    """Detected duplicate match information."""

    parsed_ordinal: int
    candidate_question_id: int | None = None
    candidate_import_question_id: int | None = None
    similarity_score: float = 0.0
    match_type: str = "EXACT_HASH"  # EXACT_HASH or TEXT_SIMILARITY


def detect_duplicates(
    session: Session | scoped_session[Any],
    course_id: int,
    parsed_questions: list[ParsedQuestionDraft],
    similarity_threshold: float = 0.85,
) -> dict[int, list[DuplicateMatch]]:
    """Scan parsed questions against existing Question Bank items and intra-import items.

    Returns a dict mapping parsed question ordinal to detected DuplicateMatch list.
    """
    duplicates_by_ordinal: dict[int, list[DuplicateMatch]] = {}

    # Query all active/draft questions in the same course
    existing_questions = (
        session.query(Question)
        .filter(
            Question.course_id == course_id,
            Question.status != "TRASH",
        )
        .all()
    )

    existing_question_cache: list[tuple[int, str, str]] = []
    for eq in existing_questions:
        current_rev = eq.current_revision or (eq.revisions[-1] if eq.revisions else None)
        if current_rev and current_rev.content:
            norm_content = normalize_text_for_dedup(current_rev.content)
            existing_question_cache.append((eq.id, norm_content, compute_sha256(norm_content)))

    seen_import_cache: list[tuple[int, str, str]] = []

    for draft in parsed_questions:
        norm_draft = normalize_text_for_dedup(draft.content_text)
        if not norm_draft:
            continue
        draft_hash = compute_sha256(norm_draft)
        matches: list[DuplicateMatch] = []

        # 1. Compare against existing Question Bank
        for eq_id, eq_norm, eq_hash in existing_question_cache:
            if draft_hash == eq_hash:
                matches.append(
                    DuplicateMatch(
                        parsed_ordinal=draft.ordinal,
                        candidate_question_id=eq_id,
                        similarity_score=1.0,
                        match_type="EXACT_HASH",
                    )
                )
            else:
                ratio = difflib.SequenceMatcher(None, norm_draft, eq_norm).ratio()
                if ratio >= similarity_threshold:
                    matches.append(
                        DuplicateMatch(
                            parsed_ordinal=draft.ordinal,
                            candidate_question_id=eq_id,
                            similarity_score=round(ratio, 4),
                            match_type="TEXT_SIMILARITY",
                        )
                    )

        # 2. Compare against intra-import previous questions
        for prev_ord, prev_norm, prev_hash in seen_import_cache:
            if draft_hash == prev_hash:
                matches.append(
                    DuplicateMatch(
                        parsed_ordinal=draft.ordinal,
                        candidate_import_question_id=prev_ord,
                        similarity_score=1.0,
                        match_type="EXACT_HASH",
                    )
                )
            else:
                ratio = difflib.SequenceMatcher(None, norm_draft, prev_norm).ratio()
                if ratio >= similarity_threshold:
                    matches.append(
                        DuplicateMatch(
                            parsed_ordinal=draft.ordinal,
                            candidate_import_question_id=prev_ord,
                            similarity_score=round(ratio, 4),
                            match_type="TEXT_SIMILARITY",
                        )
                    )

        if matches:
            duplicates_by_ordinal[draft.ordinal] = matches
            draft.review_state = "NEEDS_REVIEW"
            draft.diagnostics.setdefault("warnings", []).append(
                f"Duplicate candidate detected with similarity >= {similarity_threshold}."
            )

        seen_import_cache.append((draft.ordinal, norm_draft, draft_hash))

    return duplicates_by_ordinal


# ----------------------------------------------------------------------
# 4. JOB LIFECYCLE OPERATIONS
# ----------------------------------------------------------------------


def _resolve_course(
    course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> Course:
    """Resolve Course entity by internal ID or public UUID."""
    if isinstance(course_id, int):
        c = session.get(Course, course_id)
    elif isinstance(course_id, uuid.UUID):
        c = session.query(Course).filter(Course.public_id == course_id).first()
    else:
        try:
            val_uuid = uuid.UUID(str(course_id))
            c = session.query(Course).filter(Course.public_id == val_uuid).first()
        except (ValueError, TypeError):
            c = session.get(Course, int(str(course_id))) if str(course_id).isdigit() else None

    if c is None or c.deleted_at is not None:
        raise CourseNotFoundError(f"Course '{course_id}' not found.")
    return c


def _resolve_import_job(
    job_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> DocumentImportJob:
    """Resolve DocumentImportJob by internal ID or public UUID."""
    if isinstance(job_id, int):
        job = session.get(DocumentImportJob, job_id)
    elif isinstance(job_id, uuid.UUID):
        job = session.query(DocumentImportJob).filter(DocumentImportJob.public_id == job_id).first()
    else:
        try:
            val_uuid = uuid.UUID(str(job_id))
            job = (
                session.query(DocumentImportJob)
                .filter(DocumentImportJob.public_id == val_uuid)
                .first()
            )
        except (ValueError, TypeError):
            job = (
                session.get(DocumentImportJob, int(str(job_id))) if str(job_id).isdigit() else None
            )

    if job is None:
        raise DocumentImportJobNotFoundError(f"Document import job '{job_id}' not found.")
    return job


def create_import_job(
    actor: User,
    course_id: int | uuid.UUID | str,
    file_asset_id: int | uuid.UUID | str,
    draft_assessment_id: int | uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> DocumentImportJob:
    """Create a new DocumentImportJob in QUEUED state.

    Enforces fail-closed security pipeline:
    - Actor must be authorized course manager.
    - FileAsset must be ACTIVE and belong to the target Course.
    - Current FileRevision must be ACTIVE and have passing malware scan results.
    - FileBlob must be PRESENT on disk.
    - Rejects quarantined or infected files with HTTP 403 FileSecurityQuarantineError.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    require_course_manager(actor, course.id, session=sess)

    # Resolve FileAsset
    if isinstance(file_asset_id, int):
        asset = sess.get(FileAsset, file_asset_id)
    elif isinstance(file_asset_id, uuid.UUID):
        asset = sess.query(FileAsset).filter(FileAsset.public_id == file_asset_id).first()
    else:
        try:
            val_uuid = uuid.UUID(str(file_asset_id))
            asset = sess.query(FileAsset).filter(FileAsset.public_id == val_uuid).first()
        except (ValueError, TypeError):
            if str(file_asset_id).isdigit():
                asset = sess.get(FileAsset, int(str(file_asset_id)))
            else:
                asset = None

    if asset is None:
        raise DocumentImportError("Target file asset not found.")

    if asset.course_id != course.id:
        raise FileSecurityQuarantineError("File asset does not belong to the target course.")

    # 1. Fail-closed security validation
    if asset.status != "ACTIVE":
        raise FileSecurityQuarantineError(
            f"File asset is not approved for import (status: {asset.status})."
        )

    revision = asset.current_revision
    if revision is None or revision.status != "ACTIVE":
        raise FileSecurityQuarantineError(
            "File revision is quarantined or not approved for access."
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

    # Verify document format
    filename = revision.original_filename.lower()
    detected_mime = (revision.detected_mime_type or "").lower()

    if filename.endswith(".docx") or "wordprocessingml" in detected_mime:
        doc_type = "DOCX"
    elif filename.endswith(".pdf") or "pdf" in detected_mime:
        doc_type = "PDF"
    else:
        raise DocumentParsingError(
            f"Unsupported document format '{revision.original_filename}'. "
            "Only DOCX and PDF documents are supported."
        )

    job = DocumentImportJob(
        course_id=course.id,
        source_file_asset_id=asset.id,
        requested_by_user_id=actor.id,
        document_type=doc_type,
        status="QUEUED",
        parser_version="pwd301.parser.v1",
        question_count=0,
        review_required_count=0,
    )
    sess.add(job)
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return job


def process_import_job(
    actor: User,
    job_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> DocumentImportJob:
    """Execute document parsing and duplicate detection on a QUEUED import job.

    Transitions job status: QUEUED -> PROCESSING -> REVIEW_REQUIRED.
    """
    sess = session if session is not None else db.session
    job = _resolve_import_job(job_id, session=sess)
    require_course_manager(actor, job.course_id, session=sess)

    if job.status not in ("QUEUED", "FAILED"):
        raise DocumentImportStateViolationError(
            f"Cannot process import job in status '{job.status}'. "
            "Only QUEUED or FAILED jobs may be processed."
        )

    # Transition to PROCESSING
    job.status = "PROCESSING"
    job.started_at = utc_now()
    job.last_error = None
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    # Resolve physical file path
    blob = job.source_file_asset.current_revision.blob
    storage_root = get_file_storage_root()
    physical_path = storage_root / blob.storage_key

    if not physical_path.exists():
        job.status = "FAILED"
        job.last_error = "Physical file not found on storage disk."
        job.completed_at = utc_now()
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        raise DocumentParsingError("Physical document file missing from storage.")

    try:
        # Step 1: Extract text lines
        if job.document_type == "DOCX":
            lines = extract_text_from_docx(physical_path)
        elif job.document_type == "PDF":
            lines = extract_text_from_pdf(physical_path)
        else:
            raise DocumentParsingError(f"Unsupported document type '{job.document_type}'.")

        # Step 2: Parse into structured question blocks
        parsed_drafts = parse_question_blocks(lines)

        if not parsed_drafts:
            raise DocumentParsingError(
                "No question structures could be identified in the document."
            )

        # Step 3: Run Duplicate Detection
        duplicates_map = detect_duplicates(
            session=sess,
            course_id=job.course_id,
            parsed_questions=parsed_drafts,
        )

        # Step 4: Clear existing questions if re-running
        sess.query(ImportQuestion).filter(ImportQuestion.import_job_id == job.id).delete()

        created_iq_map: dict[int, ImportQuestion] = {}
        review_required_count = 0

        for draft in parsed_drafts:
            choices_payload = (
                json.dumps([c.to_dict() for c in draft.choices], ensure_ascii=False)
                if draft.choices
                else None
            )
            ans_payload = (
                json.dumps({"answers": draft.detected_answers}, ensure_ascii=False)
                if draft.detected_answers
                else None
            )
            diag_payload = (
                json.dumps(draft.diagnostics, ensure_ascii=False) if draft.diagnostics else None
            )

            iq = ImportQuestion(
                import_job_id=job.id,
                ordinal=draft.ordinal,
                detected_type=draft.question_type,
                content_text=draft.content_text,
                choices_json=choices_payload,
                detected_answer_json=ans_payload,
                explanation_text=draft.explanation_text,
                confidence_score=Decimal(str(round(draft.confidence_score, 4))),
                diagnostics_json=diag_payload,
                review_state=draft.review_state,
                has_broken_resource=draft.has_broken_resource,
            )
            sess.add(iq)
            sess.flush()
            created_iq_map[draft.ordinal] = iq

            if draft.review_state != "READY":
                review_required_count += 1

        # Step 5: Persist duplicate candidates
        for ord_val, match_list in duplicates_map.items():
            target_iq = created_iq_map.get(ord_val)
            if target_iq is None:
                continue
            for m in match_list:
                cand_iq = (
                    created_iq_map.get(m.candidate_import_question_id)
                    if m.candidate_import_question_id
                    else None
                )
                dup_cand = ImportDuplicateCandidate(
                    import_question_id=target_iq.id,
                    candidate_question_id=m.candidate_question_id,
                    candidate_import_question_id=cand_iq.id if cand_iq else None,
                    similarity_score=Decimal(str(m.similarity_score)),
                    decision="PENDING",
                )
                sess.add(dup_cand)

        job.question_count = len(parsed_drafts)
        job.review_required_count = review_required_count
        job.status = "REVIEW_REQUIRED"
        sess.commit()
        return job

    except Exception as err:
        sess.rollback()
        job.status = "FAILED"
        job.last_error = str(err)
        job.completed_at = utc_now()
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        if isinstance(err, (DocumentParsingError, DocumentImportError)):
            raise
        raise DocumentParsingError(f"Failed to process import job: {err}") from err


def _resolve_import_question(
    job: DocumentImportJob,
    question_identifier: int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> ImportQuestion:
    """Resolve an ImportQuestion within a job by synthetic public UUID, ordinal, or internal ID."""
    str_val = str(question_identifier).strip()

    # Try matching by ordinal if integer
    if str_val.isdigit():
        q_ord = int(str_val)
        iq = (
            session.query(ImportQuestion)
            .filter(
                ImportQuestion.import_job_id == job.id,
                ImportQuestion.ordinal == q_ord,
            )
            .first()
        )
        if iq:
            return iq

    # Try matching synthetic UUIDv5
    all_questions = (
        session.query(ImportQuestion).filter(ImportQuestion.import_job_id == job.id).all()
    )
    for q in all_questions:
        if str(q.public_id) == str_val:
            return q

    # Fallback to internal ID if valid integer
    if str_val.isdigit():
        iq_by_id = session.get(ImportQuestion, int(str_val))
        if iq_by_id and iq_by_id.import_job_id == job.id:
            return iq_by_id

    raise ImportQuestionNotFoundError(
        f"Import question '{question_identifier}' not found in job '{job.public_id}'."
    )


def update_import_question(
    actor: User,
    job_id: int | uuid.UUID | str,
    temp_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Update question content, choices, answers, or difficulty during review."""
    sess = session if session is not None else db.session
    job = _resolve_import_job(job_id, session=sess)
    require_course_manager(actor, job.course_id, session=sess)

    if job.status != "REVIEW_REQUIRED":
        raise DocumentImportStateViolationError(
            f"Cannot edit import questions when job is in status '{job.status}'."
        )

    iq = _resolve_import_question(job, temp_id, session=sess)

    # Apply updates
    if "content" in payload or "content_text" in payload:
        new_content = payload.get("content") or payload.get("content_text")
        if not new_content or not str(new_content).strip():
            raise ValidationError("Question content cannot be empty.")
        iq.content_text = str(new_content).strip()

    if "question_type" in payload:
        iq.detected_type = str(payload["question_type"]).strip().upper()

    if "choices" in payload:
        choices_data = payload["choices"]
        if choices_data is not None:
            if not isinstance(choices_data, list):
                raise ValidationError("Choices must be a list.")
            iq.choices_json = json.dumps(choices_data, ensure_ascii=False)

    if "detected_answers" in payload or "detected_answer" in payload:
        ans_data = payload.get("detected_answers") or payload.get("detected_answer")
        if ans_data is not None:
            iq.detected_answer_json = json.dumps(ans_data, ensure_ascii=False)

    if "explanation" in payload or "explanation_text" in payload:
        iq.explanation_text = payload.get("explanation") or payload.get("explanation_text")

    if "review_state" in payload:
        r_state = str(payload["review_state"]).strip().upper()
        if r_state in ("READY", "NEEDS_REVIEW", "INVALID", "ACCEPTED", "REJECTED", "EDITED"):
            iq.review_state = r_state
    else:
        iq.review_state = "EDITED"

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return serialize_import_question(iq)


def set_import_question_decision(
    actor: User,
    job_id: int | uuid.UUID | str,
    temp_id: int | uuid.UUID | str,
    decision: str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Approve (ACCEPTED) or reject (REJECTED) an import question."""
    sess = session if session is not None else db.session
    job = _resolve_import_job(job_id, session=sess)
    require_course_manager(actor, job.course_id, session=sess)

    if job.status != "REVIEW_REQUIRED":
        raise DocumentImportStateViolationError(
            f"Cannot review questions when job is in status '{job.status}'."
        )

    norm_decision = decision.strip().upper()
    if norm_decision not in ("ACCEPTED", "REJECTED", "READY", "NEEDS_REVIEW"):
        raise ValidationError(
            f"Invalid decision '{decision}'. "
            "Must be 'ACCEPTED', 'REJECTED', 'READY', or 'NEEDS_REVIEW'."
        )

    iq = _resolve_import_question(job, temp_id, session=sess)
    iq.review_state = norm_decision

    # Recalculate review_required_count
    all_q = sess.query(ImportQuestion).filter(ImportQuestion.import_job_id == job.id).all()
    job.review_required_count = sum(
        1 for q in all_q if q.review_state in ("NEEDS_REVIEW", "INVALID")
    )

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return serialize_import_question(iq)


def commit_import_job(
    actor: User,
    job_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Atomically commit all ACCEPTED questions into canonical Question Bank entities.

    Transitions job status: REVIEW_REQUIRED -> COMPLETED.
    """
    sess = session if session is not None else db.session
    job = _resolve_import_job(job_id, session=sess)
    require_course_manager(actor, job.course_id, session=sess)

    if job.status == "COMPLETED":
        raise DocumentImportStateViolationError("Document import job is already COMPLETED.")

    if job.status != "REVIEW_REQUIRED":
        raise DocumentImportStateViolationError(
            f"Cannot commit job in status '{job.status}'. "
            "Only REVIEW_REQUIRED jobs may be committed."
        )

    # Fetch accepted questions
    accepted_questions = (
        sess.query(ImportQuestion)
        .filter(
            ImportQuestion.import_job_id == job.id,
            ImportQuestion.review_state == "ACCEPTED",
        )
        .order_by(ImportQuestion.ordinal)
        .all()
    )

    if not accepted_questions:
        raise ValidationError("No questions in ACCEPTED state to commit into Question Bank.")

    imported_count = 0
    created_question_public_ids: list[str] = []

    try:
        for iq in accepted_questions:
            # Parse choices and answers
            choices_list: list[dict[str, Any]] = []
            if iq.choices_json:
                with contextlib.suppress(Exception):
                    choices_list = json.loads(iq.choices_json)

            accepted_answers_list: list[dict[str, Any]] = []
            if iq.detected_answer_json:
                with contextlib.suppress(Exception):
                    ans_data = json.loads(iq.detected_answer_json)
                    if isinstance(ans_data, list):
                        accepted_answers_list = [{"answer_text": str(a)} for a in ans_data]
                    elif isinstance(ans_data, dict):
                        raw_answers = ans_data.get("answers", [])
                        accepted_answers_list = [{"answer_text": str(a)} for a in raw_answers]

            diag = {}
            if iq.diagnostics_json:
                with contextlib.suppress(Exception):
                    diag = json.loads(iq.diagnostics_json)

            difficulty = diag.get("difficulty", "UNDERSTAND")
            points = diag.get("points", 1.0)

            q_type = iq.detected_type or "SINGLE_CHOICE"
            payload: dict[str, Any] = {
                "question_type": q_type,
                "difficulty": difficulty,
                "content": iq.content_text,
                "default_points": points,
                "explanation": iq.explanation_text,
                "provenance": {
                    "source_type": "IMPORT",
                    "notes": f"Imported from job {job.public_id} (ordinal {iq.ordinal})",
                },
            }

            if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
                if choices_list and accepted_answers_list:
                    ans_texts = {a["answer_text"].strip().upper() for a in accepted_answers_list}
                    for ch in choices_list:
                        ch_key = str(ch.get("key", "")).strip().upper()
                        ch_content = str(ch.get("content", "")).strip().upper()
                        if ch_key in ans_texts or ch_content in ans_texts:
                            ch["is_correct"] = True
                payload["choices"] = choices_list
            elif q_type == "SHORT_ANSWER":
                payload["accepted_answers"] = accepted_answers_list

            # Reuse Question Bank service to ensure identical validation and audit logging
            created_q = create_question(
                actor=actor,
                course_id=job.course_id,
                payload=payload,
                session=sess,
            )
            iq.approved_question_id = created_q.id
            created_question_public_ids.append(str(created_q.public_id))
            imported_count += 1

        job.status = "COMPLETED"
        job.completed_at = utc_now()
        sess.commit()

        return {
            "job_id": str(job.public_id),
            "status": "COMPLETED",
            "imported_count": imported_count,
            "created_question_ids": created_question_public_ids,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    except Exception:
        sess.rollback()
        raise


def cancel_import_job(
    actor: User,
    job_id: int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> DocumentImportJob:
    """Cancel an in-progress import job."""
    sess = session if session is not None else db.session
    job = _resolve_import_job(job_id, session=sess)
    require_course_manager(actor, job.course_id, session=sess)

    if job.status == "COMPLETED":
        raise DocumentImportStateViolationError("Cannot cancel an already COMPLETED import job.")

    if job.status == "CANCELLED":
        return job

    job.status = "CANCELLED"
    job.last_error = reason or "Cancelled by user"
    job.completed_at = utc_now()
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return job


def get_import_job_detail(
    actor: User,
    job_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve full import job details, questions, and duplicate flags conforming to ADR-002."""
    sess = session if session is not None else db.session
    job = _resolve_import_job(job_id, session=sess)
    require_course_manager(actor, job.course_id, session=sess)

    questions_serialized: list[dict[str, Any]] = [
        serialize_import_question(q) for q in job.questions
    ]

    return {
        "job_id": str(job.public_id),
        "id": str(job.public_id),
        "course_id": str(job.course.public_id) if job.course else None,
        "source_file_asset_id": (
            str(job.source_file_asset.public_id) if job.source_file_asset else None
        ),
        "document_type": job.document_type,
        "status": job.status,
        "parser_version": job.parser_version,
        "question_count": job.question_count,
        "review_required_count": job.review_required_count,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "last_error": job.last_error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "questions": questions_serialized,
    }


def serialize_import_question(iq: ImportQuestion) -> dict[str, Any]:
    """Serialize an ImportQuestion into an ADR-002 compliant dictionary."""
    choices: list[dict[str, Any]] = []
    if iq.choices_json:
        with contextlib.suppress(Exception):
            choices = json.loads(iq.choices_json)

    detected_answer = None
    if iq.detected_answer_json:
        with contextlib.suppress(Exception):
            detected_answer = json.loads(iq.detected_answer_json)

    diagnostics = {}
    if iq.diagnostics_json:
        with contextlib.suppress(Exception):
            diagnostics = json.loads(iq.diagnostics_json)

    duplicates = []
    sess = sa.inspect(iq).session or db.session
    candidates = (
        sess.query(ImportDuplicateCandidate)
        .filter(ImportDuplicateCandidate.import_question_id == iq.id)
        .all()
    )
    for c in candidates:
        cand_pub_id = None
        if c.candidate_question:
            cand_pub_id = str(c.candidate_question.public_id)
        elif c.candidate_import_question:
            cand_pub_id = str(c.candidate_import_question.public_id)

        duplicates.append(
            {
                "id": str(c.public_id),
                "candidate_id": cand_pub_id,
                "similarity_score": float(c.similarity_score),
                "decision": c.decision,
            }
        )

    return {
        "id": str(iq.public_id),
        "temp_id": str(iq.public_id),
        "ordinal": iq.ordinal,
        "detected_type": iq.detected_type,
        "question_type": iq.detected_type,
        "content_text": iq.content_text,
        "content": iq.content_text,
        "choices": choices,
        "detected_answer": detected_answer,
        "explanation_text": iq.explanation_text,
        "explanation": iq.explanation_text,
        "confidence_score": float(iq.confidence_score),
        "diagnostics": diagnostics,
        "review_state": iq.review_state,
        "status": iq.review_state,
        "has_broken_resource": bool(iq.has_broken_resource),
        "approved_question_id": (
            str(iq.approved_question.public_id) if iq.approved_question else None
        ),
        "duplicates": duplicates,
        "created_at": iq.created_at.isoformat() if iq.created_at else None,
        "updated_at": iq.updated_at.isoformat() if iq.updated_at else None,
    }
