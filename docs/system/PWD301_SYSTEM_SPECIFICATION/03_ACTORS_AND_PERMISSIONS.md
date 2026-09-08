# Actors and Permissions

## Role composition
| User category | Required roles |
|---|---|
| Student | STUDENT |
| Instructor | STUDENT + INSTRUCTOR |
| Admin | STUDENT + INSTRUCTOR + ADMIN |

Role upgrade retains the same User and learning history.

## Permission principles
- Student may read/change only own profile/learning/attempt data unless public aggregate/catalog content.
- Instructor may manage only currently owned/assigned Course resources and current Student data in those Courses.
- Previous Instructor loses current Student-detail access after reassignment; audit retains former ownership.
- Admin has governance power but sensitive mutations require reason/audit; detailed individual Student result viewing requires a reason.
- Worker acts through narrowly scoped service operations, never as an arbitrary user.

For the full action-by-resource matrix see `authorization/02_PERMISSION_MATRIX.md`.
