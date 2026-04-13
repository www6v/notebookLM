#!/usr/bin/env bash
# 部署中间件（Redis / Milvus / etcd / MinIO / Attu）
# 用法：任意目录执行 bash deploy/middleware/deploy-middleware.sh
# 或设置 DEPLOY_DIR 为仓库根目录后执行
#
# 说明：docker compose 会从仓库根目录的 .env 读取变量，用于 compose 文件中的
# ${MYSQL_*:-...} 等插值（可选；不设则使用默认值）。应用层配置见 config.yaml，
# 由 deploy/ha/deploy-app-ha.sh 部署的后端容器挂载。

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 脚本位于 deploy/middleware/，仓库根为其上两级
PROJECT_ROOT="${DEPLOY_DIR:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose-middleware.yml"
BUILD_ARGS=()

if [ "${NO_CACHE:-false}" = "true" ]; then
    BUILD_ARGS+=(--no-cache)
fi

cd "${PROJECT_ROOT}"
git fetch origin && git reset --hard origin/master
docker compose --project-directory "${PROJECT_ROOT}" -f "${COMPOSE_FILE}" down
docker compose --project-directory "${PROJECT_ROOT}" -f "${COMPOSE_FILE}" build "${BUILD_ARGS[@]}"
docker compose --project-directory "${PROJECT_ROOT}" -f "${COMPOSE_FILE}" up -d
