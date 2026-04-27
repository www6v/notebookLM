#!/usr/bin/env bash
# 独立 Nginx 反向代理到上游 HTTP 服务（默认 124.221.28.203）
# 用法：bash deploy/nginx/deploy-nginx.sh
# 或设置 DEPLOY_DIR 为仓库根目录后执行
#
# 阿里云没有可匿名拉取的 library/nginx 仓库；需使用「镜像加速器」：
# 控制台 ACR → 镜像工具 → 镜像加速器，复制地址后执行一次：
#   sudo ./setup-docker-aliyun-mirror.sh https://xxxxx.mirror.aliyuncs.com
# 再运行本脚本（镜像名保持 nginx:alpine 即可）。
# 未配加速器又超时：export NGINX_IMAGE=docker.m.daocloud.io/library/nginx:alpine

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${DEPLOY_DIR:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose-nginx.yml"

cd "${PROJECT_ROOT}"
docker compose -f "${COMPOSE_FILE}" down
docker compose -f "${COMPOSE_FILE}" up -d
