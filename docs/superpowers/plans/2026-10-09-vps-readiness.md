# PWD301 VPS readiness implementation plan

Approved 2026-10-09. Execute with subagent-driven-development/TDD and verification-before-completion.

## Goal and scope
Prepare a tested deployment artifact on isolated staging for Ubuntu22/Linux x64,8GB RAM,2 CPUs,40GB disk,SQLServer2022Express,YouTube official embedding and private BackblazeB2 documents. Never change DNS, publish production, or migrate real data in this round.

## Packages and dependencies
1. Safety: record clean6ebbaaa baseline; disposable DB guard before any destructive fixture, baseline checks and source contracts.
2. Playback: durable per-period+lesson lease, public session token, strict sequence and receipts, first-credit0, no per-request jitter, gap>20s0, bounded position/rate, per-media frontier, server response and preserved quiz/history rules. SQLite logic checks plus real SQLExpress concurrency required.
3. Player: existing driver, official unobscured iframe, outside controls/identity, supported rates confirmed from driver, volume/keyboard/fullscreen, shared APIloader15s retry, complete controller disposal,10s active heartbeats, same-payload retry, terminal flush and server-authoritative resume/completion. HLS watermark remains visible and CSS-protected.
4. Storage: local|s3 only, pinned boto3, fail-closed configuration, all-engine scan, streamed cloudSHA/size verification, location metadata migration, commit-before-local-removal,60s authorized browser-CSRF/JWT tickets, bounded1GiB cache/1h and2GiB quarantine, staging-only resumable migration, conservative24h orphan reconciliation.
5. Artifact: immutable production images, no source bindmounts, CaddyTLS/private ports, no secretdefaults/demo seed, runtime DB user/migrator separation, one-shot release bootstrap, SQL2560MiB limit withmemory2048, ClamAV3072MiB, web600MiB,worker300MiB,proxy128MiB,10MBx3 logs, adaptiveworker10s. Health requires real DB/scanner/cloud/worker signals.
6. Recovery: realExpress backup+checksum, streamingAES-GCM cloudarchive, separate restore drill/database with integrity and data comparison; no automatic live restore/downgrade.

## Verification and release gates
G1 code/lint/types/frontend/backend/review;G2 SQLExpress/migrations/races;G3 browser+realYouTube;G4 realprivateB2;G5 cleanLinuxartifact;G6 physicalbackup+isolatedrestore;G7 workload/resources;G8 runbook/evidence.

Workload:20syntheticcourses,50activelearningusers60min,10sheartbeats,5documentdownloads,2upload/scans;4hsoak including signature update; p95API<2s,errorrate<1%,noOOM/restarts,≥1GiBRAM available and≥10GBdiskfree. Provider streaming latency is excluded from backendAPI measurements.

No skipped/blocked/mock/source-only result counts as livePASS. DEPLOY_READY requires all G1–G8. B2/YouTube secrets must come from a private staging env file; never logs/chat/commit. Prepare20courses without mocked trusted metadata if credentials are absent; retain G3/G4/G7 blockers.

## Rulings
- Reuse current source checkout on dedicated codex/vps-readiness branch rather than copying user work into another checkout; baseline was clean.
- Synthetic SQL staging uses pwd301_test_readiness and project pwd301-readiness-20261009. Existing running containers/database are not test targets.
- Storage reconciliation is report-only by default; deletion requires explicit staging tool action and verified cloud copy/reference checks.
- Historical TASK087 completion does not certify the revised readiness gates.
