<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get } from '@/utils/request'
import type { ProductListItem, TagGroup, Category, PaginatedData } from '@/types'
import ProductCard from '@/components/product/ProductCard.vue'
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const products = ref<ProductListItem[]>([])
const tagGroups = ref<TagGroup[]>([])
const categories = ref<Category[]>([])
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
  pages: 0,
})

// 筛选条件
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedTags = ref<Record<string, string>>({}) // key -> value
const showFilters = ref(false)

// 当前分类信息
const currentCategory = computed(() => {
  if (!selectedCategory.value) return null
  for (const cat of categories.value) {
    if (cat.slug === selectedCategory.value) return cat
    if (cat.children) {
      const child = cat.children.find(c => c.slug === selectedCategory.value)
      if (child) return child
    }
  }
  return null
})

// 页面标题
const pageTitle = computed(() => {
  if (searchQuery.value) return `搜索: ${searchQuery.value}`
  if (currentCategory.value) return currentCategory.value.name
  return '全部商品'
})

// 有效筛选数量
const activeFilterCount = computed(() => {
  return Object.keys(selectedTags.value).length
})

// 初始化
onMounted(async () => {
  // 从 URL 读取参数
  const query = route.query
  searchQuery.value = (query.search as string) || ''
  selectedCategory.value = (route.params.slug as string) || null

  // 解析标签参数
  if (query.tags) {
    const tagsStr = query.tags as string
    tagsStr.split(',').forEach(tag => {
      const [key, value] = tag.split(':')
      if (key && value) {
        selectedTags.value[key] = value
      }
    })
  }

  // 加载数据
  await Promise.all([loadProducts(), loadFilters()])
})

// 监听路由变化
watch(() => route.params.slug, (newSlug) => {
  selectedCategory.value = (newSlug as string) || null
  pagination.value.page = 1
  loadProducts()
})

watch(() => route.query, () => {
  const query = route.query
  searchQuery.value = (query.search as string) || ''
  pagination.value.page = 1
  loadProducts()
}, { deep: true })

async function loadFilters() {
  try {
    const [tagsRes, categoriesRes] = await Promise.all([
      get<TagGroup[]>('/products/tags'),
      get<Category[]>('/products/categories'),
    ])
    tagGroups.value = tagsRes.data
    categories.value = categoriesRes.data
  } catch {
    // 忽略错误
  }
}

async function loadProducts() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    }

    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    if (selectedCategory.value) {
      params.category_slug = selectedCategory.value
    }

    // 构建标签筛选参数
    const tagFilters = Object.entries(selectedTags.value)
      .map(([key, value]) => `${key}:${value}`)
      .join(',')
    if (tagFilters) {
      params.tags = tagFilters
    }

    const res = await get<PaginatedData<ProductListItem>>('/products', { params })
    products.value = res.data.items
    pagination.value.total = res.data.total
    pagination.value.pages = res.data.pages
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  const query: Record<string, string> = {}
  if (searchQuery.value.trim()) {
    query.search = searchQuery.value.trim()
  }
  router.push({ path: '/products', query })
}

function toggleTag(key: string, value: string) {
  if (selectedTags.value[key] === value) {
    delete selectedTags.value[key]
  } else {
    selectedTags.value[key] = value
  }
  pagination.value.page = 1
  updateUrl()
  loadProducts()
}

function clearFilters() {
  selectedTags.value = {}
  pagination.value.page = 1
  updateUrl()
  loadProducts()
}

function updateUrl() {
  const query: Record<string, string> = {}
  if (searchQuery.value) {
    query.search = searchQuery.value
  }
  const tagFilters = Object.entries(selectedTags.value)
    .map(([key, value]) => `${key}:${value}`)
    .join(',')
  if (tagFilters) {
    query.tags = tagFilters
  }

  const path = selectedCategory.value ? `/category/${selectedCategory.value}` : '/products'
  router.replace({ path, query })
}

function changePage(page: number) {
  pagination.value.page = page
  loadProducts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="min-h-screen">
    <!-- 页面头部 -->
    <div class="bg-white border-b">
      <div class="container-lg py-6">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ pageTitle }}</h1>
            <p class="text-gray-500 mt-1">共 {{ pagination.total }} 件商品</p>
          </div>

          <!-- 搜索框 -->
          <div class="flex gap-3">
            <div class="relative flex-1 md:w-80">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索商品名称..."
                class="input pr-12"
                @keyup.enter="handleSearch"
              />
              <button
                class="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-primary-600"
                @click="handleSearch"
              >
                <MagnifyingGlassIcon class="w-5 h-5" />
              </button>
            </div>
            <button
              class="btn-secondary md:hidden relative"
              @click="showFilters = !showFilters"
            >
              <FunnelIcon class="w-5 h-5" />
              <span v-if="activeFilterCount > 0" class="absolute -top-1 -right-1 w-5 h-5 bg-primary-500 text-white text-xs rounded-full flex items-center justify-center">
                {{ activeFilterCount }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="container-lg py-6">
      <div class="flex gap-6">
        <!-- 侧边栏筛选 - 桌面端 -->
        <aside class="hidden md:block w-64 shrink-0">
          <div class="sticky top-20">
            <!-- 分类筛选 -->
            <div class="bg-white rounded-2xl p-5 mb-4">
              <h3 class="font-semibold text-gray-900 mb-4">商品分类</h3>
              <div class="space-y-1">
                <button
                  class="w-full text-left px-3 py-2 rounded-xl text-sm transition-colors"
                  :class="!selectedCategory ? 'bg-primary-50 text-primary-600 font-medium' : 'text-gray-600 hover:bg-gray-50'"
                  @click="selectedCategory = null; loadProducts()"
                >
                  全部商品
                </button>
                <template v-for="cat in categories" :key="cat.id">
                  <button
                    class="w-full text-left px-3 py-2 rounded-xl text-sm transition-colors"
                    :class="selectedCategory === cat.slug ? 'bg-primary-50 text-primary-600 font-medium' : 'text-gray-600 hover:bg-gray-50'"
                    @click="selectedCategory = cat.slug; loadProducts()"
                  >
                    {{ cat.name }}
                  </button>
                  <template v-if="cat.children && cat.children.length > 0">
                    <button
                      v-for="child in cat.children"
                      :key="child.id"
                      class="w-full text-left px-3 py-2 pl-6 rounded-xl text-sm transition-colors"
                      :class="selectedCategory === child.slug ? 'bg-primary-50 text-primary-600 font-medium' : 'text-gray-500 hover:bg-gray-50'"
                      @click="selectedCategory = child.slug; loadProducts()"
                    >
                      {{ child.name }}
                    </button>
                  </template>
                </template>
              </div>
            </div>

            <!-- 标签筛选 -->
            <div v-if="tagGroups.length > 0" class="bg-white rounded-2xl p-5">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-gray-900">筛选条件</h3>
                <button
                  v-if="activeFilterCount > 0"
                  class="text-xs text-primary-600 hover:text-primary-700"
                  @click="clearFilters"
                >
                  清除
                </button>
              </div>
              <div class="space-y-4">
                <div v-for="group in tagGroups" :key="group.key">
                  <h4 class="text-sm font-medium text-gray-700 mb-2">{{ group.key }}</h4>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="value in group.values"
                      :key="value"
                      class="text-xs px-2.5 py-1 rounded-full transition-all"
                      :class="selectedTags[group.key] === value
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                      @click="toggleTag(group.key, value)"
                    >
                      {{ value }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <!-- 移动端筛选抽屉 -->
        <Transition name="fade">
          <div v-if="showFilters" class="fixed inset-0 z-40 bg-black/50 md:hidden" @click="showFilters = false" />
        </Transition>
        <Transition name="slide-up">
          <div v-if="showFilters" class="fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-3xl max-h-[80vh] overflow-y-auto md:hidden">
            <div class="sticky top-0 bg-white px-5 py-4 border-b flex items-center justify-between">
              <h3 class="font-semibold text-gray-900">筛选</h3>
              <button @click="showFilters = false">
                <XMarkIcon class="w-6 h-6 text-gray-400" />
              </button>
            </div>
            <div class="p-5 space-y-6">
              <!-- 分类 -->
              <div>
                <h4 class="font-medium text-gray-900 mb-3">商品分类</h4>
                <div class="flex flex-wrap gap-2">
                  <button
                    class="filter-chip"
                    :class="{ 'filter-chip-active': !selectedCategory }"
                    @click="selectedCategory = null; loadProducts(); showFilters = false"
                  >
                    全部
                  </button>
                  <button
                    v-for="cat in categories"
                    :key="cat.id"
                    class="filter-chip"
                    :class="{ 'filter-chip-active': selectedCategory === cat.slug }"
                    @click="selectedCategory = cat.slug; loadProducts(); showFilters = false"
                  >
                    {{ cat.name }}
                  </button>
                </div>
              </div>

              <!-- 标签 -->
              <div v-for="group in tagGroups" :key="group.key">
                <h4 class="font-medium text-gray-900 mb-3">{{ group.key }}</h4>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="value in group.values"
                    :key="value"
                    class="filter-chip"
                    :class="{ 'filter-chip-active': selectedTags[group.key] === value }"
                    @click="toggleTag(group.key, value)"
                  >
                    {{ value }}
                  </button>
                </div>
              </div>
            </div>
            <div class="sticky bottom-0 bg-white border-t p-4 flex gap-3">
              <button class="btn-secondary flex-1" @click="clearFilters">重置</button>
              <button class="btn-primary flex-1" @click="showFilters = false">确定</button>
            </div>
          </div>
        </Transition>

        <!-- 商品列表 -->
        <div class="flex-1">
          <!-- 已选筛选标签 -->
          <div v-if="activeFilterCount > 0" class="flex flex-wrap gap-2 mb-4">
            <span class="text-sm text-gray-500">已选:</span>
            <button
              v-for="(value, key) in selectedTags"
              :key="key"
              class="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-50 text-primary-700 text-xs rounded-full"
              @click="toggleTag(key as string, value)"
            >
              {{ key }}: {{ value }}
              <XMarkIcon class="w-3.5 h-3.5" />
            </button>
            <button class="text-xs text-gray-500 hover:text-gray-700" @click="clearFilters">
              清除全部
            </button>
          </div>

          <!-- 加载骨架 -->
          <div v-if="loading" class="grid grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            <div v-for="i in 9" :key="i" class="bg-white rounded-2xl overflow-hidden">
              <div class="aspect-[4/3] skeleton" />
              <div class="p-4 space-y-3">
                <div class="h-4 skeleton rounded w-1/3" />
                <div class="h-5 skeleton rounded w-full" />
                <div class="flex justify-between items-center mt-3">
                  <div class="h-6 skeleton rounded w-20" />
                  <div class="h-8 skeleton rounded-lg w-16" />
                </div>
              </div>
            </div>
          </div>

          <!-- 商品网格 -->
          <div v-else-if="products.length > 0" class="grid grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            <ProductCard v-for="product in products" :key="product.id" :product="product" />
          </div>

          <!-- 空状态 -->
          <div v-else class="text-center py-16">
            <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <MagnifyingGlassIcon class="w-10 h-10 text-gray-400" />
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">没有找到商品</h3>
            <p class="text-gray-500 mb-4">试试修改搜索条件或清除筛选</p>
            <button class="btn-secondary" @click="clearFilters">清除筛选</button>
          </div>

          <!-- 分页 -->
          <div v-if="pagination.pages > 1" class="mt-8 flex justify-center">
            <div class="inline-flex items-center gap-1">
              <button
                class="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="pagination.page === 1"
                @click="changePage(pagination.page - 1)"
              >
                上一页
              </button>
              <template v-for="p in pagination.pages" :key="p">
                <button
                  v-if="p === 1 || p === pagination.pages || (p >= pagination.page - 2 && p <= pagination.page + 2)"
                  class="w-10 h-10 text-sm rounded-lg"
                  :class="p === pagination.page ? 'bg-primary-500 text-white' : 'text-gray-600 hover:bg-gray-100'"
                  @click="changePage(p)"
                >
                  {{ p }}
                </button>
                <span
                  v-else-if="p === pagination.page - 3 || p === pagination.page + 3"
                  class="px-2 text-gray-400"
                >
                  ...
                </span>
              </template>
              <button
                class="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="pagination.page === pagination.pages"
                @click="changePage(pagination.page + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
