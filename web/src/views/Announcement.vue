<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { get } from '@/utils/request'
import type { Announcement } from '@/types'
import { formatDate } from '@/utils/storage'
import { ChevronLeftIcon, MegaphoneIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const loading = ref(true)
const announcement = ref<Announcement | null>(null)

onMounted(async () => {
  const id = route.params.id as string
  try {
    const res = await get<Announcement>(`/platform/announcements/${id}`)
    announcement.value = res.data
    document.title = `${res.data.title} - CardStore`
  } catch {
    // 错误处理
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container-lg py-8">
      <!-- 返回按钮 -->
      <RouterLink to="/" class="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-6">
        <ChevronLeftIcon class="w-4 h-4" />
        返回首页
      </RouterLink>

      <!-- 加载状态 -->
      <div v-if="loading" class="bg-white rounded-2xl p-8">
        <div class="h-8 skeleton rounded w-2/3 mb-4" />
        <div class="h-4 skeleton rounded w-1/4 mb-8" />
        <div class="space-y-3">
          <div class="h-4 skeleton rounded w-full" />
          <div class="h-4 skeleton rounded w-full" />
          <div class="h-4 skeleton rounded w-3/4" />
        </div>
      </div>

      <!-- 公告内容 -->
      <div v-else-if="announcement" class="bg-white rounded-2xl overflow-hidden">
        <div class="bg-gradient-to-r from-primary-500 to-primary-600 px-8 py-6 text-white">
          <div class="flex items-center gap-2 mb-2">
            <MegaphoneIcon class="w-5 h-5" />
            <span class="text-sm font-medium opacity-90">公告</span>
          </div>
          <h1 class="text-2xl font-bold">{{ announcement.title }}</h1>
          <p class="text-sm opacity-80 mt-2">{{ formatDate(announcement.created_at) }}</p>
        </div>

        <div class="p-8">
          <div v-if="announcement.description" class="text-gray-500 mb-6 pb-6 border-b">
            {{ announcement.description }}
          </div>
          <div class="prose prose-sm max-w-none" v-html="announcement.content" />
        </div>
      </div>

      <!-- 不存在 -->
      <div v-else class="text-center py-16">
        <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <MegaphoneIcon class="w-10 h-10 text-gray-400" />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">公告不存在</h2>
        <p class="text-gray-500 mb-6">该公告可能已被删除或不存在</p>
        <RouterLink to="/" class="btn-primary">
          返回首页
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prose {
  color: #374151;
  line-height: 1.75;
}

.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.prose :deep(p) {
  margin-top: 1em;
  margin-bottom: 1em;
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5em;
  margin-top: 1em;
  margin-bottom: 1em;
}

.prose :deep(img) {
  max-width: 100%;
  border-radius: 0.5rem;
}

.prose :deep(a) {
  color: #4f46e5;
  text-decoration: underline;
}
</style>
