<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1>仪表盘</h1>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon video">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z" />
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">总视频数</div>
          <div class="stat-value">{{ totalVideos }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon keyword">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M17.63 5.84C17.27 5.33 16.67 5 16 5L5 5.01C3.9 5.01 3 5.9 3 7v10c0 1.1.9 1.99 2 1.99L16 19c.67 0 1.27-.33 1.63-.84L22 12l-4.37-6.16z" />
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">关键词数</div>
          <div class="stat-value">{{ totalKeywords }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon category">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">领域数</div>
          <div class="stat-value">{{ totalCategories }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon today">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z" />
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">今日新增</div>
          <div class="stat-value">{{ todayNew }}</div>
        </div>
      </div>
    </div>

    <div class="table-section">
      <div class="section-header">
        <h2>关键词统计</h2>
      </div>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>领域名称</th>
              <th>图标</th>
              <th>关键词数量</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in categories" :key="item.id">
              <td class="name-cell">{{ item.name }}</td>
              <td class="icon-cell">{{ item.icon || '-' }}</td>
              <td>{{ item.keyword_count }}</td>
              <td>
                <span class="status-badge" :class="item.status">
                  {{ item.status === 'active' ? '启用' : '禁用' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoryApi, type Category } from '@/api/category'
import { videoApi } from '@/api/video'
import { statsApi } from '@/api/stats'

const categories = ref<Category[]>([])
const totalVideos = ref(0)
const totalKeywords = ref(0)
const totalCategories = ref(0)
const todayNew = ref(0)

async function fetchData() {
  try {
    // 获取领域列表
    categories.value = await categoryApi.adminList()
    totalCategories.value = categories.value.length

    // 计算总关键词数
    totalKeywords.value = categories.value.reduce((sum, cat) => sum + cat.keyword_count, 0)

    // 获取总视频数
    const videoRes = await videoApi.list({ limit: 1 })
    totalVideos.value = videoRes.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

async function fetchTodayStats() {
  try {
    const stats = await statsApi.today()
    todayNew.value = stats.total
  } catch (error) {
    console.error('加载今日新增失败:', error)
    todayNew.value = 0
  }
}

onMounted(() => {
  fetchData()
  fetchTodayStats()
})
</script>

<style scoped>
.dashboard-page {
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xxl);
}

.stat-card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.video {
  background: linear-gradient(135deg, #007aff, #5856d6);
}

.stat-icon.keyword {
  background: linear-gradient(135deg, #34c759, #30d158);
}

.stat-icon.category {
  background: linear-gradient(135deg, #ff9500, #ff6b00);
}

.stat-icon.today {
  background: linear-gradient(135deg, #ff375f, #ff2d55);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.table-section {
  margin-top: var(--spacing-xxl);
}

.section-header {
  margin-bottom: var(--spacing-lg);
}

.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
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
  font-size: 24px;
  line-height: 1;
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
</style>
