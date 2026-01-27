<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get } from '@/utils/request'
import type { PaginatedData, Product, Order } from '@/types'
import { ShoppingCart, Goods, Money, TrendCharts } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const loading = ref(false)

const stats = ref({
  totalProducts: 0,
  totalOrders: 0,
  pendingOrders: 0,
  todayOrders: 0,
})

const recentOrders = ref<Order[]>([])

onMounted(async () => {
  loading.value = true
  try {
    // 获取商品数量
    const productRes = await get<PaginatedData<Product>>('/admin/products', { page_size: 1 })
    stats.value.totalProducts = productRes.data.total

    // 获取订单统计
    const orderRes = await get<PaginatedData<Order>>('/admin/orders', { page_size: 5 })
    stats.value.totalOrders = orderRes.data.total
    recentOrders.value = orderRes.data.items

    // 待处理订单
    const pendingRes = await get<PaginatedData<Order>>('/admin/orders', { status: 'pending', page_size: 1 })
    stats.value.pendingOrders = pendingRes.data.total

    // 今日订单
    const today = new Date().toISOString().slice(0, 10)
    
    const todayRes = await get<PaginatedData<Order>>('/admin/orders', {date: today, page_size: 1})
    stats.value.todayOrders = todayRes.data.total
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
})

// 订单状态映射
const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'warning' },
  paid: { label: '已支付', type: 'success' },
  processing: { label: '处理中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
  refunded: { label: '已退款', type: 'danger' },
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
            <el-icon><Goods /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalProducts }}</div>
            <div class="stat-label">商品总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
            <el-icon><ShoppingCart /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalOrders }}</div>
            <div class="stat-label">订单总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pendingOrders }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.todayOrders }}</div>
            <div class="stat-label">今日订单</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近订单 -->
    <el-card class="recent-orders">
      <template #header>
        <div class="card-header">
          <span>最近订单</span>
          <router-link to="/order/list">
            <el-button type="primary" link>查看全部</el-button>
          </router-link>
        </div>
      </template>

      <el-table :data="recentOrders" style="width: 100%">
        <el-table-column prop="order_no" label="订单号" min-width="180" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="total_price" label="金额" width="120">
          <template #default="{ row }">
            {{ appStore.formatPrice(row.total_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any" size="small">
              {{ statusMap[row.status]?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  :deep(.el-card__body) {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
  }

  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;

    .el-icon {
      font-size: 28px;
      color: #fff;
    }
  }

  .stat-content {
    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .stat-label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin-top: 4px;
    }
  }
}

.recent-orders {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
