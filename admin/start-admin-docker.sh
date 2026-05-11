#!/usr/bin/env bash
# 启动 admin/docker-compose.yml（admin-backend + admin-frontend）。
# 依赖 Docker 与外部网络 notebooklm_default（若不存在则创建）。
# 用法：在任意目录执行 bash admin/start-admin-docker.sh
#       附加参数会传给 docker compose up（例如 --build、--force-recreate）。
#       前台运行：bash admin/start-admin-docker.sh --attach

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
ENV_FILE="${SCRIPT_DIR}/backend/.env"
CONFIG_YAML="${SCRIPT_DIR}/backend/config.yaml"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker 未安装或不在 PATH 中。" >&2
    exit 1
fi

if ! docker network inspect notebooklm_default >/dev/null 2>&1; then
    echo "创建外部网络 notebooklm_default（主栈 MySQL/Redis 等也应使用该网络）。"
    docker network create notebooklm_default >/dev/null
fi

if [ ! -f "${CONFIG_YAML}" ]; then
    echo "缺少配置文件: ${CONFIG_YAML}" >&2
    exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
    echo "缺少环境文件: ${ENV_FILE}" >&2
    exit 1
fi

cd "${SCRIPT_DIR}"

UP_ARGS=(-d)
MODE="后台（-d）"
EXTRA=()
while [ $# -gt 0 ]; do
    case "$1" in
        --attach)
            UP_ARGS=()
            MODE="前台"
            shift
            ;;
        *)
            EXTRA+=("$1")
            shift
            ;;
    esac
done

echo "在 ${SCRIPT_DIR} 启动 admin 栈：${MODE}"
docker compose -f "${COMPOSE_FILE}" up "${UP_ARGS[@]}" "${EXTRA[@]}"
