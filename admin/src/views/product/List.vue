<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get, del } from '@/utils/request'
import type {Product, Category, PaginatedData, ApiResponse} from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View, Search } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()
const loading = ref(false)
const list = ref<Product[]>([])
const categories = ref<Category[]>([])

// 分页
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

// 搜索
const searchForm = ref({
  category_id: null as number | null,
  is_active: null as boolean | null,
  search: '',
})

onMounted(async () => {
  await loadCategories()
  await loadList()
})

async function loadCategories() {
  const res = await get<Category[]>('/admin/products/categories')
  categories.value = res.data
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
    }
    if (searchForm.value.category_id) params.category_id = searchForm.value.category_id
    if (searchForm.value.is_active !== null) params.is_active = searchForm.value.is_active
    if (searchForm.value.search) params.search = searchForm.value.search

    const res = await get<PaginatedData<Product>>('/admin/products', params)
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
    category_id: null,
    is_active: null,
    search: '',
  }
  handleSearch()
}

function handlePageChange(page: number) {
  pagination.value.page = page
  loadList()
}

function handleCreate() {
  router.push('/product/create')
}

function handleEdit(row: Product) {
  router.push(`/product/edit/${row.id}`)
}

async function handleDelete(row: Product) {
  await ElMessageBox.confirm(`确定要删除商品「${row.name}」吗？`, '提示', { type: 'warning' })
  try {
    const res = await del<ApiResponse>(`/admin/products/${row.id}`)
    ElMessage.success(res.message)
    await loadList()
  } catch {
    // 错误已处理
  }
}

// 商品类型
const productTypes: Record<string, string> = {
  virtual: '虚拟商品',
  physical: '实体商品',
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <h1 class="page-title">商品列表</h1>
      <el-button type="primary" :icon="Plus" @click="handleCreate">添加商品</el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="商品名称">
          <el-input v-model="searchForm.search" placeholder="搜索商品名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="searchForm.category_id" placeholder="全部分类" clearable style="width: 150px">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="已上架" :value="true" />
            <el-option label="已下架" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 商品列表 -->
    <el-card>
      <el-table :data="list" style="width: 100%">
        <el-table-column label="商品" min-width="280">
          <template #default="{ row }">
            <div class="product-info">
              <el-image
                v-if="row.primary_image"
                :src="row.primary_image"
                fit="cover"
                class="product-image"
              />
              <div v-else class="product-image placeholder">
                <el-icon><Goods /></el-icon>
              </div>
              <div class="product-detail">
                <div class="product-name">{{ row.name }}</div>
                <div class="product-meta">
                  <el-tag size="small" type="info">{{ productTypes[row.product_type] }}</el-tag>
                  <span v-if="row.category">{{ row.category.name }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="120">
          <template #default="{ row }">
            <span class="price">{{ appStore.formatPrice(row.price) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '上架' : '下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button type="primary" :icon="Edit" link @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" :icon="Delete" link @click="handleDelete(row)">删除</el-button>
            </div>
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

.product-info {
  display: flex;
  align-items: center;
  gap: 12px;

  .product-image {
    width: 60px;
    height: 60px;
    border-radius: 6px;
    flex-shrink: 0;

    &.placeholder {
      background: var(--el-fill-color);
      display: flex;
      align-items: center;
      justify-content: center;

      .el-icon {
        font-size: 24px;
        color: var(--el-text-color-placeholder);
      }
    }
  }

  .product-detail {
    .product-name {
      font-weight: 500;
      margin-bottom: 4px;
    }

    .product-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
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
