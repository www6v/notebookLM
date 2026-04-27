#!/usr/bin/env bash
# Shared by deploy/*.sh: call Compose whether the host has V2 plugin or legacy CLI.
#
# Optional override: export DOCKER_COMPOSE_BIN="docker-compose"
# or full path if neither auto-detection works.

run_docker_compose() {
    if [ -n "${DOCKER_COMPOSE_BIN:-}" ]; then
        "${DOCKER_COMPOSE_BIN}" "$@"
        return
    fi
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
        return
    fi
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
        return
    fi
    echo "error: install Docker Compose V2 plugin (docker compose) or docker-compose" >&2
    return 1
}
