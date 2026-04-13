#!/usr/bin/env bash
# 部署核心服务（backend / frontend / nginx），依赖中间件（postgres / redis / milvus 等）
# 用法：在项目根目录执行 bash deploy/deploy-core.sh，或设置 DEPLOY_DIR 后执行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${DEPLOY_DIR:-$(dirname "${SCRIPT_DIR}")}"
COMPOSE_CORE="${SCRIPT_DIR}/docker-compose-core.yml"

cd "${PROJECT_ROOT}"
git fetch origin && git reset --hard origin/master
docker compose --project-directory "${PROJECT_ROOT}"  -f "${COMPOSE_CORE}" down
