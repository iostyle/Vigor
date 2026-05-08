<template>
  <div class="video-list">
    <div class="list-header">
      <h2>热门视频</h2>
      <div class="filters">
        <select v-model="platform" class="select" @change="handlePlatformChange">
          <option value="">全部</option>
          <option value="dy">抖音</option>
          <option value="bili">B站</option>
        </select>
        <select v-model="sortBy" class="select" @change="handleSortChange">
          <option value="heat_score">按热度</option>
          <option value="publish_time">按时间</option>
        </select>
        <select v-model="timeWindow" class="select" @change="handleTimeWindowChange">
          <option value="">全部时间</option>
          <option value="1d">最近 1 天</option>
          <option value="3d">最近 3 天</option>
          <option value="7d">最近 7 天</option>
          <option value="15d">最近 15 天</option>
          <option value="30d">最近 30 天</option>
        </select>
      </div>
    </div>

    <div v-if="loading && videos.length === 0" class="list-state">
      <div class="loader"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="videos.length === 0" class="list-state">
      <p>暂无数据</p>
      <span class="hint">请确保后端服务已启动,或切换其他领域</span>
    </div>

    <div v-else class="list-content">
      <VideoCard
        v-for="video in videos"
        :key="video.id"
        :video="video"
        :is-active="video.id === selectedId"
        @click="handleSelect(video.id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Video } from '@/types/video'
import VideoCard from './VideoCard.vue'

const props = defineProps<{
  videos: Video[]
  loading: boolean
  selectedId: number | null
  initialPlatform?: string | null
  initialSortBy?: 'heat_score' | 'publish_time'
  initialTimeWindow?: '1d' | '3d' | '7d' | '15d' | '30d' | null
}>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'change-sort', sort: 'heat_score' | 'publish_time'): void
  (e: 'change-time-window', window: '1d' | '3d' | '7d' | '15d' | '30d' | null): void
  (e: 'change-platform', platform: string | null): void
}>()

const sortBy = ref<'heat_score' | 'publish_time'>(props.initialSortBy || 'heat_score')
const timeWindow = ref<string>(props.initialTimeWindow || '')
const platform = ref<string>(props.initialPlatform || '')

function handleSelect(id: number) {
  emit('select', id)
}

function handleSortChange() {
  emit('change-sort', sortBy.value)
}

function handleTimeWindowChange() {
  const value = timeWindow.value as '1d' | '3d' | '7d' | '15d' | '30d' | ''
  emit('change-time-window', value === '' ? null : value)
}

function handlePlatformChange() {
  emit('change-platform', platform.value === '' ? null : platform.value)
}
</script>

<style scoped>
.video-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-primary);
}

.list-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.filters {
  display: flex;
  gap: var(--spacing-sm);
}

.select {
  padding: 6px 12px;
  font-size: 13px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  outline: none;
  transition: border-color var(--transition-fast);
}

.select:focus {
  border-color: var(--primary-color);
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.list-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.list-state .hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.loader {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .list-header {
    padding: var(--spacing-md);
  }

  .list-header h2 {
    font-size: 16px;
  }

  .filters {
    flex-direction: column;
    gap: 4px;
  }

  .select {
    padding: 4px 8px;
    font-size: 12px;
  }
}
</style>
