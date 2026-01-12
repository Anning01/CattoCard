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

# 创建必要目录
RUN mkdir -p uploads logs data migrations

# 暴露端口
EXPOSE 8000

# 启动命令
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
