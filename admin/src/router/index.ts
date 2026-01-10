import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      // 平台管理
      {
        path: 'platform',
        name: 'Platform',
        redirect: '/platform/config',
        meta: { title: '平台管理', icon: 'Setting' },
        children: [
          {
            path: 'config',
            name: 'PlatformConfig',
            component: () => import('@/views/platform/Config.vue'),
            meta: { title: '基础配置' },
          },
          {
            path: 'announcement',
            name: 'Announcement',
            component: () => import('@/views/platform/Announcement.vue'),
            meta: { title: '公告管理' },
          },
          {
            path: 'banner',
            name: 'Banner',
            component: () => import('@/views/platform/Banner.vue'),
            meta: { title: 'Banner管理' },
          },
          {
            path: 'footer',
            name: 'Footer',
            component: () => import('@/views/platform/Footer.vue'),
            meta: { title: '底部链接' },
          },
        ],
      },
      // 商品管理
      {
        path: 'product',
        name: 'Product',
        redirect: '/product/list',
        meta: { title: '商品管理', icon: 'Goods' },
        children: [
          {
            path: 'category',
            name: 'Category',
            component: () => import('@/views/product/Category.vue'),
            meta: { title: '分类管理' },
          },
          {
            path: 'list',
            name: 'ProductList',
            component: () => import('@/views/product/List.vue'),
            meta: { title: '商品列表' },
          },
          {
            path: 'create',
            name: 'ProductCreate',
            component: () => import('@/views/product/Edit.vue'),
            meta: { title: '添加商品', hidden: true },
          },
          {
            path: 'edit/:id',
            name: 'ProductEdit',
            component: () => import('@/views/product/Edit.vue'),
            meta: { title: '编辑商品', hidden: true },
          },
          {
            path: 'payment',
            name: 'PaymentMethod',
            component: () => import('@/views/product/Payment.vue'),
            meta: { title: '支付方式' },
          },
        ],
      },
      // 订单管理
      {
        path: 'order',
        name: 'Order',
        redirect: '/order/list',
        meta: { title: '订单管理', icon: 'List' },
        children: [
          {
            path: 'list',
            name: 'OrderList',
            component: () => import('@/views/order/List.vue'),
            meta: { title: '订单列表' },
          },
          {
            path: 'detail/:id',
            name: 'OrderDetail',
            component: () => import('@/views/order/Detail.vue'),
            meta: { title: '订单详情', hidden: true },
          },
        ],
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404', public: true },
  },
]

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || 'CardStore'} - 管理后台`

  const userStore = useUserStore()

  // 公开页面直接放行
  if (to.meta.public) {
    // 已登录用户访问登录页，跳转到首页
    if (to.name === 'Login' && userStore.isLoggedIn) {
      next({ name: 'Dashboard' })
      return
    }
    next()
    return
  }

  // 未登录跳转到登录页
  if (!userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 已登录但没有用户信息，获取用户信息
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      userStore.logout()
      next({ name: 'Login' })
      return
    }
  }

  next()
})

export default router
