from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "announcement" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "description" VARCHAR(500),
    "content" TEXT NOT NULL,
    "is_popup" BOOL NOT NULL DEFAULT False,
    "is_active" BOOL NOT NULL DEFAULT True,
    "sort_order" INT NOT NULL DEFAULT 0
);
COMMENT ON COLUMN "announcement"."created_at" IS '创建时间';
COMMENT ON COLUMN "announcement"."updated_at" IS '更新时间';
COMMENT ON COLUMN "announcement"."id" IS '主键ID';
COMMENT ON COLUMN "announcement"."title" IS '公告标题';
COMMENT ON COLUMN "announcement"."description" IS '公告描述';
COMMENT ON COLUMN "announcement"."content" IS '公告内容(富文本HTML)';
COMMENT ON COLUMN "announcement"."is_popup" IS '是否弹窗显示';
COMMENT ON COLUMN "announcement"."is_active" IS '是否启用';
COMMENT ON COLUMN "announcement"."sort_order" IS '排序';
COMMENT ON TABLE "announcement" IS '平台公告表';
CREATE TABLE IF NOT EXISTS "banner" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "image_url" VARCHAR(500) NOT NULL,
    "link_url" VARCHAR(500),
    "title" VARCHAR(100),
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "banner"."created_at" IS '创建时间';
COMMENT ON COLUMN "banner"."updated_at" IS '更新时间';
COMMENT ON COLUMN "banner"."id" IS '主键ID';
COMMENT ON COLUMN "banner"."image_url" IS '图片URL';
COMMENT ON COLUMN "banner"."link_url" IS '跳转链接';
COMMENT ON COLUMN "banner"."title" IS 'Banner标题';
COMMENT ON COLUMN "banner"."sort_order" IS '排序';
COMMENT ON COLUMN "banner"."is_active" IS '是否启用';
COMMENT ON TABLE "banner" IS '首页Banner表';
CREATE TABLE IF NOT EXISTS "contact_config" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "contact_config"."created_at" IS '创建时间';
COMMENT ON COLUMN "contact_config"."updated_at" IS '更新时间';
COMMENT ON COLUMN "contact_config"."id" IS '主键ID';
COMMENT ON COLUMN "contact_config"."content" IS '客服联系信息内容';
COMMENT ON COLUMN "contact_config"."is_active" IS '是否启用';
COMMENT ON TABLE "contact_config" IS '联系客服配置表';
CREATE TABLE IF NOT EXISTS "email_config" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "smtp_host" VARCHAR(255) NOT NULL,
    "smtp_port" INT NOT NULL DEFAULT 587,
    "smtp_user" VARCHAR(255) NOT NULL,
    "smtp_password" VARCHAR(255) NOT NULL,
    "from_email" VARCHAR(255) NOT NULL,
    "from_name" VARCHAR(100),
    "use_tls" BOOL NOT NULL DEFAULT True,
    "is_verified" BOOL NOT NULL DEFAULT False
);
COMMENT ON COLUMN "email_config"."created_at" IS '创建时间';
COMMENT ON COLUMN "email_config"."updated_at" IS '更新时间';
COMMENT ON COLUMN "email_config"."id" IS '主键ID';
COMMENT ON COLUMN "email_config"."smtp_host" IS 'SMTP服务器地址';
COMMENT ON COLUMN "email_config"."smtp_port" IS 'SMTP端口';
COMMENT ON COLUMN "email_config"."smtp_user" IS 'SMTP用户名';
COMMENT ON COLUMN "email_config"."smtp_password" IS 'SMTP密码';
COMMENT ON COLUMN "email_config"."from_email" IS '发件人邮箱';
COMMENT ON COLUMN "email_config"."from_name" IS '发件人名称';
COMMENT ON COLUMN "email_config"."use_tls" IS '是否使用TLS';
COMMENT ON COLUMN "email_config"."is_verified" IS '是否已验证';
COMMENT ON TABLE "email_config" IS '邮件服务器配置表';
CREATE TABLE IF NOT EXISTS "footer_link" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(100) NOT NULL,
    "url" VARCHAR(500) NOT NULL,
    "link_type" VARCHAR(11) NOT NULL DEFAULT 'friend_link',
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "footer_link"."created_at" IS '创建时间';
COMMENT ON COLUMN "footer_link"."updated_at" IS '更新时间';
COMMENT ON COLUMN "footer_link"."id" IS '主键ID';
COMMENT ON COLUMN "footer_link"."title" IS '链接标题';
COMMENT ON COLUMN "footer_link"."url" IS '链接地址';
COMMENT ON COLUMN "footer_link"."link_type" IS '链接类型';
COMMENT ON COLUMN "footer_link"."sort_order" IS '排序';
COMMENT ON COLUMN "footer_link"."is_active" IS '是否启用';
COMMENT ON TABLE "footer_link" IS '底部链接表';
CREATE TABLE IF NOT EXISTS "platform_config" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "key" VARCHAR(100) NOT NULL UNIQUE,
    "value" TEXT NOT NULL,
    "description" VARCHAR(255)
);
COMMENT ON COLUMN "platform_config"."created_at" IS '创建时间';
COMMENT ON COLUMN "platform_config"."updated_at" IS '更新时间';
COMMENT ON COLUMN "platform_config"."id" IS '主键ID';
COMMENT ON COLUMN "platform_config"."key" IS '配置键';
COMMENT ON COLUMN "platform_config"."value" IS '配置值';
COMMENT ON COLUMN "platform_config"."description" IS '配置描述';
COMMENT ON TABLE "platform_config" IS '平台配置表';
CREATE TABLE IF NOT EXISTS "category" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "description" VARCHAR(500),
    "icon" VARCHAR(500),
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True,
    "parent_id" INT REFERENCES "category" ("id") ON DELETE SET NULL
);
COMMENT ON COLUMN "category"."created_at" IS '创建时间';
COMMENT ON COLUMN "category"."updated_at" IS '更新时间';
COMMENT ON COLUMN "category"."id" IS '主键ID';
COMMENT ON COLUMN "category"."name" IS '分类名称';
COMMENT ON COLUMN "category"."slug" IS '分类别名';
COMMENT ON COLUMN "category"."description" IS '分类描述';
COMMENT ON COLUMN "category"."icon" IS '分类图标';
COMMENT ON COLUMN "category"."sort_order" IS '排序';
COMMENT ON COLUMN "category"."is_active" IS '是否启用';
COMMENT ON COLUMN "category"."parent_id" IS '父分类';
COMMENT ON TABLE "category" IS '商品分类表';
CREATE TABLE IF NOT EXISTS "payment_method" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "icon" VARCHAR(500),
    "fee_type" VARCHAR(10) NOT NULL DEFAULT 'percentage',
    "fee_value" DECIMAL(10,4) NOT NULL DEFAULT 0,
    "description" TEXT,
    "meta_data" JSONB NOT NULL,
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "payment_method"."created_at" IS '创建时间';
COMMENT ON COLUMN "payment_method"."updated_at" IS '更新时间';
COMMENT ON COLUMN "payment_method"."id" IS '主键ID';
COMMENT ON COLUMN "payment_method"."name" IS '支付名称';
COMMENT ON COLUMN "payment_method"."icon" IS '支付图标';
COMMENT ON COLUMN "payment_method"."fee_type" IS '手续费类型';
COMMENT ON COLUMN "payment_method"."fee_value" IS '手续费值';
COMMENT ON COLUMN "payment_method"."description" IS '支付描述';
COMMENT ON COLUMN "payment_method"."meta_data" IS '支付元数据配置';
COMMENT ON COLUMN "payment_method"."sort_order" IS '排序';
COMMENT ON COLUMN "payment_method"."is_active" IS '是否启用';
COMMENT ON TABLE "payment_method" IS '支付方式表';
CREATE TABLE IF NOT EXISTS "product" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "slug" VARCHAR(255) NOT NULL UNIQUE,
    "product_type" VARCHAR(8) NOT NULL DEFAULT 'virtual',
    "price" DECIMAL(10,2) NOT NULL,
    "stock" INT NOT NULL DEFAULT 0,
    "intro_title" VARCHAR(255),
    "intro_content" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "sort_order" INT NOT NULL DEFAULT 0,
    "category_id" INT REFERENCES "category" ("id") ON DELETE SET NULL
);
COMMENT ON COLUMN "product"."created_at" IS '创建时间';
COMMENT ON COLUMN "product"."updated_at" IS '更新时间';
COMMENT ON COLUMN "product"."id" IS '主键ID';
COMMENT ON COLUMN "product"."name" IS '商品名称';
COMMENT ON COLUMN "product"."slug" IS '商品别名';
COMMENT ON COLUMN "product"."product_type" IS '商品类型';
COMMENT ON COLUMN "product"."price" IS '商品价格';
COMMENT ON COLUMN "product"."stock" IS '库存数量';
COMMENT ON COLUMN "product"."intro_title" IS '介绍标题';
COMMENT ON COLUMN "product"."intro_content" IS '介绍内容(富文本HTML)';
COMMENT ON COLUMN "product"."is_active" IS '是否上架';
COMMENT ON COLUMN "product"."sort_order" IS '排序';
COMMENT ON COLUMN "product"."category_id" IS '商品分类';
COMMENT ON TABLE "product" IS '商品表';
CREATE TABLE IF NOT EXISTS "inventory_item" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "is_sold" BOOL NOT NULL DEFAULT False,
    "sold_at" TIMESTAMPTZ,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "inventory_item"."created_at" IS '创建时间';
COMMENT ON COLUMN "inventory_item"."updated_at" IS '更新时间';
COMMENT ON COLUMN "inventory_item"."id" IS '主键ID';
COMMENT ON COLUMN "inventory_item"."content" IS '库存内容(卡密等)';
COMMENT ON COLUMN "inventory_item"."is_sold" IS '是否已售出';
COMMENT ON COLUMN "inventory_item"."sold_at" IS '售出时间';
COMMENT ON COLUMN "inventory_item"."product_id" IS '关联商品';
COMMENT ON TABLE "inventory_item" IS '虚拟商品库存项表';
CREATE TABLE IF NOT EXISTS "product_image" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "image_url" VARCHAR(500) NOT NULL,
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_primary" BOOL NOT NULL DEFAULT False,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "product_image"."created_at" IS '创建时间';
COMMENT ON COLUMN "product_image"."updated_at" IS '更新时间';
COMMENT ON COLUMN "product_image"."id" IS '主键ID';
COMMENT ON COLUMN "product_image"."image_url" IS '图片URL';
COMMENT ON COLUMN "product_image"."sort_order" IS '排序';
COMMENT ON COLUMN "product_image"."is_primary" IS '是否主图';
COMMENT ON COLUMN "product_image"."product_id" IS '关联商品';
COMMENT ON TABLE "product_image" IS '商品图片表';
CREATE TABLE IF NOT EXISTS "product_tag" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "key" VARCHAR(100) NOT NULL,
    "value" VARCHAR(255) NOT NULL,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "product_tag"."created_at" IS '创建时间';
COMMENT ON COLUMN "product_tag"."updated_at" IS '更新时间';
COMMENT ON COLUMN "product_tag"."id" IS '主键ID';
COMMENT ON COLUMN "product_tag"."key" IS '标签键';
COMMENT ON COLUMN "product_tag"."value" IS '标签值';
COMMENT ON COLUMN "product_tag"."product_id" IS '关联商品';
COMMENT ON TABLE "product_tag" IS '商品标签表';
CREATE TABLE IF NOT EXISTS "order" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "order_no" VARCHAR(64) NOT NULL UNIQUE DEFAULT '',
    "status" VARCHAR(10) NOT NULL DEFAULT 'pending',
    "email" VARCHAR(255) NOT NULL,
    "currency" VARCHAR(10) NOT NULL DEFAULT 'USD',
    "total_price" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "paid_at" TIMESTAMPTZ,
    "payment_data" JSONB NOT NULL,
    "shipping_name" VARCHAR(100),
    "shipping_phone" VARCHAR(50),
    "shipping_address" TEXT,
    "remark" TEXT,
    "payment_method_id" INT REFERENCES "payment_method" ("id") ON DELETE SET NULL
);
COMMENT ON COLUMN "order"."created_at" IS '创建时间';
COMMENT ON COLUMN "order"."updated_at" IS '更新时间';
COMMENT ON COLUMN "order"."id" IS '主键ID';
COMMENT ON COLUMN "order"."order_no" IS '订单号';
COMMENT ON COLUMN "order"."status" IS '订单状态';
COMMENT ON COLUMN "order"."email" IS '下单邮箱';
COMMENT ON COLUMN "order"."currency" IS '结算币种';
COMMENT ON COLUMN "order"."total_price" IS '订单总价';
COMMENT ON COLUMN "order"."paid_at" IS '支付时间';
COMMENT ON COLUMN "order"."payment_data" IS '支付回调数据';
COMMENT ON COLUMN "order"."shipping_name" IS '收货人姓名';
COMMENT ON COLUMN "order"."shipping_phone" IS '收货人电话';
COMMENT ON COLUMN "order"."shipping_address" IS '收货地址';
COMMENT ON COLUMN "order"."remark" IS '订单备注';
COMMENT ON COLUMN "order"."payment_method_id" IS '支付方式';
COMMENT ON TABLE "order" IS '订单表';
CREATE TABLE IF NOT EXISTS "order_item" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "product_name" VARCHAR(255) NOT NULL,
    "quantity" INT NOT NULL DEFAULT 1,
    "price" DECIMAL(10,2) NOT NULL,
    "subtotal" DECIMAL(10,2) NOT NULL,
    "delivery_content" TEXT,
    "delivered_at" TIMESTAMPTZ,
    "order_id" INT NOT NULL REFERENCES "order" ("id") ON DELETE CASCADE,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE RESTRICT
);
COMMENT ON COLUMN "order_item"."created_at" IS '创建时间';
COMMENT ON COLUMN "order_item"."updated_at" IS '更新时间';
COMMENT ON COLUMN "order_item"."id" IS '主键ID';
COMMENT ON COLUMN "order_item"."product_name" IS '商品名称(快照)';
COMMENT ON COLUMN "order_item"."quantity" IS '购买数量';
COMMENT ON COLUMN "order_item"."price" IS '商品单价(下单时价格)';
COMMENT ON COLUMN "order_item"."subtotal" IS '小计金额';
COMMENT ON COLUMN "order_item"."delivery_content" IS '发货内容(卡密等)';
COMMENT ON COLUMN "order_item"."delivered_at" IS '发货时间';
COMMENT ON COLUMN "order_item"."order_id" IS '关联订单';
COMMENT ON COLUMN "order_item"."product_id" IS '关联商品';
COMMENT ON TABLE "order_item" IS '订单商品项表';
CREATE TABLE IF NOT EXISTS "order_log" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "action" VARCHAR(50) NOT NULL,
    "content" TEXT,
    "operator" VARCHAR(100),
    "order_id" INT NOT NULL REFERENCES "order" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "order_log"."created_at" IS '创建时间';
COMMENT ON COLUMN "order_log"."updated_at" IS '更新时间';
COMMENT ON COLUMN "order_log"."id" IS '主键ID';
COMMENT ON COLUMN "order_log"."action" IS '操作类型';
COMMENT ON COLUMN "order_log"."content" IS '日志内容';
COMMENT ON COLUMN "order_log"."operator" IS '操作人';
COMMENT ON COLUMN "order_log"."order_id" IS '关联订单';
COMMENT ON TABLE "order_log" IS '订单日志表';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "product_payment_method" (
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE,
    "paymentmethod_id" INT NOT NULL REFERENCES "payment_method" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "product_payment_method" IS '支付方式';
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_product_pay_product_833a63" ON "product_payment_method" ("product_id", "paymentmethod_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "FiPw=="
)
