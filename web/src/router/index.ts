import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/components/layout/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('@/views/Home.vue'),
          meta: { title: '首页' },
        },
        {
          path: 'products',
          name: 'Products',
          component: () => import('@/views/Products.vue'),
          meta: { title: '全部商品' },
        },
        {
          path: 'category/:slug',
          name: 'Category',
          component: () => import('@/views/Products.vue'),
          meta: { title: '商品分类' },
        },
        {
          path: 'product/:slug',
          name: 'ProductDetail',
          component: () => import('@/views/ProductDetail.vue'),
          meta: { title: '商品详情' },
        },
        {
          path: 'cart',
          name: 'Cart',
          component: () => import('@/views/Cart.vue'),
          meta: { title: '购物车' },
        },
        {
          path: 'checkout',
          name: 'Checkout',
          component: () => import('@/views/Checkout.vue'),
          meta: { title: '结算' },
        },
        {
          path: 'order/:orderNo',
          name: 'OrderDetail',
          component: () => import('@/views/OrderDetail.vue'),
          meta: { title: '订单详情' },
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('@/views/Orders.vue'),
          meta: { title: '查询订单' },
        },
        {
          path: 'announcements',
          name: 'Announcements',
          component: () => import('@/views/Announcements.vue'),
          meta: { title: '公告通知' },
        },
        {
          path: 'announcement/:id',
          name: 'Announcement',
          component: () => import('@/views/Announcement.vue'),
          meta: { title: '公告详情' },
        },
      ],
    },
  ],
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})

// 更新页面标题
router.afterEach((to) => {
  const title = to.meta.title as string
  document.title = title ? `${title} - CardStore` : 'CardStore'
})

export default router
