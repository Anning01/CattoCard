<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, post, put, del } from '@/utils/request'
import type { Announcement } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const list = ref<Announcement[]>([])

// 弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref<Partial<Announcement>>({
  title: '',
  description: '',
  content: '',
  is_popup: false,
  is_active: true,
})

const rules = {
  title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }],
}

onMounted(() => {
  loadList()
})

async function loadList() {
  loading.value = true
  try {
    const res = await get<Announcement[]>('/admin/platform/announcements')
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogTitle.value = '添加公告'
  form.value = {
    title: '',
    description: '',
    content: '',
    is_popup: false,
    is_active: true,
  }
  dialogVisible.value = true
}

function openEdit(row: Announcement) {
  dialogTitle.value = '编辑公告'
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.value.id) {
      await put(`/admin/platform/announcements/${form.value.id}`, form.value)
    } else {
      await post('/admin/platform/announcements', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadList()
  } catch {
    // 错误已处理
  }
}

async function handleDelete(row: Announcement) {
  await ElMessageBox.confirm('确定要删除该公告吗？', '提示', { type: 'warning' })
  try {
    await del(`/admin/platform/announcements/${row.id}`)
    ElMessage.success('删除成功')
    await loadList()
  } catch {
    // 错误已处理
  }
}
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <h1 class="page-title">公告管理</h1>
      <el-button type="primary" :icon="Plus" @click="openCreate">添加公告</el-button>
    </div>

    <el-card>
      <el-table :data="list" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_popup" label="弹窗显示" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_popup ? 'success' : 'info'" size="small">
              {{ row.is_popup ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
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
              <el-button type="primary" :icon="Edit" link @click="openEdit(row)">编辑</el-button>
              <el-button type="danger" :icon="Delete" link @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" class="form-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="公告标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="公告描述" prop="description">
          <el-input v-model="form.description" placeholder="请输入公告描述（可选）" />
        </el-form-item>
        <el-form-item label="公告内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="支持HTML富文本" />
        </el-form-item>
        <el-form-item label="弹窗显示">
          <el-switch v-model="form.is_popup" />
          <span style="margin-left: 10px; color: var(--el-text-color-secondary); font-size: 12px">
            开启后将在首页弹窗显示（仅一个生效）
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
