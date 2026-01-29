import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { get } from '@/utils/request'
import type { SiteConfig } from '@/types'
import defaultLogo from '@/assets/logo.png'

interface Toast {
  id: number
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration: number
}

export const useAppStore = defineStore('app', () => {
  const isDark = ref(false)
  const siteConfig = reactive<SiteConfig>({
    site_name: 'CardStore',
    site_description: '虚拟商品交易平台',
    site_logo: defaultLogo,
    site_favicon: '',
    currency: 'CNY',
    currency_symbol: '$',
    contact_info: '',
  })
  const configLoaded = ref(false)

  // Toast 通知
  const toasts = reactive<Toast[]>([])
  let toastId = 0

  function showToast(message: string, type: Toast['type'] = 'info', duration = 3000) {
    const id = ++toastId
    toasts.push({ id, type, message, duration })

    setTimeout(() => {
      const index = toasts.findIndex(t => t.id === id)
      if (index > -1) {
        toasts.splice(index, 1)
      }
    }, duration)
  }

  function success(message: string) {
    showToast(message, 'success')
  }

  function error(message: string) {
    showToast(message, 'error', 5000)
  }

  function warning(message: string) {
    showToast(message, 'warning')
  }

  function info(message: string) {
    showToast(message, 'info')
  }

  // 切换暗色模式
  function toggleDark() {
    isDark.value = !isDark.value
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('cardstore_dark', isDark.value ? '1' : '0')
  }

  // 初始化主题
  function initTheme() {
    const saved = localStorage.getItem('cardstore_dark')
    if (saved === '1' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      isDark.value = true
      document.documentElement.classList.add('dark')
    }
  }

  // 加载站点配置
  async function loadSiteConfig() {
    if (configLoaded.value) return

    try {
      const res = await get<SiteConfig>('/platform/site-config')
      // 只覆盖非空值，保留默认值
      if (res.data.site_name) siteConfig.site_name = res.data.site_name
      if (res.data.site_description) siteConfig.site_description = res.data.site_description
      if (res.data.site_logo) siteConfig.site_logo = res.data.site_logo
      if (res.data.site_favicon) siteConfig.site_favicon = res.data.site_favicon
      if (res.data.currency) siteConfig.currency = res.data.currency
      if (res.data.currency_symbol) siteConfig.currency_symbol = res.data.currency_symbol
      if (res.data.contact_info) siteConfig.contact_info = res.data.contact_info
      configLoaded.value = true

      // 更新页面标题和 favicon
      document.title = siteConfig.site_name
      if (siteConfig.site_favicon) {
        const link = document.querySelector("link[rel*='icon']") as HTMLLinkElement
          || document.createElement('link')
        link.type = 'image/x-icon'
        link.rel = 'shortcut icon'
        link.href = siteConfig.site_favicon
        document.head.appendChild(link)
      }
    } catch {
      // 使用默认配置
    }
  }

  // 格式化价格
  function formatPrice(price: string | number): string {
    const num = typeof price === 'string' ? parseFloat(price) : price
    return `${siteConfig.currency_symbol}${num.toFixed(2)}`
  }

  return {
    isDark,
    siteConfig,
    configLoaded,
    toasts,
    showToast,
    success,
    error,
    warning,
    info,
    toggleDark,
    initTheme,
    loadSiteConfig,
    formatPrice,
  }
})
