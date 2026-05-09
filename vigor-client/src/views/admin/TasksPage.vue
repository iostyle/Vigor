<template>
  <div class="tasks-page">
    <div class="page-header">
      <h1>爬取管理</h1>
      <p class="subtitle">手动触发视频爬取任务</p>
    </div>

    <div class="trigger-section">
      <n-card title="触发新爬取" :bordered="false">
        <n-form ref="formRef" :model="formData" label-placement="left" label-width="80">
          <n-form-item label="关键词" path="keyword_id">
            <n-select
              v-model:value="formData.keyword_id"
              :options="keywordOptions"
              placeholder="选择要爬取的关键词"
              filterable
              :loading="loadingKeywords"
            />
          </n-form-item>
          <n-form-item label="平台" path="platform">
            <n-radio-group v-model:value="formData.platform">
              <n-radio value="bilibili">B站</n-radio>
              <n-radio value="douyin">抖音</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item>
            <n-button
              type="primary"
              :loading="triggering"
              :disabled="!formData.keyword_id"
              @click="handleTrigger"
            >
              开始爬取
            </n-button>
          </n-form-item>
        </n-form>
      </n-card>
    </div>

    <div class="history-section">
      <n-card title="爬取历史" :bordered="false">
        <n-data-table
          :columns="columns"
          :data="tasks"
          :loading="loadingTasks"
          :pagination="pagination"
          :bordered="false"
        />
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NCard, NForm, NFormItem, NSelect, NRadioGroup, NRadio, NButton, NDataTable, NTag, useMessage } from 'naive-ui'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { taskApi, type Task } from '@/api/task'
import { keywordApi, type Keyword } from '@/api/keyword'

const message = useMessage()

const formData = ref({
  keyword_id: null as number | null,
  platform: 'bilibili'
})

const keywordOptions = ref<SelectOption[]>([])
const loadingKeywords = ref(false)
const triggering = ref(false)

const tasks = ref<Task[]>([])
const loadingTasks = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    pagination.value.page = page
    fetchTasks()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
    fetchTasks()
  }
})

const columns: DataTableColumns<Task> = [
  {
    title: 'ID',
    key: 'id',
    width: 60
  },
  {
    title: '关键词ID',
    key: 'keyword_id',
    width: 100
  },
  {
    title: '任务类型',
    key: 'task_type',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const statusMap: Record<string, { type: 'success' | 'warning' | 'error' | 'info', text: string }> = {
        pending: { type: 'info', text: '等待中' },
        running: { type: 'warning', text: '运行中' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '失败' }
      }
      const status = statusMap[row.status] || { type: 'info', text: row.status }
      return h(NTag, { type: status.type }, { default: () => status.text })
    }
  },
  {
    title: '爬取数量',
    key: 'videos_crawled',
    width: 100
  },
  {
    title: '开始时间',
    key: 'started_at',
    width: 180,
    render(row) {
      return new Date(row.started_at).toLocaleString('zh-CN')
    }
  },
  {
    title: '完成时间',
    key: 'completed_at',
    width: 180,
    render(row) {
      return row.completed_at ? new Date(row.completed_at).toLocaleString('zh-CN') : '-'
    }
  },
  {
    title: '错误信息',
    key: 'error_message',
    ellipsis: {
      tooltip: true
    }
  }
]

async function fetchKeywords() {
  loadingKeywords.value = true
  try {
    const res = await keywordApi.list({ limit: 100 })
    keywordOptions.value = res.map((k: Keyword) => ({
      label: `${k.keyword} (ID: ${k.id})`,
      value: k.id
    }))
  } catch (error) {
    message.error('加载关键词失败')
  } finally {
    loadingKeywords.value = false
  }
}

async function fetchTasks() {
  loadingTasks.value = true
  try {
    const offset = (pagination.value.page - 1) * pagination.value.pageSize
    const res = await taskApi.list({
      limit: pagination.value.pageSize,
      offset
    })
    tasks.value = res.data
  } catch (error) {
    message.error('加载任务历史失败')
  } finally {
    loadingTasks.value = false
  }
}

async function handleTrigger() {
  if (!formData.value.keyword_id) {
    message.warning('请选择关键词')
    return
  }

  triggering.value = true
  try {
    const res = await taskApi.triggerCrawl({
      keyword_id: formData.value.keyword_id,
      platform: formData.value.platform
    })
    message.success(`爬取任务已触发 (Task ID: ${res.task_id})`)
    // 刷新任务列表
    setTimeout(() => {
      fetchTasks()
    }, 1000)
  } catch (error: any) {
    message.error(error.message || '触发爬取失败')
  } finally {
    triggering.value = false
  }
}

onMounted(() => {
  fetchKeywords()
  fetchTasks()
})
</script>

<style scoped>
.tasks-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.trigger-section {
  margin-bottom: 24px;
}

.history-section {
  margin-top: 24px;
}
</style>
