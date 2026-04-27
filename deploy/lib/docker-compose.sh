#!/usr/bin/env bash
# Shared by deploy/*.sh: call Compose whether the host has V2 plugin or legacy CLI.
#
# Some hosts report success for "docker compose version" but the plugin is not
# actually usable; "docker compose -f ..." then fails with:
#   unknown shorthand flag: 'f' in -f
# So we prefer standalone docker-compose when present, and require recognizable
# Compose V2 output before using "docker compose".
#
# Optional override: export DOCKER_COMPOSE_BIN="/usr/bin/docker-compose"

run_docker_compose() {
    if [ -n "${DOCKER_COMPOSE_BIN:-}" ]; then
        "${DOCKER_COMPOSE_BIN}" "$@"
        return $?
    fi
    if command -v docker-compose >/dev/null 2>&1 \
        && docker-compose --version >/dev/null 2>&1; then
        docker-compose "$@"
        return $?
    fi
    _dc_ver_out=$(docker compose version 2>&1) || _dc_ver_out=
    if echo "${_dc_ver_out}" | grep -qiE 'Docker Compose version|Compose version v[0-9]'; then
        docker compose "$@"
        return $?
    fi
    echo "error: need a working Compose CLI. Install one of:" >&2
    echo "  sudo apt-get install -y docker-compose-plugin   # docker compose (recommended)" >&2
    echo "  sudo apt-get install -y docker-compose           # docker-compose (legacy)" >&2
    echo "Or set DOCKER_COMPOSE_BIN to the full path of your compose binary." >&2
    return 1
}
