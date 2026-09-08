"""Domain models package for PWD301.

Aggregates and re-exports all 71 canonical domain models across 9 logical domains:
1. Identity & Auth (8 tables)
2. Course & Learning (10 tables)
3. Question Bank (5 tables)
4. Assessment Structure (6 tables)
5. Assessment Attempt & Regrading (13 tables)
6. File Storage & Document Import (10 tables)
7. AI & RAG Retrieval (8 tables)
8. Notifications & Audit (5 tables)
9. Operations & Health (6 tables)
"""

from __future__ import annotations

from pwd301.models.ai_rag import (
    AIConversation,
    AIGeneratedQuestionDraft,
    AIMessage,
    AIRequest,
    AISourceUsage,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeVersion,
)
from pwd301.models.assessment import (
    Assessment,
    AssessmentBlueprint,
    AssessmentBlueprintRule,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
    AssessmentSection,
)
from pwd301.models.attempt_regrade import (
    AssessmentAttempt,
    AssessmentResult,
    AssessmentResultHistory,
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
    AttemptChoiceSnapshot,
    AttemptQuestion,
    AttemptQuestionGrade,
    AttemptQuestionGradeHistory,
    QuestionCorrection,
    RegradeItem,
    RegradeJob,
)
from pwd301.models.course import (
    Course,
    CourseChangeRequest,
    CourseCompletionRule,
    CourseCompletionSummary,
    CoursePrerequisite,
    Enrollment,
    EnrollmentEvent,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from pwd301.models.file_import import (
    DocumentImportJob,
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    ImportDuplicateCandidate,
    ImportQuestion,
    ImportQuestionResource,
    LessonResource,
    QuestionRevisionResource,
)
from pwd301.models.identity import (
    AuthSession,
    InstructorApplication,
    JwtTokenGrant,
    Role,
    SecurityEvent,
    User,
    UserRole,
    UserSecurityToken,
)
from pwd301.models.notification_audit import (
    AuditEvent,
    EmailDelivery,
    Notification,
    NotificationEvent,
    NotificationPreference,
)
from pwd301.models.operations import (
    AnalyticsSnapshot,
    BackgroundJob,
    BackupRun,
    GradeExport,
    SystemAlert,
    SystemHealthSnapshot,
)
from pwd301.models.question_bank import (
    Question,
    QuestionProvenance,
    QuestionRevision,
    QuestionRevisionAcceptedAnswer,
    QuestionRevisionChoice,
)
from pwd301.models.types import register_sqlite_functions

__all__ = [
    # Identity & Auth
    "User",
    "Role",
    "UserRole",
    "AuthSession",
    "JwtTokenGrant",
    "UserSecurityToken",
    "InstructorApplication",
    "SecurityEvent",
    # Course & Learning
    "Course",
    "CoursePrerequisite",
    "CourseCompletionRule",
    "CourseChangeRequest",
    "Lesson",
    "Enrollment",
    "EnrollmentPeriod",
    "EnrollmentEvent",
    "LessonProgress",
    "CourseCompletionSummary",
    # Question Bank
    "Question",
    "QuestionRevision",
    "QuestionRevisionChoice",
    "QuestionRevisionAcceptedAnswer",
    "QuestionProvenance",
    # Assessment Structure
    "Assessment",
    "AssessmentSection",
    "AssessmentQuestionAssignment",
    "AssessmentBlueprint",
    "AssessmentBlueprintRule",
    "AssessmentQuestionPool",
    # Assessment Attempt & Regrading
    "AssessmentAttempt",
    "AttemptQuestion",
    "AttemptChoiceSnapshot",
    "AttemptAnswer",
    "AttemptAnswerChoice",
    "AttemptAnswerEvent",
    "AttemptQuestionGrade",
    "AttemptQuestionGradeHistory",
    "AssessmentResult",
    "AssessmentResultHistory",
    "QuestionCorrection",
    "RegradeJob",
    "RegradeItem",
    # File Storage & Import
    "FileBlob",
    "FileAsset",
    "FileRevision",
    "FileScanResult",
    "LessonResource",
    "QuestionRevisionResource",
    "DocumentImportJob",
    "ImportQuestion",
    "ImportDuplicateCandidate",
    "ImportQuestionResource",
    # AI & RAG
    "AIConversation",
    "AIMessage",
    "AIRequest",
    "AIGeneratedQuestionDraft",
    "KnowledgeDocument",
    "KnowledgeVersion",
    "KnowledgeChunk",
    "AISourceUsage",
    # Notification & Audit
    "NotificationEvent",
    "Notification",
    "NotificationPreference",
    "EmailDelivery",
    "AuditEvent",
    # Operations & Health
    "BackgroundJob",
    "SystemAlert",
    "BackupRun",
    "GradeExport",
    "AnalyticsSnapshot",
    "SystemHealthSnapshot",
    # Dialect compatibility helpers
    "register_sqlite_functions",
]
