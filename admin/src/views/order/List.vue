<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get } from '@/utils/request'
import type { Order, PaginatedData, Product } from '@/types'
import { View, Search } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()
const loading = ref(false)
const list = ref<Order[]>([])

// 商品列表（用于筛选）
const products = ref<Product[]>([])

// 分页
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

// 搜索
const searchForm = ref({
  status: '' as string,
  search: '',
  dateRange: [] as string[],
  product_id: null as number | null,
})

// 订单状态
const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待支付' },
  { value: 'paid', label: '已支付' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
  { value: 'refunded', label: '已退款' },
]

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'warning' },
  paid: { label: '已支付', type: 'success' },
  processing: { label: '处理中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
  refunded: { label: '已退款', type: 'danger' },
}

// 时间快捷选项
const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const end = new Date()
      end.setHours(23, 59, 59, 999)
      return [today, end]
    },
  },
  {
    text: '昨天',
    value: () => {
      const start = new Date()
      start.setDate(start.getDate() - 1)
      start.setHours(0, 0, 0, 0)
      const end = new Date()
      end.setDate(end.getDate() - 1)
      end.setHours(23, 59, 59, 999)
      return [start, end]
    },
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 6)
      start.setHours(0, 0, 0, 0)
      return [start, end]
    },
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 29)
      start.setHours(0, 0, 0, 0)
      return [start, end]
    },
  },
  {
    text: '本月',
    value: () => {
      const start = new Date()
      start.setDate(1)
      start.setHours(0, 0, 0, 0)
      const end = new Date()
      return [start, end]
    },
  },
]

onMounted(() => {
  loadList()
  loadProducts()
})

async function loadProducts() {
  try {
    const res = await get<PaginatedData<Product>>('/admin/products', { page_size: 100 })
    products.value = res.data.items
  } catch {
    // 忽略错误
  }
}

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
    }
    if (searchForm.value.status) params.status = searchForm.value.status
    if (searchForm.value.search) params.search = searchForm.value.search
    if (searchForm.value.product_id) params.product_id = searchForm.value.product_id

    // 时间段筛选
    if (searchForm.value.dateRange && searchForm.value.dateRange.length === 2 &&
        searchForm.value.dateRange[0] && searchForm.value.dateRange[1]) {
      params.start_date = formatDate(new Date(searchForm.value.dateRange[0]))
      params.end_date = formatDate(new Date(searchForm.value.dateRange[1]))
    }

    const res = await get<PaginatedData<Order>>('/admin/orders', params)
    list.value = res.data.items
    pagination.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.value.page = 1
  loadList()
}

function handleReset() {
  searchForm.value = {
    status: '',
    search: '',
    dateRange: [],
    product_id: null,
  }
  handleSearch()
}

function handlePageChange(page: number) {
  pagination.value.page = page
  loadList()
}

function handleView(row: Order) {
  router.push(`/order/detail/${row.id}`)
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">订单列表</h1>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="订单号/邮箱">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索订单号或邮箱"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" style="width: 120px">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间段">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :shortcuts="dateShortcuts"
            style="width: 260px"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="商品">
          <el-select
            v-model="searchForm.product_id"
            placeholder="全部商品"
            clearable
            filterable
            style="width: 180px"
          >
            <el-option
              v-for="item in products"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 订单列表 -->
    <el-card>
      <el-table :data="list" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="order_no" label="订单号" min-width="200" />
        <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span class="price">{{ appStore.formatPrice(row.total_price) }}</span>
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
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" :icon="View" link @click="handleView(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.search-card {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding-bottom: 0;
  }
}

.price {
  font-weight: 600;
  color: var(--el-color-danger);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
