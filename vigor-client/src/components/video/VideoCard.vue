<template>
  <div class="video-card" :class="{ active: isActive }" @click="$emit('click')">
    <div class="cover">
      <img
        v-if="video.cover_url"
        :src="video.cover_url"
        :alt="video.title"
        loading="lazy"
        @error="handleImageError"
      />
      <div v-else class="cover-placeholder">
        <span>{{ video.title.slice(0, 2) }}</span>
      </div>
      <div class="heat-badge" :class="heatColor">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
          <path d="M13.5 0.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5 0.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z" />
        </svg>
        <span>{{ heatText }}</span>
      </div>
    </div>
    <div class="info">
      <h3 class="title">{{ video.title }}</h3>
      <div class="author">
        <span>{{ video.author_name || '匿名作者' }}</span>
      </div>
      <div class="stats">
        <span class="stat-item">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
          </svg>
          {{ formatNumber(video.like_count) }}
        </span>
        <span class="stat-item">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" />
          </svg>
          {{ formatNumber(video.comment_count) }}
        </span>
        <span class="stat-item">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z" />
          </svg>
          {{ formatNumber(video.share_count) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Video } from '@/types/video'
import { formatNumber, formatHeatScore } from '@/utils/format'

const props = defineProps<{
  video: Video
  isActive?: boolean
}>()

defineEmits<{
  (e: 'click'): void
}>()

const heatInfo = computed(() => formatHeatScore(props.video.heat_score))
const heatText = computed(() => heatInfo.value.text)
const heatColor = computed(() => `heat-${heatInfo.value.color}`)

function handleImageError(event: Event) {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}
</script>

<style scoped>
.video-card {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
  background-color: var(--bg-primary);
}

.video-card:hover {
  background-color: var(--bg-secondary);
  transform: translateY(-1px);
}

.video-card.active {
  background-color: var(--bg-secondary);
  border-color: var(--primary-color);
}

.cover {
  position: relative;
  flex: 0 0 140px;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-md);
  overflow: hidden;
  background-color: var(--bg-tertiary);
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--border-color));
  color: var(--text-tertiary);
  font-size: 24px;
  font-weight: 600;
}

.heat-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  backdrop-filter: blur(8px);
}

.heat-red {
  background-color: rgba(255, 59, 48, 0.9);
}

.heat-orange {
  background-color: rgba(255, 149, 0, 0.9);
}

.heat-gray {
  background-color: rgba(142, 142, 147, 0.9);
}

.info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.author {
  font-size: 12px;
  color: var(--text-secondary);
}

.stats {
  display: flex;
  gap: var(--spacing-md);
  margin-top: auto;
  font-size: 12px;
  color: var(--text-tertiary);
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 640px) {
  .cover {
    flex: 0 0 100px;
  }

  .title {
    font-size: 13px;
  }

  .stats {
    gap: var(--spacing-sm);
  }
}
</style>
