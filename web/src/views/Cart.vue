<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useCartStore } from '@/stores/cart'
import { useAppStore } from '@/stores/app'
import { formatPrice } from '@/utils/storage'
import {
  TrashIcon,
  MinusIcon,
  PlusIcon,
  ShoppingCartIcon,
  ArrowRightIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const cartStore = useCartStore()
const appStore = useAppStore()

const totalPrice = computed(() => formatPrice(cartStore.totalPrice))

function updateQuantity(productId: number, delta: number) {
  const item = cartStore.items.find(i => i.product.id === productId)
  if (!item) return

  const newQuantity = item.quantity + delta
  if (newQuantity < 1) {
    removeItem(productId)
  } else if (newQuantity <= item.product.stock) {
    cartStore.updateQuantity(productId, newQuantity)
  } else {
    appStore.warning('已达到库存上限')
  }
}

function removeItem(productId: number) {
  cartStore.removeItem(productId)
  appStore.success('已从购物车移除')
}

function clearCart() {
  if (confirm('确定要清空购物车吗？')) {
    cartStore.clearCart()
    appStore.success('购物车已清空')
  }
}

function checkout() {
  if (cartStore.isEmpty) {
    appStore.warning('购物车是空的')
    return
  }
  router.push('/checkout')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container-lg py-8">
      <!-- 页头 -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">购物车</h1>
          <p v-if="!cartStore.isEmpty" class="text-gray-500 mt-1">
            共 {{ cartStore.itemCount }} 件商品
          </p>
        </div>
        <button
          v-if="!cartStore.isEmpty"
          class="text-sm text-gray-500 hover:text-red-500 transition-colors"
          @click="clearCart"
        >
          清空购物车
        </button>
      </div>

      <!-- 空购物车 -->
      <div v-if="cartStore.isEmpty" class="text-center py-16">
        <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-gray-100 flex items-center justify-center">
          <ShoppingCartIcon class="w-12 h-12 text-gray-400" />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">购物车是空的</h2>
        <p class="text-gray-500 mb-6">快去挑选心仪的商品吧</p>
        <RouterLink to="/products" class="btn-primary">
          去逛逛
          <ArrowRightIcon class="w-4 h-4" />
        </RouterLink>
      </div>

      <!-- 购物车列表 -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- 商品列表 -->
        <div class="lg:col-span-2 space-y-4">
          <TransitionGroup name="list">
            <div
              v-for="item in cartStore.items"
              :key="item.product.id"
              class="bg-white rounded-2xl p-4 sm:p-6 flex gap-4 sm:gap-6"
            >
              <!-- 图片 -->
              <RouterLink
                :to="`/product/${item.product.slug}`"
                class="w-24 h-24 sm:w-32 sm:h-32 shrink-0 rounded-xl overflow-hidden bg-gray-100"
              >
                <img
                  v-if="item.product.primary_image"
                  :src="item.product.primary_image"
                  :alt="item.product.name"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <span class="text-3xl">📦</span>
                </div>
              </RouterLink>

              <!-- 信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex justify-between gap-4">
                  <div class="min-w-0">
                    <RouterLink :to="`/product/${item.product.slug}`">
                      <h3 class="font-medium text-gray-900 hover:text-primary-600 transition-colors line-clamp-2">
                        {{ item.product.name }}
                      </h3>
                    </RouterLink>
                    <div class="flex flex-wrap gap-2 mt-2">
                      <span
                        v-for="tag in item.product.tags.slice(0, 2)"
                        :key="tag.id"
                        class="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded"
                      >
                        {{ tag.value }}
                      </span>
                    </div>
                    <p v-if="item.product.stock <= 3" class="text-xs text-amber-600 mt-2">
                      仅剩 {{ item.product.stock }} 件
                    </p>
                  </div>
                  <button
                    class="shrink-0 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    @click="removeItem(item.product.id)"
                  >
                    <TrashIcon class="w-5 h-5" />
                  </button>
                </div>

                <!-- 价格和数量 -->
                <div class="flex items-end justify-between mt-4">
                  <div class="flex items-center">
                    <button
                      class="w-8 h-8 flex items-center justify-center border border-gray-200 bg-white text-gray-700 rounded-l-lg hover:bg-gray-50 disabled:opacity-50"
                      :disabled="item.quantity <= 1"
                      @click="updateQuantity(item.product.id, -1)"
                    >
                      <MinusIcon class="w-4 h-4" />
                    </button>
                    <span class="w-12 h-8 flex items-center justify-center border-y border-gray-200 bg-white text-gray-700 text-sm font-medium">
                      {{ item.quantity }}
                    </span>
                    <button
                      class="w-8 h-8 flex items-center justify-center border border-gray-200 bg-white text-gray-700 rounded-r-lg hover:bg-gray-50 disabled:opacity-50"
                      :disabled="item.quantity >= item.product.stock"
                      @click="updateQuantity(item.product.id, 1)"
                    >
                      <PlusIcon class="w-4 h-4" />
                    </button>
                  </div>
                  <div class="text-right">
                    <div class="text-lg font-bold text-primary-600">
                      {{ formatPrice(parseFloat(item.product.price) * item.quantity) }}
                    </div>
                    <div v-if="item.quantity > 1" class="text-xs text-gray-400">
                      {{ formatPrice(item.product.price) }} × {{ item.quantity }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>

        <!-- 结算卡片 -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-2xl p-6 sticky top-20">
            <h3 class="font-semibold text-gray-900 mb-4">订单摘要</h3>

            <div class="space-y-3 pb-4 border-b">
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">商品数量</span>
                <span class="text-gray-900">{{ cartStore.itemCount }} 件</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">商品金额</span>
                <span class="text-gray-900">{{ totalPrice }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500">支付手续费</span>
                <span class="text-gray-500">结算时计算</span>
              </div>
            </div>

            <div class="flex justify-between items-center py-4">
              <span class="font-medium text-gray-900">合计</span>
              <span class="text-2xl font-bold text-primary-600">{{ totalPrice }}</span>
            </div>

            <button class="btn-primary w-full btn-lg" @click="checkout">
              去结算
              <ArrowRightIcon class="w-5 h-5" />
            </button>

            <RouterLink
              to="/products"
              class="block text-center text-sm text-gray-500 hover:text-primary-600 mt-4"
            >
              继续购物
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
