# Database Backup and Restore

Automatic daily backups plus Admin-triggered manual backup. Record start/end/status/location/verification metadata in `backup_runs`. Periodically test backup integrity and perform restore drill in non-production. Services may auto-restart after simple failure, but **database restore never automatically overwrites live DB**. Restore requires Admin fresh password re-authentication, exact confirmation phrase, mandatory reason and audit.
