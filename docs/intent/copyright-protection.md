# Copyright protection and deployment intent — approved 2026-10-09

## Approved outcome
PWD301 reuses its YouTube/custom-player backend and frontend. Official YouTube embedding keeps branding and navigation visible where the provider requires it. No obscuring shields or watermark overlays cover the iframe. PWD301 controls and identity are outside that surface. Unlisted links can be shared; no promise of DRM or complete prevention of copying is made.

## Internal media
Internal encrypted HLS retains continuous forensic watermark and DOM/CSS blackout defense. Raw lesson video downloads are denied to learners across every download entrypoint. Blackout stops playback and heartbeat; client tamper checks are deterrence, not proof of misconduct.

## Learning progress
Server-clock durable playback sessions serialize credit, bound movement and persist per-media frontiers. Start credits zero, retry is idempotent, multiple workers/tabs do not multiply time, and long gaps are not credited. Existing minimum-time, viewed-most, quiz and historical completion rules remain. Signals cannot prove attention.

## Storage and deployment
YouTube Unlisted is the target delivery for 20 staging courses. Backblaze B2 private stores scanned documents with verified content and short-lived download tickets. Local quarantine/cache have bounded budgets; cloud egress follows provider pricing. VPS target is Linux x64, 8 GB RAM, at least two CPUs and 40 GB SSD; SQL Server 2022 Express is the production database edition.

## Acceptance
Only fresh automated, real SQL Express, browser, B2, backup/restore and load evidence can close their respective gates. Synthetic metadata or mocked providers never count as live proof. This round prepares artifacts/staging and does not migrate real data, change DNS or open production.
