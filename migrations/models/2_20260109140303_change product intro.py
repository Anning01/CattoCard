from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "product_intro" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "intro_type" VARCHAR(50) NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "content" TEXT NOT NULL,
    "icon" VARCHAR(255),
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "product_intro"."created_at" IS '创建时间';
COMMENT ON COLUMN "product_intro"."updated_at" IS '更新时间';
COMMENT ON COLUMN "product_intro"."id" IS '主键ID';
COMMENT ON COLUMN "product_intro"."intro_type" IS '介绍类型(如: info/advantage/tutorial/after_sale)';
COMMENT ON COLUMN "product_intro"."title" IS '介绍标题';
COMMENT ON COLUMN "product_intro"."content" IS '介绍内容(富文本HTML)';
COMMENT ON COLUMN "product_intro"."icon" IS '图标(可选)';
COMMENT ON COLUMN "product_intro"."sort_order" IS '排序';
COMMENT ON COLUMN "product_intro"."is_active" IS '是否启用';
COMMENT ON COLUMN "product_intro"."product_id" IS '关联商品';
COMMENT ON TABLE "product_intro" IS '商品介绍内容表';
        ALTER TABLE "product" DROP COLUMN "intro_content";
        ALTER TABLE "product" DROP COLUMN "intro_title";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "product" ADD "intro_content" TEXT;
        ALTER TABLE "product" ADD "intro_title" VARCHAR(255);
        COMMENT ON COLUMN "product"."intro_content" IS '介绍内容(富文本HTML)';
COMMENT ON COLUMN "product"."intro_title" IS '介绍标题';
        DROP TABLE IF EXISTS "product_intro";"""


MODELS_STATE = (
    "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"
    "5FRblkcrx+kG6zHKagp79TG3l+//B35zMWo="
)
