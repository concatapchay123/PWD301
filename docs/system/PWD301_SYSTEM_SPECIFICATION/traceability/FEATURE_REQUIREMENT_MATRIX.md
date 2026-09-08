# Feature Requirement Matrix

| Feature | Rules | Workflow/Algorithm | API group | Database | Acceptance/Test |
|---|---|---|---|---|---|
| Login/suspension | AUTH-001..006 | account/auth docs | Auth API | identity tables | AC-AUTH + auth/security |
| Course lifecycle | COURSE-001..007 | Course lifecycle/prerequisite | Course API | course/learning | AC-COURSE/ENROLL |
| Enrollment/progress | ENROLL/LESSON | enrollment/progress algorithms | Enrollment API | enrollment/progress | AC-ENROLL/LESSON |
| Question revision | QBANK | Question lifecycle/correction | Question API | question tables | AC-QREV |
| Assessment build/publish | ASSESS | selection/blueprint | Assessment API | assessment tables | AC-ASSESS |
| Attempt/autosave/submit | ATTEMPT | deadline/lease/autosave/submit | Attempt API | attempt tables | AC-ATTEMPT/AUTOSAVE/TIMER/SUBMIT |
| Grading/regrade | GRADE/REGRADE | grading/regrading | Attempt/Regrade API | grade/regrade | AC-GRADE/REGRADE |
| File/import | FILE/IMPORT | file/import workflows | File/Import API | files/import | AC-FILE/IMPORT |
| AI/RAG | AI | knowledge/recommendation | AI API | AI/RAG | AC-AI |
| Notification/audit | NOTIF/AUDIT | notification/admin | Notification/Admin API | notify/audit | AC-NOTIF/AUDIT/ADMIN |
| Retention/operations | DELETE/OPS | cleanup/backup | Admin/system | operations + history | AC-RET/BACKUP |
