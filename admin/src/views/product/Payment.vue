<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { get, post, put, del, upload } from '@/utils/request'
import type { PaymentMethod } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Upload, InfoFilled } from '@element-plus/icons-vue'

const loading = ref(false)
const list = ref<PaymentMethod[]>([])
const fileInputRef = ref<HTMLInputElement>()

// 弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref<Partial<PaymentMethod>>({
  name: '',
  icon: '',
  fee_type: 'percentage',
  fee_value: '0',
  description: '',
  meta_data: {},
  sort_order: 0,
  is_active: true,
})

// 当前选择的支付提供商
const selectedProvider = ref('')

const rules = {
  name: [{ required: true, message: '请输入支付名称', trigger: 'blur' }],
}

const feeTypes = [
  { value: 'percentage', label: '百分比' },
  { value: 'fixed', label: '固定金额' },
]

// 支付提供商配置模板
const providerTemplates: Record<string, {
  name: string
  description: string
  fields: Array<{
    key: string
    label: string
    type: 'text' | 'number' | 'password' | 'select'
    placeholder?: string
    required?: boolean
    default?: string | number
    options?: Array<{ label: string; value: string | number }>
    tip?: string
  }>
}> = {
  trc20_usdt: {
    name: 'TRC20 USDT',
    description: '通过 TRC20 网络接收 USDT 支付，系统自动扫描区块链确认交易',
    fields: [
      {
        key: 'wallet_address',
        label: '收款钱包地址',
        type: 'text',
        placeholder: 'T...',
        required: true,
        tip: 'TRC20 网络的 USDT 收款地址',
      },
      {
        key: 'trongrid_api_key',
        label: 'TronGrid API Key',
        type: 'password',
        placeholder: '可选，提高 API 调用限额',
        tip: '前往 trongrid.io 免费申请',
      },
      {
        key: 'scan_interval',
        label: '扫描间隔(秒)',
        type: 'number',
        default: 30,
        tip: '区块链交易扫描间隔，建议 20-60 秒',
      },
      {
        key: 'amount_precision',
        label: '金额精度',
        type: 'number',
        default: 4,
        tip: '小数位数，用于生成唯一支付金额',
      },
    ],
  },
  manual: {
    name: '人工确认',
    description: '用户支付后需管理员手动确认，适用于银行转账等场景',
    fields: [
      {
        key: 'payment_info',
        label: '收款信息',
        type: 'text',
        placeholder: '如：银行卡号、收款码说明等',
        required: true,
        tip: '显示给用户的收款信息',
      },
      {
        key: 'qrcode_url',
        label: '收款二维码',
        type: 'text',
        placeholder: '收款码图片 URL',
        tip: '可上传收款码图片',
      },
    ],
  },
  // 预留扩展
  wechat_native: {
    name: '微信支付(Native)',
    description: '微信扫码支付，适用于 PC 端',
    fields: [
      {
        key: 'appid',
        label: 'AppID',
        type: 'text',
        required: true,
      },
      {
        key: 'mchid',
        label: '商户号',
        type: 'text',
        required: true,
      },
      {
        key: 'api_key',
        label: 'API 密钥',
        type: 'password',
        required: true,
      },
      {
        key: 'cert_serial_no',
        label: '证书序列号',
        type: 'text',
        required: true,
      },
      {
        key: 'private_key',
        label: '商户私钥',
        type: 'password',
        required: true,
        tip: 'apiclient_key.pem 文件内容',
      },
    ],
  },
  alipay: {
    name: '支付宝',
    description: '支付宝扫码支付',
    fields: [
      {
        key: 'app_id',
        label: 'App ID',
        type: 'text',
        required: true,
      },
      {
        key: 'private_key',
        label: '应用私钥',
        type: 'password',
        required: true,
      },
      {
        key: 'alipay_public_key',
        label: '支付宝公钥',
        type: 'password',
        required: true,
      },
    ],
  },
}

// 当前选中的提供商模板
const currentTemplate = computed(() => {
  return selectedProvider.value ? providerTemplates[selectedProvider.value] : null
})

onMounted(() => {
  loadList()
})

async function loadList() {
  loading.value = true
  try {
    const res = await get<PaymentMethod[]>('/admin/products/payment-methods')
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogTitle.value = '添加支付方式'
  selectedProvider.value = ''
  form.value = {
    name: '',
    icon: '',
    fee_type: 'percentage',
    fee_value: '0',
    description: '',
    meta_data: {},
    sort_order: 0,
    is_active: true,
  }
  dialogVisible.value = true
}

function openEdit(row: PaymentMethod) {
  dialogTitle.value = '编辑支付方式'
  form.value = { ...row, meta_data: { ...row.meta_data } }
  // 尝试识别已有的 provider
  const providerId = row.meta_data?.provider_id as string
  selectedProvider.value = providerId && providerTemplates[providerId] ? providerId : ''
  dialogVisible.value = true
}

function onProviderChange(providerId: string) {
  const template = providerTemplates[providerId]
  if (!template) return

  // 设置默认值
  form.value.name = template.name
  form.value.description = template.description
  form.value.meta_data = { provider_id: providerId }

  // 设置字段默认值
  for (const field of template.fields) {
    if (field.default !== undefined) {
      form.value.meta_data[field.key] = field.default
    }
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  // 验证必填的 meta_data 字段
  if (currentTemplate.value) {
    for (const field of currentTemplate.value.fields) {
      if (field.required && !form.value.meta_data?.[field.key]) {
        ElMessage.warning(`请填写 ${field.label}`)
        return
      }
    }
  }

  try {
    if (form.value.id) {
      await put(`/admin/products/payment-methods/${form.value.id}`, form.value)
    } else {
      await post('/admin/products/payment-methods', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadList()
  } catch {
    // 错误已处理
  }
}

async function handleDelete(row: PaymentMethod) {
  await ElMessageBox.confirm('确定要删除该支付方式吗？', '提示', { type: 'warning' })
  try {
    await del(`/admin/products/payment-methods/${row.id}`)
    ElMessage.success('删除成功')
    await loadList()
  } catch {
    // 错误已处理
  }
}

// 上传图标
async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  if (!file) return
  try {
    const res = await upload<{ url: string }>('/common/upload', file, 'icons')
    form.value.icon = res.data.url
    ElMessage.success('上传成功')
  } catch {
    // 错误已处理
  }
  input.value = ''
}

// 获取提供商显示名称
function getProviderName(metaData: Record<string, unknown>) {
  const providerId = metaData?.provider_id as string
  if (providerId && providerTemplates[providerId]) {
    return providerTemplates[providerId].name
  }
  return '自定义'
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <h1 class="page-title">支付方式</h1>
      <el-button type="primary" :icon="Plus" @click="openCreate">添加支付方式</el-button>
    </div>

    <el-card>
      <el-table :data="list" style="width: 100%">
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <el-image v-if="row.icon" :src="row.icon" fit="cover" style="width: 40px; height: 40px; border-radius: 4px" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column label="类型" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ getProviderName(row.meta_data) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="手续费" width="120">
          <template #default="{ row }">
            {{ row.fee_type === 'percentage' ? `${row.fee_value}%` : `$${row.fee_value}` }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button type="primary" :icon="Edit" link @click="openEdit(row)">编辑</el-button>
              <el-button type="danger" :icon="Delete" link @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" class="form-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <!-- 选择支付类型 -->
        <el-form-item label="支付类型">
          <el-select
            v-model="selectedProvider"
            placeholder="选择支付类型"
            style="width: 100%"
            @change="onProviderChange"
            :disabled="!!form.id"
          >
            <el-option
              v-for="(template, key) in providerTemplates"
              :key="key"
              :label="template.name"
              :value="key"
            >
              <div class="provider-option">
                <span class="provider-name">{{ template.name }}</span>
                <span class="provider-desc">{{ template.description }}</span>
              </div>
            </el-option>
          </el-select>
          <div v-if="form.id" class="form-tip">编辑时不可更改支付类型</div>
        </el-form-item>

        <!-- 类型描述 -->
        <el-alert
          v-if="currentTemplate"
          :title="currentTemplate.name"
          :description="currentTemplate.description"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px"
        />

        <el-divider v-if="currentTemplate">基础信息</el-divider>

        <el-form-item label="支付名称" prop="name">
          <el-input v-model="form.name" placeholder="如：TRC20 USDT" />
        </el-form-item>

        <el-form-item label="支付图标">
          <div class="upload-area">
            <el-image v-if="form.icon" :src="form.icon" fit="cover" class="icon-preview" />
            <input ref="fileInputRef" type="file" accept="image/*" style="display: none" @change="handleUpload" />
            <el-button size="small" :icon="Upload" @click="fileInputRef?.click()">
              {{ form.icon ? '更换' : '上传' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="手续费类型">
          <el-radio-group v-model="form.fee_type">
            <el-radio v-for="item in feeTypes" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="手续费值">
          <el-input v-model="form.fee_value" placeholder="0" style="width: 200px">
            <template #append>{{ form.fee_type === 'percentage' ? '%' : '元' }}</template>
          </el-input>
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="支付方式说明（可选）" />
        </el-form-item>

        <!-- 支付配置 -->
        <template v-if="currentTemplate">
          <el-divider>支付配置</el-divider>

          <el-form-item
            v-for="field in currentTemplate.fields"
            :key="field.key"
            :label="field.label"
            :required="field.required"
          >
            <template v-if="field.type === 'text'">
              <el-input
                v-model="form.meta_data![field.key]"
                :placeholder="field.placeholder"
              />
            </template>
            <template v-else-if="field.type === 'password'">
              <el-input
                v-model="form.meta_data![field.key]"
                type="password"
                show-password
                :placeholder="field.placeholder"
              />
            </template>
            <template v-else-if="field.type === 'number'">
              <el-input-number
                v-model="form.meta_data![field.key]"
                :min="0"
              />
            </template>
            <template v-else-if="field.type === 'select'">
              <el-select v-model="form.meta_data![field.key]" style="width: 100%">
                <el-option
                  v-for="opt in field.options"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </template>
            <div v-if="field.tip" class="field-tip">
              <el-icon><InfoFilled /></el-icon>
              {{ field.tip }}
            </div>
          </el-form-item>
        </template>

        <el-divider>其他设置</el-divider>

        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
          <span class="form-tip">数值越小越靠前</span>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.upload-area {
  display: flex;
  align-items: center;
  gap: 10px;

  .icon-preview {
    width: 40px;
    height: 40px;
    border-radius: 4px;
  }
}

.provider-option {
  display: flex;
  flex-direction: column;
  padding: 4px 0;

  .provider-name {
    font-weight: 500;
  }

  .provider-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

.field-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);

  .el-icon {
    font-size: 14px;
  }
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
