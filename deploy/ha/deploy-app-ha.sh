#!/usr/bin/env bash
# 部署应用层（backend / frontend / nginx / workers），依赖中间件已就绪
# 用法：在项目根目录执行 bash deploy/ha/deploy-app-ha.sh，或设置 DEPLOY_DIR 后执行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 脚本位于 deploy/ha/，仓库根为其上两级
PROJECT_ROOT="${DEPLOY_DIR:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
COMPOSE_APP_HA="${SCRIPT_DIR}/docker-compose.app-ha.yml"
COMPOSE_WORKERS_HA="${SCRIPT_DIR}/docker-compose.workers-ha.yml"
ENV_FILE="${PROJECT_ROOT}/.env"
CONFIG_YAML="${PROJECT_ROOT}/config.yaml"
BUILD_ARGS=()

if [ "${NO_CACHE:-false}" = "true" ]; then
    BUILD_ARGS+=(--no-cache)
fi

cd "${PROJECT_ROOT}"

if [ ! -f "${CONFIG_YAML}" ]; then
    echo "Missing config: ${CONFIG_YAML}"
    echo "Create it first, for example: cp config.yaml.example config.yaml"
    exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
    echo "Missing env file: ${ENV_FILE}"
    echo 'Required for docker compose env_file and for $VAR expansion in config.yaml.'
    echo "Create it first, for example: cp .env.example .env"
    exit 1
fi

git fetch origin && git reset --hard origin/master
docker compose --project-directory "${PROJECT_ROOT}" -f "${COMPOSE_APP_HA}" -f "${COMPOSE_WORKERS_HA}" down
docker compose --project-directory "${PROJECT_ROOT}" -f "${COMPOSE_APP_HA}" -f "${COMPOSE_WORKERS_HA}" build "${BUILD_ARGS[@]}" backend frontend
docker compose --project-directory "${PROJECT_ROOT}" -f "${COMPOSE_APP_HA}" -f "${COMPOSE_WORKERS_HA}" up -d
