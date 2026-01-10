<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { post } from '@/utils/request'
import { getOrderHistory, formatPrice, formatDate, getOrderStatusText, getOrderStatusColor, clearOrderHistory } from '@/utils/storage'
import type { OrderListItem, LocalOrderRecord } from '@/types'
import { useAppStore } from '@/stores/app'
import {
  MagnifyingGlassIcon,
  ClockIcon,
  EnvelopeIcon,
  DocumentTextIcon,
  TrashIcon,
  ArrowRightIcon,
  MapPinIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const appStore = useAppStore()

const activeTab = ref<'query' | 'history'>('query')
const loading = ref(false)

// 查询表单
const queryForm = ref({
  email: '',
  orderNo: '',
})

// 查询结果
const queryResults = ref<OrderListItem[]>([])

// 本地历史记录
const localHistory = ref<LocalOrderRecord[]>([])

onMounted(() => {
  localHistory.value = getOrderHistory()
  // 如果有历史记录，默认显示历史标签
  if (localHistory.value.length > 0) {
    activeTab.value = 'history'
  }
})

async function handleQuery() {
  if (!queryForm.value.email) {
    appStore.warning('请输入邮箱地址')
    return
  }

  loading.value = true
  try {
    const res = await post<OrderListItem[]>('/orders/query', {
      email: queryForm.value.email,
      order_no: queryForm.value.orderNo || undefined,
    })
    queryResults.value = res.data

    if (res.data.length === 0) {
      appStore.info('未找到相关订单')
    }
  } catch (error: unknown) {
    appStore.error((error as Error).message || '查询失败')
  } finally {
    loading.value = false
  }
}

function viewOrder(orderNo: string, email: string) {
  router.push(`/order/${orderNo}?email=${encodeURIComponent(email)}`)
}

function handleClearHistory() {
  if (confirm('确定要清除所有历史记录吗？')) {
    clearOrderHistory()
    localHistory.value = []
    appStore.success('历史记录已清除')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container-lg py-8">
      <h1 class="text-2xl font-bold text-gray-900 mb-8">查询订单</h1>

      <div class="max-w-3xl mx-auto">
        <!-- Tab 切换 -->
        <div class="flex gap-1 p-1 bg-gray-100 rounded-xl mb-6">
          <button
            class="flex-1 py-2.5 text-sm font-medium rounded-lg transition-all"
            :class="activeTab === 'query' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'query'"
          >
            <MagnifyingGlassIcon class="w-4 h-4 inline-block mr-1.5" />
            邮箱查询
          </button>
          <button
            class="flex-1 py-2.5 text-sm font-medium rounded-lg transition-all relative"
            :class="activeTab === 'history' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'history'"
          >
            <ClockIcon class="w-4 h-4 inline-block mr-1.5" />
            历史记录
            <span v-if="localHistory.length > 0" class="absolute -top-1 -right-1 w-5 h-5 bg-primary-500 text-white text-xs rounded-full flex items-center justify-center">
              {{ localHistory.length > 99 ? '99+' : localHistory.length }}
            </span>
          </button>
        </div>

        <!-- 邮箱查询 -->
        <div v-if="activeTab === 'query'" class="space-y-6">
          <div class="bg-white rounded-2xl p-6">
            <h2 class="font-semibold text-gray-900 mb-4">通过邮箱查询订单</h2>
            <p class="text-gray-500 text-sm mb-6">输入下单时使用的邮箱地址，可选择性输入订单号精确查询</p>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  邮箱地址 <span class="text-red-500">*</span>
                </label>
                <div class="relative">
                  <EnvelopeIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    v-model="queryForm.email"
                    type="email"
                    placeholder="请输入下单邮箱"
                    class="input pl-12"
                    @keyup.enter="handleQuery"
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  订单号（可选）
                </label>
                <div class="relative">
                  <DocumentTextIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    v-model="queryForm.orderNo"
                    type="text"
                    placeholder="输入订单号可精确查询"
                    class="input pl-12"
                    @keyup.enter="handleQuery"
                  />
                </div>
              </div>

              <button
                class="btn-primary w-full btn-lg"
                :disabled="loading || !queryForm.email"
                @click="handleQuery"
              >
                <MagnifyingGlassIcon v-if="!loading" class="w-5 h-5" />
                <span v-if="loading">查询中...</span>
                <span v-else>查询订单</span>
              </button>
            </div>
          </div>

          <!-- 查询结果 -->
          <div v-if="queryResults.length > 0" class="bg-white rounded-2xl overflow-hidden">
            <div class="px-6 py-4 border-b">
              <h3 class="font-semibold text-gray-900">查询结果</h3>
              <p class="text-sm text-gray-500 mt-1">共找到 {{ queryResults.length }} 个订单</p>
            </div>
            <div class="divide-y">
              <div
                v-for="order in queryResults"
                :key="order.id"
                class="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                @click="viewOrder(order.order_no, order.email)"
              >
                <div class="flex items-start justify-between gap-4">
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-mono text-sm text-gray-900">{{ order.order_no }}</span>
                      <span
                        class="px-2 py-0.5 text-xs rounded-full"
                        :class="getOrderStatusColor(order.status)"
                      >
                        {{ getOrderStatusText(order.status) }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-500">{{ formatDate(order.created_at) }}</p>
                    <!-- 收货信息（实体商品） -->
                    <div v-if="order.shipping_name || order.shipping_address" class="mt-2 p-2 bg-gray-50 rounded-lg text-xs text-gray-600">
                      <div class="flex items-start gap-1">
                        <MapPinIcon class="w-3.5 h-3.5 text-gray-400 shrink-0 mt-0.5" />
                        <div>
                          <span v-if="order.shipping_name">{{ order.shipping_name }}</span>
                          <span v-if="order.shipping_phone" class="ml-2">{{ order.shipping_phone }}</span>
                          <p v-if="order.shipping_address" class="mt-0.5 text-gray-500">{{ order.shipping_address }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="text-right shrink-0">
                    <div class="font-medium text-gray-900">{{ formatPrice(order.total_price) }}</div>
                    <ArrowRightIcon class="w-4 h-4 text-gray-400 ml-auto mt-1" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 历史记录 -->
        <div v-else class="space-y-4">
          <div v-if="localHistory.length === 0" class="bg-white rounded-2xl p-12 text-center">
            <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <ClockIcon class="w-8 h-8 text-gray-400" />
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">暂无历史记录</h3>
            <p class="text-gray-500">您在此浏览器下单后，订单会自动保存在这里</p>
          </div>

          <template v-else>
            <div class="flex items-center justify-between mb-4">
              <p class="text-gray-500 text-sm">共 {{ localHistory.length }} 条记录（保存在本地浏览器）</p>
              <button
                class="text-sm text-red-500 hover:text-red-600 flex items-center gap-1"
                @click="handleClearHistory"
              >
                <TrashIcon class="w-4 h-4" />
                清除记录
              </button>
            </div>

            <div class="bg-white rounded-2xl overflow-hidden">
              <div class="divide-y">
                <div
                  v-for="order in localHistory"
                  :key="order.order_no"
                  class="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  @click="viewOrder(order.order_no, order.email)"
                >
                  <div class="flex items-start justify-between gap-4">
                    <div class="min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-mono text-sm text-gray-900">{{ order.order_no }}</span>
                        <span
                          class="px-2 py-0.5 text-xs rounded-full"
                          :class="getOrderStatusColor(order.status)"
                        >
                          {{ getOrderStatusText(order.status) }}
                        </span>
                      </div>
                      <p class="text-sm text-gray-500">{{ order.email }}</p>
                      <p class="text-xs text-gray-400 mt-1">{{ formatDate(order.created_at) }}</p>
                    </div>
                    <div class="text-right shrink-0">
                      <div class="font-medium text-gray-900">{{ formatPrice(order.total_price) }}</div>
                      <ArrowRightIcon class="w-4 h-4 text-gray-400 ml-auto mt-1" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
