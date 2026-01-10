<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { ProductListItem } from '@/types'
import { useCartStore } from '@/stores/cart'
import { useAppStore } from '@/stores/app'
import { ShoppingCartIcon, MinusIcon, PlusIcon, TrashIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{
  product: ProductListItem
}>()

const cartStore = useCartStore()
const appStore = useAppStore()

const cartQuantity = computed(() => cartStore.getItemQuantity(props.product.id))
const isInCart = computed(() => cartQuantity.value > 0)

function addToCart() {
  if (props.product.stock <= 0) return
  cartStore.addItem(props.product)
  appStore.success('已添加到购物车')
}

function increaseQuantity() {
  if (cartQuantity.value >= props.product.stock) {
    appStore.warning('已达到最大库存')
    return
  }
  cartStore.updateQuantity(props.product.id, cartQuantity.value + 1)
}

function decreaseQuantity() {
  if (cartQuantity.value <= 1) {
    cartStore.removeItem(props.product.id)
    appStore.info('已从购物车移除')
  } else {
    cartStore.updateQuantity(props.product.id, cartQuantity.value - 1)
  }
}
</script>

<template>
  <div class="card-hover group overflow-hidden">
    <!-- 图片 -->
    <RouterLink :to="`/product/${product.slug}`" class="block aspect-[4/3] overflow-hidden bg-gray-100 relative">
      <img
        v-if="product.primary_image"
        :src="product.primary_image"
        :alt="product.name"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
        <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <!-- 库存状态 -->
      <div
        v-if="product.stock <= 0"
        class="absolute inset-0 bg-black/50 flex items-center justify-center"
      >
        <span class="px-4 py-2 bg-white/90 rounded-full text-sm font-medium text-gray-700">
          暂无库存
        </span>
      </div>
      <!-- 分类标签 -->
      <div v-if="product.category" class="absolute top-3 left-3">
        <span class="badge-primary">{{ product.category.name }}</span>
      </div>
      <!-- 购物车数量标签 -->
      <div v-if="isInCart" class="absolute top-3 right-3">
        <span class="px-2 py-1 bg-primary-500 text-white text-xs font-bold rounded-full">
          {{ cartQuantity }}
        </span>
      </div>
    </RouterLink>

    <!-- 信息 -->
    <div class="p-4">
      <!-- 标签 -->
      <div v-if="product.tags.length > 0" class="flex flex-wrap gap-1.5 mb-2">
        <span
          v-for="tag in product.tags.slice(0, 3)"
          :key="tag.id"
          class="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
        >
          {{ tag.value }}
        </span>
      </div>

      <!-- 标题 -->
      <RouterLink :to="`/product/${product.slug}`">
        <h3 class="font-medium text-gray-900 line-clamp-2 hover:text-primary-600 transition-colors mb-2">
          {{ product.name }}
        </h3>
      </RouterLink>

      <!-- 价格和操作 -->
      <div class="flex items-center justify-between mt-3">
        <div class="price-sm">
          {{ appStore.formatPrice(product.price) }}
        </div>

        <!-- 未加入购物车：显示加入按钮 -->
        <button
          v-if="!isInCart && product.stock > 0"
          class="btn-primary btn-sm"
          @click.prevent="addToCart"
        >
          <ShoppingCartIcon class="w-4 h-4" />
          加入
        </button>

        <!-- 已加入购物车：显示数量控制 -->
        <div v-else-if="isInCart" class="flex items-center gap-1">
          <button
            class="w-7 h-7 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
            @click.prevent="decreaseQuantity"
          >
            <MinusIcon v-if="cartQuantity > 1" class="w-3.5 h-3.5 text-gray-600" />
            <TrashIcon v-else class="w-3.5 h-3.5 text-red-500" />
          </button>
          <span class="w-8 text-center text-sm font-medium text-gray-900">{{ cartQuantity }}</span>
          <button
            class="w-7 h-7 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors disabled:opacity-50"
            :disabled="cartQuantity >= product.stock"
            @click.prevent="increaseQuantity"
          >
            <PlusIcon class="w-3.5 h-3.5 text-gray-600" />
          </button>
        </div>

        <span v-else class="text-sm text-gray-400">缺货</span>
      </div>
    </div>
  </div>
</template>
