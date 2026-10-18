# Copyright protection and deployment intent — approved 2026-10-09

> **SUPERSEDED NOTICE (2026-10-18)**:
> Historical statements below asserting that *"Official YouTube embedding keeps branding and navigation visible... No obscuring shields or watermark overlays cover the iframe"* are STRICTLY SUPERSEDED by the platform invariant **YouTube Standard 16:9 Player** codified in `AGENTS.md` (Mục 10.8) and `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md` (Invariant 25).
> PWD301 strictly enforces YouTube Standard 16:9 Player across all YouTube playback touchpoints (Student Lesson Player, Course Hero Trailer autoplay muted loop, Trailer Lightbox Modal, and Reviewer/Instructor Preview Modals) using standard 16:9 full responsive viewport (100% width, 100% height, zero crop), Cover Poster Shield eliminating 100% of YouTube red button and thumbnail before playback, Error 153 fix (`youtube-nocookie.com`, no `origin`), 5-second seek unlock, and resilient duration fallback.

## Approved outcome (Historical / Superseded)
Historical outcome: PWD301 reuses its YouTube/custom-player backend and frontend. [SUPERSEDED by YouTube Standard 16:9 Player in AGENTS.md §10.8: Official YouTube embedding now uses standard 16:9 uncropped viewport, Cover Poster Shield, and custom controls; all external YouTube branding and navigation are eliminated.] Unlisted links can be shared; no promise of DRM or complete prevention of copying is made.

## Internal media
Internal encrypted HLS retains continuous forensic watermark and DOM/CSS blackout defense. Raw lesson video downloads are denied to learners across every download entrypoint. Blackout stops playback and heartbeat; client tamper checks are deterrence, not proof of misconduct.

## Learning progress
Server-clock durable playback sessions serialize credit, bound movement and persist per-media frontiers. Start credits zero, retry is idempotent, multiple workers/tabs do not multiply time, and long gaps are not credited. Existing minimum-time, viewed-most, quiz and historical completion rules remain. Signals cannot prove attention.

## Storage and deployment
YouTube Unlisted is the target delivery for 20 staging courses. Backblaze B2 private stores scanned documents with verified content and short-lived download tickets. Local quarantine/cache have bounded budgets; cloud egress follows provider pricing. VPS target is Linux x64, 8 GB RAM, at least two CPUs and 40 GB SSD; SQL Server 2022 Express is the production database edition.

## Acceptance
Only fresh automated, real SQL Express, browser, B2, backup/restore and load evidence can close their respective gates. Synthetic metadata or mocked providers never count as live proof. This round prepares artifacts/staging and does not migrate real data, change DNS or open production.
