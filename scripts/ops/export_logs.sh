#!/usr/bin/env bash
set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUT_DIR="/opt/apps/pwd301/logs_export_${TIMESTAMP}"
ARCHIVE="/opt/apps/pwd301/system_logs_${TIMESTAMP}.tar.gz"

mkdir -p "$OUT_DIR"
echo "======================================================================"
echo "  TRÍCH XUẤT TOÀN BỘ LOG HỆ THỐNG PWD301 (${TIMESTAMP})"
echo "======================================================================"

echo "-> [1/5] Trích xuất log Web API (Gunicorn / Flask)..."
docker logs --timestamps pwd301-production-web-1 > "$OUT_DIR/web.log" 2>&1

echo "-> [2/5] Trích xuất log Worker (Background Jobs)..."
docker logs --timestamps pwd301-production-worker-1 > "$OUT_DIR/worker.log" 2>&1

echo "-> [3/5] Trích xuất log Proxy (Nginx / Network Access)..."
docker logs --timestamps pwd301-production-proxy-1 > "$OUT_DIR/proxy.log" 2>&1

echo "-> [4/5] Trích xuất log CSDL (SQL Server)..."
docker logs --timestamps pwd301-production-db-1 > "$OUT_DIR/db.log" 2>&1

echo "-> [5/5] Trích xuất log Antivirus (ClamAV)..."
docker logs --timestamps pwd301-production-clamav-1 > "$OUT_DIR/clamav.log" 2>&1

echo "-> Đang nén tệp lưu trữ..."
tar -czf "$ARCHIVE" -C "$OUT_DIR" .
rm -rf "$OUT_DIR"

SIZE=$(du -h "$ARCHIVE" | cut -f1)
echo "======================================================================"
echo "  HOÀN TẤT! Tệp log đã được lưu tại:"
echo "  * Tệp nén: $ARCHIVE ($SIZE)"
echo "======================================================================"
