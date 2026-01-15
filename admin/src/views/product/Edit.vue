<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { get, post, put, upload, del } from '@/utils/request'
import { useAppStore } from '@/stores/app'
import type { Product, Category, PaymentMethod, ProductImage, ProductTag, ProductIntro, InventoryItem } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Upload } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const fileInputRef = ref<HTMLInputElement>()
const appStore = useAppStore()

const isEdit = computed(() => !!route.params.id)
const pageTitle = computed(() => (isEdit.value ? '编辑商品' : '添加商品'))

// 表单数据
const formRef = ref()
const form = ref<{
  name: string
  slug: string
  product_type: 'virtual' | 'physical'
  price: string
  stock: number
  category_id: number | null
  is_active: boolean
  sort_order: number
  payment_method_ids: number[]
  images: ProductImage[]
  tags: ProductTag[]
  intros: ProductIntro[]
}>({
  name: '',
  slug: '',
  product_type: 'virtual',
  price: '',
  stock: 0,
  category_id: null,
  is_active: true,
  sort_order: 0,
  payment_method_ids: [],
  images: [],
  tags: [],
  intros: [],
})

const rules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入商品别名', trigger: 'blur' },
    { pattern: /^[a-z0-9]+(?:-[a-z0-9]+)*$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' },
  ],
  price: [{ required: true, message: '请输入商品价格', trigger: 'blur' }],
}

// 选项数据
const categories = ref<Category[]>([])
const paymentMethods = ref<PaymentMethod[]>([])
const tagSuggestions = ref<Record<string, string[]>>({})

// 标签输入
const tagInput = ref({ key: '', value: '' })

// 常用介绍标题
const introTitleSuggestions = ['商品信息', '商品优势', '使用教程', '售后说明', '购买须知', '常见问题']

// 库存管理（仅虚拟商品）
const inventoryItems = ref<InventoryItem[]>([])
const inventoryLoading = ref(false)
const showInventoryDialog = ref(false)
const inventoryInput = ref('')
const inventoryInputMode = ref<'single' | 'batch'>('single')

// 创建模式下的临时卡密列表
const tempInventoryItems = ref<{ content: string }[]>([])

// 是否显示库存管理
const showInventory = computed(() => form.value.product_type === 'virtual')

onMounted(async () => {
  await Promise.all([loadCategories(), loadPaymentMethods(), loadTagSuggestions()])
  if (isEdit.value) {
    await loadProduct()
  }
})

// 监听商品类型变化，加载库存
watch(() => form.value.product_type, async (newType) => {
  if (isEdit.value && newType === 'virtual') {
    await loadInventory()
  }
})

async function loadCategories() {
  const res = await get<Category[]>('/admin/products/categories')
  categories.value = res.data
}

async function loadPaymentMethods() {
  const res = await get<PaymentMethod[]>('/admin/products/payment-methods')
  paymentMethods.value = res.data
}

async function loadTagSuggestions() {
  try {
    const res = await get<Record<string, string[]>>('/admin/products/tags/suggestions')
    tagSuggestions.value = res.data
  } catch {
    // 忽略错误
  }
}

async function loadProduct() {
  loading.value = true
  try {
    const res = await get<Product>(`/admin/products/${route.params.id}`)
    const product = res.data
    form.value = {
      name: product.name,
      slug: product.slug,
      product_type: product.product_type,
      price: product.price,
      stock: product.stock,
      category_id: product.category?.id || null,
      is_active: product.is_active,
      sort_order: product.sort_order,
      payment_method_ids: product.payment_methods.map((p) => p.id),
      images: product.images,
      tags: product.tags,
      intros: product.intros,
    }
    // 加载虚拟商品库存
    if (product.product_type === 'virtual') {
      await loadInventory()
    }
  } finally {
    loading.value = false
  }
}

// 加载库存
async function loadInventory() {
  if (!isEdit.value) return
  inventoryLoading.value = true
  try {
    const res = await get<InventoryItem[]>(`/admin/products/${route.params.id}/inventory`)
    inventoryItems.value = res.data
  } finally {
    inventoryLoading.value = false
  }
}

// 打开添加库存对话框
function openInventoryDialog() {
  inventoryInput.value = ''
  inventoryInputMode.value = 'single'
  showInventoryDialog.value = true
}

// 添加库存
async function handleAddInventory() {
  if (!inventoryInput.value.trim()) {
    ElMessage.warning('请输入卡密内容')
    return
  }

  const contents = inventoryInputMode.value === 'batch'
    ? inventoryInput.value.split('\n').map(s => s.trim()).filter(s => s)
    : [inventoryInput.value.trim()]

  if (contents.length === 0) {
    ElMessage.warning('请输入卡密内容')
    return
  }

  // 编辑模式：直接保存到数据库
  if (isEdit.value) {
    try {
      await post(`/admin/products/${route.params.id}/inventory`, { contents })
      ElMessage.success(`成功添加 ${contents.length} 条卡密`)
      showInventoryDialog.value = false
      await loadInventory()
      // 更新库存数量
      form.value.stock = inventoryItems.value.filter(i => !i.is_sold).length
    } catch {
      // 错误已处理
    }
  } else {
    // 创建模式：添加到临时列表
    contents.forEach(content => {
      tempInventoryItems.value.push({ content })
    })
    ElMessage.success(`成功添加 ${contents.length} 条卡密`)
    showInventoryDialog.value = false
    // 更新库存数量
    form.value.stock = tempInventoryItems.value.length
  }
}

// 删除库存项
async function handleDeleteInventory(item: InventoryItem | { content: string }, index?: number) {
  await ElMessageBox.confirm('确定要删除该卡密吗？', '删除确认', { type: 'warning' })
  
  // 编辑模式：从数据库删除
  if (isEdit.value && 'id' in item) {
    try {
      await del(`/admin/products/${route.params.id}/inventory/${item.id}`)
      ElMessage.success('删除成功')
      await loadInventory()
      // 更新库存数量
      form.value.stock = inventoryItems.value.filter(i => !i.is_sold).length
    } catch {
      // 错误已处理
    }
  } else {
    // 创建模式：从临时列表删除
    if (index !== undefined) {
      tempInventoryItems.value.splice(index, 1)
      ElMessage.success('删除成功')
      // 更新库存数量
      form.value.stock = tempInventoryItems.value.length
    }
  }
}

// 上传图片
async function handleUploadImage(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  for (const file of Array.from(input.files)) {
    try {
      const res = await upload<{ url: string }>('/common/upload', file, 'images')
      form.value.images.push({
        id: 0,
        image_url: res.data.url,
        sort_order: form.value.images.length,
        is_primary: form.value.images.length === 0,
      })
    } catch {
      // 错误已处理
    }
  }
  input.value = ''
}

function removeImage(index: number) {
  const image = form.value.images[index]
  if (!image) return
  const wasPrimary = image.is_primary
  form.value.images.splice(index, 1)
  if (wasPrimary && form.value.images.length > 0 && form.value.images[0]) {
    form.value.images[0].is_primary = true
  }
}

function setPrimaryImage(index: number) {
  form.value.images.forEach((img, i) => {
    img.is_primary = i === index
  })
}

// 标签相关
const tagKeyOptions = computed(() => Object.keys(tagSuggestions.value))
const tagValueOptions = computed(() => tagSuggestions.value[tagInput.value.key] || [])

function addTag() {
  if (!tagInput.value.key || !tagInput.value.value) {
    ElMessage.warning('请输入标签键和值')
    return
  }
  form.value.tags.push({
    id: 0,
    key: tagInput.value.key,
    value: tagInput.value.value,
  })
  tagInput.value = { key: '', value: '' }
}

function removeTag(index: number) {
  form.value.tags.splice(index, 1)
}

// 介绍相关
function addIntro() {
  form.value.intros.push({
    id: 0,
    title: '',
    content: '',
    icon: null,
    sort_order: form.value.intros.length,
    is_active: true,
    created_at: '',
    updated_at: '',
  })
}

function removeIntro(index: number) {
  form.value.intros.splice(index, 1)
}

// 提交
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const data = {
      ...form.value,
      images: form.value.images.map((img) => ({
        image_url: img.image_url,
        sort_order: img.sort_order,
        is_primary: img.is_primary,
      })),
      tags: form.value.tags.map((tag) => ({
        key: tag.key,
        value: tag.value,
      })),
      intros: form.value.intros.map((intro, index) => ({
        title: intro.title,
        content: intro.content,
        icon: intro.icon,
        sort_order: index,
        is_active: intro.is_active,
      })),
      // 创建模式下添加卡密列表
      ...((!isEdit.value && form.value.product_type === 'virtual') ? {
        inventory_contents: tempInventoryItems.value.map(item => item.content)
      } : {})
    }

    if (isEdit.value) {
      await put(`/admin/products/${route.params.id}`, data)
    } else {
      await post('/admin/products', data)
    }
    ElMessage.success('保存成功')
    router.push('/product/list')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.back()
}

// 未售出数量
const unsoldCount = computed(() => {
  if (isEdit.value) {
    return inventoryItems.value.filter(i => !i.is_sold).length
  } else {
    return tempInventoryItems.value.length
  }
})
const soldCount = computed(() => {
  if (isEdit.value) {
    return inventoryItems.value.filter(i => i.is_sold).length
  } else {
    return 0
  }
})

// 显示的库存列表
const displayInventoryItems = computed(() => {
  if (isEdit.value) {
    return inventoryItems.value
  } else {
    return tempInventoryItems.value.map((item, index) => ({
      id: index,
      content: item.content,
      is_sold: false,
      sold_at: null,
      created_at: '',
      updated_at: ''
    }))
  }
})
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <h1 class="page-title">{{ pageTitle }}</h1>
      <div class="header-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存商品</el-button>
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-row :gutter="20">
        <!-- 左栏 -->
        <el-col :span="16">
          <!-- 基本信息 -->
          <el-card class="form-card">
            <template #header>基本信息</template>

            <el-form-item label="商品名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入商品名称" />
            </el-form-item>

            <el-form-item label="商品别名" prop="slug">
              <el-input v-model="form.slug" placeholder="用于URL，如 steam-card-50" />
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="商品价格" prop="price">
                  <el-input v-model="form.price" placeholder="0.00">
                    <template #prepend>{{ appStore.siteConfig.currency_symbol }}</template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="商品分类">
                  <el-select v-model="form.category_id" placeholder="请选择分类" clearable style="width: 100%">
                    <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="商品类型">
                  <el-radio-group v-model="form.product_type">
                    <el-radio value="virtual">虚拟</el-radio>
                    <el-radio value="physical">实体</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="库存数量">
                  <el-input-number
                    v-model="form.stock"
                    :min="0"
                    :disabled="form.product_type === 'virtual'"
                    style="width: 100%"
                  />
                  <div v-if="form.product_type === 'virtual'" class="form-tip">
                    虚拟商品库存由卡密数量决定
                  </div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="排序">
                  <el-input-number v-model="form.sort_order" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-card>

          <!-- 卡密管理（虚拟商品显示） -->
          <el-card v-if="showInventory" class="form-card" v-loading="inventoryLoading">
            <template #header>
              <div class="flex-between">
                <span>
                  卡密管理
                  <el-tag size="small" type="success" style="margin-left: 8px">未售出: {{ unsoldCount }}</el-tag>
                  <el-tag v-if="isEdit" size="small" type="info" style="margin-left: 4px">已售出: {{ soldCount }}</el-tag>
                </span>
                <el-button type="primary" :icon="Plus" size="small" @click="openInventoryDialog">添加卡密</el-button>
              </div>
            </template>

            <el-table :data="displayInventoryItems" style="width: 100%" max-height="400">
              <el-table-column prop="content" label="卡密内容" min-width="200">
                <template #default="{ row }">
                  <span :class="{ 'sold-content': row.is_sold }">{{ row.content }}</span>
                </template>
              </el-table-column>
              <el-table-column v-if="isEdit" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag v-if="row.is_sold" type="info" size="small">已售出</el-tag>
                  <el-tag v-else type="success" size="small">未售出</el-tag>
                </template>
              </el-table-column>
              <el-table-column v-if="isEdit" label="售出时间" width="180">
                <template #default="{ row }">
                  <span v-if="row.sold_at">{{ new Date(row.sold_at).toLocaleString() }}</span>
                  <span v-else class="text-gray">-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row, $index }">
                  <el-button
                    v-if="!row.is_sold"
                    type="danger"
                    :icon="Delete"
                    link
                    @click="handleDeleteInventory(row, $index)"
                  >
                    删除
                  </el-button>
                  <span v-else class="text-gray">-</span>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!displayInventoryItems.length" description="暂无卡密" :image-size="60" />
          </el-card>

          <!-- 商品图片 -->
          <el-card class="form-card">
            <template #header>商品图片</template>

            <div class="image-list">
              <div v-for="(img, index) in form.images" :key="index" class="image-item">
                <el-image :src="img.image_url" fit="cover" class="image-preview" />
                <div class="image-actions">
                  <el-button v-if="!img.is_primary" size="small" link @click="setPrimaryImage(index)">设为主图</el-button>
                  <el-tag v-else size="small" type="success">主图</el-tag>
                  <el-button size="small" type="danger" link @click="removeImage(index)">删除</el-button>
                </div>
              </div>
              <div class="image-upload" @click="fileInputRef?.click()">
                <input ref="fileInputRef" type="file" accept="image/*" multiple style="display: none" @change="handleUploadImage" />
                <el-icon><Plus /></el-icon>
                <span>上传图片</span>
              </div>
            </div>
          </el-card>

          <!-- 商品介绍 -->
          <el-card class="form-card">
            <template #header>
              <div class="flex-between">
                <span>商品介绍</span>
                <el-button type="primary" :icon="Plus" size="small" @click="addIntro">添加介绍</el-button>
              </div>
            </template>

            <div v-for="(intro, index) in form.intros" :key="index" class="intro-item">
              <div class="intro-header">
                <el-autocomplete
                  v-model="intro.title"
                  :fetch-suggestions="(q: string, cb: (s: {value: string}[]) => void) => cb(introTitleSuggestions.filter(s => s.includes(q)).map(s => ({ value: s })))"
                  placeholder="介绍标题（如：商品信息）"
                  style="width: 200px"
                />
                <el-input-number v-model="intro.sort_order" :min="0" placeholder="排序" style="width: 100px; margin-left: 10px" />
                <el-switch v-model="intro.is_active" style="margin-left: 10px" />
                <el-button type="danger" :icon="Delete" link style="margin-left: 10px" @click="removeIntro(index)" />
              </div>
              <el-input
                v-model="intro.content"
                type="textarea"
                :rows="4"
                placeholder="介绍内容，支持HTML"
                style="margin-top: 10px"
              />
            </div>
            <el-empty v-if="!form.intros.length" description="暂无介绍内容" :image-size="60" />
          </el-card>
        </el-col>

        <!-- 右栏 -->
        <el-col :span="8">
          <!-- 状态 -->
          <el-card class="form-card">
            <template #header>状态</template>
            <el-form-item label="上架状态" label-width="80px">
              <el-switch v-model="form.is_active" active-text="上架" inactive-text="下架" />
            </el-form-item>
          </el-card>

          <!-- 支付方式 -->
          <el-card class="form-card">
            <template #header>支付方式</template>
            <el-checkbox-group v-model="form.payment_method_ids">
              <el-checkbox v-for="item in paymentMethods" :key="item.id" :value="item.id" style="display: block; margin-bottom: 8px">
                {{ item.name }}
              </el-checkbox>
            </el-checkbox-group>
            <el-empty v-if="!paymentMethods.length" description="暂无支付方式" :image-size="40" />
          </el-card>

          <!-- 商品标签 -->
          <el-card class="form-card">
            <template #header>商品标签</template>

            <div class="tag-list">
              <el-tag v-for="(tag, index) in form.tags" :key="index" closable @close="removeTag(index)">
                {{ tag.key }}: {{ tag.value }}
              </el-tag>
            </div>
            <div class="tag-input">
              <el-autocomplete
                v-model="tagInput.key"
                :fetch-suggestions="(q: string, cb: (s: {value: string}[]) => void) => cb(tagKeyOptions.filter(s => s.includes(q)).map(s => ({ value: s })))"
                placeholder="标签键"
                style="width: 100%"
                size="default"
              />
              <el-autocomplete
                v-model="tagInput.value"
                :fetch-suggestions="(q: string, cb: (s: {value: string}[]) => void) => cb(tagValueOptions.filter(s => s.includes(q)).map(s => ({ value: s })))"
                placeholder="标签值"
                style="width: 100%"
                size="default"
              />
              <el-button type="primary" size="default" @click="addTag">添加标签</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-form>

    <!-- 添加卡密对话框 -->
    <el-dialog v-model="showInventoryDialog" title="添加卡密" width="600">
      <el-radio-group v-model="inventoryInputMode" style="margin-bottom: 16px">
        <el-radio-button value="single">单条添加</el-radio-button>
        <el-radio-button value="batch">批量导入</el-radio-button>
      </el-radio-group>

      <el-input
        v-model="inventoryInput"
        :type="inventoryInputMode === 'batch' ? 'textarea' : 'text'"
        :rows="inventoryInputMode === 'batch' ? 10 : 1"
        :placeholder="inventoryInputMode === 'batch' ? '每行一条卡密，支持批量粘贴' : '请输入卡密内容'"
      />

      <div v-if="inventoryInputMode === 'batch'" class="dialog-tip">
        提示：每行一条卡密，可直接从Excel或文本文件中复制粘贴
      </div>

      <template #footer>
        <el-button @click="showInventoryDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddInventory">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.form-card {
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;

  .image-item {
    .image-preview {
      width: 100px;
      height: 100px;
      border-radius: 6px;
    }

    .image-actions {
      display: flex;
      justify-content: center;
      gap: 8px;
      margin-top: 6px;
    }
  }

  .image-upload {
    width: 100px;
    height: 100px;
    border: 1px dashed var(--el-border-color);
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: var(--el-text-color-placeholder);
    transition: all 0.3s;

    &:hover {
      border-color: var(--el-color-primary);
      color: var(--el-color-primary);
    }

    .el-icon {
      font-size: 20px;
      margin-bottom: 6px;
    }
  }
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  min-height: 24px;
}

.tag-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.intro-item {
  padding: 15px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  margin-bottom: 15px;

  .intro-header {
    display: flex;
    align-items: center;
  }
}

.sold-content {
  color: var(--el-text-color-placeholder);
  text-decoration: line-through;
}

.text-gray {
  color: var(--el-text-color-placeholder);
}

.dialog-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
