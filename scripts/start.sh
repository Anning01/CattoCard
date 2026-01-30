#!/bin/bash
# CardStore 启动脚本
# 根据 .env 配置自动处理域名和 SSL

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 加载 .env（支持带空格的值）
if [ -f .env ]; then
    while IFS='=' read -r key value; do
        # 跳过注释和空行
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        # 去掉值两端的引号
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        export "$key=$value"
    done < .env
fi

DOMAIN="${DOMAIN:-localhost}"
ENABLE_SSL="${ENABLE_SSL:-false}"
SSL_EMAIL="${SSL_EMAIL:-}"

# 配置 nginx：根据 DOMAIN 替换 server_name
setup_nginx() {
    log_info "配置 Nginx (域名: $DOMAIN)"

    # 替换 default.conf 中的 server_name
    sed -i.bak "s/server_name .*/server_name ${DOMAIN};/" ./nginx/conf.d/default.conf
    rm -f ./nginx/conf.d/default.conf.bak

    if [ "$ENABLE_SSL" = "true" ] && [ -f "./nginx/ssl/fullchain.pem" ]; then
        # 启用 SSL 配置
        log_info "检测到 SSL 证书，启用 HTTPS"
        cp ./nginx/conf.d/default_ssl.conf ./nginx/conf.d/ssl.conf
        sed -i.bak "s/server_name .*/server_name ${DOMAIN};/" ./nginx/conf.d/ssl.conf
        rm -f ./nginx/conf.d/ssl.conf.bak
    else
        # 移除 SSL 配置
        rm -f ./nginx/conf.d/ssl.conf
    fi
}

# 申请 SSL 证书
request_cert() {
    if [ "$ENABLE_SSL" != "true" ]; then
        return 0
    fi

    if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "localhost" ]; then
        log_warn "域名为 localhost 或 IP，跳过 SSL 证书申请"
        return 0
    fi

    if [ -z "$SSL_EMAIL" ]; then
        log_error "启用 SSL 需要设置 SSL_EMAIL"
        exit 1
    fi

    mkdir -p ./nginx/ssl
    mkdir -p ./certbot/www

    # 检查证书是否已存在且有效
    if [ -f "./nginx/ssl/fullchain.pem" ]; then
        if openssl x509 -checkend 2592000 -noout -in "./nginx/ssl/fullchain.pem" 2>/dev/null; then
            log_info "SSL 证书有效，无需重新申请"
            return 0
        fi
        log_warn "SSL 证书即将过期，重新申请..."
    fi

    log_info "申请 SSL 证书 (域名: $DOMAIN)..."

    # 确保 nginx 已启动（用于 HTTP 验证）
    # 先用 HTTP 模式启动
    rm -f ./nginx/conf.d/ssl.conf
    docker compose up -d nginx
    sleep 3

    # certbot 申请
    docker run --rm \
        -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$SSL_EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"

    if [ $? -eq 0 ]; then
        # 复制证书到 nginx/ssl 根目录（简化路径）
        cp "./nginx/ssl/live/${DOMAIN}/fullchain.pem" "./nginx/ssl/fullchain.pem"
        cp "./nginx/ssl/live/${DOMAIN}/privkey.pem" "./nginx/ssl/privkey.pem"
        log_info "SSL 证书申请成功！"
    else
        log_error "SSL 证书申请失败，将以 HTTP 模式运行"
    fi
}

# 更新证书
renew_cert() {
    if [ "$ENABLE_SSL" != "true" ] || [ -z "$DOMAIN" ] || [ "$DOMAIN" = "localhost" ]; then
        return 0
    fi

    log_info "检查证书续期..."

    docker run --rm \
        -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        certbot/certbot renew --quiet

    # 更新证书副本
    if [ -f "./nginx/ssl/live/${DOMAIN}/fullchain.pem" ]; then
        cp "./nginx/ssl/live/${DOMAIN}/fullchain.pem" "./nginx/ssl/fullchain.pem"
        cp "./nginx/ssl/live/${DOMAIN}/privkey.pem" "./nginx/ssl/privkey.pem"
    fi

    docker compose exec nginx nginx -s reload 2>/dev/null || true
    log_info "证书续期检查完成"
}

# 启动
start() {
    request_cert
    setup_nginx

    log_info "启动服务..."
    docker compose up -d

    echo ""
    echo "=========================================="
    if [ "$ENABLE_SSL" = "true" ] && [ -f "./nginx/ssl/fullchain.pem" ]; then
        echo -e "  ${GREEN}网站:${NC} https://${DOMAIN}"
        echo -e "  ${GREEN}后台:${NC} https://${DOMAIN}/admin"
    else
        echo -e "  ${GREEN}网站:${NC} http://${DOMAIN}"
        echo -e "  ${GREEN}后台:${NC} http://${DOMAIN}/admin"
    fi
    echo "=========================================="
}

case "${1:-start}" in
    start)     start ;;
    stop)      docker compose down ;;
    restart)   docker compose restart ;;
    renew-ssl) renew_cert ;;
    *)
        echo "用法: $0 {start|stop|restart|renew-ssl}"
        exit 1
        ;;
esac
