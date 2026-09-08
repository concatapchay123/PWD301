# ERD

The diagrams intentionally omit most columns. Full columns and constraints are in the Data Dictionary.

## 1. High-level domain ERD

```mermaid
erDiagram
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : grants
    users ||--o{ courses : owns
    courses ||--o{ lessons : contains
    users ||--o{ enrollments : enrolls
    courses ||--o{ enrollments : receives
    enrollments ||--o{ enrollment_periods : segments
    enrollment_periods ||--o{ lesson_progress : tracks
    courses ||--o{ questions : owns
    questions ||--o{ question_revisions : versions
    courses ||--o{ assessments : owns
    assessments ||--o{ assessment_attempts : generates
    assessment_attempts ||--o{ attempt_questions : freezes
    questions ||--o{ attempt_questions : sourced_from
    file_blobs ||--o{ file_revisions : stores
    file_assets ||--o{ file_revisions : versions
    courses ||--o{ knowledge_documents : scopes
    notification_events ||--o{ notifications : fans_out
    users ||--o{ audit_events : acts
```

## 2. Identity / Auth ERD

```mermaid
erDiagram
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : contains
    users ||--o{ auth_sessions : opens
    users ||--o{ jwt_token_grants : receives
    users ||--o{ user_security_tokens : verifies
    users ||--o{ instructor_applications : applies
    users ||--o{ security_events : involved_in
```

## 3. Course / Learning ERD

```mermaid
erDiagram
    users o|--o{ courses : owns
    courses ||--o{ lessons : contains
    courses ||--o{ course_prerequisites : requires
    courses ||--o{ course_prerequisites : prerequisite_for
    courses ||--|| course_completion_rules : configured_by
    courses ||--o{ course_change_requests : stages
    users ||--o{ enrollments : student
    courses ||--o{ enrollments : has
    enrollments ||--o{ enrollment_periods : periods
    enrollments ||--o{ enrollment_events : history
    enrollment_periods ||--o{ lesson_progress : records
    lessons ||--o{ lesson_progress : completed
    users ||--o{ course_completion_summaries : earned
    courses ||--o{ course_completion_summaries : summarizes
```

## 4. Question Bank ERD

```mermaid
erDiagram
    courses ||--o{ questions : owns
    lessons o|--o{ questions : categorizes
    questions ||--o{ question_revisions : versions
    question_revisions ||--o{ question_revision_choices : choices
    question_revisions ||--o{ question_revision_accepted_answers : accepts
    questions ||--o{ question_provenance : provenance
    question_revisions o|--o{ question_provenance : revision_source
```

## 5. Assessment Structure ERD

```mermaid
erDiagram
    courses ||--o{ assessments : has
    assessments ||--o{ assessment_sections : sections
    assessments ||--o{ assessment_question_assignments : fixed_questions
    questions ||--o{ assessment_question_assignments : mapped
    assessments ||--o{ assessment_blueprints : blueprint
    assessment_blueprints ||--o{ assessment_blueprint_rules : rules
    assessments ||--o{ assessment_question_pool : pool
    questions ||--o{ assessment_question_pool : candidates
    assessment_blueprint_rules o|--o{ assessment_question_pool : materializes
```

## 6. Assessment Attempt / Grading ERD

```mermaid
erDiagram
    assessments ||--o{ assessment_attempts : attempts
    enrollment_periods ||--o{ assessment_attempts : contains
    assessment_attempts ||--o{ attempt_questions : freezes
    question_revisions ||--o{ attempt_questions : source_revision
    attempt_questions ||--o{ attempt_choice_snapshots : choices
    attempt_questions ||--|| attempt_answers : current_answer
    attempt_answers ||--o{ attempt_answer_choices : selected
    attempt_choice_snapshots ||--o{ attempt_answer_choices : chosen
    attempt_questions ||--o{ attempt_answer_events : changes
    attempt_questions ||--|| attempt_question_grades : current_grade
    attempt_questions ||--o{ attempt_question_grade_history : grade_history
    assessment_attempts ||--|| assessment_results : result
    assessment_attempts ||--o{ assessment_result_history : result_history
```

## 7. Correction / Regrade ERD

```mermaid
erDiagram
    questions ||--o{ question_corrections : corrected
    question_revisions ||--o{ question_corrections : from_revision
    question_revisions ||--o{ question_corrections : to_revision
    question_corrections ||--|| regrade_jobs : launches
    regrade_jobs ||--o{ regrade_items : items
    assessment_attempts ||--o{ regrade_items : target
    question_corrections o|--o{ attempt_question_grade_history : explains
    regrade_jobs o|--o{ assessment_result_history : explains
```

## 8. File / Import ERD

```mermaid
erDiagram
    courses ||--o{ file_assets : scopes
    file_assets ||--o{ file_revisions : versions
    file_blobs ||--o{ file_revisions : physical_bytes
    file_revisions ||--o{ file_scan_results : scanned
    lessons ||--o{ lesson_resources : resources
    file_assets ||--o{ lesson_resources : linked
    question_revisions ||--o{ question_revision_resources : resources
    file_assets ||--o{ question_revision_resources : linked
    file_assets ||--o{ document_import_jobs : source
    document_import_jobs ||--o{ import_questions : parses
    import_questions ||--o{ import_duplicate_candidates : duplicate_flags
    import_questions ||--o{ import_question_resources : images
    file_assets ||--o{ import_question_resources : extracted
```

## 9. AI / RAG ERD

```mermaid
erDiagram
    users ||--o{ ai_conversations : chats
    ai_conversations ||--o{ ai_messages : contains
    users ||--o{ ai_requests : requests
    ai_conversations o|--o{ ai_requests : context
    courses ||--o{ knowledge_documents : authorizes
    knowledge_documents ||--o{ knowledge_versions : versions
    knowledge_versions ||--o{ knowledge_chunks : chunks
    ai_requests ||--o{ ai_source_usages : cites
    knowledge_versions ||--o{ ai_source_usages : source
    knowledge_chunks o|--o{ ai_source_usages : chunk
    ai_requests o|--o{ ai_generated_question_drafts : generates
    questions o|--o{ ai_generated_question_drafts : approved_as
```

## 10. Notification / Audit / Operations ERD

```mermaid
erDiagram
    notification_events ||--o{ notifications : creates
    notification_events ||--o{ email_deliveries : emails
    users ||--o{ notifications : receives
    users ||--o{ notification_preferences : configures
    users ||--o{ audit_events : acts
    users ||--o{ security_events : involved
    users ||--o{ system_alerts : acknowledges
    users o|--o{ backup_runs : starts
    analytics_snapshots {
        BIGINT id PK
    }
    system_health_snapshots {
        BIGINT id PK
    }
    background_jobs o|--o{ regrade_jobs : runs
    background_jobs o|--o{ document_import_jobs : runs
    background_jobs o|--o{ knowledge_versions : indexes
    background_jobs o|--o{ grade_exports : generates
```

## 11. Physical relationship notes

- `users.avatar_file_asset_id`, `courses.thumbnail_file_asset_id`, current revision pointers and background-job pointers are deferred FKs to break DDL cycles.
- `audit_events.target_type/target_id` and `notification_events.target_type/target_id` are deliberately weak/polymorphic references because audit/notification history must survive target deletion. They are the exception, not the modeling default.
- Vector store `vector_key` is not an FK because embeddings are not stored in the primary SQL Server schema.
