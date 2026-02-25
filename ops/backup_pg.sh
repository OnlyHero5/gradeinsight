#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-/var/backups/gradeinsight}"
KEEP_DAYS="${KEEP_DAYS:-30}"
TS="$(date +%F_%H%M%S)"

mkdir -p "$OUT_DIR"

docker compose exec -T db pg_dump -U gradeinsight gradeinsight > "$OUT_DIR/gradeinsight_${TS}.sql"
find "$OUT_DIR" -type f -name 'gradeinsight_*.sql' -mtime +"$KEEP_DAYS" -delete

echo "backup done: $OUT_DIR/gradeinsight_${TS}.sql"
