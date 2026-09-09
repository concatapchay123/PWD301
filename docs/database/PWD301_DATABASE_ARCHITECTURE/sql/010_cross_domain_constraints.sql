/*
PWD301 Database Architecture — Reference DDL
Engine: Microsoft SQL Server
All DATETIME2 values are UTC by application convention.
This is reference architecture, not evidence that migrations have been executed.
*/
SET XACT_ABORT ON;
GO


/* Deferred and circular foreign keys */

ALTER TABLE users ADD CONSTRAINT fk_users_avatar_file_asset_id FOREIGN KEY (avatar_file_asset_id) REFERENCES file_assets (id) ON DELETE SET NULL;
GO

ALTER TABLE courses ADD CONSTRAINT fk_courses_thumbnail_file_asset_id FOREIGN KEY (thumbnail_file_asset_id) REFERENCES file_assets (id) ON DELETE SET NULL;
GO

ALTER TABLE enrollments ADD CONSTRAINT fk_enrollments_current_period_id FOREIGN KEY (current_period_id) REFERENCES enrollment_periods (id) ON DELETE SET NULL;
GO

ALTER TABLE attempt_question_grade_history ADD CONSTRAINT fk_attempt_question_grade_history_question_correction_id FOREIGN KEY (question_correction_id) REFERENCES question_corrections (id) ON DELETE SET NULL;
GO

ALTER TABLE assessment_result_history ADD CONSTRAINT fk_assessment_result_history_regrade_job_id FOREIGN KEY (regrade_job_id) REFERENCES regrade_jobs (id) ON DELETE SET NULL;
GO

ALTER TABLE regrade_jobs ADD CONSTRAINT fk_regrade_jobs_background_job_id FOREIGN KEY (background_job_id) REFERENCES background_jobs (id) ON DELETE SET NULL;
GO

ALTER TABLE document_import_jobs ADD CONSTRAINT fk_document_import_jobs_background_job_id FOREIGN KEY (background_job_id) REFERENCES background_jobs (id) ON DELETE SET NULL;
GO

ALTER TABLE knowledge_versions ADD CONSTRAINT fk_knowledge_versions_background_job_id FOREIGN KEY (background_job_id) REFERENCES background_jobs (id) ON DELETE SET NULL;
GO

ALTER TABLE grade_exports ADD CONSTRAINT fk_grade_exports_background_job_id FOREIGN KEY (background_job_id) REFERENCES background_jobs (id) ON DELETE SET NULL;
GO
