<template>
  <div class="tasks-page">
    <div class="page-header">
      <h1>任务管理</h1>
      <p class="subtitle">手动触发爬取、数据更新及评论摘要任务,并查看历史</p>
    </div>

    <div class="trigger-section">
      <n-card class="trigger-card" title="触发新爬取" :bordered="false">
        <n-form class="trigger-form" :model="formData" label-placement="left" label-width="80">
          <n-form-item label="爬取方式" path="mode">
            <n-radio-group v-model:value="formData.mode">
              <n-radio value="category">按领域</n-radio>
              <n-radio value="keyword">按关键词</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item v-if="formData.mode === 'keyword'" label="关键词" path="keyword_id">
            <n-select
              v-model:value="formData.keyword_id"
              :options="keywordOptions"
              placeholder="选择要爬取的关键词"
              filterable
              :loading="loadingKeywords"
            />
          </n-form-item>
          <n-form-item v-else label="领域" path="category_id">
            <n-select
              v-model:value="formData.category_id"
              :options="categoryOptions"
              placeholder="选择要爬取的领域"
              filterable
              :loading="loadingCategories"
            />
          </n-form-item>
          <n-form-item label="平台" path="platform">
            <n-checkbox-group v-model:value="formData.platforms">
              <n-space>
                <n-checkbox value="bilibili">B站</n-checkbox>
                <n-checkbox value="douyin">抖音</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
          <div class="form-actions">
            <button
              type="button"
              class="trigger-btn"
              :disabled="triggerDisabled"
              @click="handleTrigger"
            >
              {{ triggering ? '爬取中...' : '开始爬取' }}
            </button>
          </div>
        </n-form>
      </n-card>

      <n-card class="trigger-card" title="触发数据更新" :bordered="false">
        <n-form
          class="trigger-form"
          :model="updateFormData"
          label-placement="left"
          label-width="80"
        >
          <n-form-item label="更新方式" path="mode">
            <n-radio-group v-model:value="updateFormData.mode">
              <n-radio value="category">按领域</n-radio>
              <n-radio value="keyword">按关键词</n-radio>
              <n-radio value="video">按视频 ID</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item v-if="updateFormData.mode === 'keyword'" label="关键词" path="keyword_id">
            <n-select
              v-model:value="updateFormData.keyword_id"
              :options="keywordOptions"
              placeholder="选择要更新的关键词"
              filterable
              :loading="loadingKeywords"
            />
          </n-form-item>
          <n-form-item
            v-if="updateFormData.mode === 'keyword'"
            label="更新数量"
            path="keyword_limit"
          >
            <n-input-number
              v-model:value="updateFormData.keyword_limit"
              :min="1"
              :max="500"
              placeholder="默认 20 条"
            />
          </n-form-item>
          <n-form-item v-if="updateFormData.mode === 'category'" label="领域" path="category_id">
            <n-select
              v-model:value="updateFormData.category_id"
              :options="categoryOptions"
              placeholder="选择要更新的领域"
              filterable
              :loading="loadingCategories"
            />
          </n-form-item>
          <n-form-item
            v-if="updateFormData.mode === 'category'"
            label="更新数量"
            path="category_limit"
          >
            <n-input-number
              v-model:value="updateFormData.category_limit"
              :min="1"
              :max="1000"
              placeholder="默认 100 条"
            />
          </n-form-item>
          <n-form-item v-if="updateFormData.mode === 'video'" label="视频 ID" path="video_id">
            <n-input-number
              v-model:value="updateFormData.video_id"
              placeholder="输入视频 ID"
              :min="1"
              clearable
            />
          </n-form-item>
          <div class="form-actions">
            <button
              type="button"
              class="trigger-btn"
              :disabled="updateDisabled"
              @click="handleTriggerUpdate"
            >
              {{ updateTriggering ? '更新中...' : '开始更新' }}
            </button>
          </div>
        </n-form>
      </n-card>
    </div>

    <div class="history-section">
      <n-card title="任务历史" :bordered="false">
        <n-data-table
          remote
          :columns="columns"
          :data="tasks"
          :loading="loadingTasks"
          :pagination="pagination"
          :bordered="false"
          table-layout="fixed"
        />
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, h } from 'vue'
import {
  NCard,
  NCheckbox,
  NCheckboxGroup,
  NDataTable,
  NForm,
  NFormItem,
  NInputNumber,
  NPopover,
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  NTag,
  useMessage
} from 'naive-ui'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { keywordApi } from '@/api/keyword'
import { categoryApi, type Category } from '@/api/category'
import { taskApi, type Task } from '@/api/task'
import type { Keyword } from '@/types/keyword'
import { buildKeywordOption } from '@/utils/keywordOptions'

const message = useMessage()

const formData = ref({
  mode: 'category' as 'keyword' | 'category',
  keyword_id: null as number | null,
  category_id: null as number | null,
  platforms: ['bilibili'] as string[]
})

const updateFormData = ref({
  mode: 'category' as 'keyword' | 'category' | 'video',
  keyword_id: null as number | null,
  category_id: null as number | null,
  video_id: null as number | null,
  keyword_limit: 20,
  category_limit: 100
})

const keywordOptions = ref<SelectOption[]>([])
const loadingKeywords = ref(false)
const categoryOptions = ref<SelectOption[]>([])
const loadingCategories = ref(false)
const triggering = ref(false)
const updateTriggering = ref(false)

const triggerDisabled = computed(() => {
  if (triggering.value) return true
  if (!formData.value.platforms.length) return true
  if (formData.value.mode === 'keyword') return !formData.value.keyword_id
  return !formData.value.category_id
})

const updateDisabled = computed(() => {
  if (updateTriggering.value) return true
  if (updateFormData.value.mode === 'keyword') return !updateFormData.value.keyword_id
  if (updateFormData.value.mode === 'category') return !updateFormData.value.category_id
  return !updateFormData.value.video_id
})

const tasks = ref<Task[]>([])
const loadingTasks = ref(false)
let pollingTimer: number | null = null

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  itemCount: 0,
  onChange: (page: number) => {
    pagination.page = page
    fetchTasks()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
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
    title: '摘要',
    key: 'summary',
    minWidth: 240,
    ellipsis: {
      tooltip: true
    },
    render(row) {
      return row.summary || '-'
    }
  },
  {
    title: '任务类型',
    key: 'task_type',
    width: 100,
    render(row) {
      const typeMap: Record<string, string> = {
        crawl: '爬取',
        update: '更新',
        summary: '评论摘要'
      }
      return typeMap[row.task_type] || row.task_type
    }
  },
  {
    title: '平台',
    key: 'platform',
    width: 90,
    render(row) {
      return platformText(row.platform)
    }
  },
  {
    title: '来源',
    key: 'source',
    width: 120,
    render(row) {
      const sourceMap: Record<
        string,
        { type: 'default' | 'success' | 'warning' | 'error' | 'info'; text: string }
      > = {
        manual: { type: 'info', text: '手动' },
        scheduled: { type: 'warning', text: row.source_id ? `定时 #${row.source_id}` : '定时' },
        system: { type: 'default', text: '系统' },
        legacy: { type: 'default', text: '历史' }
      }
      const source = sourceMap[row.source] || { type: 'default', text: row.source || '-' }
      return h(NTag, { type: source.type }, { default: () => source.text })
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const statusMap: Record<
        string,
        { type: 'success' | 'warning' | 'error' | 'info'; text: string }
      > = {
        pending: { type: 'info', text: '等待中' },
        running: { type: 'warning', text: '爬取中' },
        success: { type: 'success', text: '已完成' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '失败' }
      }
      const status = statusMap[row.status] || { type: 'info', text: row.status }
      return h(NTag, { type: status.type }, { default: () => status.text })
    }
  },
  {
    title: '文件数量',
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
    width: 220,
    className: 'error-message-column',
    render(row) {
      const errorMessage = getTaskErrorMessage(row)
      if (!errorMessage) {
        return '-'
      }
      const previewText = getErrorPreview(errorMessage)

      return h('div', { class: 'error-message-cell' }, [
        h(
          NPopover,
          {
            trigger: 'hover',
            placement: 'left',
            scrollable: true,
            style: {
              maxWidth: 'calc(100vw - 64px)'
            },
            contentClass: 'error-message-popover-shell'
          },
          {
            trigger: () =>
              h(
                'span',
                {
                  class: 'error-message-preview',
                  title: '悬停查看完整错误'
                },
                previewText
              ),
            default: () =>
              h(
                'pre',
                {
                  class: 'error-message-popover'
                },
                errorMessage
              )
          }
        )
      ])
    }
  }
]

function getTaskErrorMessage(row: Task) {
  if (row.error_message?.trim()) {
    return row.error_message
  }
  if (row.status === 'failed') {
    return '任务失败,但后端未返回错误详情'
  }
  return null
}

function platformText(value: string | null | undefined) {
  const map: Record<string, string> = {
    bilibili: 'B站',
    douyin: '抖音'
  }
  return value ? map[value] || value : '-'
}

function getErrorPreview(text: string) {
  const normalized = text.replace(/\s+/g, ' ').trim()
  return normalized.length > 26 ? `${normalized.slice(0, 26)}...` : normalized
}

async function fetchKeywords() {
  loadingKeywords.value = true
  try {
    const res = await keywordApi.list({ limit: 100 })
    keywordOptions.value = res.map((k: Keyword) => buildKeywordOption(k, { disableInactive: true }))
  } catch {
    message.error('加载关键词失败')
  } finally {
    loadingKeywords.value = false
  }
}

async function fetchCategories() {
  loadingCategories.value = true
  try {
    const res = await categoryApi.adminList()
    categoryOptions.value = res.map((c: Category) => ({
      label: `${c.name} (${c.keyword_count}个关键词)`,
      value: c.id
    }))
  } catch {
    message.error('加载领域失败')
  } finally {
    loadingCategories.value = false
  }
}

async function fetchTasks(showLoading = true) {
  if (showLoading) {
    loadingTasks.value = true
  }
  try {
    const res = await taskApi.list({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tasks.value = res.data
    pagination.itemCount = res.total
  } catch {
    if (showLoading) {
      message.error('加载任务历史失败')
    }
  } finally {
    if (showLoading) {
      loadingTasks.value = false
    }
  }
}

async function handleTrigger() {
  triggering.value = true
  try {
    if (formData.value.mode === 'keyword') {
      const results = await Promise.all(
        formData.value.platforms.map((platform) =>
          taskApi.triggerCrawl({
            keyword_id: formData.value.keyword_id!,
            platform
          })
        )
      )
      message.success(`已触发 ${results.length} 个平台的爬取任务`)
    } else {
      const results = await Promise.all(
        formData.value.platforms.map((platform) =>
          taskApi.triggerCrawlByCategory({
            category_id: formData.value.category_id!,
            platform
          })
        )
      )
      const keywordCount = results.reduce((total, item) => total + item.keyword_count, 0)
      message.success(`已触发 ${results.length} 个平台、${keywordCount} 个关键词的爬取任务`)
    }
    fetchTasks()
  } catch (error: any) {
    message.error(error.message || '触发爬取失败')
  } finally {
    triggering.value = false
  }
}

async function handleTriggerUpdate() {
  updateTriggering.value = true
  try {
    if (updateFormData.value.mode === 'keyword') {
      const res = await taskApi.triggerUpdate({
        keyword_id: updateFormData.value.keyword_id!,
        limit: updateFormData.value.keyword_limit
      })
      const count = res.video_count ?? 1
      message.success(`已触发 ${count} 个视频的更新任务`)
    } else if (updateFormData.value.mode === 'category') {
      const res = await taskApi.triggerUpdateByCategory({
        category_id: updateFormData.value.category_id!,
        limit: updateFormData.value.category_limit
      })
      message.success(`已触发 ${res.video_count} 个视频的更新任务`)
    } else {
      const res = await taskApi.triggerUpdate({
        video_id: updateFormData.value.video_id!
      })
      message.success(`更新任务已触发 (Task ID: ${res.task_id ?? '-'})`)
    }
    fetchTasks()
  } catch (error: any) {
    message.error(error.message || '触发更新失败')
  } finally {
    updateTriggering.value = false
  }
}

onMounted(() => {
  fetchKeywords()
  fetchCategories()
  fetchTasks()
  pollingTimer = window.setInterval(() => {
    fetchTasks(false)
  }, 4000)
})

onUnmounted(() => {
  if (pollingTimer !== null) {
    window.clearInterval(pollingTimer)
    pollingTimer = null
  }
})
</script>

<style scoped>
.tasks-page {
}

.page-header {
  margin-bottom: var(--spacing-xl);
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
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.trigger-card {
  flex: 1;
  max-width: none;
}

.trigger-form {
  max-width: 720px;
}

.form-actions {
  padding-left: 80px;
  margin-top: 4px;
}

.trigger-btn {
  min-width: 120px;
  padding: 10px 18px;
  border-radius: 10px;
  border: 1px solid rgba(0, 122, 255, 0.18);
  background: linear-gradient(180deg, #2997ff 0%, #007aff 100%);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.08),
    0 6px 18px rgba(0, 122, 255, 0.18);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease,
    opacity 0.15s ease;
}

.trigger-btn:hover:not(:disabled) {
  filter: brightness(1.03);
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.1),
    0 8px 22px rgba(0, 122, 255, 0.24);
  transform: translateY(-1px);
}

.trigger-btn:active:not(:disabled) {
  transform: translateY(0);
  filter: brightness(0.98);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.08),
    0 4px 12px rgba(0, 122, 255, 0.18);
}

.trigger-btn:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px rgba(0, 122, 255, 0.18),
    0 6px 18px rgba(0, 122, 255, 0.18);
}

.trigger-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.history-section {
  margin-top: 24px;
}

:deep(.error-message-column) {
  white-space: nowrap;
}

.error-message-cell {
  display: block;
  width: 200px;
  max-width: 200px;
  min-width: 0;
  max-height: 24px;
  overflow: hidden;
  white-space: nowrap;
}

.error-message-preview {
  display: block;
  width: 100%;
  min-width: 0;
  overflow: hidden;
  color: var(--error-color);
  font-size: 13px;
  line-height: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: help;
}

.error-message-popover {
  width: clamp(360px, 72vw, 960px);
  max-width: calc(100vw - 96px);
  max-height: min(620px, calc(100vh - 128px));
  margin: 0;
  padding: 10px 2px;
  overflow: auto;
  color: var(--text-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.error-message-popover-shell) {
  max-width: calc(100vw - 64px);
}

@media (max-width: 768px) {
  .trigger-section {
    flex-direction: column;
  }
}
</style>
