<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { get } from '@/utils/request'
import type { Announcement } from '@/types'
import { useAppStore } from '@/stores/app'
import { ChevronRightIcon } from '@heroicons/vue/24/outline'

const appStore = useAppStore()
const loading = ref(true)
const announcements = ref<Announcement[]>([])
const expandedId = ref<number | null>(null)

onMounted(async () => {
  document.title = `公告通知 - ${appStore.siteConfig.site_name}`
  try {
    const res = await get<Announcement[]>('/platform/announcements')
    announcements.value = res.data
  } catch {
    // 错误处理
  } finally {
    loading.value = false
  }
})

// 按年月分组公告
const groupedAnnouncements = computed(() => {
  const groups: { [key: string]: Announcement[] } = {}
  for (const item of announcements.value) {
    const date = new Date(item.created_at)
    const key = `${date.getFullYear()}年${date.getMonth() + 1}月`
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(item)
  }
  return groups
})

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container-lg py-8">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-gray-900">公告通知</h1>
        <p class="text-gray-500 mt-1">了解最新动态和重要通知</p>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="space-y-6">
        <div v-for="i in 3" :key="i" class="bg-white rounded-2xl p-6">
          <div class="h-5 skeleton rounded w-1/4 mb-4" />
          <div class="space-y-4">
            <div class="flex gap-4">
              <div class="w-3 h-3 skeleton rounded-full mt-1.5" />
              <div class="flex-1">
                <div class="h-5 skeleton rounded w-2/3 mb-2" />
                <div class="h-4 skeleton rounded w-1/3" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="announcements.length === 0" class="bg-white rounded-2xl p-12 text-center">
        <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <svg class="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">暂无公告</h2>
        <p class="text-gray-500">目前还没有发布任何公告</p>
      </div>

      <!-- 时间线公告列表 -->
      <div v-else class="space-y-8">
        <div v-for="(items, monthKey) in groupedAnnouncements" :key="monthKey">
          <!-- 月份标题 -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
              <span class="text-sm font-bold text-primary-600">最新</span>
            </div>
            <span class="text-lg font-semibold text-gray-900">{{ monthKey }}</span>
          </div>

          <!-- 时间线内容 -->
          <div class="ml-5 border-l-2 border-gray-200 pl-8 space-y-4">
            <div
              v-for="item in items"
              :key="item.id"
              class="relative bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"
            >
              <!-- 时间线圆点 -->
              <div class="absolute -left-[2.6rem] top-6 w-3 h-3 rounded-full bg-primary-500 ring-4 ring-white" />

              <!-- 公告卡片 -->
              <div class="p-5">
                <div class="flex items-start justify-between gap-4">
                  <div class="flex-1 min-w-0">
                    <RouterLink
                      :to="`/announcement/${item.id}`"
                      class="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors line-clamp-1"
                    >
                      {{ item.title }}
                    </RouterLink>
                    <p v-if="item.description" class="text-gray-500 mt-1 line-clamp-2">
                      {{ item.description }}
                    </p>
                    <div class="flex items-center gap-4 mt-3 text-sm text-gray-400">
                      <span>{{ formatDate(item.created_at) }}</span>
                      <span v-if="item.is_popup" class="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium">
                        置顶
                      </span>
                    </div>
                  </div>
                  <button
                    class="shrink-0 w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition-colors"
                    @click="toggleExpand(item.id)"
                  >
                    <ChevronRightIcon
                      class="w-5 h-5 text-gray-400 transition-transform"
                      :class="{ 'rotate-90': expandedId === item.id }"
                    />
                  </button>
                </div>

                <!-- 展开内容 -->
                <Transition name="expand">
                  <div v-if="expandedId === item.id" class="mt-4 pt-4 border-t border-gray-100">
                    <div class="prose prose-sm max-w-none text-gray-600" v-html="item.content" />
                    <RouterLink
                      :to="`/announcement/${item.id}`"
                      class="inline-flex items-center gap-1 mt-4 text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                      查看完整内容
                      <ChevronRightIcon class="w-4 h-4" />
                    </RouterLink>
                  </div>
                </Transition>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

.prose {
  color: #4b5563;
  line-height: 1.7;
}

.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
  color: #1f2937;
}

.prose :deep(p) {
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5em;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :deep(img) {
  max-width: 100%;
  border-radius: 0.5rem;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.prose :deep(a) {
  color: #4f46e5;
  text-decoration: underline;
}
</style>
