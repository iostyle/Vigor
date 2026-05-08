<template>
  <div class="categories-page">
    <div class="page-header">
      <h1>领域管理</h1>
      <button class="btn-primary" @click="showCreateDialog = true">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
        </svg>
        新增领域
      </button>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>图标</th>
            <th>描述</th>
            <th>关键词数</th>
            <th>排序</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in categories" :key="item.id">
            <td>{{ item.id }}</td>
            <td class="name-cell">{{ item.name }}</td>
            <td class="icon-cell">{{ item.icon || '-' }}</td>
            <td class="desc-cell">{{ item.description || '-' }}</td>
            <td>{{ item.keyword_count }}</td>
            <td>{{ item.sort_order }}</td>
            <td>
              <span class="status-badge" :class="item.status">
                {{ item.status === 'active' ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="actions-cell">
              <button class="btn-icon" @click="handleEdit(item)">编辑</button>
              <button class="btn-icon danger" @click="handleDelete(item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑对话框 -->
    <div v-if="showCreateDialog || showEditDialog" class="dialog-overlay" @click.self="closeDialogs">
      <div class="dialog">
        <div class="dialog-header">
          <h2>{{ showCreateDialog ? '新增领域' : '编辑领域' }}</h2>
          <button class="close-btn" @click="closeDialogs">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>名称 *</label>
            <input v-model="formData.name" class="input" placeholder="如:财经" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="formData.icon" class="input" placeholder="如:💰" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="formData.description" class="input" rows="3" placeholder="领域描述"></textarea>
          </div>
          <div class="form-group">
            <label>排序</label>
            <input v-model.number="formData.sort_order" type="number" class="input" />
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="formData.status" class="input">
              <option value="active">启用</option>
              <option value="inactive">禁用</option>
            </select>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeDialogs">取消</button>
          <button class="btn-primary" @click="handleSubmit">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoryApi, type Category, type CategoryCreateInput, type CategoryUpdateInput } from '@/api/category'

const categories = ref<Category[]>([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingId = ref<number | null>(null)

const formData = ref<CategoryCreateInput & { status?: 'active' | 'inactive' }>({
  name: '',
  description: '',
  icon: '',
  sort_order: 0,
  status: 'active'
})

async function fetchCategories() {
  try {
    categories.value = await categoryApi.adminList()
  } catch (error) {
    alert('加载失败:' + error)
  }
}

function handleEdit(item: Category) {
  editingId.value = item.id
  formData.value = {
    name: item.name,
    description: item.description || '',
    icon: item.icon || '',
    sort_order: item.sort_order,
    status: item.status as 'active' | 'inactive'
  }
  showEditDialog.value = true
}

async function handleDelete(item: Category) {
  if (!confirm(`确定删除领域"${item.name}"吗?`)) return
  try {
    await categoryApi.delete(item.id)
    await fetchCategories()
  } catch (error: any) {
    alert('删除失败:' + (error.message || error))
  }
}

async function handleSubmit() {
  if (!formData.value.name) {
    alert('请输入名称')
    return
  }

  try {
    if (showCreateDialog.value) {
      await categoryApi.create(formData.value)
    } else if (editingId.value) {
      const updateData: CategoryUpdateInput = { ...formData.value }
      await categoryApi.update(editingId.value, updateData)
    }
    await fetchCategories()
    closeDialogs()
  } catch (error: any) {
    alert('操作失败:' + (error.message || error))
  }
}

function closeDialogs() {
  showCreateDialog.value = false
  showEditDialog.value = false
  editingId.value = null
  formData.value = {
    name: '',
    description: '',
    icon: '',
    sort_order: 0,
    status: 'active'
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style scoped>
.categories-page {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  padding: 10px 20px;
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

.table-container {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background-color: var(--bg-secondary);
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background-color: var(--bg-secondary);
}

.name-cell {
  font-weight: 500;
}

.icon-cell {
  font-size: 20px;
}

.desc-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background-color: rgba(52, 199, 89, 0.1);
  color: var(--success-color);
}

.status-badge.inactive {
  background-color: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.btn-icon {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-icon.danger:hover {
  background-color: rgba(255, 59, 48, 0.1);
  border-color: var(--error-color);
  color: var(--error-color);
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--border-color);
}

.dialog-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 24px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.dialog-body {
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.input {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

textarea.input {
  resize: vertical;
  font-family: inherit;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--border-color);
}
</style>
