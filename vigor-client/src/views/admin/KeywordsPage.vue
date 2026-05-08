<template>
  <div class="keywords-page">
    <div class="page-header">
      <h1>关键词管理</h1>
      <button class="btn-primary" @click="showCreateDialog = true">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
        </svg>
        新增关键词
      </button>
    </div>

    <div class="filter-bar">
      <div class="filter-group">
        <label>领域筛选:</label>
        <select v-model="selectedCategoryId" @change="fetchKeywords" class="filter-select">
          <option :value="null">全部</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">
            {{ cat.name }}
          </option>
        </select>
      </div>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>领域名</th>
            <th>关键词</th>
            <th>状态</th>
            <th>优先级</th>
            <th>爬取阈值</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in keywords" :key="item.id">
            <td>{{ item.id }}</td>
            <td class="name-cell">{{ getCategoryName(item.category_id) }}</td>
            <td class="keyword-cell">{{ item.keyword }}</td>
            <td>
              <span class="status-badge" :class="item.status">
                {{ getStatusText(item.status) }}
              </span>
            </td>
            <td>{{ item.priority }}</td>
            <td>{{ item.crawl_threshold }}</td>
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
          <h2>{{ showCreateDialog ? '新增关键词' : '编辑关键词' }}</h2>
          <button class="close-btn" @click="closeDialogs">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>领域 *</label>
            <select v-model="formData.category_id" class="input" required>
              <option :value="null" disabled>请选择领域</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>关键词 *</label>
            <input v-model="formData.keyword" class="input" placeholder="如:财经新闻" required />
          </div>
          <div class="form-group">
            <label>优先级 (1-10)</label>
            <input v-model.number="formData.priority" type="number" min="1" max="10" class="input" />
          </div>
          <div class="form-group">
            <label>爬取阈值</label>
            <input v-model.number="formData.crawl_threshold" type="number" min="0" class="input" />
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="formData.status" class="input">
              <option value="active">启用</option>
              <option value="paused">暂停</option>
              <option value="archived">归档</option>
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
import { keywordApi } from '@/api/keyword'
import { categoryApi, type Category } from '@/api/category'
import type { Keyword, KeywordCreateInput, KeywordUpdateInput } from '@/types/keyword'

const keywords = ref<Keyword[]>([])
const categories = ref<Category[]>([])
const selectedCategoryId = ref<number | null>(null)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingId = ref<number | null>(null)

const formData = ref<KeywordCreateInput & { status?: 'active' | 'paused' | 'archived' }>({
  category_id: null as any,
  keyword: '',
  priority: 5,
  crawl_threshold: 100,
  status: 'active'
})

async function fetchCategories() {
  try {
    categories.value = await categoryApi.adminList()
  } catch (error) {
    alert('加载领域失败:' + error)
  }
}

async function fetchKeywords() {
  try {
    const params = selectedCategoryId.value ? { category_id: selectedCategoryId.value } : {}
    keywords.value = await keywordApi.list(params)
  } catch (error) {
    alert('加载关键词失败:' + error)
  }
}

function getCategoryName(categoryId: number): string {
  const cat = categories.value.find(c => c.id === categoryId)
  return cat ? cat.name : '-'
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    active: '启用',
    paused: '暂停',
    archived: '归档'
  }
  return map[status] || status
}

function handleEdit(item: Keyword) {
  editingId.value = item.id
  formData.value = {
    category_id: item.category_id,
    keyword: item.keyword,
    priority: item.priority,
    crawl_threshold: item.crawl_threshold,
    status: item.status
  }
  showEditDialog.value = true
}

async function handleDelete(item: Keyword) {
  if (!confirm(`确定删除关键词"${item.keyword}"吗?`)) return
  try {
    await keywordApi.delete(item.id)
    await fetchKeywords()
  } catch (error: any) {
    alert('删除失败:' + (error.message || error))
  }
}

async function handleSubmit() {
  if (!formData.value.category_id || !formData.value.keyword) {
    alert('请填写必填项')
    return
  }

  try {
    if (showCreateDialog.value) {
      await keywordApi.create(formData.value)
    } else if (editingId.value) {
      const updateData: KeywordUpdateInput = { ...formData.value }
      await keywordApi.update(editingId.value, updateData)
    }
    await fetchKeywords()
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
    category_id: null as any,
    keyword: '',
    priority: 5,
    crawl_threshold: 100,
    status: 'active'
  }
}

onMounted(() => {
  fetchCategories()
  fetchKeywords()
})
</script>

<style scoped>
.keywords-page {
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-bar {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.filter-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
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

.keyword-cell {
  font-weight: 500;
  color: var(--primary-color);
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

.status-badge.paused {
  background-color: rgba(255, 149, 0, 0.1);
  color: #ff9500;
}

.status-badge.archived {
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--border-color);
}
</style>
