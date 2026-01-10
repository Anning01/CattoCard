<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { get, post, put, del, upload } from '@/utils/request'
import type { Category } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Upload } from '@element-plus/icons-vue'

const loading = ref(false)
const list = ref<Category[]>([])
const fileInputRef = ref<HTMLInputElement>()

// 弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref<Partial<Category>>({
  name: '',
  slug: '',
  description: '',
  icon: '',
  parent_id: null,
  sort_order: 0,
  is_active: true,
})

const rules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入分类别名', trigger: 'blur' },
    { pattern: /^[a-z0-9]+(?:-[a-z0-9]+)*$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' },
  ],
}

// 顶级分类（用于选择父分类）
const parentCategories = computed(() => list.value.filter((c) => !c.parent_id))

onMounted(() => {
  loadList()
})

async function loadList() {
  loading.value = true
  try {
    const res = await get<Category[]>('/admin/products/categories')
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate(parentId: number | null = null) {
  dialogTitle.value = '添加分类'
  form.value = {
    name: '',
    slug: '',
    description: '',
    icon: '',
    parent_id: parentId,
    sort_order: 0,
    is_active: true,
  }
  dialogVisible.value = true
}

function openEdit(row: Category) {
  dialogTitle.value = '编辑分类'
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.value.id) {
      await put(`/admin/products/categories/${form.value.id}`, form.value)
    } else {
      await post('/admin/products/categories', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadList()
  } catch {
    // 错误已处理
  }
}

async function handleDelete(row: Category) {
  await ElMessageBox.confirm('确定要删除该分类吗？', '提示', { type: 'warning' })
  try {
    await del(`/admin/products/categories/${row.id}`)
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

// 树形数据：将扁平列表转换为树形结构
const treeData = computed(() => {
  const topLevel = list.value.filter((c) => !c.parent_id)
  return topLevel.map((parent) => ({
    ...parent,
    children: list.value.filter((c) => c.parent_id === parent.id),
  }))
})
</script>

<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header flex-between">
      <h1 class="page-title">分类管理</h1>
      <el-button type="primary" :icon="Plus" @click="openCreate()">添加分类</el-button>
    </div>

    <el-card>
      <el-table
        :data="treeData"
        row-key="id"
        :tree-props="{ children: 'children' }"
        default-expand-all
        style="width: 100%"
      >
        <el-table-column prop="name" label="分类名称" min-width="200">
          <template #default="{ row }">
            <span class="category-name">
              <el-image v-if="row.icon" :src="row.icon" fit="cover" class="category-icon" />
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="slug" label="别名" width="150" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button v-if="!row.parent_id" type="success" link size="small" @click.stop="openCreate(row.id)">
                添加子分类
              </el-button>
              <el-button type="primary" :icon="Edit" link size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button type="danger" :icon="Delete" link size="small" @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" class="form-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="如：游戏充值" />
        </el-form-item>
        <el-form-item label="分类别名" prop="slug">
          <el-input v-model="form.slug" placeholder="如：game-recharge" />
        </el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="form.parent_id" placeholder="无（顶级分类）" clearable style="width: 100%">
            <el-option
              v-for="item in parentCategories"
              :key="item.id"
              :label="item.name"
              :value="item.id"
              :disabled="item.id === form.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类图标">
          <div class="upload-area">
            <el-image v-if="form.icon" :src="form.icon" fit="cover" class="icon-preview" />
            <input ref="fileInputRef" type="file" accept="image/*" style="display: none" @change="handleUpload" />
            <el-button size="small" :icon="Upload" @click="fileInputRef?.click()">
              {{ form.icon ? '更换' : '上传' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选" />
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

<style scoped lang="scss">
.category-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  .category-icon {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    flex-shrink: 0;
  }
}

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

.table-actions {
  display: flex;
  gap: 4px;
}
</style>
