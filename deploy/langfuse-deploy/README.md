# Langfuse 部署脚本（47.118.30.86）

在服务器 `47.118.30.86` 上用 Docker 部署 Langfuse Server 与 Web 控制台，文件位于 `/home/wei/langfuse`。

## 方式一：本机一键部署（推荐）

在 **Windows** 本机执行（会提示 2 次输入 SSH 密码）：

```powershell
cd langfuse-deploy
.\deploy.ps1
```

若已配置 SSH 公钥到服务器，可免密执行。

## 方式二：在服务器上直接执行

1. 登录服务器：`ssh root@47.118.30.86`
2. 创建目录并下载脚本：

```bash
mkdir -p /home/wei/langfuse
cd /home/wei/langfuse
# 从本地上传 setup-on-server.sh 到该目录，或从项目复制内容后保存为 setup-on-server.sh
chmod +x setup-on-server.sh
./setup-on-server.sh
```

或在本机用 SCP 上传后 SSH 执行：

```powershell
scp langfuse-deploy/setup-on-server.sh root@47.118.30.86:/home/wei/langfuse/
ssh root@47.118.30.86 "cd /home/wei/langfuse && chmod +x setup-on-server.sh && ./setup-on-server.sh"
```

## 部署结果

- **Langfuse 控制台**: http://47.118.30.86:3000  
- **MinIO 控制台**: http://47.118.30.86:9090（若防火墙已开放）  
- 首次访问 Langfuse 需注册账号。  
- 密钥与数据库密码在首次运行时自动生成，保存在 `/home/wei/langfuse/.env`。

## 常用命令（在服务器上）

```bash
cd /home/wei/langfuse
docker compose ps      # 查看容器
docker compose logs -f # 查看日志
docker compose down   # 停止并删除容器（数据卷保留）
docker compose up -d  # 后台启动
```

## 安全说明

- 脚本中的 SSH 密码仅用于本机连接服务器，请勿提交到公共仓库。
- 生产环境建议：使用 SSH 密钥登录、修改 `.env` 中的默认密钥、并限制防火墙仅开放 3000（及可选 9090）端口。
