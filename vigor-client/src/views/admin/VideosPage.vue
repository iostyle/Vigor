<template>
  <div class="videos-page">
    <div class="page-header">
      <h1>视频管理</h1>
      <p class="subtitle">查看和管理已爬取的视频数据</p>
    </div>

    <div class="filter-section">
      <n-space>
        <n-select
          v-model:value="filters.platform"
          :options="platformOptions"
          placeholder="选择平台"
          clearable
          style="width: 150px"
          @update:value="handleFilterChange"
        />
        <n-select
          v-model:value="filters.keyword_id"
          :options="keywordOptions"
          placeholder="选择关键词"
          clearable
          filterable
          style="width: 200px"
          @update:value="handleFilterChange"
        />
        <n-select
          v-model:value="filters.video_status"
          :options="statusFilterOptions"
          placeholder="选择状态"
          clearable
          style="width: 150px"
          @update:value="handleFilterChange"
        />
        <n-date-picker
          v-model:value="filters.dateRange"
          type="daterange"
          clearable
          placeholder="选择时间范围"
          @update:value="handleFilterChange"
        />
      </n-space>
    </div>

    <n-card :bordered="false">
      <n-data-table
        remote
        :columns="columns"
        :data="videos"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Video) => row.id"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NDropdown,
  NSpace,
  NSelect,
  NTag,
  useMessage
} from 'naive-ui'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { videoApi, type VideoStatus } from '@/api/video'
import type { Video } from '@/types/video'
import { keywordApi } from '@/api/keyword'
import { buildKeywordOption } from '@/utils/keywordOptions'
import { getOriginalVideoUrl } from '@/utils/media'

const message = useMessage()

const videos = ref<Video[]>([])
const loading = ref(false)

const filters = ref({
  platform: null as string | null,
  keyword_id: null as number | null,
  video_status: null as 'active' | 'hidden' | 'archived' | null,
  dateRange: null as [number, number] | null
})

const platformOptions: SelectOption[] = [
  { label: 'B站', value: 'bilibili' },
  { label: '抖音', value: 'douyin' }
]

const keywordOptions = ref<SelectOption[]>([])
const updatingStatusIds = ref<Set<number>>(new Set())

const statusFilterOptions: SelectOption[] = [
  { label: '启用', value: 'active' },
  { label: '隐藏', value: 'hidden' },
  { label: '归档', value: 'archived' }
]

const statusOptions = [
  { label: '设为启用', key: 'active' },
  { label: '设为隐藏', key: 'hidden' },
  { label: '设为归档', key: 'archived' }
]

const statusMap: Record<
  string,
  { type: 'success' | 'warning' | 'default'; text: string }
> = {
  active: { type: 'success', text: '启用' },
  hidden: { type: 'warning', text: '隐藏' },
  archived: { type: 'default', text: '归档' }
}

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0,
  onChange: (page: number) => {
    pagination.page = page
    fetchVideos()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchVideos()
  }
})

const columns: DataTableColumns<Video> = [
  {
    title: 'ID',
    key: 'id',
    width: 60
  },
  {
    title: '平台',
    key: 'platform',
    width: 80,
    render(row) {
      const platformMap: Record<string, { type: 'info' | 'success', text: string }> = {
        bilibili: { type: 'info', text: 'B站' },
        douyin: { type: 'success', text: '抖音' }
      }
      const platform = platformMap[row.platform] || { type: 'info', text: row.platform }
      return h(NTag, { type: platform.type, size: 'small' }, { default: () => platform.text })
    }
  },
  {
    title: '标题',
    key: 'title',
    ellipsis: {
      tooltip: true
    },
    width: 300
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render(row) {
      const status = statusMap[row.status || 'active'] || { type: 'default', text: row.status || '-' }
      return h(NTag, { type: status.type, size: 'small' }, { default: () => status.text })
    }
  },
  {
    title: '作者',
    key: 'author_name',
    width: 120,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '点赞',
    key: 'like_count',
    width: 80,
    render(row) {
      return formatNumber(row.like_count)
    }
  },
  {
    title: '评论',
    key: 'comment_count',
    width: 80,
    render(row) {
      return formatNumber(row.comment_count)
    }
  },
  {
    title: '分享',
    key: 'share_count',
    width: 80,
    render(row) {
      return formatNumber(row.share_count)
    }
  },
  {
    title: '热度',
    key: 'heat_score',
    width: 100,
    render(row) {
      return row.heat_score ? row.heat_score.toFixed(2) : '-'
    }
  },
  {
    title: '发布时间',
    key: 'publish_time',
    width: 180,
    render(row) {
      return row.publish_time ? new Date(row.publish_time).toLocaleString('zh-CN') : '-'
    }
  },
  {
    title: '爬取更新时间',
    key: 'last_updated_at',
    width: 200,
    render(row) {
      const t = row.last_updated_at || row.crawled_at
      return t ? new Date(t).toLocaleString('zh-CN') : '-'
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render(row) {
      return h(
        NSpace,
        { size: 12 },
        {
          default: () => [
            h(
              NButton,
              {
                size: 'small',
                text: true,
                type: 'primary',
                onClick: () => {
                  const url = getOriginalVideoUrl(row)
                  if (url !== '#') {
                    window.open(url, '_blank')
                  }
                }
              },
              { default: () => '查看原视频' }
            ),
            h(
              NDropdown,
              {
                trigger: 'click',
                options: statusOptions.filter((item) => item.key !== (row.status || 'active')),
                onSelect: (key: string) => handleStatusChange(row, key as VideoStatus)
              },
              {
                default: () =>
                  h(
                    NButton,
                    {
                      size: 'small',
                      text: true,
                      type: 'primary',
                      loading: updatingStatusIds.value.has(row.id)
                    },
                    { default: () => '状态变更' }
                  )
              }
            )
          ]
        }
      )
    }
  }
]

function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

async function fetchKeywords() {
  try {
    const res = await keywordApi.list({ limit: 100 })
    keywordOptions.value = res.map((k) => buildKeywordOption(k))
  } catch (error) {
    console.error('Failed to fetch keywords:', error)
  }
}

async function fetchVideos() {
  loading.value = true
  try {
    const offset = (pagination.page - 1) * pagination.pageSize
    const params: any = {
      limit: pagination.pageSize,
      offset
    }

    if (filters.value.platform) {
      params.platform = filters.value.platform
    }
    if (filters.value.keyword_id) {
      params.keyword_id = filters.value.keyword_id
    }

    if (filters.value.video_status) {
      params.video_status = filters.value.video_status
    }

    const res = await videoApi.adminList(params)
    videos.value = res.data
    pagination.itemCount = res.total
  } catch (error) {
    message.error('加载视频列表失败')
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(row: Video, status: VideoStatus) {
  const next = new Set(updatingStatusIds.value)
  next.add(row.id)
  updatingStatusIds.value = next
  try {
    const updated = await videoApi.updateStatus(row.id, status)
    const index = videos.value.findIndex((item) => item.id === row.id)
    if (index !== -1) {
      videos.value[index] = { ...videos.value[index], status: updated.status }
    }
    message.success('视频状态已更新')
  } catch {
    message.error('视频状态更新失败')
  } finally {
    const done = new Set(updatingStatusIds.value)
    done.delete(row.id)
    updatingStatusIds.value = done
  }
}

function handleFilterChange() {
  pagination.page = 1
  fetchVideos()
}

onMounted(() => {
  fetchKeywords()
  fetchVideos()
})
</script>

<style scoped>
.videos-page {
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

.filter-section {
  margin-bottom: 16px;
}
</style>
