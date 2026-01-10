<template>
  <div class="not-found">
    <div class="content">
      <h1>404</h1>
      <p>页面不存在</p>
      <router-link to="/dashboard">
        <el-button type="primary">返回首页</el-button>
      </router-link>
    </div>
  </div>
</template>

<style scoped lang="scss">
.not-found {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-bg-color);

  .content {
    text-align: center;

    h1 {
      font-size: 120px;
      font-weight: 600;
      color: var(--el-color-primary);
      margin: 0;
    }

    p {
      font-size: 24px;
      color: var(--el-text-color-secondary);
      margin: 20px 0 40px;
    }
  }
}
</style>
