#!/usr/bin/env bash

set -Eeuo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${NEXTPOST_ENV_FILE:-/etc/nextpost/production.env}"
public_origin="https://nextpost.formcadence.app"

fail() {
    echo "Error: $1" >&2
    exit 1
}

[[ -n "${DEPLOY_SHA:-}" ]] || fail "DEPLOY_SHA is required"
[[ "$DEPLOY_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "DEPLOY_SHA must be a full Git commit SHA"
[[ -f "$env_file" ]] || fail "production environment file is missing"

cd "$project_dir"
git fetch --quiet origin "$DEPLOY_SHA"
git cat-file -e "$DEPLOY_SHA^{commit}" || fail "requested revision is unavailable"
git checkout --quiet --detach --force "$DEPLOY_SHA"

export DEPLOY_SHA
export COMPOSE_PARALLEL_LIMIT="${COMPOSE_PARALLEL_LIMIT:-1}"
compose=(docker compose --env-file "$env_file" -f compose.production.yml)

"${compose[@]}" config --quiet
if ! docker network inspect nextpost-proxy >/dev/null 2>&1; then
    docker network create --label com.nextpost.shared-proxy=true nextpost-proxy >/dev/null
fi
"${compose[@]}" up --build -d

backend_container="$("${compose[@]}" ps -q backend)"
[[ -n "$backend_container" ]] || fail "backend container was not created"

health=""
for _ in {1..90}; do
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$backend_container" 2>/dev/null || true)"
    case "$health" in
        healthy) break ;;
        unhealthy|exited|dead)
            "${compose[@]}" logs --no-color --tail 200 backend >&2 || true
            fail "backend became unhealthy"
            ;;
    esac
    sleep 1
done
[[ "$health" == "healthy" ]] || fail "backend readiness timed out"

running_sha="$(docker inspect --format '{{ index .Config.Labels "com.nextpost.revision" }}' "$backend_container")"
[[ "$running_sha" == "$DEPLOY_SHA" ]] || fail "running revision does not match DEPLOY_SHA"

curl --fail --silent --show-error --retry 5 --retry-all-errors --retry-max-time 90 \
    --resolve nextpost.formcadence.app:443:127.0.0.1 "$public_origin/api/ready" >/dev/null
curl --fail --silent --show-error --retry 5 --retry-all-errors --retry-max-time 90 \
    --resolve nextpost.formcadence.app:443:127.0.0.1 "$public_origin/" >/dev/null

printf '%s\n' "$DEPLOY_SHA" > .deployed-sha
echo "NextPost deployed revision $DEPLOY_SHA successfully."
