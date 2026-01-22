<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, post, put, upload } from '@/utils/request'
import type { PlatformConfig, EmailConfig } from '@/types'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const loading = ref(false)
const activeTab = ref('basic')
const logoInputRef = ref<HTMLInputElement>()
const faviconInputRef = ref<HTMLInputElement>()

// 基础配置
const configs = ref<PlatformConfig[]>([])
const configForm = ref<Record<string, string>>({})

// 邮件配置
const emailForm = ref<Partial<EmailConfig>>({
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  from_name: '',
  from_email: '',
  use_tls: true,
})
const testEmail = ref('')
const testingEmail = ref(false)

onMounted(async () => {
  await loadConfigs()
  loadOrderConfig()
  await loadEmailConfig()
})

// 加载基础配置
async function loadConfigs() {
  loading.value = true
  try {
    const res = await get<PlatformConfig[]>('/admin/platform/config')
    configs.value = res.data
    // 转换为表单格式
    configForm.value = res.data.reduce((acc, item) => {
      acc[item.key] = item.value
      return acc
    }, {} as Record<string, string>)
  } finally {
    loading.value = false
  }
}

// 保存基础配置
async function saveConfig(key: string) {
  const existing = configs.value.find((c) => c.key === key)
  try {
    if (existing) {
      await put(`/admin/platform/config/${key}`, { value: configForm.value[key] })
    } else {
      await post('/admin/platform/config', { key, value: configForm.value[key] })
    }
    ElMessage.success('保存成功')
    await loadConfigs()
  } catch {
    // 错误已处理
  }
}

// 加载邮件配置
async function loadEmailConfig() {
  try {
    const res = await get<EmailConfig>('/admin/platform/email-config')
    if (res.data) {
      emailForm.value = res.data
    }
  } catch {
    // 可能还没有配置
  }
}

// 保存邮件配置
async function saveEmailConfig() {
  try {
    await post('/admin/platform/email-config', emailForm.value)
    ElMessage.success('保存成功，请发送测试邮件验证配置')
    await loadEmailConfig()
  } catch {
    // 错误已处理
  }
}

// 测试邮件配置
async function testEmailConfig() {
  if (!testEmail.value) {
    ElMessage.warning('请输入测试邮箱地址')
    return
  }
  testingEmail.value = true
  try {
    await post(`/admin/platform/email-config/test?test_email=${encodeURIComponent(testEmail.value)}`)
    ElMessage.success('测试邮件发送成功，配置已验证')
    await loadEmailConfig()
  } catch {
    // 错误已处理
  } finally {
    testingEmail.value = false
  }
}

// 预设配置项
const defaultConfigs = [
  { key: 'site_name', label: '站点名称', placeholder: 'CardStore' },
  { key: 'site_description', label: '站点描述', placeholder: '虚拟物品交易平台' },
  { key: 'currency', label: '结算币种', placeholder: 'USD' },
  { key: 'currency_symbol', label: '货币符号', placeholder: '$' },
]

// 订单配置 - Switch 类型
const autoDeliveryEnabled = ref(false)

// 加载订单配置
function loadOrderConfig() {
  const config = configs.value.find((c) => c.key === 'auto_delivery_virtual')
  autoDeliveryEnabled.value = config?.value?.toLowerCase() === 'true'
}

// 保存自动发货配置
async function saveAutoDeliveryConfig(value: string | number | boolean) {
  const key = 'auto_delivery_virtual'
  const existing = configs.value.find((c) => c.key === key)
  try {
    if (existing) {
      await put(`/admin/platform/config/${key}`, { value: String(value) })
    } else {
      await post('/admin/platform/config', { key, value: String(value) })
    }
    ElMessage.success('保存成功')
    await loadConfigs()
    loadOrderConfig()
  } catch {
    // 错误已处理，恢复开关状态
    autoDeliveryEnabled.value = !value
  }
}

// 上传 Logo
async function handleUploadLogo(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  if (!file) return
  try {
    const res = await upload<{ url: string }>('/common/upload', file, 'logos')
    configForm.value['site_logo'] = res.data.url
    await saveConfig('site_logo')
  } catch {
    // 错误已处理
  }
  input.value = ''
}

// 上传 Favicon
async function handleUploadFavicon(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  if (!file) return
  try {
    const res = await upload<{ url: string }>('/common/upload', file, 'logos')
    configForm.value['site_favicon'] = res.data.url
    await saveConfig('site_favicon')
  } catch {
    // 错误已处理
  }
  input.value = ''
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">基础配置</h1>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 基础设置 -->
      <el-tab-pane label="基础设置" name="basic">
        <el-card>
          <el-form label-width="120px" style="max-width: 600px">
            <!-- Logo 配置 -->
            <el-form-item label="站点 Logo">
              <div class="upload-area">
                <el-image
                  v-if="configForm['site_logo']"
                  :src="configForm['site_logo']"
                  fit="contain"
                  class="logo-preview"
                />
                <input ref="logoInputRef" type="file" accept="image/*" style="display: none" @change="handleUploadLogo" />
                <el-button :icon="Upload" @click="logoInputRef?.click()">
                  {{ configForm['site_logo'] ? '更换 Logo' : '上传 Logo' }}
                </el-button>
              </div>
            </el-form-item>

            <!-- Favicon 配置 -->
            <el-form-item label="站点图标">
              <div class="upload-area">
                <el-image
                  v-if="configForm['site_favicon']"
                  :src="configForm['site_favicon']"
                  fit="contain"
                  class="favicon-preview"
                />
                <input ref="faviconInputRef" type="file" accept="image/*" style="display: none" @change="handleUploadFavicon" />
                <el-button :icon="Upload" @click="faviconInputRef?.click()">
                  {{ configForm['site_favicon'] ? '更换图标' : '上传图标' }}
                </el-button>
                <span class="upload-tip">建议尺寸 32x32 或 64x64</span>
              </div>
            </el-form-item>

            <el-divider />

            <el-form-item v-for="item in defaultConfigs" :key="item.key" :label="item.label">
              <el-input v-model="configForm[item.key]" :placeholder="item.placeholder">
                <template #append>
                  <el-button type="primary" @click="saveConfig(item.key)">保存</el-button>
                </template>
              </el-input>
            </el-form-item>

            <el-divider />

            <!-- 客服联系信息 -->
            <el-form-item label="客服联系信息">
              <div style="width: 100%">
                <el-input
                  v-model="configForm['contact_info']"
                  type="textarea"
                  :rows="4"
                  placeholder="输入客服联系方式，支持HTML格式，如：&#10;QQ: 123456&#10;微信: example&#10;邮箱: support@example.com"
                />
                <div style="margin-top: 8px; display: flex; gap: 8px">
                  <el-button type="primary" @click="saveConfig('contact_info')">保存客服信息</el-button>
                  <el-text type="info" size="small">此信息将在用户订单页面显示</el-text>
                </div>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 邮件配置 -->
      <el-tab-pane label="邮件配置" name="email">
        <el-card>
          <el-form :model="emailForm" label-width="120px" style="max-width: 600px">
            <el-form-item label="验证状态">
              <el-tag v-if="emailForm.is_verified" type="success">已验证</el-tag>
              <el-tag v-else type="warning">未验证</el-tag>
            </el-form-item>
            <el-form-item label="SMTP 服务器">
              <el-input v-model="emailForm.smtp_host" placeholder="smtp.example.com" />
            </el-form-item>
            <el-form-item label="SMTP 端口">
              <el-input-number v-model="emailForm.smtp_port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="SMTP 用户名">
              <el-input v-model="emailForm.smtp_user" placeholder="user@example.com" />
            </el-form-item>
            <el-form-item label="SMTP 密码">
              <el-input v-model="emailForm.smtp_password" type="password" show-password placeholder="********" />
            </el-form-item>
            <el-form-item label="发件人名称">
              <el-input v-model="emailForm.from_name" placeholder="CardStore" />
            </el-form-item>
            <el-form-item label="发件人邮箱">
              <el-input v-model="emailForm.from_email" placeholder="noreply@example.com" />
            </el-form-item>
            <el-form-item label="使用 TLS">
              <el-switch v-model="emailForm.use_tls" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveEmailConfig">保存配置</el-button>
            </el-form-item>

            <el-divider />

            <el-form-item label="测试邮箱">
              <el-input v-model="testEmail" placeholder="输入接收测试邮件的邮箱地址">
                <template #append>
                  <el-button type="success" :loading="testingEmail" @click="testEmailConfig">
                    发送测试
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-text type="info" size="small">
                保存配置后，请发送测试邮件验证配置是否正确。验证成功后才能正常发送订单通知邮件。
              </el-text>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 订单配置 -->
      <el-tab-pane label="订单配置" name="order">
        <el-card>
          <el-form label-width="140px" style="max-width: 600px">
            <el-form-item label="虚拟商品自动发货">
              <div class="switch-item">
                <el-switch
                  v-model="autoDeliveryEnabled"
                  @change="saveAutoDeliveryConfig"
                />
                <span class="switch-description">
                  开启后，用户支付成功时系统会自动发货虚拟商品（从库存中扣除卡密并发送邮件通知用户）
                </span>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped lang="scss">
.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;

  .logo-preview {
    width: 160px;
    height: 48px;
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    padding: 4px;
    background: var(--el-fill-color-light);
  }

  .favicon-preview {
    width: 48px;
    height: 48px;
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    padding: 4px;
    background: var(--el-fill-color-light);
  }

  .upload-tip {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

.switch-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;

  .switch-description {
    color: var(--el-text-color-secondary);
    font-size: 13px;
    line-height: 1.5;
    flex: 1;
  }
}
</style>
