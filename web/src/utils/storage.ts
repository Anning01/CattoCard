import type { LocalOrderRecord } from '@/types'

const ORDER_HISTORY_KEY = 'cardstore_order_history'
const CART_KEY = 'cardstore_cart'

// 订单历史记录
export function getOrderHistory(): LocalOrderRecord[] {
  try {
    const data = localStorage.getItem(ORDER_HISTORY_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function addOrderToHistory(order: LocalOrderRecord): void {
  const history = getOrderHistory()
  // 去重
  const exists = history.findIndex(o => o.order_no === order.order_no)
  if (exists > -1) {
    history[exists] = order
  } else {
    history.unshift(order)
  }
  // 最多保存50条
  const trimmed = history.slice(0, 50)
  localStorage.setItem(ORDER_HISTORY_KEY, JSON.stringify(trimmed))
}

export function updateOrderInHistory(orderNo: string, updates: Partial<LocalOrderRecord>): void {
  const history = getOrderHistory()
  const index = history.findIndex(o => o.order_no === orderNo)
  if (index > -1) {
    const existing = history[index]
    if (existing) {
      history[index] = { ...existing, ...updates }
      localStorage.setItem(ORDER_HISTORY_KEY, JSON.stringify(history))
    }
  }
}

export function clearOrderHistory(): void {
  localStorage.removeItem(ORDER_HISTORY_KEY)
}

// 购物车
export interface CartStorageItem {
  productId: number
  quantity: number
}

export function getCartItems(): CartStorageItem[] {
  try {
    const data = localStorage.getItem(CART_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function saveCartItems(items: CartStorageItem[]): void {
  localStorage.setItem(CART_KEY, JSON.stringify(items))
}

export function clearCart(): void {
  localStorage.removeItem(CART_KEY)
}

// 格式化价格
export function formatPrice(price: string | number, currency = '¥'): string {
  const num = typeof price === 'string' ? parseFloat(price) : price
  return `${currency}${num.toFixed(2)}`
}

// 格式化日期
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 订单状态文本
export function getOrderStatusText(status: string): string {
  const map: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    processing: '处理中',
    completed: '已完成',
    cancelled: '已取消',
    refunded: '已退款',
  }
  return map[status] || status
}

// 订单状态颜色
export function getOrderStatusColor(status: string): string {
  const map: Record<string, string> = {
    pending: 'text-amber-600 bg-amber-50',
    paid: 'text-blue-600 bg-blue-50',
    processing: 'text-purple-600 bg-purple-50',
    completed: 'text-green-600 bg-green-50',
    cancelled: 'text-gray-600 bg-gray-100',
    refunded: 'text-red-600 bg-red-50',
  }
  return map[status] || 'text-gray-600 bg-gray-100'
}

// 复制文本到剪贴板
export async function copyText(text: string): Promise<boolean> {
  if (!text) return false

  try {
    // 优先使用 clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }

    // 降级方案：使用 textarea + execCommand
    const textArea = document.createElement('textarea')
    textArea.value = text

    // 确保 textarea 不可见但可选中
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    textArea.style.top = '0'
    document.body.appendChild(textArea)

    textArea.focus()
    textArea.select()

    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch (err) {
    console.error('Copy failed', err)
    return false
  }
}
