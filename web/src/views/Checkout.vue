<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useCartStore } from '@/stores/cart'
import { useAppStore } from '@/stores/app'
import { get, post } from '@/utils/request'
import { formatPrice, addOrderToHistory } from '@/utils/storage'
import type { PaymentMethod, OrderCreate, OrderDetail } from '@/types'
import {
  ChevronLeftIcon,
  CheckCircleIcon,
  EnvelopeIcon,
  UserIcon,
  PhoneIcon,
  MapPinIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const cartStore = useCartStore()
const appStore = useAppStore()

const loading = ref(false)
const submitting = ref(false)
const paymentMethods = ref<PaymentMethod[]>([])

// 判断是否有实体商品
const hasPhysicalProduct = computed(() => {
  return cartStore.items.some(item => item.product.product_type === 'physical')
})

// 表单数据
const form = ref({
  email: '',
  confirmEmail: '',
  paymentMethodId: null as number | null,
  remark: '',
  // 实体商品收货信息
  shippingName: '',
  shippingPhone: '',
  shippingAddress: '',
})

// 计算手续费
const selectedPayment = computed(() => {
  return paymentMethods.value.find(p => p.id === form.value.paymentMethodId)
})

const fee = computed(() => {
  if (!selectedPayment.value) return 0
  const pm = selectedPayment.value
  if (pm.fee_type === 'percentage') {
    return cartStore.totalPrice * parseFloat(pm.fee_value) / 100
  }
  return parseFloat(pm.fee_value)
})

const totalPrice = computed(() => cartStore.totalPrice + fee.value)

// 表单验证
const emailValid = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(form.value.email)
})

const emailMatch = computed(() => {
  return form.value.email === form.value.confirmEmail
})

// 收货信息验证（实体商品必填）
const shippingValid = computed(() => {
  if (!hasPhysicalProduct.value) return true
  return form.value.shippingName.trim() !== '' &&
         form.value.shippingPhone.trim() !== '' &&
         form.value.shippingAddress.trim() !== ''
})

const canSubmit = computed(() => {
  return emailValid.value &&
         emailMatch.value &&
         shippingValid.value &&
         form.value.paymentMethodId !== null &&
         !cartStore.isEmpty &&
         !submitting.value
})

onMounted(async () => {
  // 检查购物车
  if (cartStore.isEmpty) {
    router.push('/cart')
    return
  }

  loading.value = true
  try {
    const res = await get<PaymentMethod[]>('/products/payment-methods')
    paymentMethods.value = res.data

    // 默认选择第一个支付方式
    if (res.data.length > 0 && res.data[0]) {
      form.value.paymentMethodId = res.data[0].id
    }
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  if (!canSubmit.value) return

  submitting.value = true
  try {
    const orderData: OrderCreate = {
      email: form.value.email,
      payment_method_id: form.value.paymentMethodId!,
      currency: 'CNY',
      items: cartStore.items.map(item => ({
        product_id: item.product.id,
        quantity: item.quantity,
      })),
      remark: form.value.remark || undefined,
      // 实体商品收货信息
      shipping_name: hasPhysicalProduct.value ? form.value.shippingName : undefined,
      shipping_phone: hasPhysicalProduct.value ? form.value.shippingPhone : undefined,
      shipping_address: hasPhysicalProduct.value ? form.value.shippingAddress : undefined,
    }

    const res = await post<OrderDetail>('/orders', orderData)
    const order = res.data

    // 保存到本地历史
    addOrderToHistory({
      order_no: order.order_no,
      email: order.email,
      total_price: order.total_price,
      status: order.status,
      created_at: order.created_at,
    })

    // 清空购物车
    cartStore.clearCart()

    appStore.success('订单创建成功')

    // 跳转到订单详情页
    router.push(`/order/${order.order_no}?email=${encodeURIComponent(order.email)}`)
  } catch (error: unknown) {
    appStore.error((error as Error).message || '订单创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container-lg py-8">
      <!-- 返回按钮 -->
      <RouterLink to="/cart" class="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-6">
        <ChevronLeftIcon class="w-4 h-4" />
        返回购物车
      </RouterLink>

      <h1 class="text-2xl font-bold text-gray-900 mb-8">确认订单</h1>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- 左侧表单 -->
        <div class="lg:col-span-2 space-y-6">
          <!-- 商品清单 -->
          <div class="bg-white rounded-2xl p-6">
            <h2 class="font-semibold text-gray-900 mb-4">商品清单</h2>
            <div class="space-y-4">
              <div
                v-for="item in cartStore.items"
                :key="item.product.id"
                class="flex gap-4 pb-4 border-b last:border-0 last:pb-0"
              >
                <div class="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                  <img
                    v-if="item.product.primary_image"
                    :src="item.product.primary_image"
                    :alt="item.product.name"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="font-medium text-gray-900 line-clamp-1">{{ item.product.name }}</h3>
                  <p class="text-sm text-gray-500">数量: {{ item.quantity }}</p>
                </div>
                <div class="text-right shrink-0">
                  <div class="font-medium text-gray-900">
                    {{ formatPrice(parseFloat(item.product.price) * item.quantity) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 联系方式 -->
          <div class="bg-white rounded-2xl p-6">
            <h2 class="font-semibold text-gray-900 mb-4">联系方式</h2>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  邮箱地址 <span class="text-red-500">*</span>
                </label>
                <div class="relative">
                  <EnvelopeIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    v-model="form.email"
                    type="email"
                    placeholder="请输入您的邮箱"
                    class="input pl-12"
                    :class="{ 'border-red-300 focus:border-red-500 focus:ring-red-500/20': form.email && !emailValid }"
                  />
                </div>
                <p v-if="form.email && !emailValid" class="text-red-500 text-sm mt-1">
                  请输入有效的邮箱地址
                </p>
                <p class="text-gray-500 text-sm mt-1">订单信息将发送到此邮箱</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  确认邮箱 <span class="text-red-500">*</span>
                </label>
                <div class="relative">
                  <EnvelopeIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    v-model="form.confirmEmail"
                    type="email"
                    placeholder="请再次输入邮箱"
                    class="input pl-12"
                    :class="{ 'border-red-300 focus:border-red-500 focus:ring-red-500/20': form.confirmEmail && !emailMatch }"
                  />
                </div>
                <p v-if="form.confirmEmail && !emailMatch" class="text-red-500 text-sm mt-1">
                  两次输入的邮箱不一致
                </p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  备注（可选）
                </label>
                <textarea
                  v-model="form.remark"
                  rows="3"
                  placeholder="如有特殊要求请在此备注"
                  class="input resize-none"
                />
              </div>
            </div>
          </div>

          <!-- 收货信息（仅实体商品显示） -->
          <div v-if="hasPhysicalProduct" class="bg-white rounded-2xl p-6">
            <h2 class="font-semibold text-gray-900 mb-4">
              收货信息 <span class="text-red-500">*</span>
            </h2>
            <p class="text-sm text-gray-500 mb-4">您的购物车中包含实体商品，请填写收货信息</p>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  收货人姓名 <span class="text-red-500">*</span>
                </label>
                <div class="relative">
                  <UserIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    v-model="form.shippingName"
                    type="text"
                    placeholder="请输入收货人姓名"
                    class="input pl-12"
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  联系电话 <span class="text-red-500">*</span>
                </label>
                <div class="relative">
                  <PhoneIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    v-model="form.shippingPhone"
                    type="tel"
                    placeholder="请输入联系电话"
                    class="input pl-12"
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  收货地址 <span class="text-red-500">*</span>
                </label>
                <div class="relative">
                  <MapPinIcon class="absolute left-4 top-3 w-5 h-5 text-gray-400" />
                  <textarea
                    v-model="form.shippingAddress"
                    rows="3"
                    placeholder="请输入详细收货地址（省市区 + 详细地址）"
                    class="input pl-12 resize-none"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 支付方式 -->
          <div class="bg-white rounded-2xl p-6">
            <h2 class="font-semibold text-gray-900 mb-4">支付方式</h2>
            <div v-if="loading" class="space-y-3">
              <div v-for="i in 3" :key="i" class="h-16 skeleton rounded-xl" />
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label
                v-for="pm in paymentMethods"
                :key="pm.id"
                class="relative flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all"
                :class="form.paymentMethodId === pm.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <input
                  v-model="form.paymentMethodId"
                  type="radio"
                  :value="pm.id"
                  class="sr-only"
                />
                <div v-if="pm.icon" class="w-10 h-10 rounded-lg overflow-hidden shrink-0">
                  <img :src="pm.icon" :alt="pm.name" class="w-full h-full object-contain" />
                </div>
                <div v-else class="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                  <span class="text-xl">💳</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-900">{{ pm.name }}</div>
                  <div class="text-sm text-gray-500">
                    手续费: {{ pm.fee_type === 'percentage' ? `${pm.fee_value}%` : formatPrice(pm.fee_value) }}
                  </div>
                </div>
                <CheckCircleIcon
                  v-if="form.paymentMethodId === pm.id"
                  class="w-6 h-6 text-primary-500 shrink-0"
                />
              </label>
            </div>
          </div>
        </div>

        <!-- 右侧摘要 -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-2xl p-6 sticky top-20">
            <h3 class="font-semibold text-gray-900 mb-4">订单摘要</h3>

            <div class="space-y-3 pb-4 border-b">
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">商品金额</span>
                <span class="text-gray-900">{{ formatPrice(cartStore.totalPrice) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">支付手续费</span>
                <span class="text-gray-900">{{ formatPrice(fee) }}</span>
              </div>
            </div>

            <div class="flex justify-between items-center py-4">
              <span class="font-medium text-gray-900">应付金额</span>
              <span class="text-2xl font-bold text-primary-600">{{ formatPrice(totalPrice) }}</span>
            </div>

            <button
              class="btn-primary w-full btn-lg"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              <span v-if="submitting">处理中...</span>
              <span v-else>提交订单</span>
            </button>

            <p class="text-xs text-gray-400 text-center mt-4">
              提交订单即表示您同意我们的服务条款
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
