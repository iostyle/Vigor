<template>
  <div class="scheduled-page">
    <div class="page-header">
      <h1>定时任务管理</h1>
      <p class="subtitle">配置自动爬取与数据更新节奏,支持启停、编辑和删除</p>
    </div>

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
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
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
  .trigger-section {
    flex-direction: column;
  }
}
</style>
