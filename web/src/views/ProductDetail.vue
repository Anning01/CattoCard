<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { get, post } from '@/utils/request'
import type { ProductDetail, OrderCreate } from '@/types'
import { useCartStore } from '@/stores/cart'
import { useAppStore } from '@/stores/app'
import { addOrderToHistory } from '@/utils/storage'
import {
  ShoppingCartIcon,
  MinusIcon,
  PlusIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckBadgeIcon,
  TruckIcon,
  ShieldCheckIcon,
  XMarkIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()
const appStore = useAppStore()

const loading = ref(true)
const product = ref<ProductDetail | null>(null)
const quantity = ref(1)
const currentImageIndex = ref(0)
const activeTab = ref(0)

// 立即购买弹窗
const showBuyNowModal = ref(false)
const buyNowForm = ref({
  email: '',
  emailConfirm: '',
  paymentMethodId: 0,
  // 收货信息
  shippingName: '',
  shippingPhone: '',
  shippingAddress: '',
})
const submitting = ref(false)

const isInCart = computed(() => product.value ? cartStore.isInCart(product.value.id) : false)
const cartQuantity = computed(() => product.value ? cartStore.getItemQuantity(product.value.id) : 0)

// 监听数量变化，强制限制在有效范围内
watch(quantity, (newVal) => {
  if (!product.value) return
  const stock = product.value.stock
  // 处理无效值（NaN、0、负数）
  if (!newVal || newVal < 1 || isNaN(newVal)) {
    quantity.value = 1
  } else if (newVal > stock) {
    quantity.value = stock
  }
})

// 判断是否为实体商品
const isPhysicalProduct = computed(() => product.value?.product_type === 'physical')

// 收货信息验证
const shippingValid = computed(() => {
  if (!isPhysicalProduct.value) return true
  return buyNowForm.value.shippingName.trim() !== '' &&
         buyNowForm.value.shippingPhone.trim() !== '' &&
         buyNowForm.value.shippingAddress.trim() !== ''
})

const canSubmitBuyNow = computed(() => {
  return buyNowForm.value.email &&
    buyNowForm.value.email === buyNowForm.value.emailConfirm &&
    buyNowForm.value.paymentMethodId > 0 &&
    shippingValid.value &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(buyNowForm.value.email)
})

const totalPrice = computed(() => {
  if (!product.value) return 0
  return parseFloat(product.value.price) * quantity.value
})

onMounted(async () => {
  const slug = route.params.slug as string
  try {
    const res = await get<ProductDetail>(`/products/${slug}`)
    product.value = res.data
    document.title = `${res.data.name} - ${appStore.siteConfig.site_name}`
    // 设置默认支付方式
    if (res.data.payment_methods.length > 0 && res.data.payment_methods[0]) {
      buyNowForm.value.paymentMethodId = res.data.payment_methods[0].id
    }
  } catch (error: unknown) {
    appStore.error((error as Error).message || '商品不存在')
    router.push('/products')
  } finally {
    loading.value = false
  }
})

function changeImage(direction: 'prev' | 'next') {
  if (!product.value) return
  const total = product.value.images.length
  if (direction === 'prev') {
    currentImageIndex.value = (currentImageIndex.value - 1 + total) % total
  } else {
    currentImageIndex.value = (currentImageIndex.value + 1) % total
  }
}

function addToCart() {
  if (!product.value || product.value.stock <= 0) return
  cartStore.addItem(product.value, quantity.value)
  appStore.success(`已添加 ${quantity.value} 件商品到购物车`)
}

function increaseCartQuantity() {
  if (!product.value) return
  if (cartQuantity.value >= product.value.stock) {
    appStore.warning('已达到最大库存')
    return
  }
  cartStore.updateQuantity(product.value.id, cartQuantity.value + 1)
}

function decreaseCartQuantity() {
  if (!product.value) return
  if (cartQuantity.value <= 1) {
    cartStore.removeItem(product.value.id)
    appStore.info('已从购物车移除')
  } else {
    cartStore.updateQuantity(product.value.id, cartQuantity.value - 1)
  }
}

function openBuyNowModal() {
  if (!product.value || product.value.stock <= 0) return
  showBuyNowModal.value = true
}

async function handleBuyNow() {
  if (!product.value || !canSubmitBuyNow.value) return

  submitting.value = true
  try {
    const orderData: OrderCreate = {
      email: buyNowForm.value.email,
      items: [{
        product_id: product.value.id,
        quantity: quantity.value,
      }],
      payment_method_id: buyNowForm.value.paymentMethodId,
      currency: appStore.siteConfig.currency,
      // 实体商品需要收货信息
      shipping_name: isPhysicalProduct.value ? buyNowForm.value.shippingName : undefined,
      shipping_phone: isPhysicalProduct.value ? buyNowForm.value.shippingPhone : undefined,
      shipping_address: isPhysicalProduct.value ? buyNowForm.value.shippingAddress : undefined,
    }

    const res = await post<{ order_no: string; total_price: string }>('/orders', orderData)

    // 保存到本地历史
    addOrderToHistory({
      order_no: res.data.order_no,
      email: buyNowForm.value.email,
      total_price: res.data.total_price,
      status: 'pending',
      created_at: new Date().toISOString(),
    })

    appStore.success('下单成功！')
    showBuyNowModal.value = false

    // 跳转到订单详情
    router.push(`/order/${res.data.order_no}?email=${encodeURIComponent(buyNowForm.value.email)}`)
  } catch (error: unknown) {
    appStore.error((error as Error).message || '下单失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen">
    <!-- 加载状态 -->
    <div v-if="loading" class="bg-gray-50">
      <div class="container-lg py-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div class="aspect-square skeleton rounded-2xl" />
          <div class="space-y-4">
            <div class="h-8 skeleton rounded w-3/4" />
            <div class="h-6 skeleton rounded w-1/2" />
            <div class="h-12 skeleton rounded w-1/3" />
            <div class="h-10 skeleton rounded w-full" />
            <div class="h-10 skeleton rounded w-full" />
          </div>
        </div>
      </div>
    </div>

    <!-- 商品详情 -->
    <div v-else-if="product">
      <!-- 面包屑 -->
      <div class="bg-gray-50">
        <div class="container-lg py-4">
          <nav class="flex items-center gap-2 text-sm text-gray-500">
            <RouterLink to="/" class="hover:text-primary-600">首页</RouterLink>
            <span>/</span>
            <RouterLink to="/products" class="hover:text-primary-600">商品</RouterLink>
            <template v-if="product.category">
              <span>/</span>
              <RouterLink :to="`/category/${product.category.slug}`" class="hover:text-primary-600">
                {{ product.category.name }}
              </RouterLink>
            </template>
            <span>/</span>
            <span class="text-gray-900">{{ product.name }}</span>
          </nav>
        </div>
      </div>

      <!-- 主要内容 -->
      <div class="bg-white">
        <div class="container-lg py-8">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
            <!-- 图片区域 -->
            <div class="space-y-4">
              <!-- 主图 -->
              <div class="relative aspect-square bg-gray-50 rounded-2xl overflow-hidden group">
                <img
                  v-if="product.images.length > 0 && product.images[currentImageIndex]"
                  :src="product.images[currentImageIndex]?.image_url"
                  :alt="product.name"
                  class="w-full h-full object-contain"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <span class="text-6xl">📦</span>
                </div>

                <!-- 切换按钮 -->
                <template v-if="product.images.length > 1">
                  <button
                    class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    @click="changeImage('prev')"
                  >
                    <ChevronLeftIcon class="w-5 h-5 text-gray-700" />
                  </button>
                  <button
                    class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    @click="changeImage('next')"
                  >
                    <ChevronRightIcon class="w-5 h-5 text-gray-700" />
                  </button>
                </template>
              </div>

              <!-- 缩略图 -->
              <div v-if="product.images.length > 1" class="flex gap-3 overflow-x-auto pb-2">
                <button
                  v-for="(img, index) in product.images"
                  :key="img.id"
                  class="w-20 h-20 shrink-0 rounded-xl overflow-hidden border-2 transition-colors"
                  :class="index === currentImageIndex ? 'border-primary-500' : 'border-transparent'"
                  @click="currentImageIndex = index"
                >
                  <img :src="img.image_url" :alt="`${product.name} ${index + 1}`" class="w-full h-full object-cover" />
                </button>
              </div>
            </div>

            <!-- 商品信息 -->
            <div class="space-y-6">
              <!-- 标题和分类 -->
              <div>
                <div v-if="product.category" class="mb-2">
                  <span class="badge-primary">{{ product.category.name }}</span>
                </div>
                <h1 class="text-2xl lg:text-3xl font-bold text-gray-900 mb-2">{{ product.name }}</h1>
                <!-- 标签 -->
                <div v-if="product.tags.length > 0" class="flex flex-wrap gap-2 mt-3">
                  <span
                    v-for="tag in product.tags"
                    :key="tag.id"
                    class="px-2.5 py-1 bg-gray-100 text-gray-600 text-sm rounded-lg"
                  >
                    {{ tag.key }}: {{ tag.value }}
                  </span>
                </div>
              </div>

              <!-- 价格 -->
              <div class="py-4 border-y border-gray-100">
                <div class="flex items-baseline gap-2">
                  <span class="text-3xl font-bold text-primary-600">{{ appStore.formatPrice(product.price) }}</span>
                  <span class="text-sm text-gray-400">/ 件</span>
                </div>
              </div>

              <!-- 库存状态 -->
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                  <span class="text-gray-500">库存:</span>
                  <span :class="product.stock > 0 ? 'text-green-600' : 'text-red-500'" class="font-medium">
                    {{ product.stock > 0 ? `${product.stock} 件` : '暂无库存' }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-gray-500">类型:</span>
                  <span class="font-medium text-gray-900">
                    {{ product.product_type === 'virtual' ? '虚拟商品' : '实物商品' }}
                  </span>
                </div>
              </div>

              <!-- 数量选择 -->
              <div v-if="product.stock > 0" class="flex items-center gap-4">
                <span class="text-gray-500">数量:</span>
                <div class="flex items-center">
                  <button
                    class="w-10 h-10 flex items-center justify-center border border-gray-200 rounded-l-xl bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    :disabled="quantity <= 1"
                    @click="quantity = Math.max(1, quantity - 1)"
                  >
                    <MinusIcon class="w-4 h-4" />
                  </button>
                  <input
                    v-model.number="quantity"
                    type="number"
                    min="1"
                    :max="product.stock"
                    class="w-16 h-10 text-center border-y border-gray-200 bg-white text-gray-900 focus:outline-none"
                  />
                  <button
                    class="w-10 h-10 flex items-center justify-center border border-gray-200 rounded-r-xl bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    :disabled="quantity >= product.stock"
                    @click="quantity = Math.min(product.stock, quantity + 1)"
                  >
                    <PlusIcon class="w-4 h-4" />
                  </button>
                </div>
                <span class="text-sm text-gray-400">最多可购买 {{ product.stock }} 件</span>
              </div>

              <!-- 购买按钮 -->
              <div class="flex gap-4 pt-4">
                <!-- 未加入购物车：显示加入按钮 -->
                <button
                  v-if="product.stock > 0 && !isInCart"
                  class="btn-secondary flex-1 btn-lg"
                  @click="addToCart"
                >
                  <ShoppingCartIcon class="w-5 h-5" />
                  加入购物车
                </button>

                <!-- 已加入购物车：显示数量控制 -->
                <div v-else-if="product.stock > 0 && isInCart" class="flex items-center gap-3 flex-1">
                  <button
                    class="w-10 h-10 flex items-center justify-center rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors"
                    @click="decreaseCartQuantity"
                  >
                    <MinusIcon v-if="cartQuantity > 1" class="w-5 h-5 text-gray-600" />
                    <TrashIcon v-else class="w-5 h-5 text-red-500" />
                  </button>
                  <div class="flex-1 text-center">
                    <span class="text-lg font-semibold text-gray-900">{{ cartQuantity }}</span>
                    <span class="text-sm text-gray-500 ml-1">件在购物车</span>
                  </div>
                  <button
                    class="w-10 h-10 flex items-center justify-center rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors disabled:opacity-50"
                    :disabled="cartQuantity >= product.stock"
                    @click="increaseCartQuantity"
                  >
                    <PlusIcon class="w-5 h-5 text-gray-600" />
                  </button>
                </div>

                <button
                  v-if="product.stock > 0"
                  class="btn-primary flex-1 btn-lg"
                  @click="openBuyNowModal"
                >
                  立即购买
                </button>
                <button v-else class="btn-secondary flex-1 btn-lg" disabled>
                  暂无库存
                </button>
              </div>

              <!-- 支付方式 -->
              <div v-if="product.payment_methods.length > 0" class="pt-4 border-t">
                <span class="text-gray-500 text-sm">支持支付方式:</span>
                <div class="flex flex-wrap gap-3 mt-2">
                  <div
                    v-for="pm in product.payment_methods"
                    :key="pm.id"
                    class="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg"
                  >
                    <img v-if="pm.icon" :src="pm.icon" :alt="pm.name" class="w-5 h-5" />
                    <span class="text-sm text-gray-700">{{ pm.name }}</span>
                  </div>
                </div>
              </div>

              <!-- 服务保障 -->
              <div class="grid grid-cols-3 gap-4 pt-4 border-t">
                <div class="text-center">
                  <CheckBadgeIcon class="w-6 h-6 mx-auto text-green-500 mb-1" />
                  <span class="text-xs text-gray-500">正品保障</span>
                </div>
                <div class="text-center">
                  <TruckIcon class="w-6 h-6 mx-auto text-blue-500 mb-1" />
                  <span class="text-xs text-gray-500">即时发货</span>
                </div>
                <div class="text-center">
                  <ShieldCheckIcon class="w-6 h-6 mx-auto text-purple-500 mb-1" />
                  <span class="text-xs text-gray-500">售后保障</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 商品介绍 -->
      <div v-if="product.intros.length > 0" class="bg-gray-50">
        <div class="container-lg py-8">
          <div class="bg-white rounded-2xl overflow-hidden">
            <!-- Tab 导航 -->
            <div class="flex border-b overflow-x-auto">
              <button
                v-for="(intro, index) in product.intros"
                :key="intro.id"
                class="px-6 py-4 text-sm font-medium whitespace-nowrap transition-colors relative"
                :class="activeTab === index ? 'text-primary-600' : 'text-gray-500 hover:text-gray-900'"
                @click="activeTab = index"
              >
                {{ intro.title }}
                <span
                  v-if="activeTab === index"
                  class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"
                />
              </button>
            </div>

            <!-- Tab 内容 -->
            <div class="p-6">
              <div
                v-for="(intro, index) in product.intros"
                :key="intro.id"
                v-show="activeTab === index"
                class="prose prose-sm max-w-none"
                v-html="intro.content"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 立即购买弹窗 -->
    <Transition name="fade">
      <div v-if="showBuyNowModal" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" @mousedown.self="showBuyNowModal = false">
        <div class="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
          <div class="flex items-center justify-between p-4 border-b shrink-0">
            <h3 class="text-lg font-semibold text-gray-900">立即购买</h3>
            <button @click="showBuyNowModal = false">
              <XMarkIcon class="w-6 h-6 text-gray-400 hover:text-gray-600" />
            </button>
          </div>

          <div class="p-6 space-y-4 overflow-y-auto flex-1">
            <!-- 商品信息 -->
            <div class="flex gap-4 p-4 bg-gray-50 rounded-xl">
              <img
                v-if="product?.images.length && product.images[0]"
                :src="product.images[0].image_url"
                :alt="product.name"
                class="w-16 h-16 rounded-lg object-cover"
              />
              <div class="flex-1 min-w-0">
                <h4 class="font-medium text-gray-900 line-clamp-1">{{ product?.name }}</h4>
                <p class="text-sm text-gray-500 mt-1">数量：{{ quantity }}</p>
                <p class="text-primary-600 font-semibold mt-1">{{ appStore.formatPrice(totalPrice) }}</p>
              </div>
            </div>

            <!-- 邮箱 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                邮箱地址 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="buyNowForm.email"
                type="email"
                placeholder="请输入邮箱（用于接收订单信息）"
                class="input"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                确认邮箱 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="buyNowForm.emailConfirm"
                type="email"
                placeholder="请再次输入邮箱"
                class="input"
                :class="{ 'border-red-300 focus:border-red-500 focus:ring-red-500/20': buyNowForm.emailConfirm && buyNowForm.email !== buyNowForm.emailConfirm }"
              />
              <p v-if="buyNowForm.emailConfirm && buyNowForm.email !== buyNowForm.emailConfirm" class="text-red-500 text-sm mt-1">
                两次输入的邮箱不一致
              </p>
            </div>

            <!-- 支付方式 -->
            <div v-if="product?.payment_methods.length">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                支付方式 <span class="text-red-500">*</span>
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label
                  v-for="pm in product.payment_methods"
                  :key="pm.id"
                  class="flex items-center gap-3 p-3 border rounded-xl cursor-pointer transition-all"
                  :class="buyNowForm.paymentMethodId === pm.id ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'"
                >
                  <input
                    v-model="buyNowForm.paymentMethodId"
                    type="radio"
                    :value="pm.id"
                    class="sr-only"
                  />
                  <img v-if="pm.icon" :src="pm.icon" :alt="pm.name" class="w-6 h-6" />
                  <span class="text-sm font-medium text-gray-900">{{ pm.name }}</span>
                </label>
              </div>
            </div>

            <!-- 收货信息（仅实体商品显示） -->
            <div v-if="isPhysicalProduct" class="space-y-4 pt-4 border-t">
              <div class="text-sm font-medium text-gray-700">
                收货信息 <span class="text-red-500">*</span>
                <span class="text-gray-500 font-normal ml-2">（实物商品需要填写）</span>
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">收货人姓名</label>
                <input
                  v-model="buyNowForm.shippingName"
                  type="text"
                  placeholder="请输入收货人姓名"
                  class="input"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">联系电话</label>
                <input
                  v-model="buyNowForm.shippingPhone"
                  type="tel"
                  placeholder="请输入联系电话"
                  class="input"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">收货地址</label>
                <textarea
                  v-model="buyNowForm.shippingAddress"
                  rows="2"
                  placeholder="请输入详细收货地址（省市区 + 详细地址）"
                  class="input resize-none"
                />
              </div>
            </div>
          </div>

          <div class="p-4 border-t bg-gray-50 shrink-0">
            <div class="flex items-center justify-between mb-4">
              <span class="text-gray-500">订单金额</span>
              <span class="text-xl font-bold text-primary-600">{{ appStore.formatPrice(totalPrice) }}</span>
            </div>
            <button
              class="btn-primary w-full btn-lg"
              :disabled="!canSubmitBuyNow || submitting"
              @click="handleBuyNow"
            >
              {{ submitting ? '提交中...' : '确认下单' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>

/* 隐藏数字输入框的箭头 */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}

/* 基础 prose 样式 */
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

.prose :deep(li) {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.prose :deep(img) {
  max-width: 100%;
  border-radius: 0.5rem;
  margin-top: 1em;
  margin-bottom: 1em;
}

.prose :deep(a) {
  color: #4f46e5;
  text-decoration: underline;
}

.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1em;
  margin-bottom: 1em;
}

.prose :deep(th),
.prose :deep(td) {
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
}

.prose :deep(th) {
  background: #f9fafb;
  font-weight: 600;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<style>
/* 全局样式：移除 ProductDetail 页面的所有 padding */
body {
  padding: 0 !important;
}

html {
  padding: 0 !important;
}

#app {
  padding: 0 !important;
}
</style>
