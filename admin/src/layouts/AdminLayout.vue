<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import {
  Odometer,
  Setting,
  Goods,
  List,
  Fold,
  Expand,
  Moon,
  Sunny,
  SwitchButton,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

// 图标映射
const iconMap: Record<string, unknown> = {
  Odometer,
  Setting,
  Goods,
  List,
}

// 获取菜单项
const menuRoutes = computed(() => {
  const mainRoute = router.options.routes.find((r) => r.path === '/')
  return mainRoute?.children?.filter((r) => !r.meta?.hidden) || []
})

// 当前激活菜单
const activeMenu = computed(() => {
  // 直接返回当前路由路径
  return route.path
})

// 默认展开的菜单
const defaultOpeneds = computed(() => {
  const matched = route.matched
  // 返回父级菜单路径（排除根路由和当前路由）
  return matched.slice(1, -1).map((r) => r.path)
})

// 处理菜单点击
function handleMenuSelect(path: string) {
  router.push(path)
}

// 退出登录
function handleLogout() {
  userStore.logout()
  router.push('/login')
}

// 判断是否有子菜单
function hasChildren(route: RouteRecordRaw): boolean {
  return !!(route.children && route.children.some((c) => !c.meta?.hidden))
}

// 获取可见子菜单
function getVisibleChildren(route: RouteRecordRaw): RouteRecordRaw[] {
  return route.children?.filter((c) => !c.meta?.hidden) || []
}

// 加载站点配置
onMounted(() => {
  appStore.loadSiteConfig()
})
</script>

<template>
  <el-container class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <img v-if="!appStore.sidebarCollapsed" src="@/assets/logo.png" alt="CardStore" class="logo-full" />
        <img v-else src="@/assets/logo.png" alt="CS" class="logo-collapsed" />
      </div>

      <el-menu
        :default-active="activeMenu"
        :default-openeds="defaultOpeneds"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        :unique-opened="true"
        background-color="transparent"
        @select="handleMenuSelect"
      >
        <template v-for="menuRoute in menuRoutes" :key="menuRoute.path">
          <!-- 有子菜单 -->
          <el-sub-menu v-if="hasChildren(menuRoute)" :index="`/${menuRoute.path}`">
            <template #title>
              <el-icon v-if="menuRoute.meta?.icon">
                <component :is="iconMap[menuRoute.meta.icon as string]" />
              </el-icon>
              <span>{{ menuRoute.meta?.title }}</span>
            </template>
            <el-menu-item
              v-for="child in getVisibleChildren(menuRoute)"
              :key="child.path"
              :index="`/${menuRoute.path}/${child.path}`"
            >
              {{ child.meta?.title }}
            </el-menu-item>
          </el-sub-menu>

          <!-- 无子菜单 -->
          <el-menu-item v-else :index="`/${menuRoute.path}`">
            <el-icon v-if="menuRoute.meta?.icon">
              <component :is="iconMap[menuRoute.meta.icon as string]" />
            </el-icon>
            <template #title>{{ menuRoute.meta?.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="appStore.toggleSidebar">
            <Fold v-if="!appStore.sidebarCollapsed" />
            <Expand v-else />
          </el-icon>

          <!-- 面包屑 -->
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="item in route.matched.slice(1)" :key="item.path">
              {{ item.meta?.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 暗黑模式切换 -->
          <el-tooltip :content="appStore.isDark ? '浅色模式' : '深色模式'" placement="bottom">
            <el-icon class="header-icon" @click="appStore.toggleDark()">
              <Moon v-if="appStore.isDark" />
              <Sunny v-else />
            </el-icon>
          </el-tooltip>

          <!-- 用户菜单 -->
          <el-dropdown trigger="click">
            <div class="user-info">
              <div class="avatar-letter">{{ userStore.avatarLetter }}</div>
              <span class="username">{{ userStore.nickname }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped lang="scss">
.admin-layout {
  height: 100vh;
}

.sidebar {
  background-color: var(--el-menu-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: width var(--transition-duration);
  overflow: hidden;

  .logo {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--el-border-color-light);

    .logo-full {
      max-width: 160px;
      max-height: 40px;
      object-fit: contain;
    }

    .logo-collapsed {
      max-width: 40px;
      max-height: 40px;
      object-fit: contain;
    }
  }

  .el-menu {
    border-right: none;
  }
}

.main-container {
  flex-direction: column;
}

.header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
      color: var(--el-text-color-primary);

      &:hover {
        color: var(--el-color-primary);
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;

    .header-icon {
      font-size: 20px;
      cursor: pointer;
      color: var(--el-text-color-regular);

      &:hover {
        color: var(--el-color-primary);
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;

      .avatar-letter {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
        color: #fff;
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        user-select: none;
      }

      .username {
        font-size: 14px;
        color: var(--el-text-color-primary);
      }
    }
  }
}

.main-content {
  background-color: var(--el-fill-color-light);
  overflow: auto;
}

// 路由切换动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
