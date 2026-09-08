# Non-Negotiable Invariants

1. No JWT in localStorage for website AJAX.
2. Suspended/deactivated User cannot continue active session/JWT.
3. Role is not enough; authorize the concrete resource.
4. One active EnrollmentPeriod per Student/Course logical Enrollment; capacity/prerequisite are race-safe.
5. Prerequisite cycles forbidden; active dependency blocks archive/delete.
6. Exposed/graded QuestionRevision is historical and retained.
7. Question type cannot change after a Student has answered.
8. Attempt snapshot is immutable historical evidence.
9. Server time is authoritative; close time is hard boundary.
10. One active editing lease; stale owner takeover keeps same Attempt.
11. Late/stale offline answer cannot overwrite newer or pass deadline.
12. Submit is idempotent; one logical result.
13. Assessment timing locked after publish.
14. Assessment structure/assigned points locked after first Student start.
15. Legitimate Question corrections remain possible through revision/regrade.
16. Grade/result changes append history; historical answers/snapshots not rewritten.
17. Detail purge after >30 days no-rejoin excludes that period from future regrade but preserves compact completion/prerequisite summary.
18. Unsafe/unscanned files cannot activate; scanner failure is fail-closed; video <1 GB.
19. FileAsset has at most one ACTIVE revision; shared blob deletion respects references/recovery.
20. RAG retrieves only currently authorized published content; archived/deleted/draft excluded.
21. Raw AI chat content purges after five minutes inactivity.
22. Important audit is append-only; required-audit sensitive action fails if audit cannot persist.
23. Admin override is explicit, reasoned and notified where required; no impersonation.
24. No broad cascade deletion of historical learning/assessment data.
