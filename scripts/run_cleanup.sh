#!/usr/bin/env bash

set -u

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${NEXTPOST_ENV_FILE:-/etc/nextpost/production.env}"
cd "$project_dir"

docker compose --env-file "$env_file" -f compose.production.yml exec -T backend \
    python -m app.cleanup
status=$?

case "$status" in
    0) exit 0 ;;
    2)
        echo "NextPost cleanup skipped because another maintenance leader is active."
        exit 0
        ;;
    1)
        python scripts/notify_operator.py --event cleanup-failed \
            --summary "NextPost cleanup reported overdue work or storage anomalies" \
            --env-file "$env_file"
        exit 1
        ;;
    *)
        python scripts/notify_operator.py --event cleanup-failed \
            --summary "NextPost cleanup command failed before producing a healthy status" \
            --env-file "$env_file"
        exit "$status"
        ;;
esac
