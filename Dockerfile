FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 复制依赖文件和 README（pyproject.toml 需要）
COPY pyproject.toml README.md ./

# 安装依赖
RUN uv sync --no-dev

# 复制应用代码
COPY app ./app

# 复制启动脚本
COPY scripts ./scripts
RUN chmod +x /app/scripts/docker-entrypoint.sh

# 复制 .env.example 并自动生成 .env（如果不存在）
COPY .env.example .env.example
RUN if [ ! -f .env ]; then \
        echo "检测到 .env 文件不存在，从 .env.example 创建默认配置..."; \
        cp .env.example .env; \
        echo "生成随机密钥..."; \
        SECRET_KEY=$(openssl rand -base64 32); \
        sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/g" .env; \
        echo "生成随机管理员密码..."; \
        ADMIN_PASSWORD=123456; \
        sed -i "s/your-admin-password/$ADMIN_PASSWORD/g" .env; \
        echo "生成随机数据库密码..."; \
        DB_PASSWORD=123456; \
        sed -i "s/your-secure-password/$DB_PASSWORD/g" .env; \
        echo "✓ .env 文件已自动创建"; \
        echo "⚠️  请注意：管理员密码已自动生成，请查看日志或登录后修改"; \
    fi

# 创建必要目录
RUN mkdir -p uploads logs data migrations

# 暴露端口
EXPOSE 8000

# 启动命令
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
