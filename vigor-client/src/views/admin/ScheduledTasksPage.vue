<template>
  <div class="scheduled-page">
    <div class="page-header">
      <h1>定时任务管理</h1>
      <p class="subtitle">配置自动爬取与数据更新节奏,支持启停、编辑和删除</p>
    </div>

    <section class="monitor-section">
      <div class="monitor-head">
        <div>
          <div class="section-kicker">Scheduler Monitor</div>
          <h2>调度器运行状态</h2>
        </div>
        <n-tag :type="healthTagType" round>{{ healthStatusText }}</n-tag>
      </div>

      <div class="health-strip">
        <div>
          <span class="metric-label">状态说明</span>
          <strong>{{ monitor?.health.message || '正在读取调度器状态' }}</strong>
        </div>
        <div>
          <span class="metric-label">最近扫描</span>
          <strong>{{ formatRelativeSeconds(monitor?.health.seconds_since_last_run) }}</strong>
        </div>
        <div>
          <span class="metric-label">服务时间</span>
          <strong>{{ formatMinuteTime(monitor?.server_time || null) }}</strong>
        </div>
      </div>

      <div class="monitor-grid">
        <div v-for="item in monitorStats" :key="item.label" class="monitor-stat">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>

      <div class="monitor-columns">
        <div class="monitor-panel">
          <div class="panel-title">
            <span>最近扫描</span>
            <small>{{ loadingMonitor ? '刷新中' : '5 秒自动刷新' }}</small>
          </div>
          <div v-if="monitor?.recent_runs.length" class="run-list">
            <div v-for="run in monitor.recent_runs" :key="run.id" class="run-row">
              <div>
                <n-tag size="small" :type="runStatusTagType(run.status)" round>
                  {{ runStatusText(run.status) }}
                </n-tag>
                <span class="run-time">{{ formatMinuteTime(run.started_at) }}</span>
              </div>
              <span>应触发 {{ run.due_count }} / 已派发 {{ run.dispatched_count }} / 失败 {{ run.failed_count }}</span>
            </div>
          </div>
          <n-empty v-else size="small" description="暂无扫描记录" />
        </div>

        <div class="monitor-panel">
          <div class="panel-title">
            <span>最近定时派发任务</span>
            <small>按任务 ID 倒序</small>
          </div>
          <div v-if="monitor?.recent_tasks.length" class="task-list">
            <div v-for="task in monitor.recent_tasks" :key="task.id" class="task-row">
              <span class="task-id">#{{ task.id }}</span>
              <span class="task-main">{{ taskTypeText(task.task_type) }} · {{ taskStatusText(task.status) }}</span>
              <span class="task-extra">{{ task.videos_crawled }} 条 · {{ formatMinuteTime(task.started_at) }}</span>
            </div>
          </div>
          <n-empty v-else size="small" description="暂无定时派发任务" />
        </div>
      </div>
    </section>

    <div class="trigger-section">
      <n-card class="trigger-card" title="触发新爬取" :bordered="false">
        <n-form class="trigger-form" :model="crawlForm" label-placement="left" label-width="86">
          <n-form-item label="爬取方式">
            <n-radio-group v-model:value="crawlForm.target_mode">
              <n-radio value="category">按领域</n-radio>
              <n-radio value="keyword">按关键词</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item v-if="crawlForm.target_mode === 'keyword'" label="关键词">
            <n-select
              v-model:value="crawlForm.target_id"
              :options="keywordOptions"
              placeholder="选择关键词"
              filterable
              :loading="loadingKeywords"
            />
          </n-form-item>
          <n-form-item v-else label="领域">
            <n-select
              v-model:value="crawlForm.target_id"
              :options="categoryOptions"
              placeholder="选择领域"
              filterable
              :loading="loadingCategories"
            />
          </n-form-item>
          <n-form-item label="平台">
            <n-radio-group v-model:value="crawlForm.platform">
              <n-radio value="bilibili">B站</n-radio>
              <n-radio value="douyin">抖音</n-radio>
            </n-radio-group>
          </n-form-item>
          <schedule-fields v-model="crawlForm" />
          <div class="form-actions">
            <button
              type="button"
              class="trigger-btn"
              :disabled="saving || !canSaveCrawl"
              @click="handleCreateCrawl"
            >
              {{ saving ? '保存中...' : '创建定时爬取' }}
            </button>
          </div>
        </n-form>
      </n-card>

      <n-card class="trigger-card" title="触发数据更新" :bordered="false">
        <n-form class="trigger-form" :model="updateForm" label-placement="left" label-width="86">
          <n-form-item label="更新方式">
            <n-radio-group v-model:value="updateForm.target_mode">
              <n-radio value="category">按领域</n-radio>
              <n-radio value="keyword">按关键词</n-radio>
              <n-radio value="video">按视频 ID</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item v-if="updateForm.target_mode === 'keyword'" label="关键词">
            <n-select
              v-model:value="updateForm.target_id"
              :options="keywordOptions"
              placeholder="选择关键词"
              filterable
              :loading="loadingKeywords"
            />
          </n-form-item>
          <n-form-item v-else-if="updateForm.target_mode === 'category'" label="领域">
            <n-select
              v-model:value="updateForm.target_id"
              :options="categoryOptions"
              placeholder="选择领域"
              filterable
              :loading="loadingCategories"
            />
          </n-form-item>
          <n-form-item v-else label="视频 ID">
            <n-input-number
              v-model:value="updateForm.target_id"
              placeholder="输入视频 ID"
              :min="1"
              clearable
            />
          </n-form-item>
          <n-form-item v-if="updateForm.target_mode !== 'video'" label="更新数量">
            <n-input-number
              v-model:value="updateForm.limit"
              :min="1"
              :max="1000"
              placeholder="默认按方式填充"
            />
          </n-form-item>
          <schedule-fields v-model="updateForm" />
          <div class="form-actions">
            <button
              type="button"
              class="trigger-btn"
              :disabled="saving || !canSaveUpdate"
              @click="handleCreateUpdate"
            >
              {{ saving ? '保存中...' : '创建定时更新' }}
            </button>
          </div>
        </n-form>
      </n-card>
    </div>

    <div class="history-section">
      <n-card title="已创建的定时任务" :bordered="false">
        <n-data-table
          remote
          :columns="columns"
          :data="scheduledTasks"
          :loading="loadingTasks"
          :pagination="pagination"
          :bordered="false"
          table-layout="fixed"
        />
      </n-card>
    </div>

    <n-modal v-model:show="editingVisible" preset="card" title="编辑定时任务" class="edit-modal">
      <n-form v-if="editingForm" :model="editingForm" label-placement="left" label-width="86">
        <n-form-item label="任务类型">
          <n-radio-group v-model:value="editingForm.task_kind" @update:value="handleEditKindChange">
            <n-radio value="crawl">触发新爬取</n-radio>
            <n-radio value="update">触发数据更新</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="目标类型">
          <n-radio-group v-model:value="editingForm.target_mode" @update:value="editingForm.target_id = null">
            <n-radio value="category">按领域</n-radio>
            <n-radio value="keyword">按关键词</n-radio>
            <n-radio v-if="editingForm.task_kind === 'update'" value="video">按视频 ID</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="editingForm.target_mode === 'keyword'" label="关键词">
          <n-select v-model:value="editingForm.target_id" :options="keywordOptions" filterable />
        </n-form-item>
        <n-form-item v-else-if="editingForm.target_mode === 'category'" label="领域">
          <n-select v-model:value="editingForm.target_id" :options="categoryOptions" filterable />
        </n-form-item>
        <n-form-item v-else label="视频 ID">
          <n-input-number v-model:value="editingForm.target_id" :min="1" />
        </n-form-item>
        <n-form-item v-if="editingForm.task_kind === 'crawl'" label="平台">
          <n-radio-group v-model:value="editingForm.platform">
            <n-radio value="bilibili">B站</n-radio>
            <n-radio value="douyin">抖音</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item
          v-if="editingForm.task_kind === 'update' && editingForm.target_mode !== 'video'"
          label="更新数量"
        >
          <n-input-number v-model:value="editingForm.limit" :min="1" :max="1000" />
        </n-form-item>
        <schedule-fields v-model="editingForm" />
        <div class="modal-actions">
          <n-button @click="editingVisible = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveEdit">保存</n-button>
        </div>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NPopconfirm,
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
  NTimePicker,
  useMessage
} from 'naive-ui'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { categoryApi, type Category } from '@/api/category'
import { keywordApi } from '@/api/keyword'
import {
  scheduledTaskApi,
  type ScheduledTask,
  type ScheduledTaskInput,
  type ScheduledTaskKind,
  type ScheduledTaskMonitor,
  type ScheduledTargetMode
} from '@/api/scheduledTask'
import type { Keyword } from '@/types/keyword'
import { buildKeywordOption } from '@/utils/keywordOptions'

type ScheduleForm = ScheduledTaskInput

const ScheduleFields = defineComponent({
  name: 'ScheduleFields',
  props: {
    modelValue: {
      type: Object as () => ScheduleForm,
      required: true
    }
  },
  emits: ['update:modelValue'],
  setup(props) {
    return () =>
      h('div', { class: 'schedule-fields' }, [
        h(
          NFormItem,
          { label: '触发方式' },
          {
            default: () =>
              h(
                NRadioGroup,
                {
                  value: props.modelValue.schedule_type,
                  'onUpdate:value': (value: 'interval' | 'daily') => {
                    props.modelValue.schedule_type = value
                  }
                },
                {
                  default: () => [
                    h(NRadio, { value: 'interval' }, { default: () => '间隔时间' }),
                    h(NRadio, { value: 'daily' }, { default: () => '每日定点' })
                  ]
                }
              )
          }
        ),
        props.modelValue.schedule_type === 'interval'
          ? h(
              NFormItem,
              { label: '间隔时间' },
              {
                default: () =>
                  h(NSelect, {
                    value: props.modelValue.interval_minutes,
                    options: intervalOptions,
                    placeholder: '选择间隔时间',
                    'onUpdate:value': (value: number | null) => {
                      props.modelValue.interval_minutes = value
                    }
                  })
              }
            )
          : h(
              NFormItem,
              { label: '每日时间' },
              {
                default: () =>
                  h(NTimePicker, {
                    value: timeStringToTimestamp(props.modelValue.daily_time),
                    format: 'HH:mm',
                    clearable: false,
                    placeholder: '选择触发时间',
                    'onUpdate:value': (value: number | null) => {
                      props.modelValue.daily_time = timestampToTimeString(value)
                    }
                  })
              }
            )
      ])
  }
})

const message = useMessage()
const intervalOptions = [
  { label: '每 5 分钟', value: 5 },
  { label: '每 15 分钟', value: 15 },
  { label: '每 30 分钟', value: 30 },
  { label: '每 1 小时', value: 60 },
  { label: '每 2 小时', value: 120 },
  { label: '每 6 小时', value: 360 },
  { label: '每 12 小时', value: 720 },
  { label: '每天', value: 1440 },
  { label: '每周', value: 10080 }
]

function timeStringToTimestamp(value: string | null | undefined) {
  const safeValue = value || '08:00'
  const [hour, minute] = safeValue.split(':').map((part) => Number(part))
  const date = new Date()
  date.setHours(Number.isFinite(hour) ? hour : 8, Number.isFinite(minute) ? minute : 0, 0, 0)
  return date.getTime()
}

function timestampToTimeString(value: number | null) {
  const date = value ? new Date(value) : new Date()
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${hour}:${minute}`
}

const createBaseForm = (taskKind: ScheduledTaskKind, targetMode: ScheduledTargetMode): ScheduleForm => ({
  name: '',
  task_kind: taskKind,
  target_mode: targetMode,
  target_id: null,
  platform: 'bilibili',
  limit: taskKind === 'update' ? 100 : null,
  schedule_type: 'daily',
  interval_minutes: 60,
  daily_time: '08:00',
  enabled: true
})

const crawlForm = reactive<ScheduleForm>(createBaseForm('crawl', 'category'))
const updateForm = reactive<ScheduleForm>(createBaseForm('update', 'category'))
const editingForm = ref<(ScheduleForm & { id: number }) | null>(null)
const editingVisible = ref(false)

const keywordOptions = ref<SelectOption[]>([])
const categoryOptions = ref<SelectOption[]>([])
const loadingKeywords = ref(false)
const loadingCategories = ref(false)
const scheduledTasks = ref<ScheduledTask[]>([])
const loadingTasks = ref(false)
const monitor = ref<ScheduledTaskMonitor | null>(null)
const loadingMonitor = ref(false)
let monitorTimer: ReturnType<typeof window.setInterval> | null = null
const saving = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  itemCount: 0,
  onChange: (page: number) => {
    pagination.page = page
    fetchScheduledTasks()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchScheduledTasks()
  }
})

const canSaveCrawl = computed(() => isValidForm(crawlForm))
const canSaveUpdate = computed(() => isValidForm(updateForm))
const healthStatusText = computed(() => {
  const status = monitor.value?.health.status
  if (status === 'healthy') return '运行正常'
  if (status === 'delayed') return '等待触发'
  if (status === 'stalled') return '扫描异常'
  return '读取中'
})
const healthTagType = computed(() => {
  const status = monitor.value?.health.status
  if (status === 'healthy') return 'success'
  if (status === 'delayed') return 'warning'
  if (status === 'stalled') return 'error'
  return 'default'
})
const monitorStats = computed(() => [
  { label: '启用定时任务', value: monitor.value?.tasks.enabled_count ?? '-' },
  { label: '已暂停', value: monitor.value?.tasks.disabled_count ?? '-' },
  { label: '待触发', value: monitor.value?.tasks.due_count ?? '-' },
  { label: '24h 派发', value: monitor.value?.tasks.last_24h_total ?? '-' },
  { label: '24h 成功', value: monitor.value?.tasks.last_24h_success ?? '-' },
  { label: '24h 失败', value: monitor.value?.tasks.last_24h_failed ?? '-' },
  { label: '24h 运行中', value: monitor.value?.tasks.last_24h_running ?? '-' },
  { label: '上次触发', value: monitor.value?.scheduler.last_dispatched_count ?? '-' }
])

const columns: DataTableColumns<ScheduledTask> = [
  { title: 'ID', key: 'id', width: 64 },
  {
    title: '开关',
    key: 'enabled',
    width: 90,
    render(row) {
      return h(NSwitch, {
        value: row.enabled,
        loading: saving.value,
        'onUpdate:value': (value: boolean) => handleToggle(row, value)
      })
    }
  },
  {
    title: '类型',
    key: 'task_kind',
    width: 120,
    render(row) {
      const text = row.task_kind === 'crawl' ? '触发新爬取' : '触发数据更新'
      return h(NTag, { type: row.task_kind === 'crawl' ? 'info' : 'success' }, { default: () => text })
    }
  },
  {
    title: '目标',
    key: 'target',
    minWidth: 180,
    ellipsis: { tooltip: true },
    render(row) {
      return `${targetModeText(row.target_mode)}: ${row.target_label || row.target_id || '-'}`
    }
  },
  {
    title: '计划',
    key: 'schedule',
    width: 150,
    render(row) {
      if (row.schedule_type === 'interval') return `每 ${row.interval_minutes} 分钟`
      return `每天 ${row.daily_time}`
    }
  },
  {
    title: '下次触发',
    key: 'next_run_at',
    width: 180,
    render(row) {
      return formatMinuteTime(row.next_run_at)
    }
  },
  {
    title: '上次触发',
    key: 'last_run_at',
    width: 180,
    render(row) {
      return formatMinuteTime(row.last_run_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      return h(NSpace, { size: 8 }, () => [
        h(NButton, { size: 'small', quaternary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row) },
          {
            trigger: () => h(NButton, { size: 'small', quaternary: true, type: 'error' }, { default: () => '删除' }),
            default: () => '确认删除这个定时任务?'
          }
        )
      ])
    }
  }
]

function targetModeText(mode: ScheduledTargetMode) {
  const map = {
    category: '领域',
    keyword: '关键词',
    video: '视频'
  }
  return map[mode]
}

function formatMinuteTime(value: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

function formatRelativeSeconds(value: number | null | undefined) {
  if (value === null || value === undefined) return '暂无记录'
  if (value < 60) return `${value} 秒前`
  if (value < 3600) return `${Math.floor(value / 60)} 分钟前`
  return `${Math.floor(value / 3600)} 小时前`
}

function runStatusTagType(status: string) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'running') return 'info'
  return 'default'
}

function runStatusText(status: string) {
  const map: Record<string, string> = {
    success: '完成',
    failed: '失败',
    running: '扫描中'
  }
  return map[status] || status
}

function taskTypeText(type: string) {
  const map: Record<string, string> = {
    crawl: '爬取',
    update: '更新',
    comment_summary: '摘要'
  }
  return map[type] || type
}

function taskStatusText(status: string) {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败'
  }
  return map[status] || status
}

function isValidForm(form: ScheduleForm) {
  if (!form.target_id) return false
  if (form.task_kind === 'crawl' && form.target_mode === 'video') return false
  if (form.schedule_type === 'interval') return !!form.interval_minutes
  return !!form.daily_time
}

function normalizeForm(form: ScheduleForm): ScheduledTaskInput {
  const isInterval = form.schedule_type === 'interval'
  return {
    ...form,
    name: buildTaskName(form),
    platform: form.task_kind === 'crawl' ? form.platform : undefined,
    limit: form.task_kind === 'update' && form.target_mode !== 'video' ? form.limit : null,
    interval_minutes: isInterval ? form.interval_minutes : null,
    daily_time: isInterval ? null : form.daily_time
  }
}

function buildTaskName(form: ScheduleForm) {
  const kindText = form.task_kind === 'crawl' ? '定时爬取' : '定时更新'
  const modeText = targetModeText(form.target_mode)
  const scheduleText =
    form.schedule_type === 'interval'
      ? `每${form.interval_minutes || 60}分钟`
      : `每天${form.daily_time || '08:00'}`
  return `${scheduleText}${kindText}${modeText}`
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

async function fetchScheduledTasks() {
  loadingTasks.value = true
  try {
    const res = await scheduledTaskApi.list({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    scheduledTasks.value = res.data
    pagination.itemCount = res.total
  } catch {
    message.error('加载定时任务失败')
  } finally {
    loadingTasks.value = false
  }
}

async function fetchMonitor(showError = false) {
  loadingMonitor.value = true
  try {
    monitor.value = await scheduledTaskApi.monitor()
  } catch {
    if (showError) message.error('加载调度器监控失败')
  } finally {
    loadingMonitor.value = false
  }
}

async function handleCreateCrawl() {
  await createTask(crawlForm, '定时爬取任务已创建')
}

async function handleCreateUpdate() {
  await createTask(updateForm, '定时更新任务已创建')
}

async function createTask(form: ScheduleForm, successMessage: string) {
  saving.value = true
  try {
    await scheduledTaskApi.create(normalizeForm(form))
    message.success(successMessage)
    Object.assign(form, createBaseForm(form.task_kind, 'category'))
    fetchScheduledTasks()
  } catch (error: any) {
    message.error(error.message || '创建定时任务失败')
  } finally {
    saving.value = false
  }
}

async function handleToggle(row: ScheduledTask, enabled: boolean) {
  saving.value = true
  try {
    const updated = await scheduledTaskApi.toggle(row.id, enabled)
    const index = scheduledTasks.value.findIndex((item) => item.id === row.id)
    if (index >= 0) scheduledTasks.value[index] = updated
  } catch (error: any) {
    message.error(error.message || '更新开关失败')
  } finally {
    saving.value = false
  }
}

function openEdit(row: ScheduledTask) {
  editingForm.value = {
    id: row.id,
    name: row.name,
    task_kind: row.task_kind,
    target_mode: row.target_mode,
    target_id: row.target_id,
    platform: row.platform || 'bilibili',
    limit: row.limit,
    schedule_type: row.schedule_type,
    interval_minutes: row.interval_minutes || 60,
    daily_time: row.daily_time || '08:00',
    enabled: row.enabled
  }
  editingVisible.value = true
}

function handleEditKindChange(value: ScheduledTaskKind) {
  if (!editingForm.value) return
  if (value === 'crawl' && editingForm.value.target_mode === 'video') {
    editingForm.value.target_mode = 'category'
    editingForm.value.target_id = null
  }
}

async function handleSaveEdit() {
  if (!editingForm.value || !isValidForm(editingForm.value)) {
    message.warning('请完整填写定时任务配置')
    return
  }
  saving.value = true
  try {
    await scheduledTaskApi.update(editingForm.value.id, normalizeForm(editingForm.value))
    message.success('定时任务已更新')
    editingVisible.value = false
    fetchScheduledTasks()
  } catch (error: any) {
    message.error(error.message || '更新定时任务失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: ScheduledTask) {
  saving.value = true
  try {
    await scheduledTaskApi.delete(row.id)
    message.success('定时任务已删除')
    fetchScheduledTasks()
  } catch (error: any) {
    message.error(error.message || '删除定时任务失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchKeywords()
  fetchCategories()
  fetchScheduledTasks()
  fetchMonitor(true)
  monitorTimer = window.setInterval(() => fetchMonitor(), 5000)
})

onUnmounted(() => {
  if (monitorTimer) {
    window.clearInterval(monitorTimer)
    monitorTimer = null
  }
})
</script>

<style scoped>
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

.monitor-section {
  padding: 24px;
  margin-bottom: var(--spacing-xl);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-bg);
}

.monitor-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-kicker {
  margin-bottom: 6px;
  color: #007aff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.monitor-head h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 650;
}

.health-strip {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 1fr;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--bg-secondary);
}

.health-strip > div {
  min-width: 0;
}

.metric-label,
.monitor-stat span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

.health-strip strong,
.monitor-stat strong {
  display: block;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.monitor-stat {
  min-width: 0;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-primary);
}

.monitor-stat strong {
  font-size: 24px;
}

.monitor-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.monitor-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-primary);
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 650;
}

.panel-title small {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 400;
}

.run-list,
.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.run-row,
.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  padding: 9px 0;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 13px;
}

.run-row:last-child,
.task-row:last-child {
  border-bottom: 0;
}

.run-row > div {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.run-row > span,
.task-main,
.task-extra {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.run-time,
.task-main {
  color: var(--text-primary);
  font-weight: 500;
}

.task-id {
  width: 52px;
  flex: 0 0 auto;
  color: var(--text-secondary);
  font-weight: 650;
}

.task-main {
  flex: 1 1 auto;
  min-width: 0;
}

.task-extra {
  flex: 0 1 auto;
  max-width: 190px;
}

.trigger-section {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.trigger-card {
  flex: 1;
}

.trigger-form {
  max-width: 720px;
}

.form-actions {
  padding-left: 86px;
  margin-top: 4px;
}

.trigger-btn {
  min-width: 132px;
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

.trigger-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.history-section {
  margin-top: 24px;
}

.edit-modal {
  width: min(680px, calc(100vw - 32px));
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

@media (max-width: 900px) {
  .health-strip,
  .monitor-columns {
    grid-template-columns: 1fr;
  }

  .monitor-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .trigger-section {
    flex-direction: column;
  }
}

@media (max-width: 560px) {
  .monitor-section {
    padding: 18px;
  }

  .monitor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
