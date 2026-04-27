#!/usr/bin/env bash
# 部署核心服务（backend / frontend / nginx），依赖中间件（postgres / redis / milvus 等）
# 用法：在项目根目录执行 bash deploy/deploy-core.sh，或设置 DEPLOY_DIR 后执行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${DEPLOY_DIR:-$(dirname "${SCRIPT_DIR}")}"
COMPOSE_CORE="${SCRIPT_DIR}/docker-compose-core.yml"
ENV_FILE="${PROJECT_ROOT}/.env"
BUILD_ARGS=()

if [ "${NO_CACHE:-false}" = "true" ]; then
    BUILD_ARGS+=(--no-cache)
fi

cd "${PROJECT_ROOT}"

if [ ! -f "${ENV_FILE}" ]; then
    echo "Missing env file: ${ENV_FILE}"
    echo "Create it first, for example: cp .env.example .env"
    exit 1
fi

git fetch origin && git reset --hard origin/master
docker compose -f "${COMPOSE_CORE}" down
docker compose -f "${COMPOSE_CORE}" build "${BUILD_ARGS[@]}"
docker compose -f "${COMPOSE_CORE}" up -d
