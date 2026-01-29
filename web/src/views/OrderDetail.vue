<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { get, post } from '@/utils/request'
import {
  formatPrice,
  formatDate,
  getOrderStatusText,
  getOrderStatusColor,
  updateOrderInHistory,
  copyText,
} from '@/utils/storage'
import type { OrderDetail, PaymentInitResponse, PaymentStatusResponse } from '@/types'
import {
  CheckCircleIcon,
  ClockIcon,
  TruckIcon,
  XCircleIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  ChevronLeftIcon,
  ChatBubbleLeftRightIcon,
  MapPinIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useAppStore } from '@/stores/app'
import QrcodeVue from 'qrcode.vue'

const route = useRoute()
const appStore = useAppStore()

// 取消订单确认弹窗
const showCancelDialog = ref(false)

const loading = ref(true)
const order = ref<OrderDetail | null>(null)
const email = ref('')

// 支付相关状态
const paymentLoading = ref(false)
const paymentData = ref<PaymentInitResponse | null>(null)
const showPaymentModal = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

const statusIcon = computed(() => {
  if (!order.value) return ClockIcon
  const icons: Record<string, unknown> = {
    pending: ClockIcon,
    paid: CheckCircleIcon,
    processing: TruckIcon,
    completed: CheckCircleIcon,
    cancelled: XCircleIcon,
    refunded: ArrowPathIcon,
  }
  return icons[order.value.status] || ClockIcon
})

// 判断是否有实体商品
const hasPhysicalItems = computed(() => {
  return order.value?.items.some(item => item.product_type === 'physical') || false
})

// 格式化倒计时
const countdownText = computed(() => {
  if (countdown.value <= 0) return '已过期'
  const minutes = Math.floor(countdown.value / 60)
  const seconds = countdown.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

// 二维码内容
const qrCodeValue = computed(() => {
  if (!paymentData.value) return ''
  const data = paymentData.value.payment_data
  // 优先使用 qr_content (TRC20)，其次 code_url (微信)，最后 payment_url
  return String(data?.qr_content || data?.code_url || paymentData.value.payment_url || '')
})

// 是否是微信支付
const isWechatPay = computed(() => {
  if (!paymentData.value) return false
  const data = paymentData.value.payment_data
  return !!(data?.code_url || paymentData.value.payment_url)
})

onMounted(async () => {
  const orderNo = route.params.orderNo as string
  email.value = (route.query.email as string) || ''

  if (!email.value) {
    appStore.error('缺少邮箱参数')
    loading.value = false
    return
  }

  try {
    const res = await get<OrderDetail>(`/orders/${orderNo}`, {
      params: { email: email.value }
    })
    order.value = res.data

    // 更新本地历史记录
    updateOrderInHistory(orderNo, {
      status: res.data.status,
    })
  } catch (error: unknown) {
    appStore.error((error as Error).message || '订单不存在')
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  stopTimers()
})

function stopTimers() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 初始化支付
async function initPayment() {
  if (!order.value || paymentLoading.value) return

  paymentLoading.value = true
  try {
    const res = await post<PaymentInitResponse>('/payment/init', {
      order_no: order.value.order_no
    })
    paymentData.value = res.data
    await nextTick()
    showPaymentModal.value = true

    // 启动倒计时
    countdown.value = res.data.expires_in
    startCountdown()

    // 启动支付状态轮询
    startPolling()
  } catch (error: unknown) {
    appStore.error((error as Error).message || '初始化支付失败')
  } finally {
    paymentLoading.value = false
  }
}

// 开始倒计时
function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      stopTimers()
      showPaymentModal.value = false
      appStore.error('支付已过期，请重新下单')
    }
  }, 1000)
}

// 开始轮询支付状态
function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    if (!order.value) return

    try {
      const res = await get<PaymentStatusResponse>(`/payment/status/${order.value.order_no}`)
      if (res.data.status === 'paid' || res.data.status === 'completed') {
        stopTimers()
        showPaymentModal.value = false
        appStore.success('支付成功！')

        // 刷新订单信息
        await refreshOrder()
      } else if (res.data.status === 'cancelled' || res.data.status === 'expired') {
        stopTimers()
        showPaymentModal.value = false
        appStore.error('订单已取消或过期')
        await refreshOrder()
      }
    } catch {
      // 忽略轮询错误
    }
  }, 5000) // 每5秒检查一次
}

// 刷新订单
async function refreshOrder() {
  if (!order.value) return

  try {
    const res = await get<OrderDetail>(`/orders/${order.value.order_no}`, {
      params: { email: email.value }
    })
    order.value = res.data
    updateOrderInHistory(order.value.order_no, {
      status: res.data.status,
    })
  } catch {
    // 忽略刷新错误
  }
}

// 关闭支付弹窗
function closePaymentModal() {
  showPaymentModal.value = false
  stopTimers()
}

async function copyOrderNo() {
  if (!order.value) return
  const success = await copyText(order.value.order_no)
  if (success) {
    appStore.success('订单号已复制')
  } else {
    appStore.error('复制失败，请手动复制')
  }
}

async function copyContent(content: string) {
  const success = await copyText(content)
  if (success) {
    appStore.success('已复制到剪贴板')
  } else {
    appStore.error('复制失败，请手动复制')
  }
}

async function copyWalletAddress() {
  if (!paymentData.value?.payment_data?.wallet_address) return
  const success = await copyText(paymentData.value.payment_data.wallet_address)
  if (success) {
    appStore.success('钱包地址已复制')
  } else {
    appStore.error('复制失败，请手动复制')
  }
}

async function copyPaymentAmount() {
  if (!paymentData.value?.payment_data?.amount) return
  const success = await copyText(String(paymentData.value.payment_data.amount))
  if (success) {
    appStore.success('支付金额已复制')
  } else {
    appStore.error('复制失败，请手动复制')
  }
}

async function cancelOrder() {
  if (!order.value) return
  showCancelDialog.value = true
}

async function confirmCancel() {
  if (!order.value) return
  showCancelDialog.value = false

  loading.value = true
  try {
    await post(`/orders/${order.value.order_no}/cancel`, {}, {
      params: { email: email.value }
    })
    appStore.success('订单已取消')
    await refreshOrder()
  } catch (error: any) {
    appStore.error(error.message || '取消订单失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container-lg py-8">
      <!-- 返回按钮 -->
      <RouterLink to="/orders" class="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-6">
        <ChevronLeftIcon class="w-4 h-4" />
        返回订单列表
      </RouterLink>

      <!-- 加载状态 -->
      <div v-if="loading" class="space-y-6">
        <div class="bg-white rounded-2xl p-6">
          <div class="h-8 skeleton rounded w-1/3 mb-4" />
          <div class="h-6 skeleton rounded w-1/2" />
        </div>
        <div class="bg-white rounded-2xl p-6">
          <div class="space-y-4">
            <div class="h-20 skeleton rounded-xl" />
            <div class="h-20 skeleton rounded-xl" />
          </div>
        </div>
      </div>

      <!-- 订单不存在 -->
      <div v-else-if="!order" class="text-center py-16">
        <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
          <XCircleIcon class="w-10 h-10 text-red-500" />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">订单不存在</h2>
        <p class="text-gray-500 mb-6">请检查订单号和邮箱是否正确</p>
        <RouterLink to="/orders" class="btn-primary">
          重新查询
        </RouterLink>
      </div>

      <!-- 订单详情 -->
      <div v-else class="space-y-6">
        <!-- 订单状态 -->
        <div class="bg-white rounded-2xl p-6">
          <div class="flex items-start gap-4">
            <div class="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
                 :class="getOrderStatusColor(order.status).replace('text-', 'bg-').replace('-600', '-100').replace('-50', '-100')">
              <component :is="statusIcon" class="w-7 h-7" :class="getOrderStatusColor(order.status).split(' ')[0]" />
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-lg font-semibold" :class="getOrderStatusColor(order.status).split(' ')[0]">
                  {{ getOrderStatusText(order.status) }}
                </span>
              </div>
              <p v-if="order.status === 'pending'" class="text-gray-500 text-sm">
                请尽快完成支付，订单将在15分钟后自动取消
              </p>
              <p v-else-if="order.status === 'completed'" class="text-gray-500 text-sm">
                订单已完成，商品信息请查看下方
              </p>
            </div>

            <!-- 取消按钮 -->
            <button
              v-if="order.status === 'pending'"
              class="flex items-center gap-1.5 px-4 py-2 ml-auto text-sm font-medium text-gray-600 bg-gray-100 hover:bg-red-50 hover:text-red-600 rounded-xl transition-all duration-200"
              @click="cancelOrder"
            >
              <TrashIcon class="w-4 h-4" />
              <span>取消订单</span>
            </button>
          </div>
        </div>

        <!-- 订单信息 -->
        <div class="bg-white rounded-2xl p-6">
          <h3 class="font-semibold text-gray-900 mb-4">订单信息</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <span class="text-gray-500">订单号</span>
              <span class="flex-1 font-mono font-medium text-gray-900">{{ order.order_no }}</span>
              <button class="text-primary-600 hover:text-primary-700" @click="copyOrderNo">
                <DocumentDuplicateIcon class="w-5 h-5" />
              </button>
            </div>
            <div class="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <span class="text-gray-500">联系邮箱</span>
              <span class="flex-1 font-medium text-gray-900">{{ order.email }}</span>
            </div>
            <div class="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <span class="text-gray-500">创建时间</span>
              <span class="flex-1 font-medium text-gray-900">{{ formatDate(order.created_at) }}</span>
            </div>
            <div v-if="order.paid_at" class="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <span class="text-gray-500">支付时间</span>
              <span class="flex-1 font-medium text-gray-900">{{ formatDate(order.paid_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 商品清单 -->
        <div class="bg-white rounded-2xl p-6">
          <h3 class="font-semibold text-gray-900 mb-4">商品清单</h3>
          <div class="space-y-4">
            <div
              v-for="item in order.items"
              :key="item.id"
              class="border rounded-xl overflow-hidden"
            >
              <div class="flex gap-4 p-4">
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <h4 class="font-medium text-gray-900">{{ item.product_name }}</h4>
                    <span
                      class="px-1.5 py-0.5 text-xs rounded"
                      :class="item.product_type === 'virtual' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
                    >
                      {{ item.product_type === 'virtual' ? '虚拟' : '实体' }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-500 mt-1">
                    {{ formatPrice(item.price) }} × {{ item.quantity }}
                  </p>
                </div>
                <div class="text-right">
                  <div class="font-medium text-gray-900">{{ formatPrice(item.subtotal) }}</div>
                </div>
              </div>

              <!-- 发货内容 -->
              <div v-if="item.delivery_content" class="border-t bg-green-50 p-4">
                <div class="flex items-start gap-2">
                  <CheckCircleIcon class="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
                  <div class="flex-1">
                    <p class="text-sm font-medium text-green-700 mb-2">商品内容</p>
                    <div class="bg-white rounded-lg p-3 text-sm font-mono whitespace-pre-wrap break-all">
                      {{ item.delivery_content }}
                    </div>
                    <button
                      class="mt-2 text-sm text-primary-600 hover:text-primary-700"
                      @click="copyContent(item.delivery_content!)"
                    >
                      复制内容
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 金额汇总 -->
          <div class="mt-6 pt-6 border-t">
            <div class="flex justify-between items-center">
              <span class="text-gray-500">订单总额</span>
              <span class="text-2xl font-bold text-primary-600">{{ formatPrice(order.total_price) }}</span>
            </div>
          </div>
        </div>

        <!-- 收货信息（实体商品订单） -->
        <div v-if="hasPhysicalItems && (order.shipping_name || order.shipping_phone || order.shipping_address)" class="bg-white rounded-2xl p-6">
          <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <MapPinIcon class="w-5 h-5 text-gray-500" />
            收货信息
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div v-if="order.shipping_name" class="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <span class="text-gray-500">收货人</span>
              <span class="flex-1 font-medium text-gray-900">{{ order.shipping_name }}</span>
            </div>
            <div v-if="order.shipping_phone" class="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
              <span class="text-gray-500">联系电话</span>
              <span class="flex-1 font-medium text-gray-900">{{ order.shipping_phone }}</span>
            </div>
            <div v-if="order.shipping_address" class="flex items-start gap-3 p-4 bg-gray-50 rounded-xl sm:col-span-2">
              <span class="text-gray-500 shrink-0">收货地址</span>
              <span class="flex-1 font-medium text-gray-900">{{ order.shipping_address }}</span>
            </div>
          </div>
        </div>

        <!-- 备注 -->
        <div v-if="order.remark" class="bg-white rounded-2xl p-6">
          <h3 class="font-semibold text-gray-900 mb-4">订单备注</h3>
          <p class="text-gray-600">{{ order.remark }}</p>
        </div>

        <!-- 客服联系 -->
        <div v-if="appStore.siteConfig.contact_info" class="bg-white rounded-2xl p-6">
          <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <ChatBubbleLeftRightIcon class="w-5 h-5 text-gray-500" />
            客服联系
          </h3>
          <p class="text-gray-600 whitespace-pre-wrap">{{ appStore.siteConfig.contact_info }}</p>
        </div>

        <!-- 支付按钮 -->
        <div v-if="order.status === 'pending'" class="bg-white rounded-2xl p-6">
          <h3 class="font-semibold text-gray-900 mb-4">完成支付</h3>
          <p class="text-gray-500 mb-4">请选择以下方式完成支付</p>
          <button
            class="btn-primary btn-lg w-full sm:w-auto"
            :disabled="paymentLoading"
            @click="initPayment"
          >
            <span v-if="paymentLoading" class="flex items-center gap-2">
              <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              加载中...
            </span>
            <span v-else>去支付 {{ formatPrice(order.total_price) }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 支付弹窗 -->
    <Teleport to="body">
      <div
        v-if="showPaymentModal && paymentData"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @mousedown.self="closePaymentModal"
      >
        <div class="bg-white rounded-2xl w-full max-w-md shadow-xl overflow-hidden">
          <!-- 弹窗头部 -->
          <div class="bg-primary-600 text-white p-6 text-center">
            <h3 class="text-xl font-bold mb-2">扫码支付</h3>
            <p class="text-primary-100 text-sm">
              请在 <span class="font-mono font-bold text-white">{{ countdownText }}</span> 内完成支付
            </p>
          </div>

          <!-- 弹窗内容 -->
          <div class="p-6">
            <!-- 二维码 -->
            <div class="flex justify-center mb-6">
              <div class="p-4 bg-white border-2 border-gray-100 rounded-xl">
                <QrcodeVue
                  v-if="qrCodeValue"
                  :value="qrCodeValue"
                  :size="200"
                  level="M"
                />
              </div>
            </div>

            <!-- 支付信息 -->
            <div class="space-y-4">
              <!-- 微信支付提示 -->
              <template v-if="isWechatPay">
                <div class="flex items-center justify-between p-3 bg-green-50 rounded-xl">
                  <span class="text-gray-600">支付方式</span>
                  <span class="font-bold text-green-600">微信支付</span>
                </div>

                <!-- 支付金额 -->
                <div class="flex items-center justify-between p-3 bg-primary-50 rounded-xl">
                  <span class="text-gray-600">支付金额</span>
                  <span class="font-bold text-primary-600 text-lg">
                    ¥{{ order?.total_price }}
                  </span>
                </div>

                <!-- 微信支付提示 -->
                <div class="text-center text-sm text-gray-500 space-y-1">
                  <p>请使用微信扫一扫完成支付</p>
                  <p class="text-green-600 font-medium">支付成功后页面将自动更新</p>
                </div>

                <!-- 重要提示：不要关闭页面 -->
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                  <div class="flex items-center gap-2 text-amber-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                    <span class="font-medium text-sm">请勿关闭此页面，支付完成前请保持页面打开</span>
                  </div>
                </div>
              </template>

              <!-- TRC20/其他支付提示 -->
              <template v-else>
                <!-- 网络类型 -->
                <div v-if="paymentData.payment_data.network" class="flex items-center justify-between p-3 bg-orange-50 rounded-xl">
                  <span class="text-gray-600">网络</span>
                  <span class="font-bold text-orange-600">{{ paymentData.payment_data.network }}</span>
                </div>

                <!-- 支付金额 -->
                <div class="flex items-center justify-between p-3 bg-primary-50 rounded-xl">
                  <span class="text-gray-600">支付金额</span>
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-primary-600 text-lg">
                      {{ paymentData.payment_data.amount }} {{ paymentData.payment_data.currency || 'USDT' }}
                    </span>
                    <button
                      class="text-primary-600 hover:text-primary-700"
                      @click="copyPaymentAmount"
                    >
                      <DocumentDuplicateIcon class="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <!-- 钱包地址 -->
                <div v-if="paymentData.payment_data.wallet_address" class="p-3 bg-gray-50 rounded-xl">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-gray-600">收款地址</span>
                    <button
                      class="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1"
                      @click="copyWalletAddress"
                    >
                      <DocumentDuplicateIcon class="w-4 h-4" />
                      复制
                    </button>
                  </div>
                  <p class="font-mono text-sm text-gray-800 break-all">
                    {{ paymentData.payment_data.wallet_address }}
                  </p>
                </div>

                <!-- TRC20 提示 -->
                <div class="text-center text-sm text-gray-500 space-y-1">
                  <p>请使用支持 TRC20 的钱包扫码支付</p>
                  <p class="text-orange-600 font-medium">⚠️ 请务必转账精确金额，否则无法自动确认</p>
                </div>
              </template>
            </div>
          </div>

          <!-- 弹窗底部 -->
          <div class="p-4 bg-gray-50 border-t flex gap-3">
            <button
              class="flex-1 btn-outline"
              @click="closePaymentModal"
            >
              稍后支付
            </button>
            <button
              class="flex-1 btn-primary"
              @click="refreshOrder(); closePaymentModal()"
            >
              我已支付
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 取消订单确认弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showCancelDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <!-- 遮罩 -->
          <div class="absolute inset-0 bg-black/50" @click="showCancelDialog = false" />

          <!-- 弹窗内容 -->
          <div class="relative bg-white rounded-2xl shadow-xl max-w-sm w-full p-6">
            <!-- 关闭按钮 -->
            <button
              class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
              @click="showCancelDialog = false"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>

            <!-- 图标 -->
            <div class="w-12 h-12 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
              <ExclamationTriangleIcon class="w-6 h-6 text-red-600" />
            </div>

            <!-- 标题 -->
            <h3 class="text-lg font-semibold text-gray-900 text-center mb-2">确定取消订单？</h3>

            <!-- 内容 -->
            <p class="text-gray-500 text-sm text-center mb-6">
              订单取消后无法恢复，请确认是否继续？
            </p>

            <!-- 按钮 -->
            <div class="flex gap-3">
              <button
                class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
                @click="showCancelDialog = false"
              >
                暂不取消
              </button>
              <button
                class="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-500 rounded-xl hover:bg-red-600 transition-colors"
                :disabled="loading"
                @click="confirmCancel"
              >
                <span v-if="loading">取消中...</span>
                <span v-else>确定取消</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
