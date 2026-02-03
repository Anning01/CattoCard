<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { get } from '@/utils/request'
import type { Banner, Announcement, ProductListItem, Category, PaginatedData } from '@/types'
import ProductCard from '@/components/product/ProductCard.vue'
import { ChevronRightIcon, MegaphoneIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { formatDate } from '@/utils/storage'

const loading = ref(true)
const banners = ref<Banner[]>([])
const announcements = ref<Announcement[]>([])
const popupAnnouncement = ref<Announcement | null>(null)
const showPopup = ref(false)
const products = ref<ProductListItem[]>([])
const categories = ref<Category[]>([])
const currentBanner = ref(0)

onMounted(async () => {
  try {
    const [bannersRes, announcementsRes, popupRes, productsRes, categoriesRes] = await Promise.all([
      get<Banner[]>('/platform/banners'),
      get<Announcement[]>('/platform/announcements'),
      get<Announcement | null>('/platform/announcements/popup'),
      get<PaginatedData<ProductListItem>>('/products', { params: { page_size: 8 } }),
      get<Category[]>('/products/categories'),
    ])

    banners.value = bannersRes.data
    announcements.value = announcementsRes.data
    products.value = productsRes.data.items
    categories.value = categoriesRes.data

    if (popupRes.data) {
      popupAnnouncement.value = popupRes.data
      // 检查是否已经显示过
      const shown = sessionStorage.getItem(`popup_${popupRes.data.id}`)
      if (!shown) {
        showPopup.value = true
      }
    }

    // Banner 自动轮播
    if (banners.value.length > 1) {
      setInterval(() => {
        currentBanner.value = (currentBanner.value + 1) % banners.value.length
      }, 5000)
    }
  } finally {
    loading.value = false
  }
})

function closePopup() {
  showPopup.value = false
  if (popupAnnouncement.value) {
    sessionStorage.setItem(`popup_${popupAnnouncement.value.id}`, '1')
  }
}

function goToBanner(banner: Banner) {
  if (banner.link_url) {
    window.open(banner.link_url, '_blank')
  }
}
</script>

<template>
  <div>
    <!-- 弹窗公告 -->
    <Transition name="fade">
      <div v-if="showPopup && popupAnnouncement" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @mousedown.self="closePopup">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full animate-scale-in overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-2">
              <MegaphoneIcon class="w-5 h-5 text-primary-500" />
              <h3 class="font-semibold text-gray-900 dark:text-gray-100">{{ popupAnnouncement.title }}</h3>
            </div>
            <button class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg" @click="closePopup">
              <XMarkIcon class="w-5 h-5 text-gray-400 dark:text-gray-500" />
            </button>
          </div>
          <div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
            <div class="prose prose-sm dark:prose-invert text-gray-700 dark:text-gray-300" v-html="popupAnnouncement.content" />
          </div>
          <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
            <button class="btn-primary w-full" @click="closePopup">我知道了</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Banner 轮播 -->
    <section v-if="banners.length > 0" class="relative">
      <div class="container-lg py-6">
        <div class="relative rounded-2xl overflow-hidden aspect-[21/9] bg-gray-100">
          <TransitionGroup name="banner">
            <div
              v-for="(banner, index) in banners"
              :key="banner.id"
              v-show="index === currentBanner"
              class="absolute inset-0 cursor-pointer"
              @click="goToBanner(banner)"
            >
              <img :src="banner.image_url" :alt="`Banner ${index + 1}`" class="w-full h-full object-cover" />
            </div>
          </TransitionGroup>
          <!-- 指示器 -->
          <div v-if="banners.length > 1" class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
            <button
              v-for="(_, index) in banners"
              :key="index"
              class="w-2 h-2 rounded-full transition-all"
              :class="index === currentBanner ? 'bg-white w-6' : 'bg-white/50'"
              @click="currentBanner = index"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- 公告滚动 -->
    <section v-if="announcements.length > 0" class="border-b bg-gradient-to-r from-amber-50 to-orange-50">
      <div class="container-lg py-3">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-amber-600 shrink-0">
            <MegaphoneIcon class="w-5 h-5" />
            <span class="text-sm font-medium">公告</span>
          </div>
          <div class="flex-1 overflow-hidden">
            <div class="flex gap-8 animate-marquee">
              <RouterLink
                v-for="ann in announcements"
                :key="ann.id"
                :to="`/announcement/${ann.id}`"
                class="text-sm text-gray-600 hover:text-primary-600 whitespace-nowrap shrink-0"
              >
                {{ ann.title }}
                <span class="text-gray-400 ml-2">{{ formatDate(ann.created_at) }}</span>
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 分类导航 -->
    <section v-if="categories.length > 0" class="py-8">
      <div class="container-lg">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold text-gray-900">商品分类</h2>
          <RouterLink to="/products" class="flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium">
            查看全部
            <ChevronRightIcon class="w-4 h-4" />
          </RouterLink>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <RouterLink
            v-for="cat in categories"
            :key="cat.id"
            :to="`/category/${cat.slug}`"
            class="group p-4 bg-white rounded-2xl border border-gray-100 hover:border-primary-200 hover:shadow-lg transition-all text-center"
          >
            <div class="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-primary-100 to-primary-50 flex items-center justify-center group-hover:from-primary-200 group-hover:to-primary-100 transition-colors">
              <img v-if="cat.icon" :src="cat.icon" :alt="cat.name" class="w-6 h-6" />
              <span v-else class="text-xl">📦</span>
            </div>
            <h3 class="font-medium text-gray-900 group-hover:text-primary-600 transition-colors">
              {{ cat.name }}
            </h3>
            <p v-if="cat.children && cat.children.length > 0" class="text-xs text-gray-400 mt-1">
              {{ cat.children.length }} 个子分类
            </p>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- 热门商品 -->
    <section class="py-8 bg-gradient-to-b from-gray-50 to-white">
      <div class="container-lg">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold text-gray-900">热门商品</h2>
          <RouterLink to="/products" class="flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium">
            更多商品
            <ChevronRightIcon class="w-4 h-4" />
          </RouterLink>
        </div>

        <!-- 加载骨架 -->
        <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          <div v-for="i in 8" :key="i" class="bg-white rounded-2xl overflow-hidden">
            <div class="aspect-[4/3] skeleton" />
            <div class="p-4 space-y-3">
              <div class="h-4 skeleton rounded w-1/3" />
              <div class="h-5 skeleton rounded w-full" />
              <div class="h-5 skeleton rounded w-2/3" />
              <div class="flex justify-between items-center mt-3">
                <div class="h-6 skeleton rounded w-20" />
                <div class="h-8 skeleton rounded-lg w-16" />
              </div>
            </div>
          </div>
        </div>

        <!-- 商品列表 -->
        <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          <ProductCard v-for="product in products" :key="product.id" :product="product" />
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && products.length === 0" class="text-center py-16">
          <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <span class="text-4xl">📦</span>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">暂无商品</h3>
          <p class="text-gray-500">商品正在上架中，请稍后再来</p>
        </div>
      </div>
    </section>

    <!-- 特色服务 -->
    <section class="py-12 bg-white">
      <div class="container-lg">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="text-center">
            <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-100 to-blue-50 flex items-center justify-center">
              <span class="text-2xl">⚡</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-1">即时发货</h3>
            <p class="text-sm text-gray-500">自动发货，秒到账</p>
          </div>
          <div class="text-center">
            <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-green-100 to-green-50 flex items-center justify-center">
              <span class="text-2xl">🔒</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-1">安全交易</h3>
            <p class="text-sm text-gray-500">支付安全有保障</p>
          </div>
          <div class="text-center">
            <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-100 to-purple-50 flex items-center justify-center">
              <span class="text-2xl">💎</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-1">品质保证</h3>
            <p class="text-sm text-gray-500">正品保障，质量可靠</p>
          </div>
          <div class="text-center">
            <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-100 to-amber-50 flex items-center justify-center">
              <span class="text-2xl">🎧</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-1">售后无忧</h3>
            <p class="text-sm text-gray-500">专业客服，随时在线</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.banner-enter-active,
.banner-leave-active {
  transition: opacity 0.5s ease;
}

.banner-enter-from,
.banner-leave-to {
  opacity: 0;
}

@keyframes marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

.animate-marquee {
  animation: marquee 30s linear infinite;
}

.animate-marquee:hover {
  animation-play-state: paused;
}
</style>
