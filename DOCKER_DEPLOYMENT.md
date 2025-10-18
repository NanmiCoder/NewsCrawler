# Docker 部署指南

本文档介绍如何使用 Docker 一键启动 NewsCrawler 的**前端**、**后端**和 **MCP** 服务。

---

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [服务架构](#服务架构)
- [端口说明](#端口说明)
- [常用命令](#常用命令)
- [数据持久化](#数据持久化)
- [健康检查](#健康检查)
- [故障排除](#故障排除)

---

## 系统要求

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **系统内存**: >= 4GB 推荐
- **磁盘空间**: >= 5GB 可用空间

检查 Docker 版本：
```bash
docker --version
docker-compose --version
```

---

## 快速开始

### 1. 克隆项目（如果尚未克隆）

```bash
git clone https://github.com/NanmiCoder/NewsCrawler.git
cd NewsCrawler
```

### 2. 一键启动所有服务

```bash
docker-compose up -d
```

这将启动三个服务：
- **Backend** (FastAPI) - 端口 8000
- **MCP Server** (AI Agent Tools) - 端口 8765
- **Frontend** (Vue 3 + Nginx) - 端口 3000

### 3. 验证服务状态

```bash
docker-compose ps
```

期望输出：
```
NAME                        STATUS              PORTS
news-extractor-backend      Up 30 seconds       0.0.0.0:8000->8000/tcp
news-extractor-mcp          Up 30 seconds       0.0.0.0:8765->8765/tcp
news-extractor-frontend     Up 30 seconds       0.0.0.0:3000->80/tcp
```

### 4. 访问服务

- **前端 Web UI**: http://localhost:3000
- **后端 API 文档**: http://localhost:8000/docs
- **MCP 健康检查**: http://localhost:8765/health

---

## 服务架构

```
┌─────────────────────────────────────────────┐
│          Docker Compose Network             │
│                                             │
│  ┌──────────────┐    ┌─────────────────┐  │
│  │   Frontend   │───>│     Backend     │  │
│  │  (Nginx)     │    │    (FastAPI)    │  │
│  │  Port: 3000  │    │    Port: 8000   │  │
│  └──────────────┘    └─────────────────┘  │
│                                             │
│                      ┌─────────────────┐  │
│                      │   MCP Server    │  │
│                      │  (AI Agents)    │  │
│                      │   Port: 8765    │  │
│                      └─────────────────┘  │
│                                             │
│         Shared Volume: ./data               │
└─────────────────────────────────────────────┘
```

### 服务依赖关系

```
news_extractor_core (核心库)
    ├── news_extractor_backend (Web API)
    ├── news_extractor_mcp (MCP 工具)
    └── news-extractor-ui/frontend (UI 界面)
```

---

## 端口说明

| 服务      | 容器端口 | 宿主机端口 | 用途                          |
|-----------|----------|------------|-------------------------------|
| Frontend  | 80       | 3000       | Vue 3 用户界面                |
| Backend   | 8000     | 8000       | FastAPI RESTful API           |
| MCP       | 8765     | 8765       | Model Context Protocol 服务   |

**端口冲突解决**：如果宿主机端口已被占用，可以编辑 `docker-compose.yml` 修改映射：

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 改为 8080
```

---

## 常用命令

### 启动服务

```bash
# 后台启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d backend
docker-compose up -d frontend
docker-compose up -d mcp

# 前台启动（查看日志）
docker-compose up
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f mcp
docker-compose logs -f frontend

# 查看最近 100 行日志
docker-compose logs --tail=100 backend
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v

# 停止特定服务
docker-compose stop backend
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 重新构建

```bash
# 重新构建并启动（代码更新后使用）
docker-compose up -d --build

# 强制重新构建（忽略缓存）
docker-compose build --no-cache
docker-compose up -d
```

### 进入容器调试

```bash
# 进入 backend 容器
docker exec -it news-extractor-backend sh

# 进入 mcp 容器
docker exec -it news-extractor-mcp sh

# 进入 frontend 容器
docker exec -it news-extractor-frontend sh
```

---

## 数据持久化

### 数据卷

项目使用 Docker 卷持久化提取的新闻数据：

```yaml
volumes:
  - ./data:/app/data  # 宿主机 ./data 目录映射到容器内 /app/data
```

**说明**：
- 所有提取的新闻 JSON 文件保存在 `./data/` 目录
- Backend 和 MCP 服务共享同一数据卷
- 即使容器删除，数据依然保留在宿主机

### 清理数据

```bash
# 清理提取的新闻数据
rm -rf ./data/*

# 清理 Docker 卷（会删除所有数据）
docker-compose down -v
```

---

## 健康检查

所有服务都配置了健康检查，可以通过以下方式验证：

### 1. Docker 健康状态

```bash
docker-compose ps
```

查看 `STATUS` 列是否显示 `healthy`。

### 2. 手动健康检查

```bash
# Backend 健康检查
curl http://localhost:8000/

# MCP 健康检查
curl http://localhost:8765/health

# Frontend 健康检查
curl http://localhost:3000/
```

### 3. 健康检查配置

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
  interval: 30s      # 每 30 秒检查一次
  timeout: 5s        # 超时时间 5 秒
  retries: 3         # 失败重试 3 次
  start_period: 10s  # 启动后 10 秒开始检查
```

---

## 故障排除

### 1. 服务无法启动

**检查日志**：
```bash
docker-compose logs backend
docker-compose logs mcp
docker-compose logs frontend
```

**常见问题**：
- 端口冲突：修改 `docker-compose.yml` 中的端口映射
- 内存不足：确保 Docker 分配了至少 4GB 内存
- 依赖安装失败：检查网络连接，或使用 `--build` 重新构建

### 2. Frontend 无法连接 Backend

**检查网络**：
```bash
docker network ls
docker network inspect newscrawlercollection_news-extractor-network
```

**验证 Backend 可达性**：
```bash
docker exec -it news-extractor-frontend sh
wget http://backend:8000/
```

### 3. 数据未持久化

**检查卷挂载**：
```bash
docker inspect news-extractor-backend | grep -A 10 Mounts
```

**验证数据目录**：
```bash
ls -la ./data/
```

### 4. 构建速度慢

**使用国内镜像源**：

项目已配置清华 PyPI 镜像（`pyproject.toml`）：
```toml
[[tool.uv.index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

**使用 Docker 镜像加速**：
配置 Docker daemon (`/etc/docker/daemon.json`)：
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

### 5. MCP 服务健康检查失败

MCP 健康检查端点是 `/health`，确保代码中已实现：

```python
@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok", "name": SERVER_NAME})
```

---

## 生产环境建议

### 1. 环境变量管理

创建 `.env` 文件管理敏感配置：
```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# MCP
MCP_HOST=0.0.0.0
MCP_PORT=8765

# Database (如需添加)
DATABASE_URL=postgresql://user:pass@db:5432/news
```

在 `docker-compose.yml` 中引用：
```yaml
services:
  backend:
    env_file:
      - .env
```

### 2. CORS 配置

生产环境应限制 CORS 域名（编辑 `news_extractor_backend/main.py`）：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 替换为实际域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. 反向代理

建议使用 Nginx/Traefik 作为反向代理，统一管理 SSL 证书和域名路由。

### 4. 日志管理

配置日志驱动（`docker-compose.yml`）：
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5. 资源限制

限制容器资源使用：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 更新部署

### 拉取最新代码

```bash
git pull origin main
```

### 重新构建并启动

```bash
docker-compose down
docker-compose up -d --build
```

### 保留数据重新部署

```bash
# 停止容器但不删除卷
docker-compose down

# 重新构建
docker-compose build

# 启动
docker-compose up -d
```

---

## 许可与免责声明

本项目仅供教育和研究目的使用，请勿用于：
- 商业用途
- 大规模爬虫
- 违反目标网站服务条款的行为

使用者需自行承担使用本工具的责任。

---

## 支持

遇到问题？
- 提交 Issue: https://github.com/NanmiCoder/NewsCrawler/issues
- 查看文档: [README.md](README.md)
- 查看架构: [CLAUDE.md](CLAUDE.md)

---

**Happy Crawling! 🚀**
