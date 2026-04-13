#!/usr/bin/env bash
# Langfuse Docker 服务端安装脚本，在 47.118.30.86 上执行
# 目标目录: /home/wei/langfuse

set -e

LANGFUSE_DIR="/home/wei/langfuse"
REPO_URL="https://github.com/langfuse/langfuse.git"

echo "[1/6] 创建目录 ${LANGFUSE_DIR} ..."
mkdir -p "${LANGFUSE_DIR}"
cd "${LANGFUSE_DIR}"

echo "[2/6] 检查并安装 Docker ..."
if ! command -v docker &>/dev/null; then
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release 2>/dev/null && echo "${VERSION_CODENAME:-jammy}") stable" \
        | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "Docker 已安装，跳过"
fi

echo "[3/6] 获取 Langfuse 仓库 ..."
if [ -f "${LANGFUSE_DIR}/docker-compose.yml" ] && [ -d "${LANGFUSE_DIR}/.git" ]; then
    echo "已有仓库，拉取最新..."
    git -C "${LANGFUSE_DIR}" fetch --all
    git -C "${LANGFUSE_DIR}" pull --rebase || true
elif [ ! -f "${LANGFUSE_DIR}/docker-compose.yml" ]; then
    TMP_CLONE="/tmp/langfuse-clone-$$"
    git clone --depth 1 "${REPO_URL}" "${TMP_CLONE}"
    cp -a "${TMP_CLONE}/docker-compose.yml" "${LANGFUSE_DIR}/"
    rm -rf "${TMP_CLONE}"
fi
cd "${LANGFUSE_DIR}"

echo "[4/6] 生成密钥并创建 .env ..."
if [ -f "${LANGFUSE_DIR}/.env" ]; then
    echo "已存在 .env，跳过生成（如需重置请先删除 .env）"
else
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    POSTGRES_PWD="pg_$(openssl rand -hex 12)"
    CLICKHOUSE_PWD="ch_$(openssl rand -hex 12)"
    REDIS_AUTH="redis_$(openssl rand -hex 12)"
    MINIO_PWD="minio_$(openssl rand -hex 12)"
    NEXTAUTH_SECRET=$(openssl rand -hex 32)
    SALT="salt_$(openssl rand -hex 8)"
    NEXTAUTH_URL="${NEXTAUTH_URL:-http://47.118.30.86:3000}"

    cat > "${LANGFUSE_DIR}/.env" << EOF
# Langfuse 生产环境变量（由 setup-on-server.sh 生成）
NEXTAUTH_URL=${NEXTAUTH_URL}
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
SALT=${SALT}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PWD}
POSTGRES_DB=postgres
DATABASE_URL=postgresql://postgres:${POSTGRES_PWD}@postgres:5432/postgres

CLICKHOUSE_USER=clickhouse
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PWD}

REDIS_AUTH=${REDIS_AUTH}

MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=${MINIO_PWD}
LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=${MINIO_PWD}
LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY=${MINIO_PWD}
LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY=${MINIO_PWD}
LANGFUSE_S3_MEDIA_UPLOAD_ENDPOINT=http://minio:9000
EOF
fi

echo "[5/6] 启动 Docker Compose ..."
docker compose pull
docker compose up -d

echo "[6/6] 等待服务就绪（约 2–3 分钟）..."
for i in $(seq 1 36); do
    if docker compose logs langfuse-web 2>/dev/null | tail -20 | grep -q "Ready"; then
        echo "Langfuse Web 已就绪"
        break
    fi
    echo "等待中... ${i}/36"
    sleep 5
done

echo ""
echo "=== 部署完成 ==="
echo "  Langfuse 控制台: ${NEXTAUTH_URL}"
echo "  MinIO 控制台:    http://47.118.30.86:9090 (如已开放端口)"
echo "  数据目录:        ${LANGFUSE_DIR}"
echo "  停止服务:        cd ${LANGFUSE_DIR} && docker compose down"
echo "  查看日志:        cd ${LANGFUSE_DIR} && docker compose logs -f"
echo ""
