import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import { get } from '@/utils/request'

export interface SiteConfig {
  site_name: string
  site_description: string
  site_logo: string
  site_favicon: string
  currency: string
  currency_symbol: string
  contact_info: string
}

export const useAppStore = defineStore('app', () => {
  // 暗黑模式
  const isDark = useDark()
  const toggleDark = useToggle(isDark)

  // 侧边栏折叠
  const sidebarCollapsed = ref(false)

  // 站点配置
  const siteConfig = reactive<SiteConfig>({
    site_name: 'CardStore',
    site_description: '虚拟商品交易平台',
    site_logo: '',
    site_favicon: '',
    currency: 'CNY',
    currency_symbol: '$',
    contact_info: '',
  })
  const configLoaded = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  // 加载站点配置
  async function loadSiteConfig() {
    if (configLoaded.value) return

    try {
      const res = await get<SiteConfig>('/admin/platform/site-config')
      if (res.data.site_name) siteConfig.site_name = res.data.site_name
      if (res.data.site_description) siteConfig.site_description = res.data.site_description
      if (res.data.site_logo) siteConfig.site_logo = res.data.site_logo
      if (res.data.site_favicon) siteConfig.site_favicon = res.data.site_favicon
      if (res.data.currency) siteConfig.currency = res.data.currency
      if (res.data.currency_symbol) siteConfig.currency_symbol = res.data.currency_symbol
      if (res.data.contact_info) siteConfig.contact_info = res.data.contact_info
      configLoaded.value = true
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
    toggleDark,
    sidebarCollapsed,
    toggleSidebar,
    siteConfig,
    configLoaded,
    loadSiteConfig,
    formatPrice,
  }
})
