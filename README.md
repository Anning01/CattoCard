<p align="center">
  <img src="docs/logo.png" width="250" alt="CattoCard Logo">
</p>

<h1 align="center">🐈 CattoCard (猫托卡)</h1>

<p align="center">
  <strong>「 像猫一样敏捷，比独角兽更懂你 」</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-00584c?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D" alt="Vue3">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <strong>开源虚拟商品交易平台</strong>
</p>

<p align="center">
  <a href="#特性">特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#docker-部署">Docker 部署</a> •
  <a href="#配置说明">配置说明</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#api-文档">API 文档</a> •
  <a href="#技术栈">技术栈</a>
</p>

---

## 介绍

**猫托卡**是一个现代化的开源虚拟商品交易平台，专为卡密、激活码、会员等虚拟商品交易场景设计。同时也支持实体商品销售。

项目采用前后端分离架构，包含：
- **后端 API** - FastAPI + Tortoise ORM
- **前台界面** - Vue 3 + Tailwind CSS（用户端）
- **后台管理** - Vue 3 + Element Plus（管理员端）

## 特性

### 商品管理
- 支持虚拟商品和实体商品两种类型
- 虚拟商品自动发货（卡密库存系统）
- 多级分类、标签筛选
- 多图片展示、商品介绍（支持富文本）

### 订单系统
- 完整的订单生命周期管理
- 支持订单备注和发货记录
- 订单状态邮件通知
- 本地订单历史查询

### 支付系统
- 可扩展的支付接口设计
- 内置 TRC20 USDT / 微信 支付（无需第三方服务）
- 支付金额唯一标识，解决并发冲突
- 支付超时自动取消

### 平台配置
- 站点名称、Logo、货币符号
- 邮件服务配置（SMTP）
- 虚拟商品自动发货开关
- 联系信息配置

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+（生产环境）或 SQLite（开发环境）
- Redis 7+（支付系统需要）
- [uv](https://github.com/astral-sh/uv) 包管理器

### 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/Anning01/CattoCard.git
cd CattoCard
```

#### 2. 后端设置

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 初始化数据库（首次）
uv run aerich init-db

# 启动后端服务
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 前台界面

```bash
cd web
npm install
npm run dev
# 访问 http://localhost:5173
```

#### 4. 后台管理

```bash
cd admin
npm install
npm run dev
# 访问 http://localhost:5174
```

#### 5. 初始化管理员

首次启动后，访问后台管理界面或调用 API：

```bash
curl -X POST "http://localhost:8000/api/admin/auth/init" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

## Docker 部署

### 前置条件

- Docker 20.10+
- Docker Compose 2.0+

### 部署步骤

#### 1. 准备配置

```bash
# 克隆项目
git clone https://github.com/Anning01/CattoCard.git
cd CattoCard

# 配置环境变量
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 域名配置（必填）
DOMAIN=your-domain.com

# 是否启用 SSL（自动申请 Let's Encrypt 证书）
ENABLE_SSL=true
SSL_EMAIL=your-email@example.com

# 数据库配置
POSTGRES_USER=cardstore
POSTGRES_PASSWORD=your-secure-password  # 修改为强密码
POSTGRES_DB=cardstore

# JWT 密钥（必须修改）
SECRET_KEY=your-secret-key  # 使用 openssl rand -base64 32 生成

# 初始管理员账号（首次启动自动创建）
INIT_ADMIN_USERNAME=admin
INIT_ADMIN_PASSWORD=your-admin-password  # 请修改
```

#### 2. 启动服务

**推荐方式（使用启动脚本）：**

```bash
# 使用启动脚本（自动处理 SSL 证书申请）
./scripts/start.sh start

# 其他命令
./scripts/start.sh stop      # 停止服务
./scripts/start.sh restart   # 重启服务
./scripts/start.sh renew-ssl # 更新 SSL 证书
./scripts/start.sh logs      # 查看日志
```

**手动方式：**

```bash
# 构建并启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f backend

# 查看服务状态
docker compose ps
```

> 首次启动会自动初始化数据库并创建管理员，后续启动自动跳过。

**端口被占用？** 如果 80 端口已被其他服务使用，可以指定其他端口：

```bash
# 方式1：命令行指定
HTTP_PORT=8080 HTTPS_PORT=8443 docker compose up -d

# 方式2：在 .env 文件中配置
# HTTP_PORT=8080
# HTTPS_PORT=8443
```

然后通过 `http://localhost:8080` 访问。

#### 3. 访问服务

| 服务 | 地址 |
|------|------|
| 前台用户界面 | http://localhost |
| 后台管理界面 | http://localhost/admin |
| API 文档 | http://localhost/api/docs |

### 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                      Nginx (80/443)                     │
│                     反向代理 / 负载均衡                  │
└─────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
     ┌──────────┐   ┌──────────┐   ┌──────────┐
     │   Web    │   │  Admin   │   │ Backend  │
     │ (Vue 3)  │   │ (Vue 3)  │   │(FastAPI) │
     │  前台界面 │   │ 后台管理  │   │  API服务  │
     └──────────┘   └──────────┘   └──────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         ▼               ▼               ▼
                   ┌──────────┐   ┌──────────┐   ┌──────────┐
                   │PostgreSQL│   │  Redis   │   │ Uploads  │
                   │  数据库   │   │   缓存   │   │ 文件存储  │
                   └──────────┘   └──────────┘   └──────────┘
```

### 常用命令

```bash
# 停止服务
docker compose down

# 重启服务
docker compose restart

# 重新构建
docker compose up -d --build

# 查看后端日志
docker compose logs -f backend

# 进入容器
docker compose exec backend bash

# 数据库备份
docker compose exec db pg_dump -U cardstore cardstore > backup.sql
```

### 数据持久化

以下目录会被挂载到主机：

| 目录 | 说明 |
|------|------|
| `./uploads` | 上传的文件（图片等） |
| `./logs` | 应用日志 |
| `./data` | 应用数据 |
| `postgres_data` | 数据库文件（Docker Volume） |
| `redis_data` | Redis 数据（Docker Volume） |

### SSL 配置

#### 自动 SSL（Let's Encrypt，推荐）

在 `.env` 中配置域名并启用 SSL：

```env
DOMAIN=your-domain.com
ENABLE_SSL=true
SSL_EMAIL=your-email@example.com
```

使用启动脚本自动完成证书申请：

```bash
./scripts/start.sh start
```

脚本会自动：
1. 检查 `nginx/ssl/live/{DOMAIN}/` 目录下是否已存在有效证书
2. 如果证书不存在或即将过期（30天内），自动使用 certbot 申请/更新
3. 生成包含 HTTPS 的 Nginx 配置
4. 启动所有服务

**证书续期：**

```bash
# 手动续期
./scripts/start.sh renew-ssl

# 添加定时任务（推荐，每天凌晨2点检查）
echo "0 2 * * * cd /path/to/CattoCard && ./scripts/start.sh renew-ssl" | crontab -
```

#### 手动 SSL

将证书文件放入 `nginx/ssl/` 目录，修改 `nginx/conf.d/default.conf` 添加 HTTPS server 配置。

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DOMAIN` | 站点域名 | `localhost` | 是 |
| `ENABLE_SSL` | 是否启用 SSL | `false` | 否 |
| `SSL_EMAIL` | SSL 证书通知邮箱 | - | SSL 启用时必填 |
| `SECRET_KEY` | JWT 密钥 | - | **是** |
| `DATABASE_URL` | 数据库连接（本地开发） | `sqlite://./data/cardstore.db` | 否 |
| `POSTGRES_USER` | PostgreSQL 用户（Docker） | `cardstore` | 是 |
| `POSTGRES_PASSWORD` | PostgreSQL 密码（Docker） | - | **是** |
| `POSTGRES_DB` | PostgreSQL 数据库（Docker） | `cardstore` | 否 |
| `REDIS_URL` | Redis 连接（本地开发） | - | 否 |
| `DEBUG` | 调试模式 | `false` | 否 |
| `UPLOAD_DIR` | 上传目录 | `uploads` | 否 |
| `HTTP_PORT` | HTTP 端口 | `80` | 否 |
| `HTTPS_PORT` | HTTPS 端口 | `443` | 否 |

### 后台管理配置

大部分配置已移至后台管理界面，更加方便管理：

| 配置项 | 位置 |
|--------|------|
| 站点名称、Logo、描述 | 基础配置 → 站点设置 |
| 邮件服务器 (SMTP) | 基础配置 → 邮件配置 |
| 货币符号 | 基础配置 → 站点设置 |
| 联系信息 | 基础配置 → 站点设置 |
| 虚拟商品自动发货 | 基础配置 → 订单配置 |

## 使用指南

### 初始设置

1. **登录后台管理**
   - 访问 `/admin`，使用初始化时设置的管理员账号登录

2. **配置站点信息**
   - 进入 基础配置 → 站点设置
   - 设置站点名称、Logo、货币符号等

3. **配置邮件服务**（可选，用于订单通知）
   - 进入 基础配置 → 邮件配置
   - 填写 SMTP 服务器信息并测试

4. **添加支付方式**
   - 进入 商品管理 → 支付方式
   - 添加并配置支付方式（如 TRC20 USDT）

### 商品管理

#### 添加分类

1. 进入 商品管理 → 分类管理
2. 点击「添加分类」
3. 填写分类名称、别名（URL 用）、图标等
4. 支持二级分类（选择父分类）

#### 添加商品

1. 进入 商品管理 → 商品列表
2. 点击「添加商品」
3. 填写商品信息：
   - **基本信息**：名称、别名、价格、分类
   - **商品类型**：虚拟商品 / 实体商品
   - **库存**：实体商品手动设置库存；虚拟商品由卡密数量决定
   - **图片**：可上传多张，设置主图
   - **标签**：添加筛选标签（如：平台:PC端）
   - **介绍**：支持多个标签页，富文本内容
   - **支付方式**：选择商品支持的支付方式

#### 虚拟商品库存（卡密管理）

1. 在商品列表点击「库存」按钮
2. 添加卡密：
   - 支持单个添加
   - 支持批量导入（每行一个）
3. 卡密状态：
   - **未售出**：可用库存
   - **已售出**：已发货的卡密
4. 订单完成后自动发货卡密

### 订单管理

#### 订单列表

- 查看所有订单
- 按状态筛选：待支付、已支付、已完成、已取消
- 搜索订单号或邮箱

#### 订单处理

1. **待支付订单**
   - 等待用户支付
   - 超时自动取消

2. **已支付订单**
   - 虚拟商品：如开启自动发货，会自动发货卡密
   - 实体商品：需手动发货
   - 点击「发货」按钮，填写发货信息

3. **发货记录**
   - 虚拟商品：显示发送的卡密内容
   - 实体商品：显示物流信息

### 支付配置

#### TRC20 USDT 支付

1. 添加支付方式，选择类型 `trc20`
2. 配置项：
   - **收款地址**：您的 TRC20 钱包地址
   - **API Key**（可选）：TronGrid API Key，提高查询稳定性
3. 工作原理：
   - 系统在用户支付金额后添加随机小数（如 10.001234）
   - 通过金额精确匹配订单
   - 每 30 秒自动检查链上交易
4. 测试(uv 或者 python):
   - uv run python -m app.services.payment.providers.trc20 <你的钱包地址> <API_KEY>
   - python -m app.services.payment.providers.trc20 TXxxxxx your-api-key
## API 文档

### 文档地址

| 文档 | 地址 |
|------|------|
| Swagger UI | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |

### API 概览

| 模块 | 前缀 | 说明 |
|------|------|------|
| 前台接口 | `/api/v1/` | 商品浏览、下单等 |
| 管理接口 | `/api/admin/` | 后台管理（需 JWT 认证） |
| 通用接口 | `/api/common/` | 文件上传等 |
| 平台接口 | `/api/v1/platform/` | 站点配置、公开信息 |

### 响应格式

所有 API 返回统一 JSON 格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 认证方式

管理接口使用 JWT Bearer Token：

```bash
# 登录获取 token
curl -X POST "http://localhost:8000/api/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# 使用 token 访问接口
curl "http://localhost:8000/api/admin/products" \
  -H "Authorization: Bearer <your-token>"
```

## 技术栈

### 后端

| 技术 | 说明 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 高性能异步 Web 框架 |
| [Tortoise-ORM](https://tortoise.github.io/) | 异步 ORM |
| [Aerich](https://github.com/tortoise/aerich) | 数据库迁移工具 |
| [Pydantic](https://docs.pydantic.dev/) | 数据验证 |
| [Redis](https://redis.io/) | 缓存 & 支付状态存储 |
| [Loguru](https://github.com/Delgan/loguru) | 日志系统 |

### 前端

| 技术 | 说明 |
|------|------|
| [Vue 3](https://vuejs.org/) | 前端框架 |
| [Tailwind CSS](https://tailwindcss.com/) | 前台样式 |
| [Element Plus](https://element-plus.org/) | 后台 UI 组件库 |
| [Pinia](https://pinia.vuejs.org/) | 状态管理 |
| [Vue Router](https://router.vuejs.org/) | 路由管理 |

### 部署

| 技术 | 说明 |
|------|------|
| [Docker](https://www.docker.com/) | 容器化 |
| [Docker Compose](https://docs.docker.com/compose/) | 多容器编排 |
| [Nginx](https://nginx.org/) | 反向代理 |
| [PostgreSQL](https://www.postgresql.org/) | 生产数据库 |

## 项目结构

```
cardstore/
├── app/                      # 后端代码
│   ├── main.py               # 应用入口
│   ├── config.py             # 配置文件
│   ├── models/               # 数据库模型
│   ├── schemas/              # Pydantic 模型
│   ├── api/                  # API 路由
│   │   ├── v1/               # 前台接口
│   │   ├── admin/            # 管理接口
│   │   └── common.py         # 通用接口
│   ├── core/                 # 核心模块
│   │   ├── security.py       # 认证安全
│   │   ├── response.py       # 响应格式
│   │   └── exceptions.py     # 异常处理
│   ├── services/             # 业务逻辑
│   │   ├── email.py          # 邮件服务
│   │   ├── delivery.py       # 发货服务
│   │   └── payment/          # 支付服务
│   └── utils/                # 工具函数
├── web/                      # 前台界面（Vue 3 + Tailwind）
├── admin/                    # 后台管理（Vue 3 + Element Plus）
├── nginx/                    # Nginx 配置
│   ├── conf.d/               # 站点配置
│   ├── templates/            # 配置模板
│   └── ssl/                  # SSL 证书目录
├── scripts/                  # 管理脚本
│   ├── start.sh              # 启动脚本（含 SSL 自动化）
│   └── docker-entrypoint.sh  # Docker 入口脚本
├── certbot/                  # Certbot 验证目录
├── migrations/               # 数据库迁移文件
├── uploads/                  # 上传文件存储
├── logs/                     # 日志文件
├── docker-compose.yml        # Docker 编排配置
└── Dockerfile                # 后端 Docker 镜像
```

## 常见问题

### Q: 如何重置管理员密码？

```bash
# 进入后端容器
docker compose exec backend bash

# 使用 Python 重置
uv run python -c "
import asyncio
from tortoise import Tortoise
from app.config import TORTOISE_ORM
from app.models.admin import Admin
from app.core.security import get_password_hash

async def reset():
    await Tortoise.init(config=TORTOISE_ORM)
    admin = await Admin.filter(username='admin').first()
    if admin:
        admin.password = get_password_hash('new-password')
        await admin.save()
        print('密码已重置')
    await Tortoise.close_connections()

asyncio.run(reset())
"
```

### Q: 虚拟商品没有自动发货？

1. 检查是否开启了自动发货：后台 → 基础配置 → 订单配置
2. 检查是否有可用卡密：商品列表 → 库存管理
3. 查看后端日志是否有错误

### Q: 支付成功但订单未更新？

1. 检查 Redis 是否正常运行
2. 查看后端日志中的支付相关信息
3. TRC20 支付需要等待链上确认

### Q: 如何添加新的支付方式？

1. 在 `app/services/payment/providers/` 下创建新的提供商
2. 继承 `PaymentProvider` 基类
3. 实现 `create_payment` 和 `query_payment` 方法
4. 在 `registry.py` 中注册


### Q: 创建了支付方式但是显示支付方式不可用

1. 重启一下backend服务
2. docker compose restart backend


## 开源协议

[MIT License](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！
