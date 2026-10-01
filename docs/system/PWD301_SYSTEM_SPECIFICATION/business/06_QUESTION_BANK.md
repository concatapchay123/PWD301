# Question Bank & Assessment Questions (Decommissioned Standalone Hub)

> [!NOTE]
> Phân hệ Ngân hàng câu hỏi độc lập (Question Bank Hub) đã được gỡ bỏ khỏi giao diện và API độc lập. Toàn bộ câu hỏi được biên soạn và quản lý trực tiếp trong Bài thi / Khảo thí (Exam Studio).

## Confirmed rules
- Câu hỏi khảo thí gắn liền với bài thi (`assessments`) và khóa học (`courses`).
- Hỗ trợ 4 định dạng câu hỏi: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`.
- Phân loại 4 mức độ tư duy Bloom: `REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`.
- Khi câu hỏi đã có sinh viên làm bài, loại câu hỏi bị khóa để bảo toàn tính toàn vẹn khảo thí.
- Phương án lựa chọn và đáp án chấp nhận thuộc về phiên bản câu hỏi (`QuestionRevision`).

## Primary persistence
`questions`, `question_revisions`, `question_revision_choices`, `question_revision_accepted_answers`, `question_provenance`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Preserve historical evidence instead of rewriting past records.
- Standalone Question Bank Hub endpoints (`/api/questions/*`, `/instructor/courses/<id>/questions`) have been decommissioned.
