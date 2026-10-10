# Hướng dẫn triển khai PWD301

## Preconditions
Mục tiêu: Ubuntu 22.04 x64, ít nhất 2 vCPU, RAM 8 GB, SSD 40 GB và còn 10 GB trống. Cần Docker Engine/Compose hỗ trợ healthcheck, profiles và `!override`, domain, B2 private, YouTube Data API key và khóa mã hóa backup 32 byte giữ độc lập. Bản này chưa được công nhận DEPLOY_READY; từng cổng phải đạt trong VPS_READINESS_REPORT.md.

Sao chép `.env.production.example` thành `.env.production` ngoài Git, quyền `chmod 600`. Sinh secret độc lập và mật khẩu DB/admin mạnh. DATABASE_URL dùng pwd301_app; MIGRATION_DATABASE_URL dùng pwd301_migrator; URL-encode ký tự đặc biệt. Cả hai trỏ đến db:1433 và cùng DB_NAME với ODBC Driver 18. Bucket/key backup tách khỏi tài liệu. Không tái sử dụng credential staging.

Run `python scripts/deploy_preflight.py --env-file .env.production`. It only reports secret presence. Create2GBswap using your host admin procedure; swap is not additional workload RAM. Expose only80/443 and restrictedSSH;1433/3310/5000 are private. Set DBbackups/cloud budgets and Express10GBsize alerts before enrolling users.

## Build and one-shot release
```
docker build -t pwd301:release .
docker compose --env-file .env.production -f deploy/compose.production.yml config --quiet
docker compose --env-file .env.production -f deploy/compose.production.yml build clamav
docker compose --env-file .env.production -f deploy/compose.production.yml up -d db clamav
docker compose --env-file .env.production -f deploy/compose.production.yml --profile release run --rm release
docker compose --env-file .env.production -f deploy/compose.production.yml up -d web worker proxy
```

Record the imageID,digests,GitSHA and migrationhead. Release provisions independent runtime/migration logins,creates DB with canonical Vietnamese collation if missing,upgrades migrations and seeds only roles/rootadmin. Web/worker do not auto-migrate or seed. Revoke bootstrap secrets from runtime environments after release. No `down -v`,automaticDBrestore or unreviewed migrationdowngrade.

Confirm HTTPS,cookieSecure/HttpOnly/CSRF,login,health/deep,workerheartbeat,cleanfile/EICAR,YouTubeplayback,documentticket and backups. RequireddependencyDEGRADED/UNKNOWN is a releasefailure; `/health` alone is not readiness.

## Disposable staging
Dùng Compose project riêng và `deploy/compose.staging.yml`. DB 15439, HTTPS 18443 và HTTP smoke 18080 chỉ bind 127.0.0.1. HTTP smoke không chứng minh HTTPS. Caddy staging dùng CA nội bộ; xác minh TLS bằng CA qua client riêng, không bỏ kiểm tra chứng chỉ hoặc tự đổi trust store máy người dùng. Tên DB bắt đầu pwd301_test_; PWD301_TEST_DB_DISPOSABLE=1 bắt buộc trước destructive pytest. Seed yêu cầu đích/mật khẩu riêng; không seed production. Seed không có video không chứng minh tải video.

## Backup and recovery
Dịch vụ backup dùng BACKUP_BUCKET_NAME, BACKUP_ENCRYPTION_KEY, ADMIN_EMAIL và key backup riêng. Công cụ tái sử dụng backup Express có audit/checksum, mã hóa riêng `.bak` và manifest bằng AES-GCM streaming, đọc lại cloud để so SHA-256/kích thước, rồi mới phát receipt HMAC. Giữ khóa mã hóa ngoài VPS/B2. Retention: 2 nhóm automatic local đã xác minh, 7 daily, 4 weekly Chủ nhật UTC. Prune local trước cloud; audit/DB commit trước unlink. Bản manual/chưa archive và bằng chứng lỗi được giữ: cần giám sát đĩa, không tự xóa bản recovery duy nhất.

Chạy `docker compose --env-file .env.production -f deploy/compose.production.yml --profile operations run --rm backup`. Mẫu `deploy/pwd301-backup.service`/`.timer` giả định /opt/pwd301; rà soát đường dẫn/quyền rồi cài vào /etc/systemd/system, daemon-reload và enable timer. Lịch 02:00 UTC hằng ngày, trễ ngẫu nhiên tối đa 15 phút. Đây là lịch ngoài SQL Server Agent; mẫu chưa chạy trên systemd VPS thật.

Authenticateddecrypt uses `python scripts/backup_archive.py --decrypt encrypted-path --output new-restore-path`. Restore only to a separately named DB,runDBCCCHECKDB and compare rowcounts/keydata. VERIFYONLY is insufficient recoveryproof. Adminlive-restore safeguard remainsclosed; an actualproductionrestore is a separate confirmedmaintenance operation.

`scripts/restore_drill.py` chỉ nhận source/target khác nhau có tiền tố pwd301_test_ và xác nhận disposable, từ chối đích đã tồn tại. Chạy qua release service với RESTORE_DRILL_DB_NAME và PWD301_TEST_DB_DISPOSABLE=1. Công cụ kiểm tra Express, checksum/manifest, VERIFYONLY, restore vào DB mới, DBCC CHECKDB và số dòng mẫu. Chưa thay thế kiểm tra đầy đủ dữ liệu nghiệp vụ.

Migration sửa đường rollback giữ constraint canonical tại head. Không dừng production ở revision trung gian đã downgrade; chỉ kiểm tra round-trip trên disposable. Dịch vụ backup-permissions khởi tạo quyền volume để SQL Server UID 10001 có thể ghi.

## Rollback
Keep the prior imageID and pre-releasebackup. Stop new ingress if needed,restart Web/Worker with prior compatibleimage; preserve DB and volumes. Additive migrations remain in place. Restore/downgrade requires a separate reviewed recovery procedure; never automate overwriting live data.

## Monitoring
Observe DBdatabasesize7GBwarning/9GBcritical,freeSSD10GB,host/containerRAM,OOM/restartcount,workerheartbeat≤30s,queueage,scannerreadiness/signatureage,cloudfailures/usage/egress,backupage and HTTPerrors/latency. Activeclients are untrusted signals,not proofofattention; UnlistedURLs and60stickets can be shared.

Workload nghiệm thu: 50 phiên học trong 60 phút, heartbeat 10 giây, 5 tải tài liệu, 2 upload/quét; soak 4 giờ có chuyển bài/cập nhật signature. Dùng provider/video/tài liệu thật. Ghi p95 API <2 giây, lỗi <1%, không OOM/restart/job thất lạc/cache vô hạn, còn 1 GiB RAM và 10 GB đĩa. Host Docker 16 GB chưa chứng minh ngân sách host VPS 8 GB. Không đổi workload thành liveness rồi công bố đạt.
