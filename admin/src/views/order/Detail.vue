<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post } from '@/utils/request'
import type { Order, OrderLog } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Check, Close } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const loading = ref(false)

const order = ref<Order | null>(null)
const logs = ref<OrderLog[]>([])

// 发货对话框
const deliverDialogVisible = ref(false)
const deliverRemark = ref('')
const delivering = ref(false)
const selectedItemIds = ref<number[]>([])

// 订单状态
const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'warning' },
  paid: { label: '已支付', type: 'success' },
  processing: { label: '处理中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
  refunded: { label: '已退款', type: 'danger' },
}

// 商品类型标签
const productTypeMap: Record<string, { label: string; type: string }> = {
  virtual: { label: '虚拟', type: 'primary' },
  physical: { label: '实体', type: 'success' },
}

// 可执行的操作
const canDeliver = computed(() => {
  if (!order.value) return false
  // 已支付或处理中可以发货
  if (order.value.status !== 'paid' && order.value.status !== 'processing') return false
  // 有未发货的商品项
  return order.value.items.some(item => !item.delivered_at)
})
const canCancel = computed(() => order.value?.status === 'pending')

// 获取未发货的商品项
const undeliveredItems = computed(() => {
  return order.value?.items.filter(item => !item.delivered_at) || []
})

// 判断是否有虚拟商品
const hasVirtualItems = computed(() => {
  return order.value?.items.some(item => item.product_type === 'virtual') || false
})

// 判断是否有实体商品
const hasPhysicalItems = computed(() => {
  return order.value?.items.some(item => item.product_type === 'physical') || false
})

onMounted(async () => {
  await loadOrder()
  await loadLogs()
})

async function loadOrder() {
  loading.value = true
  try {
    const res = await get<Order>(`/admin/orders/${route.params.id}`)
    order.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  try {
    const res = await get<OrderLog[]>(`/admin/orders/${route.params.id}/logs`)
    logs.value = res.data
  } catch {
    // 忽略
  }
}

// 打开发货对话框
function openDeliverDialog() {
  deliverRemark.value = ''
  // 默认选中所有未发货的商品项
  selectedItemIds.value = undeliveredItems.value.map(item => item.id)
  deliverDialogVisible.value = true
}

// 发货
async function handleDeliver() {
  if (selectedItemIds.value.length === 0) {
    ElMessage.warning('请选择要发货的商品')
    return
  }

  delivering.value = true
  try {
    const params = new URLSearchParams()
    if (deliverRemark.value) {
      params.append('remark', deliverRemark.value)
    }
    params.append('item_ids', selectedItemIds.value.join(','))
    const url = `/admin/orders/${route.params.id}/deliver?${params.toString()}`
    await post(url)
    ElMessage.success('发货成功')
    deliverDialogVisible.value = false
    await loadOrder()
    await loadLogs()
  } catch {
    // 错误已处理
  } finally {
    delivering.value = false
  }
}

// 取消订单
async function handleCancel() {
  await ElMessageBox.confirm('确定要取消该订单吗？', '取消确认', { type: 'warning' })
  try {
    await post(`/admin/orders/${route.params.id}/cancel`)
    ElMessage.success('订单已取消')
    await loadOrder()
    await loadLogs()
  } catch {
    // 错误已处理
  }
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <div class="flex" style="align-items: center; gap: 16px">
        <el-button :icon="Back" @click="goBack">返回</el-button>
        <h1 class="page-title">订单详情</h1>
      </div>
      <div class="header-actions" v-if="order">
        <el-button v-if="canDeliver" type="primary" :icon="Check" @click="openDeliverDialog">发货</el-button>
        <el-button v-if="canCancel" type="danger" :icon="Close" @click="handleCancel">取消订单</el-button>
      </div>
    </div>

    <template v-if="order">
      <!-- 订单信息 -->
      <el-card class="info-card">
        <template #header>订单信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="statusMap[order.status]?.type as any">
              {{ statusMap[order.status]?.label }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单邮箱">{{ order.email }}</el-descriptions-item>
          <el-descriptions-item label="支付方式">
            {{ order.payment_method?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">
            <span class="price">{{ appStore.formatPrice(order.total_price) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ new Date(order.created_at).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item v-if="order.remark" label="订单备注" :span="2">
            {{ order.remark }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 收货信息（仅实体商品显示） -->
      <el-card v-if="order.shipping_name || order.shipping_phone || order.shipping_address" class="info-card">
        <template #header>收货信息</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="收货人">{{ order.shipping_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ order.shipping_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="收货地址" :span="2">{{ order.shipping_address || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 商品明细 -->
      <el-card class="info-card">
        <template #header>商品明细</template>
        <el-table :data="order.items" style="width: 100%">
          <el-table-column prop="product_name" label="商品名称" min-width="200">
            <template #default="{ row }">
              <div class="product-info">
                <span>{{ row.product_name }}</span>
                <el-tag size="small" :type="productTypeMap[row.product_type]?.type as any">
                  {{ productTypeMap[row.product_type]?.label }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="单价" width="120">
            <template #default="{ row }">
              {{ appStore.formatPrice(row.price) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="subtotal" label="小计" width="120">
            <template #default="{ row }">
              <span class="price">{{ appStore.formatPrice(row.subtotal) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="发货状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.delivered_at" type="success" size="small">已发货</el-tag>
              <el-tag v-else type="info" size="small">待发货</el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="order.status === 'completed'" label="发货内容" min-width="200">
            <template #default="{ row }">
              <div v-if="row.delivery_content" class="delivery-content">
                <pre>{{ row.delivery_content }}</pre>
              </div>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 订单日志 -->
      <el-card class="info-card">
        <template #header>订单日志</template>
        <el-timeline v-if="logs.length">
          <el-timeline-item
            v-for="log in logs"
            :key="log.id"
            :timestamp="new Date(log.created_at).toLocaleString()"
            placement="top"
          >
            <div class="log-content">
              <el-tag size="small" type="info">{{ log.action }}</el-tag>
              <span>{{ log.content }}</span>
              <span v-if="log.operator" class="operator">操作人: {{ log.operator }}</span>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无日志" />
      </el-card>
    </template>

    <!-- 发货对话框 -->
    <el-dialog v-model="deliverDialogVisible" title="订单发货" width="600">
      <div class="deliver-dialog-content">
        <el-alert v-if="hasVirtualItems" type="info" :closable="false" style="margin-bottom: 16px">
          <template #title>
            虚拟商品将自动从库存中扣除卡密并发送给用户
          </template>
        </el-alert>
        <el-alert v-if="hasPhysicalItems" type="warning" :closable="false" style="margin-bottom: 16px">
          <template #title>
            实体商品需要您手动发货，请在下方填写物流信息
          </template>
        </el-alert>

        <!-- 选择发货商品 -->
        <div class="deliver-items">
          <div class="deliver-items-header">
            <span>选择发货商品</span>
            <el-button size="small" link type="primary" @click="selectedItemIds = undeliveredItems.map(i => i.id)">全选</el-button>
          </div>
          <el-checkbox-group v-model="selectedItemIds" class="deliver-items-list">
            <div v-for="item in undeliveredItems" :key="item.id" class="deliver-item">
              <el-checkbox :value="item.id">
                <div class="deliver-item-info">
                  <span class="deliver-item-name">{{ item.product_name }}</span>
                  <el-tag size="small" :type="productTypeMap[item.product_type]?.type as any">
                    {{ productTypeMap[item.product_type]?.label }}
                  </el-tag>
                  <span class="deliver-item-qty">x{{ item.quantity }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>

        <el-form label-width="80px" style="margin-top: 16px">
          <el-form-item label="发货备注">
            <el-input
              v-model="deliverRemark"
              type="textarea"
              :rows="3"
              placeholder="可填写物流单号、发货说明等信息，将通过邮件发送给用户"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="deliverDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="delivering" :disabled="selectedItemIds.length === 0" @click="handleDeliver">
          确认发货 ({{ selectedItemIds.length }} 件)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.info-card {
  margin-bottom: 20px;
}

.price {
  font-weight: 600;
  color: var(--el-color-danger);
}

.product-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.delivery-content {
  pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-all;
    font-family: inherit;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

.text-gray {
  color: var(--el-text-color-placeholder);
}

.log-content {
  display: flex;
  align-items: center;
  gap: 10px;

  .operator {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

.header-actions {
  display: flex;
  gap: 10px;
}

.deliver-items {
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 12px;

  .deliver-items-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-weight: 500;
  }

  .deliver-items-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .deliver-item {
    background: var(--el-bg-color);
    border-radius: 6px;
    padding: 10px 12px;

    .deliver-item-info {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .deliver-item-name {
      font-weight: 500;
    }

    .deliver-item-qty {
      color: var(--el-text-color-secondary);
      font-size: 12px;
    }
  }
}
</style>
