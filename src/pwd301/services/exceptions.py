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
