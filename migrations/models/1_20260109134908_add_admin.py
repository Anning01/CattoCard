from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "admin" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "nickname" VARCHAR(100),
    "email" VARCHAR(255),
    "is_active" BOOL NOT NULL DEFAULT True,
    "is_superuser" BOOL NOT NULL DEFAULT False,
    "last_login_at" TIMESTAMPTZ
);
COMMENT ON COLUMN "admin"."created_at" IS '创建时间';
COMMENT ON COLUMN "admin"."updated_at" IS '更新时间';
COMMENT ON COLUMN "admin"."id" IS '主键ID';
COMMENT ON COLUMN "admin"."username" IS '用户名';
COMMENT ON COLUMN "admin"."password_hash" IS '密码哈希';
COMMENT ON COLUMN "admin"."nickname" IS '昵称';
COMMENT ON COLUMN "admin"."email" IS '邮箱';
COMMENT ON COLUMN "admin"."is_active" IS '是否启用';
COMMENT ON COLUMN "admin"."is_superuser" IS '是否超级管理员';
COMMENT ON COLUMN "admin"."last_login_at" IS '最后登录时间';
COMMENT ON TABLE "admin" IS '管理员表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "admin";"""


MODELS_STATE = (
    "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"
)
