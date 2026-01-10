<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, post, put, del } from '@/utils/request'
import type { FooterLink } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const list = ref<FooterLink[]>([])

// 弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref<Partial<FooterLink>>({
  title: '',
  url: '',
  link_type: 'agreement',
  sort_order: 0,
  is_active: true,
})

const rules = {
  title: [{ required: true, message: '请输入链接标题', trigger: 'blur' }],
  url: [{ required: true, message: '请输入链接地址', trigger: 'blur' }],
}

const linkTypes = [
  { value: 'agreement', label: '协议链接' },
  { value: 'friend_link', label: '友情链接' },
]

onMounted(() => {
  loadList()
})

async function loadList() {
  loading.value = true
  try {
    const res = await get<FooterLink[]>('/admin/platform/footer-links')
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogTitle.value = '添加链接'
  form.value = {
    title: '',
    url: '',
    link_type: 'agreement',
    sort_order: 0,
    is_active: true,
  }
  dialogVisible.value = true
}

function openEdit(row: FooterLink) {
  dialogTitle.value = '编辑链接'
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.value.id) {
      await put(`/admin/platform/footer-links/${form.value.id}`, form.value)
    } else {
      await post('/admin/platform/footer-links', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadList()
  } catch {
    // 错误已处理
  }
}

async function handleDelete(row: FooterLink) {
  await ElMessageBox.confirm('确定要删除该链接吗？', '提示', { type: 'warning' })
  try {
    await del(`/admin/platform/footer-links/${row.id}`)
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
      <h1 class="page-title">底部链接</h1>
      <el-button type="primary" :icon="Plus" @click="openCreate">添加链接</el-button>
    </div>

    <el-card>
      <el-table :data="list" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="url" label="链接" min-width="250" show-overflow-tooltip />
        <el-table-column prop="link_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.link_type === 'agreement' ? 'primary' : 'success'" size="small">
              {{ row.link_type === 'agreement' ? '协议链接' : '友情链接' }}
            </el-tag>
          </template>
        </el-table-column>
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
        <el-form-item label="链接标题" prop="title">
          <el-input v-model="form.title" placeholder="如：用户协议" />
        </el-form-item>
        <el-form-item label="链接地址" prop="url">
          <el-input v-model="form.url" placeholder="https://" />
        </el-form-item>
        <el-form-item label="链接类型">
          <el-radio-group v-model="form.link_type">
            <el-radio v-for="item in linkTypes" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
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
