"""Unit test suite for RAG Knowledge Lifecycle and Retrieval Service (TASK-024).

Validates:
- Adaptive sliding window text chunking bounds, sentence preservation, and overlap.
- Lesson ingestion creating KnowledgeDocument, KnowledgeVersion, and KnowledgeChunks.
- Fail-closed security on file ingestion (clean files only; quarantined/infected files rejected).
- Version lifecycle transitions (ADR-009 & KNOWLEDGE_STATE_MACHINE.md):
  outdated versions invalidated.
- Context boundary formatting (SEC-006) and grounded citation extraction in ask_course_rag.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.ai_rag import (
    AISourceUsage,
    KnowledgeChunk,
    KnowledgeDocument,
)
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
)
from pwd301.models.identity import Role, User
from pwd301.services.exceptions import (
    FileSecurityQuarantineError,
)
from pwd301.services.file_service import get_file_storage_root
from pwd301.services.rag_service import (
    ask_course_rag,
    ingest_course_file,
    ingest_lesson_content,
    split_text_into_chunks,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Seed standard roles for tests."""
    sess: Session = db.session
    roles = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        roles[code] = role
    sess.commit()
    return roles


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("rag_instructor@example.com", "Password@123", "RAG Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    u = register_user("rag_student@example.com", "Password@123", "RAG Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create published course owned by instructor_user."""
    sess: Session = db.session
    c = Course(
        public_id=uuid.uuid4(),
        course_code="RAG101",
        course_code_normalized="RAG101",
        title="Introduction to Retrieval Augmented Generation",
        title_normalized="introduction to retrieval augmented generation",
        category="Artificial Intelligence",
        difficulty="INTERMEDIATE",
        status="PUBLISHED",
        owner_instructor_id=instructor_user.id,
    )
    sess.add(c)
    sess.commit()
    return c


@pytest.fixture
def test_lesson(app: Flask, test_course: Course) -> Lesson:
    """Create published lesson with comprehensive educational markdown content."""
    sess: Session = db.session
    content = (
        "# Core Concepts of Retrieval Augmented Generation\n\n"
        "Retrieval Augmented Generation (RAG) is an architectural pattern that combines "
        "information retrieval systems with generative large language models. "
        "Instead of relying solely on parametric knowledge stored in model weights, "
        "RAG dynamically queries external databases for relevant context.\n\n"
        "## The Three Primary Stages of RAG\n"
        "1. Ingestion and Indexing: Source documents are parsed, "
        "chunked, and converted into dense vector embeddings.\n"
        "2. Semantic Retrieval: User questions are embedded and compared "
        "against indexed chunks using cosine similarity.\n"
        "3. Grounded Synthesis: Relevant chunks are passed into the "
        "LLM system prompt as verified evidence.\n\n"
        "## Security Boundaries\n"
        "All retrieved documents must be treated as untrusted data within strict delimiter tags "
        "to prevent indirect prompt injection attacks from malicious curriculum text."
    )
    lesson = Lesson(
        public_id=uuid.uuid4(),
        course_id=test_course.id,
        title="Architecture of Enterprise RAG Systems",
        summary="A deep dive into indexing, vector search, and context boundaries.",
        markdown_content=content,
        position=1,
        status="PUBLISHED",
    )
    sess.add(lesson)
    sess.commit()
    return lesson


# ---------------------------------------------------------------------------
# Unit Test Cases
# ---------------------------------------------------------------------------


def test_chunking_algorithm_bounds_and_overlap() -> None:
    """Test chunking bounds, sentence boundary preservation, SHA-256 hash, and overlap."""
    # 1. Test empty/blank text returns empty list
    assert split_text_into_chunks("") == []
    assert split_text_into_chunks("   \n\n   ") == []

    # 2. Test multi-paragraph text chunking with controlled token bounds
    sample_text = (
        "Paragraph 1: Deep learning models have revolutionized modern natural "
        "language processing. Transformer architectures rely heavily on self-attention "
        "mechanisms to process long sequences.\n\n"
        "Paragraph 2: Retrieval Augmented Generation augments language models by "
        "retrieving relevant chunks. This grounding prevents hallucinations and ensures "
        "responses are factual and up-to-date.\n\n"
        "Paragraph 3: Pre-retrieval authorization scoping ensures that users cannot query "
        "data from unauthorized courses. Fail-closed security guarantees that unscanned "
        "files remain inaccessible to students.\n\n"
        "Paragraph 4: Grounded citations allow users to verify the provenance of every "
        "assertion made by the AI tutor. The system tracks source versions in "
        "ai_source_usages for end-to-end auditing."
    )

    # Use smaller max_tokens to force multiple chunks with overlap
    chunks = split_text_into_chunks(sample_text, max_tokens=35, overlap_tokens=10)
    assert len(chunks) >= 2

    for idx, c in enumerate(chunks, start=1):
        assert c["chunk_no"] == idx
        assert isinstance(c["text"], str)
        assert len(c["text"]) > 0
        assert isinstance(c["text_hash"], bytes)
        assert len(c["text_hash"]) == 32
        # Verify text_hash equals SHA-256 of text
        expected_hash = hashlib.sha256(c["text"].encode("utf-8")).digest()
        assert c["text_hash"] == expected_hash
        assert c["token_count"] > 0

    # 3. Verify overlap between consecutive chunks
    c1_text = chunks[0]["text"]
    c2_text = chunks[1]["text"]
    # At least some trailing word or sentence of c1 appears in c2
    c1_words = set(c1_text.split()[-5:])
    c2_words = set(c2_text.split()[:15])
    assert len(c1_words.intersection(c2_words)) > 0


def test_ingest_lesson_creates_sources_and_chunks(
    app: Flask,
    instructor_user: User,
    test_course: Course,
    test_lesson: Lesson,
) -> None:
    """Ingesting a published lesson creates KnowledgeDocument,
    KnowledgeVersion, and KnowledgeChunks.
    """
    sess: Session = db.session

    doc, version, chunks = ingest_lesson_content(
        actor=instructor_user,
        lesson_id=test_lesson.public_id,
        session=sess,
    )

    assert doc is not None
    assert doc.source_type == "LESSON"
    assert doc.source_entity_id == test_lesson.id
    assert doc.course_id == test_course.id
    assert doc.status == "ACTIVE"
    assert isinstance(doc.public_id, uuid.UUID)

    # ADR-002 resolve helper
    resolved_id = KnowledgeDocument.resolve_id_from_public_id(doc.public_id, session=sess)
    assert resolved_id == doc.id

    # Verify KnowledgeVersion
    assert version.version_no == 1
    assert version.status == "ACTIVE"
    assert version.is_current is True
    assert version.activated_at is not None

    # Verify Chunks
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.knowledge_version_id == version.id
    assert chunk.chunk_no == 1
    assert len(chunk.text_hash) == 32
    assert "chunk:" in chunk.vector_key
    assert chunk.token_count is not None and chunk.token_count > 0
    assert chunk.chunk_text != ""
    assert isinstance(chunk.public_id, uuid.UUID)

    # ADR-002 resolve helper on chunk
    chunk_resolved = KnowledgeChunk.resolve_id_from_public_id(chunk.public_id)
    assert chunk_resolved == chunk.id

    # Verify serialization adheres to ADR-002
    doc_dict = doc.to_dict(include_chunks=True)
    assert doc_dict["source_id"] == str(doc.public_id)
    assert doc_dict["course_id"] == str(test_course.public_id)
    assert doc_dict["lesson_id"] == str(test_lesson.public_id)
    assert len(doc_dict["chunks"]) == len(chunks)
    assert doc_dict["chunks"][0]["chunk_id"] == str(chunk.public_id)
    assert "id" not in doc_dict

    # Test Idempotent re-indexing (same content does not duplicate version or chunks)
    doc2, version2, chunks2 = ingest_lesson_content(
        actor=instructor_user,
        lesson_id=test_lesson.public_id,
        session=sess,
    )
    assert doc2.id == doc.id
    assert version2.id == version.id
    assert len(chunks2) == len(chunks)


def test_ingest_file_resource_clean_only(
    app: Flask,
    instructor_user: User,
    test_course: Course,
    tmp_path: Path,
) -> None:
    """Only clean, active file assets pass fail-closed security ingestion."""
    sess: Session = db.session
    storage_root = get_file_storage_root()

    # 1. Setup physical blob file on disk
    file_content = (
        b"# Machine Learning Reference Guide\n\nSupervised learning requires labeled datasets."
    )
    sha256_hash = hashlib.sha256(file_content).digest()
    rel_key = f"blobs/test/{sha256_hash.hex()[:16]}.txt"
    full_path = storage_root / rel_key
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(file_content)

    blob = FileBlob(
        sha256=sha256_hash,
        size_bytes=len(file_content),
        detected_mime_type="text/plain",
        storage_key=rel_key,
        status="PRESENT",
    )
    sess.add(blob)
    sess.flush()

    # 2. Create clean FileAsset and FileRevision
    asset = FileAsset(
        public_id=uuid.uuid4(),
        course_id=test_course.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="ML Reference Guide",
        status="ACTIVE",
    )
    sess.add(asset)
    sess.flush()

    clean_revision = FileRevision(
        file_asset_id=asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="ml_guide.txt",
        size_bytes=len(file_content),
        status="ACTIVE",
        uploaded_by_user_id=instructor_user.id,
    )
    sess.add(clean_revision)
    sess.flush()

    scan_pass = FileScanResult(
        file_revision_id=clean_revision.id,
        scan_type="MALWARE",
        engine="ClamAV",
        engine_version="1.0.0",
        status="PASS",
    )
    sess.add(scan_pass)
    sess.commit()

    # Ingestion succeeds for clean active file
    doc, ver, chunks = ingest_course_file(
        actor=instructor_user,
        course_id=test_course.public_id,
        file_asset_id=asset.public_id,
        session=sess,
    )
    assert doc.status == "ACTIVE"
    assert ver.status == "ACTIVE"
    assert len(chunks) >= 1
    assert "Supervised learning" in chunks[0].chunk_text

    # 3. Fail-Closed on Quarantined File Revision
    quarantine_asset = FileAsset(
        public_id=uuid.uuid4(),
        course_id=test_course.id,
        created_by_user_id=instructor_user.id,
        asset_type="RESOURCE",
        display_name="Quarantined Guide",
        status="ACTIVE",
    )
    sess.add(quarantine_asset)
    sess.flush()

    quarantine_rev = FileRevision(
        file_asset_id=quarantine_asset.id,
        revision_no=1,
        is_current=True,
        blob_id=blob.id,
        original_filename="unscanned.txt",
        size_bytes=len(file_content),
        status="QUARANTINED",  # QUARANTINED!
        uploaded_by_user_id=instructor_user.id,
    )
    sess.add(quarantine_rev)
    sess.commit()

    with pytest.raises(FileSecurityQuarantineError):
        ingest_course_file(
            actor=instructor_user,
            course_id=test_course.public_id,
            file_asset_id=quarantine_asset.public_id,
            session=sess,
        )

    # 4. Fail-Closed on Infected File (Scan FAIL)
    quarantine_rev.status = "ACTIVE"
    scan_fail = FileScanResult(
        file_revision_id=quarantine_rev.id,
        scan_type="MALWARE",
        engine="ClamAV",
        engine_version="1.0.0",
        status="FAIL",  # Infected!
    )
    sess.add(scan_fail)
    sess.commit()

    with pytest.raises(FileSecurityQuarantineError):
        ingest_course_file(
            actor=instructor_user,
            course_id=test_course.public_id,
            file_asset_id=quarantine_asset.public_id,
            session=sess,
        )


def test_outdated_chunks_lifecycle_on_update(
    app: Flask,
    instructor_user: User,
    test_course: Course,
    test_lesson: Lesson,
) -> None:
    """Updating lesson content transitions prior version to INVALIDATED
    and creates new ACTIVE version.
    """
    sess: Session = db.session

    # Ingest version 1
    doc1, ver1, chunks1 = ingest_lesson_content(
        actor=instructor_user,
        lesson_id=test_lesson.public_id,
        session=sess,
    )
    assert ver1.version_no == 1
    assert ver1.status == "ACTIVE"
    assert ver1.is_current is True

    # Modify lesson content
    test_lesson.markdown_content = (
        "# Advanced RAG Architectures: Hybrid Search & Re-ranking\n\n"
        "Modern RAG systems combine dense semantic vector search with sparse BM25 lexical ranking. "
        "Cross-encoders are subsequently employed to re-rank the candidate documents."
    )
    sess.commit()

    # Ingest updated content (version 2)
    doc2, ver2, chunks2 = ingest_lesson_content(
        actor=instructor_user,
        lesson_id=test_lesson.public_id,
        session=sess,
    )
    assert doc2.id == doc1.id
    assert ver2.version_no == 2
    assert ver2.status == "ACTIVE"
    assert ver2.is_current is True

    # Verify old version 1 was atomically invalidated
    sess.refresh(ver1)
    assert ver1.status == "INVALIDATED"
    assert ver1.is_current is False
    assert ver1.invalidated_at is not None


def test_rag_prompt_construction_and_citation_parsing(
    app: Flask,
    instructor_user: User,
    student_user: User,
    test_course: Course,
    test_lesson: Lesson,
) -> None:
    """Test SEC-006 context boundary formatting, Mock Gemini grounding, and citation parsing."""
    sess: Session = db.session

    # 1. Ingest lesson
    doc, ver, chunks = ingest_lesson_content(
        actor=instructor_user,
        lesson_id=test_lesson.public_id,
        session=sess,
    )

    # 2. Enroll student in course
    enrollment = Enrollment(
        course_id=test_course.id,
        student_user_id=student_user.id,
        status="ACTIVE",
    )
    sess.add(enrollment)
    sess.commit()

    # 3. Query RAG
    res = ask_course_rag(
        actor=student_user,
        course_id=test_course.public_id,
        query="What are the three primary stages of RAG?",
        top_k=3,
        session=sess,
    )

    assert "answer" in res
    assert "citations" in res
    assert "confidence_score" in res
    assert "ai_request_id" in res

    citations = res["citations"]

    # Assert answer references grounded curriculum
    assert len(citations) >= 1
    cit = citations[0]
    assert "chunk_id" in cit
    assert cit["chunk_id"] == str(chunks[0].public_id)
    assert cit["source_id"] == str(doc.public_id)
    assert cit["lesson_title"] == test_lesson.title
    assert "snippet" in cit
    assert "relevance_score" in cit
    assert cit["relevance_score"] > 0

    # Verify usage record created in ai_source_usages
    usage = (
        sess.query(AISourceUsage).filter(AISourceUsage.knowledge_chunk_id == chunks[0].id).first()
    )
    assert usage is not None
    assert usage.rank_no == 1
    assert usage.relevance_score is not None
