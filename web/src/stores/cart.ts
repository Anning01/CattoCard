import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CartItem, ProductListItem, PaginatedData } from '@/types'
import { getCartItems, saveCartItems, clearCart as clearCartStorage, type CartStorageItem } from '@/utils/storage'
import { get } from '@/utils/request'

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const loading = ref(false)
  const initialized = ref(false)

  // 计算属性
  const itemCount = computed(() => items.value.reduce((sum, item) => sum + item.quantity, 0))
  const totalPrice = computed(() => {
    return items.value.reduce((sum, item) => {
      return sum + parseFloat(item.product.price) * item.quantity
    }, 0)
  })
  const isEmpty = computed(() => items.value.length === 0)

  // 初始化：从本地存储恢复购物车
  async function initialize() {
    if (initialized.value) return

    loading.value = true
    try {
      const storageItems = getCartItems()
      if (storageItems.length === 0) {
        initialized.value = true
        return
      }

      // 获取商品详情
      const validItems: CartItem[] = []

      for (const storageItem of storageItems) {
        try {
          // 尝试获取商品信息（通过列表API批量可能更高效，这里简化处理）
          const res = await get<PaginatedData<ProductListItem>>('/products', { params: { page_size: 100 } })
          const product = res.data.items.find((p: ProductListItem) => p.id === storageItem.productId)
          if (product && product.is_active && product.stock > 0) {
            validItems.push({
              product,
              quantity: Math.min(storageItem.quantity, product.stock),
            })
          }
        } catch {
          // 忽略获取失败的商品
        }
      }

      items.value = validItems
      syncToStorage()
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  // 同步到本地存储
  function syncToStorage() {
    const storageItems: CartStorageItem[] = items.value.map(item => ({
      productId: item.product.id,
      quantity: item.quantity,
    }))
    saveCartItems(storageItems)
  }

  // 添加商品
  function addItem(product: ProductListItem, quantity = 1) {
    const existingIndex = items.value.findIndex(item => item.product.id === product.id)

    if (existingIndex > -1) {
      const existingItem = items.value[existingIndex]
      if (existingItem) {
        const newQuantity = existingItem.quantity + quantity
        existingItem.quantity = Math.min(newQuantity, product.stock)
      }
    } else {
      items.value.push({
        product,
        quantity: Math.min(quantity, product.stock),
      })
    }

    syncToStorage()
  }

  // 更新数量
  function updateQuantity(productId: number, quantity: number) {
    const item = items.value.find(item => item.product.id === productId)
    if (item) {
      item.quantity = Math.max(1, Math.min(quantity, item.product.stock))
      syncToStorage()
    }
  }

  // 移除商品
  function removeItem(productId: number) {
    const index = items.value.findIndex(item => item.product.id === productId)
    if (index > -1) {
      items.value.splice(index, 1)
      syncToStorage()
    }
  }

  // 清空购物车
  function clearCart() {
    items.value = []
    clearCartStorage()
  }

  // 检查商品是否在购物车中
  function isInCart(productId: number): boolean {
    return items.value.some(item => item.product.id === productId)
  }

  // 获取购物车中商品数量
  function getItemQuantity(productId: number): number {
    const item = items.value.find(item => item.product.id === productId)
    return item?.quantity || 0
  }

  return {
    items,
    loading,
    initialized,
    itemCount,
    totalPrice,
    isEmpty,
    initialize,
    addItem,
    updateQuantity,
    removeItem,
    clearCart,
    isInCart,
    getItemQuantity,
  }
})
