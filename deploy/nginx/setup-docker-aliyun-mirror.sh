#!/usr/bin/env bash
# 将阿里云「镜像加速器」地址写入 Docker daemon（每个账号在 ACR 控制台单独分配）。
# 获取地址：容器镜像服务 ACR → 镜像工具 → 镜像加速器。
# 用法（需 root）：sudo ./setup-docker-aliyun-mirror.sh https://xxxxx.mirror.aliyuncs.com
#
# 说明：
# - apt 安装的 Docker：写入 /etc/docker/daemon.json，并 systemctl restart docker
# - snap 安装的 Docker：无 /etc/docker/daemon.json，写入
#   /var/snap/docker/current/config/daemon.json，并 snap restart docker

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "请使用 root 或 sudo 执行本脚本。" >&2
    exit 1
fi

MIRROR_URL="${1:-}"
if [ -z "${MIRROR_URL}" ]; then
    echo "用法: sudo $0 https://<你的ID>.mirror.aliyuncs.com" >&2
    exit 1
fi

case "${MIRROR_URL}" in
    http://*|https://*) ;;
    *)
        echo "加速器地址应以 http:// 或 https:// 开头。" >&2
        exit 1
        ;;
esac

# snap 版 Docker 不使用 /etc/docker/daemon.json
DOCKER_IS_SNAP=0
if command -v snap >/dev/null 2>&1; then
    if snap list docker 2>/dev/null | grep -q '^docker[[:space:]]'; then
        DOCKER_IS_SNAP=1
    fi
fi

if [ "${DOCKER_IS_SNAP}" -eq 1 ]; then
    DAEMON_JSON="/var/snap/docker/current/config/daemon.json"
else
    DAEMON_JSON="/etc/docker/daemon.json"
fi

mkdir -p "$(dirname "${DAEMON_JSON}")"

export MIRROR_URL
export DAEMON_JSON
python3 <<'PY'
import json
import os
import sys

path = os.environ["DAEMON_JSON"]
mirror = os.environ["MIRROR_URL"].rstrip("/")

data = {}
if os.path.isfile(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        print("error: 现有 daemon.json 不是合法 JSON，请先手动修复。", file=sys.stderr)
        sys.exit(1)

mirrors = data.get("registry-mirrors")
if mirrors is None:
    mirrors = []
if not isinstance(mirrors, list):
    print("error: registry-mirrors 必须是数组。", file=sys.stderr)
    sys.exit(1)

if mirror not in mirrors:
    mirrors.insert(0, mirror)
    data["registry-mirrors"] = mirrors
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4, ensure_ascii=False)
        handle.write("\n")
    print("已写入", path, "并加入加速器:", mirror)
else:
    print("加速器已在配置中，未修改:", mirror)
PY

if [ "${DOCKER_IS_SNAP}" -eq 1 ]; then
    snap restart docker
    echo "已执行: snap restart docker"
else
    systemctl daemon-reload
    systemctl restart docker
    echo "已执行: systemctl restart docker"
fi

echo "可执行: docker info | grep -A5 'Registry Mirrors'"
