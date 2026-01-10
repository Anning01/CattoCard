<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, post, put, del, upload } from '@/utils/request'
import type { Banner } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Upload } from '@element-plus/icons-vue'

const loading = ref(false)
const list = ref<Banner[]>([])
const fileInputRef = ref<HTMLInputElement>()

// 弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref<Partial<Banner>>({
  image_url: '',
  link_url: '',
  sort_order: 0,
  is_active: true,
})

const rules = {
  image_url: [{ required: true, message: '请上传Banner图片', trigger: 'change' }],
}

onMounted(() => {
  loadList()
})

async function loadList() {
  loading.value = true
  try {
    const res = await get<Banner[]>('/admin/platform/banners')
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogTitle.value = '添加Banner'
  form.value = {
    image_url: '',
    link_url: '',
    sort_order: 0,
    is_active: true,
  }
  dialogVisible.value = true
}

function openEdit(row: Banner) {
  dialogTitle.value = '编辑Banner'
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.value.id) {
      await put(`/admin/platform/banners/${form.value.id}`, form.value)
    } else {
      await post('/admin/platform/banners', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadList()
  } catch {
    // 错误已处理
  }
}

async function handleDelete(row: Banner) {
  await ElMessageBox.confirm('确定要删除该Banner吗？', '提示', { type: 'warning' })
  try {
    await del(`/admin/platform/banners/${row.id}`)
    ElMessage.success('删除成功')
    await loadList()
  } catch {
    // 错误已处理
  }
}

// 上传图片
async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  if (!file) return
  try {
    const res = await upload<{ url: string }>('/common/upload', file, 'banners')
    form.value.image_url = res.data.url
    ElMessage.success('上传成功')
  } catch {
    // 错误已处理
  }
  input.value = ''
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <h1 class="page-title">Banner管理</h1>
      <el-button type="primary" :icon="Plus" @click="openCreate">添加Banner</el-button>
    </div>

    <el-card>
      <el-table :data="list" style="width: 100%">
        <el-table-column label="图片" width="200">
          <template #default="{ row }">
            <el-image :src="row.image_url" :preview-src-list="[row.image_url]" fit="cover" style="width: 160px; height: 60px" />
          </template>
        </el-table-column>
        <el-table-column prop="link_url" label="跳转链接" min-width="200" show-overflow-tooltip />
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" class="form-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="Banner图片" prop="image_url">
          <div class="upload-area">
            <el-image v-if="form.image_url" :src="form.image_url" fit="cover" class="preview-image" />
            <input ref="fileInputRef" type="file" accept="image/*" style="display: none" @change="handleUpload" />
            <el-button :icon="Upload" @click="fileInputRef?.click()">
              {{ form.image_url ? '更换图片' : '上传图片' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.link_url" placeholder="点击后跳转的URL（可选）" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
          <span style="margin-left: 10px; color: var(--el-text-color-secondary); font-size: 12px">
            数值越小越靠前
          </span>
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
  .preview-image {
    width: 200px;
    height: 80px;
    margin-bottom: 10px;
    border-radius: 4px;
  }
}
</style>
