# Docker and Environment

Baseline containers/processes: Flask web, SQL Server, worker, ClamAV when enabled, private file volume/storage. Use non-root app image, pinned base/dependencies, health checks, resource limits and no Docker socket/privileged mode. SQL Server data and upload/backup paths are durable volumes; app secrets arrive at runtime. `docker-compose.yml` is appropriate for project deployment.
