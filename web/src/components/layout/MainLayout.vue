<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useCartStore } from '@/stores/cart'
import { useAppStore } from '@/stores/app'
import { get } from '@/utils/request'
import type { Category, FooterLink } from '@/types'
import {
  ShoppingCartIcon,
  MagnifyingGlassIcon,
  Bars3Icon,
  XMarkIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/vue/24/outline'

const cartStore = useCartStore()
const appStore = useAppStore()
const categories = ref<Category[]>([])
const footerLinks = ref<FooterLink[]>([])
const mobileMenuOpen = ref(false)
const searchQuery = ref('')

onMounted(async () => {
  // 加载站点配置
  await appStore.loadSiteConfig()

  try {
    const [catRes, linksRes] = await Promise.all([
      get<Category[]>('/products/categories'),
      get<FooterLink[]>('/platform/footer-links'),
    ])
    categories.value = catRes.data
    footerLinks.value = linksRes.data
  } catch {
    // 忽略错误
  }
})

function handleSearch() {
  if (searchQuery.value.trim()) {
    window.location.href = `/products?search=${encodeURIComponent(searchQuery.value.trim())}`
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <!-- Header -->
    <header class="sticky top-0 z-40 glass border-b border-gray-200/50">
      <div class="container-lg">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <RouterLink to="/" class="flex items-center gap-2">
            <img
              :src="appStore.siteConfig.site_logo"
              :alt="appStore.siteConfig.site_name"
              class="h-8 w-auto"
            />
            <span class="text-xl font-bold text-gray-900 hidden sm:block">{{ appStore.siteConfig.site_name }}</span>
          </RouterLink>

          <!-- 桌面端导航 -->
          <nav class="hidden md:flex items-center gap-6">
            <RouterLink to="/" class="text-gray-600 hover:text-primary-600 transition-colors font-medium">
              首页
            </RouterLink>
            <RouterLink to="/products" class="text-gray-600 hover:text-primary-600 transition-colors font-medium">
              全部商品
            </RouterLink>
            <RouterLink to="/announcements" class="text-gray-600 hover:text-primary-600 transition-colors font-medium">
              公告通知
            </RouterLink>
          </nav>

          <!-- 右侧操作区 -->
          <div class="flex items-center gap-3">
            <!-- 搜索框 -->
            <div class="hidden sm:flex items-center relative">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索商品..."
                class="w-48 lg:w-64 pl-10 pr-4 py-2 text-sm bg-gray-100 text-gray-900 border-0 rounded-full focus:ring-2 focus:ring-primary-500/20 focus:bg-white transition-all"
                @keyup.enter="handleSearch"
              />
              <MagnifyingGlassIcon class="absolute left-3 w-5 h-5 text-gray-400" />
            </div>

            <!-- 订单查询 -->
            <RouterLink
              to="/orders"
              class="hidden sm:flex items-center gap-1.5 px-3 py-2 text-gray-600 hover:text-primary-600 transition-colors"
            >
              <ClipboardDocumentListIcon class="w-5 h-5" />
              <span class="text-sm font-medium">查订单</span>
            </RouterLink>

            <!-- 购物车 -->
            <RouterLink
              to="/cart"
              class="relative flex items-center gap-1.5 px-3 py-2 text-gray-600 hover:text-primary-600 transition-colors"
            >
              <ShoppingCartIcon class="w-5 h-5" />
              <span class="hidden sm:inline text-sm font-medium">购物车</span>
              <span
                v-if="cartStore.itemCount > 0"
                class="absolute -top-1 -right-1 w-5 h-5 bg-primary-500 text-white text-xs font-bold rounded-full flex items-center justify-center"
              >
                {{ cartStore.itemCount > 99 ? '99+' : cartStore.itemCount }}
              </span>
            </RouterLink>

            <!-- 移动端菜单按钮 -->
            <button class="md:hidden p-2" @click="mobileMenuOpen = true">
              <Bars3Icon class="w-6 h-6 text-gray-700" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- 移动端菜单 -->
    <Transition name="fade">
      <div v-if="mobileMenuOpen" class="fixed inset-0 z-50 bg-black/50" @click="mobileMenuOpen = false" />
    </Transition>
    <Transition name="slide">
      <div v-if="mobileMenuOpen" class="fixed inset-y-0 right-0 z-50 w-72 bg-white shadow-xl">
        <div class="flex items-center justify-between p-4 border-b">
          <span class="font-semibold text-gray-900">菜单</span>
          <button @click="mobileMenuOpen = false">
            <XMarkIcon class="w-6 h-6 text-gray-500" />
          </button>
        </div>
        <div class="p-4">
          <!-- 移动端搜索 -->
          <div class="relative mb-4">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索商品..."
              class="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-100 text-gray-900 border-0 rounded-xl focus:ring-2 focus:ring-primary-500/20"
              @keyup.enter="handleSearch"
            />
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
          <!-- 导航链接 -->
          <nav class="space-y-1">
            <RouterLink
              to="/"
              class="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-100 font-medium"
              @click="mobileMenuOpen = false"
            >
              首页
            </RouterLink>
            <RouterLink
              to="/products"
              class="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-100 font-medium"
              @click="mobileMenuOpen = false"
            >
              全部商品
            </RouterLink>
            <RouterLink
              to="/announcements"
              class="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-100 font-medium"
              @click="mobileMenuOpen = false"
            >
              公告通知
            </RouterLink>
            <RouterLink
              to="/orders"
              class="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-100 font-medium"
              @click="mobileMenuOpen = false"
            >
              查询订单
            </RouterLink>
          </nav>
        </div>
      </div>
    </Transition>

    <!-- 主内容 -->
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-900 text-gray-400">
      <div class="container-lg py-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <!-- 品牌信息 -->
          <div class="md:col-span-2">
            <div class="flex items-center gap-2 mb-4">
              <img
                :src="appStore.siteConfig.site_logo"
                :alt="appStore.siteConfig.site_name"
                class="h-8 w-auto"
              />
              <span class="text-xl font-bold text-white">{{ appStore.siteConfig.site_name }}</span>
            </div>
            <p class="text-sm leading-relaxed mb-4">
              {{ appStore.siteConfig.site_description }}
            </p>
          </div>

          <!-- 快速链接 -->
          <div>
            <h3 class="text-white font-semibold mb-4">快速链接</h3>
            <ul class="space-y-2 text-sm">
              <li>
                <RouterLink to="/" class="hover:text-white transition-colors">首页</RouterLink>
              </li>
              <li>
                <RouterLink to="/products" class="hover:text-white transition-colors">全部商品</RouterLink>
              </li>
              <li>
                <RouterLink to="/orders" class="hover:text-white transition-colors">查询订单</RouterLink>
              </li>
            </ul>
          </div>

          <!-- 协议链接 -->
          <div>
            <h3 class="text-white font-semibold mb-4">服务协议</h3>
            <ul class="space-y-2 text-sm">
              <li v-for="link in footerLinks.filter(l => l.link_type === 'agreement')" :key="link.id">
                <a :href="link.url" target="_blank" class="hover:text-white transition-colors">
                  {{ link.title }}
                </a>
              </li>
            </ul>
          </div>
        </div>

        <!-- 底部版权 -->
        <div class="border-t border-gray-800 mt-8 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p class="text-sm">© {{ new Date().getFullYear() }} {{ appStore.siteConfig.site_name }}. All rights reserved.</p>
          <div class="flex items-center gap-4">
            <a
              v-for="link in footerLinks.filter(l => l.link_type === 'friend_link')"
              :key="link.id"
              :href="link.url"
              target="_blank"
              class="text-sm hover:text-white transition-colors"
            >
              {{ link.title }}
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
