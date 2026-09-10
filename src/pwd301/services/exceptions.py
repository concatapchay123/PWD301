"""Domain and service exceptions for PWD301.

Provides domain-specific exceptions for business logic, user management,
and security token verification.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base exception for all service-layer domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UserAlreadyExistsError(ServiceError):
    """Raised when an email is already registered to another user."""


class UserNotFoundError(ServiceError):
    """Raised when a requested user cannot be found."""


class InvalidEmailError(ServiceError):
    """Raised when an email address does not conform to valid structure."""


class InvalidPasswordError(ServiceError):
    """Raised when a provided password fails verification or complexity criteria."""


class AccountNotActiveError(ServiceError):
    """Raised when an operation is attempted on a suspended or inactive user."""


class InvalidTokenError(ServiceError):
    """Raised when a security token is invalid or does not exist."""


class TokenExpiredError(InvalidTokenError):
    """Raised when a security token has expired."""


class TokenAlreadyConsumedError(InvalidTokenError):
    """Raised when a single-use security token has already been consumed."""


class TokenPurposeMismatchError(InvalidTokenError):
    """Raised when a token purpose does not match the expected purpose."""


class AuthenticationError(ServiceError):
    """Base exception for all authentication errors."""


class UnauthorizedError(AuthenticationError):
    """Raised when authentication is required to access a resource."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided login credentials (email or password) are incorrect."""


class SessionExpiredError(AuthenticationError):
    """Raised when an auth session has passed its expiration time."""


class SessionRevokedError(AuthenticationError):
    """Raised when an auth session has been explicitly revoked."""


class JwtTokenInvalidError(AuthenticationError):
    """Raised when a JWT is malformed, has invalid signature, or wrong claims."""


class JwtTokenExpiredError(AuthenticationError):
    """Raised when a JWT has expired according to exp claim or grant record."""


class JwtTokenRevokedError(AuthenticationError):
    """Raised when a JWT grant has been revoked or replayed."""


class AuthVersionMismatchError(AuthenticationError):
    """Raised when a token or session auth_version does not match current user auth_version."""


class AuthorizationError(ServiceError):
    """Base exception for all authorization and access control errors."""


class ForbiddenError(AuthorizationError):
    """Raised when an authenticated user lacks required roles or resource ownership."""


class InvalidRoleAssignmentError(AuthorizationError):
    """Raised when attempting an invalid role combination or transition (violates AUTH-002)."""


class ResourceNotFoundError(ServiceError):
    """Raised when a requested resource (course, lesson, question, etc.) cannot be found."""


class CourseError(ServiceError):
    """Base exception for all course domain errors."""


class CourseAlreadyExistsError(CourseError):
    """Raised when a course with the same code or title already exists."""


class CourseNotFoundError(ResourceNotFoundError):
    """Raised when a requested course cannot be found."""


class StateViolationError(ServiceError):
    """Base exception for invalid state machine transitions or state violations."""


class CourseStateViolationError(StateViolationError, CourseError):
    """Raised when an illegal course state machine transition is attempted."""


class CourseDependencyError(CourseError):
    """Raised when an action is blocked by course prerequisite dependencies."""


class CourseValidationError(CourseError):
    """Raised when course metadata fails domain validation rules."""


class LessonError(ServiceError):
    """Base exception for all lesson domain errors."""


class LessonNotFoundError(ResourceNotFoundError, LessonError):
    """Raised when a requested lesson cannot be found."""


class LessonStateViolationError(StateViolationError, LessonError):
    """Raised when an illegal lesson state transition is attempted."""


class LessonPositionConflictError(LessonError):
    """Raised when there is a collision or inconsistency in lesson sequence positioning."""


class LessonValidationError(LessonError):
    """Raised when lesson data fails domain validation rules."""


class LessonProgressError(LessonError):
    """Raised when lesson progress tracking encounters an error or tampering."""


class EnrollmentError(ServiceError):
    """Base exception for all enrollment and prerequisite domain errors."""


class EnrollmentNotFoundError(ResourceNotFoundError, EnrollmentError):
    """Raised when a requested enrollment cannot be found."""


class EnrollmentCapacityExceededError(EnrollmentError):
    """Raised when course enrollment capacity limit has been reached."""


class EnrollmentPrerequisiteError(EnrollmentError):
    """Raised when a student has not satisfied all prerequisite courses."""


class EnrollmentStateViolationError(StateViolationError, EnrollmentError):
    """Raised when an illegal enrollment lifecycle state transition is attempted."""


class PrerequisiteCycleError(EnrollmentError):
    """Raised when adding a course prerequisite would introduce a cyclic dependency."""


class CourseNotAvailableError(EnrollmentError):
    """Raised when a course is not open or published for enrollment."""


class ValidationError(ServiceError):
    """Base exception for domain validation errors."""


class CompletionRuleError(ServiceError):
    """Base exception for all course completion rule and progress domain errors."""


class CompletionRuleNotFoundError(ResourceNotFoundError, CompletionRuleError):
    """Raised when a course completion rule cannot be found."""


class CompletionRuleValidationError(ValidationError, CompletionRuleError):
    """Raised when course completion rule configuration fails validation."""


class QuestionBankError(ServiceError):
    """Base exception for all question bank and authoring domain errors."""


class QuestionNotFoundError(ResourceNotFoundError, QuestionBankError):
    """Raised when a requested question cannot be found."""


class QuestionValidationError(ValidationError, QuestionBankError):
    """Raised when question content, structure, or choices fail domain validation."""


class QuestionStateViolationError(StateViolationError, QuestionBankError):
    """Raised when an illegal question lifecycle transition or locked-mutation is attempted."""


class QuestionRevisionNotFoundError(ResourceNotFoundError, QuestionBankError):
    """Raised when a requested question revision cannot be found."""


class QuestionRevisionConflictError(StateViolationError, QuestionBankError):
    """Raised when an operation violates revision immutability, type locking, or sequence state."""


class QuestionCorrectionError(QuestionBankError):
    """Raised when a question correction incident fails domain validation or processing rules."""


class QuestionImmutableError(QuestionBankError):
    """Raised when attempting in-place modification of an immutable or in-use question revision."""


class ConflictError(ServiceError):
    """Base exception for conflicting state, locked resource, or concurrency errors."""


class AssessmentError(ServiceError):
    """Base exception for all assessment domain errors."""


class AssessmentNotFoundError(ResourceNotFoundError, AssessmentError):
    """Raised when a requested assessment cannot be found."""


class AssessmentValidationError(ValidationError, AssessmentError):
    """Raised when assessment configuration, timings, or parameters fail domain validation."""


class AssessmentStateViolationError(StateViolationError, AssessmentError):
    """Raised when an illegal assessment lifecycle state transition is attempted."""


class AssessmentLockedError(ConflictError, AssessmentError):
    """Raised when attempting to modify frozen structure, timing, or points of an assessment."""


class AssessmentSectionNotFoundError(ResourceNotFoundError, AssessmentError):
    """Raised when a requested assessment section cannot be found."""


class BlueprintValidationError(ValidationError, AssessmentError):
    """Raised when assessment blueprint rules, constraints, or candidate pool generation fails."""


class AttemptError(ServiceError):
    """Base exception for all assessment attempt and delivery domain errors."""


class AttemptNotFoundError(ResourceNotFoundError, AttemptError):
    """Raised when a requested assessment attempt cannot be found."""


class AttemptValidationError(ValidationError, AttemptError):
    """Raised when attempt preconditions or parameters fail domain validation."""


class AttemptLimitExceededError(ConflictError, AttemptError):
    """Raised when student has reached or exceeded the allowed attempt limit."""


class AssessmentNotOpenError(ValidationError, AttemptError):
    """Raised when starting an attempt on an assessment that is not yet open or not published."""


class AssessmentClosedError(ValidationError, AttemptError):
    """Raised when starting an attempt on an assessment that has passed its close deadline."""


class ActiveAttemptExistsError(ConflictError, AttemptError):
    """Raised when a student starts an attempt while an active attempt is in progress."""


class AttemptLeaseError(ConflictError, AttemptError):
    """Raised when an attempt editing lease conflict or authorization error occurs."""


class AttemptLeaseConflictError(AttemptLeaseError):
    """Raised when editing lease token does not match or was taken over by another window."""


class AttemptLeaseExpiredError(AttemptLeaseError):
    """Raised when editing lease has expired and requires renewal or takeover."""


class AttemptExpiredError(ConflictError, AttemptError):
    """Raised when an assessment attempt has exceeded its server-authoritative deadline."""


class StaleLeaseEpochError(AttemptLeaseError):
    """Raised when an autosave payload has a stale lease_epoch."""


class StaleAnswerSequenceError(AttemptLeaseError):
    """Raised when an autosave payload has a stale client sequence."""


class SubmissionIdempotencyConflictError(ConflictError, AttemptError):
    """Raised when submitting with a different idempotency key than recorded."""


class AttemptAlreadySubmittedError(StateViolationError, AttemptError):
    """Raised when attempting an operation on an attempt that has already been submitted."""


class GradingError(ServiceError):
    """Base exception for all assessment grading domain errors."""


class ScoreReleasePolicyError(ForbiddenError, GradingError):
    """Raised when attempting to view scores before the configured release policy permits."""


class MaxPointsExceededError(ValidationError, GradingError):
    """Raised when awarded manual points exceed points_assigned or are negative."""


class AttemptNotSubmittedError(StateViolationError, GradingError):
    """Raised when grading is attempted on an attempt that has not been submitted."""


AttemptNotSubmitedError = AttemptNotSubmittedError


class RegradeError(ServiceError):
    """Base exception for all regrading engine errors."""


NotFoundError = ResourceNotFoundError


class RegradeJobNotFoundError(ResourceNotFoundError, RegradeError):
    """Raised when a requested RegradeJob cannot be found."""


class QuestionCorrectionNotFoundError(ResourceNotFoundError, RegradeError):
    """Raised when a requested QuestionCorrection cannot be found."""


class FileError(ServiceError):
    """Base exception for all file domain errors."""


class FileStorageError(FileError):
    """Raised when an underlying physical file storage I/O operation fails."""


class FileValidationError(ValidationError, FileError):
    """Raised when an uploaded file fails validation (format, dangerous extension, invalid MIME)."""


class FileSizeLimitExceededError(ValidationError, FileError):
    """Raised when an uploaded file exceeds the configured size limit (e.g. video >= 1 GB)."""


class FileAssetNotFoundError(ResourceNotFoundError, FileError):
    """Raised when a requested logical file asset cannot be found."""


class FileAccessDeniedError(ForbiddenError, FileError):
    """Raised when an actor is denied access to a file asset or physical blob."""


class FileSecurityQuarantineError(ForbiddenError, FileError):
    """Raised when accessing a quarantined or blocked file asset/blob."""


class FileInfectedError(FileSecurityQuarantineError):
    """Raised when accessing an infected file asset/blob."""


class DocumentImportError(ServiceError):
    """Base exception for all document import engine errors."""


class DocumentParsingError(DocumentImportError):
    """Raised when parsing a DOCX or PDF document fails or structure is corrupted."""


class DocumentImportJobNotFoundError(ResourceNotFoundError, DocumentImportError):
    """Raised when a requested DocumentImportJob cannot be found."""


class DocumentImportStateViolationError(StateViolationError, DocumentImportError):
    """Raised when an invalid state transition is attempted on a DocumentImportJob."""


class ImportQuestionNotFoundError(ResourceNotFoundError, DocumentImportError):
    """Raised when a requested ImportQuestion cannot be found within an import job."""


class NotificationError(ServiceError):
    """Base exception for all notification domain errors."""


class NotificationNotFoundError(ResourceNotFoundError, NotificationError):
    """Raised when a requested Notification cannot be found."""


class NotificationPreferenceError(ValidationError, NotificationError):
    """Raised when a notification preference payload or transition is invalid."""


class MandatoryNotificationOptOutError(ValidationError, NotificationError):
    """Raised when an actor attempts to disable mandatory security alerts."""


class EmailDeliveryError(ServiceError):
    """Base exception for all email delivery and queue errors."""


class EmailDeliveryNotFoundError(ResourceNotFoundError, EmailDeliveryError):
    """Raised when a requested EmailDelivery cannot be found."""


class EmailRateLimitExceededError(ServiceError):
    """Raised when outbound email dispatch exceeds the configured rate limit."""


class AuditError(ServiceError):
    """Base exception for all audit domain errors."""


class AuditPersistenceError(AuditError):
    """Raised when an append-only audit event cannot be reliably persisted.

    Triggers fail-closed abort on sensitive administrative operations.
    """


class AuditNotFoundError(ResourceNotFoundError, AuditError):
    """Raised when a requested audit log entry cannot be found."""


class AdminActionForbiddenError(ForbiddenError):
    """Raised when an administrative action violates authorization or privilege policy."""


class AIError(ServiceError):
    """Base exception for all AI and Gemini integration domain errors."""


class AIValidationError(ValidationError, AIError):
    """Raised when AI input parameters, context target, or prompt payload are invalid."""


class AIPromptInjectionError(AIValidationError):
    """Raised when suspicious prompt injection or instruction override patterns are detected."""


class AIConversationNotFoundError(ResourceNotFoundError, AIError):
    """Raised when a requested AI conversation cannot be found."""


class AIConversationExpiredError(StateViolationError, AIError):
    """Raised when an operation is attempted on an expired AI conversation session."""


class AIQuotaExceededError(AIError):
    """Raised when Gemini API quota or external AI rate limit is exceeded."""


class AIServiceUnavailableError(AIError):
    """Raised when Gemini API is unreachable, timed out, or returns 503 Service Unavailable."""


class AIDraftNotFoundError(ResourceNotFoundError, AIError):
    """Raised when a requested AI-generated question draft cannot be found."""


class BackupError(ServiceError):
    """Base exception for database backup and restore operations."""


class BackupNotFoundError(ResourceNotFoundError, BackupError):
    """Raised when a requested database backup cannot be found."""


class BackupIntegrityError(BackupError):
    """Raised when a database backup fails SHA-256 verification or structural checks."""


class RestoreForbiddenError(ForbiddenError, BackupError):
    """Raised when a database restore is unauthorized, unconfirmed, or lacks admin credentials."""


class RestoreVerificationFailedError(BackupError):
    """Raised when a backup restore drill or dry-run validation fails compatibility checks."""


class MaintenanceModeActiveError(ServiceError):
    """Raised when user access is blocked due to active scheduled system maintenance."""
