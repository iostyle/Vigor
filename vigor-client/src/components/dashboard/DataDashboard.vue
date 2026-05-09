<template>
  <div class="dashboard">
    <div v-if="!video" class="empty-state">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
        </svg>
      </div>
      <h3>请选择一个视频查看详细数据</h3>
      <p>点击左侧视频卡片,这里将展示完整的数据分析</p>
    </div>

    <div v-else class="dashboard-content">
      <!-- 视频详情 -->
      <section class="section video-detail">
        <div class="video-player-container">
          <!-- B站:iframe 播放器 -->
          <iframe
            v-if="video.platform === 'bilibili' && video.external_id"
            :src="`https://player.bilibili.com/player.html?bvid=${video.external_id}&high_quality=1&danmaku=0&autoplay=0`"
            allowfullscreen
            scrolling="no"
            frameborder="0"
            class="video-player"
          ></iframe>

          <!-- 抖音:封面+跳转按钮 -->
          <div v-else-if="video.platform === 'douyin'" class="video-poster">
            <img
              v-if="video.cover_url"
              :src="normalizeCover(video.cover_url)"
              :alt="video.title"
              referrerpolicy="no-referrer"
            />
            <div class="video-overlay">
              <a
                v-if="video.video_url"
                :href="video.video_url"
                target="_blank"
                rel="noopener"
                class="open-douyin-btn"
              >
                <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
                <span>在抖音打开</span>
              </a>
            </div>
          </div>

          <!-- Fallback:封面+查看原视频 -->
          <div v-else class="video-poster">
            <img
              v-if="video.cover_url"
              :src="normalizeCover(video.cover_url)"
              :alt="video.title"
              referrerpolicy="no-referrer"
            />
            <div class="video-overlay">
              <a
                v-if="video.video_url"
                :href="video.video_url"
                target="_blank"
                rel="noopener"
                class="open-douyin-btn"
              >
                <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
                <span>点击查看原视频</span>
              </a>
            </div>
          </div>
        </div>
        <div class="video-info">
          <h1 class="video-title">{{ video.title }}</h1>
          <div class="video-meta">
            <span class="author">{{ video.author_name || '匿名作者' }}</span>
            <span class="divider">·</span>
            <span class="publish-time">{{ formatDate(video.publish_time) }}</span>
            <a class="external-link" :href="originalUrl" target="_blank" rel="noopener">
              查看原视频
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z" />
              </svg>
            </a>
          </div>
          <div class="metrics">
            <div class="metric">
              <div class="metric-value">{{ formatNumber(video.like_count) }}</div>
              <div class="metric-label">点赞</div>
            </div>
            <div class="metric">
              <div class="metric-value">{{ formatNumber(video.comment_count) }}</div>
              <div class="metric-label">评论</div>
            </div>
            <div class="metric">
              <div class="metric-value">{{ formatNumber(video.share_count) }}</div>
              <div class="metric-label">分享</div>
            </div>
            <div class="metric heat-metric">
              <div class="metric-value" :class="`heat-${heatInfo.color}`">
                {{ heatInfo.text }}
              </div>
              <div class="metric-label">热度</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 互动数据图表 -->
      <section class="section">
        <h2 class="section-title">互动数据趋势</h2>
        <div class="chart-placeholder">
          <svg viewBox="0 0 400 200" class="mock-chart">
            <polyline
              points="0,150 40,140 80,120 120,130 160,100 200,90 240,80 280,60 320,50 360,40 400,30"
              fill="none"
              stroke="var(--primary-color)"
              stroke-width="2"
            />
            <polyline
              points="0,180 40,170 80,160 120,155 160,140 200,135 240,120 280,110 320,95 360,85 400,75"
              fill="none"
              stroke="var(--success-color)"
              stroke-width="2"
              stroke-dasharray="4,4"
            />
          </svg>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-dot" style="background: var(--primary-color)"></span>
              点赞
            </span>
            <span class="legend-item">
              <span class="legend-dot" style="background: var(--success-color)"></span>
              评论
            </span>
          </div>
        </div>
      </section>

      <!-- 评论摘要 -->
      <section class="section">
        <h2 class="section-title">评论摘要</h2>
        <div v-if="video.comment_summary" class="comment-summary">
          <p class="summary-text">{{ video.comment_summary.summary }}</p>
          <div class="summary-meta">
            <div class="keywords">
              <span
                v-for="keyword in video.comment_summary.top_keywords"
                :key="keyword"
                class="keyword-tag"
              >
                {{ keyword }}
              </span>
            </div>
            <div class="sentiment" :class="`sentiment-${sentimentInfo.color}`">
              情感倾向: {{ sentimentInfo.text }}
            </div>
          </div>
          <div class="regenerate-summary">
            <span class="generated-at">
              生成于 {{ generatedAtText }}
            </span>
            <button
              type="button"
              class="regenerate-btn"
              :disabled="generating"
              @click="handleGenerateSummary"
            >
              {{ generating ? '生成中...' : '重新生成' }}
            </button>
          </div>
        </div>
        <div v-else-if="video.comment_count > 0" class="generate-summary">
          <p class="hint">该视频有 {{ video.comment_count }} 条评论,可点击生成 AI 评论摘要</p>
          <button
            type="button"
            class="generate-btn"
            :disabled="generating"
            @click="handleGenerateSummary"
          >
            {{ generating ? '生成中...' : '生成评论摘要' }}
          </button>
        </div>
        <div v-else class="no-data">
          <p>暂无评论摘要</p>
        </div>
      </section>

      <!-- AI 领域专家分析 -->
      <section class="section">
        <h2 class="section-title">
          <span>AI 领域专家分析</span>
          <span class="coming-soon">敬请期待</span>
        </h2>
        <div class="ai-analysis">
          <div class="analysis-card">
            <h4>🎯 行业洞察</h4>
            <p class="placeholder">AI 将从专业角度解读视频内容的行业意义</p>
          </div>
          <div class="analysis-card">
            <h4>📊 数据解读</h4>
            <p class="placeholder">分析热度背后的原因和传播逻辑</p>
          </div>
          <div class="analysis-card">
            <h4>🚀 趋势预测</h4>
            <p class="placeholder">基于当前数据预测话题发展方向</p>
          </div>
        </div>
      </section>

      <!-- 趋势对比 -->
      <section class="section">
        <h2 class="section-title">趋势对比</h2>
        <div class="trend-comparison">
          <div class="comparison-item">
            <span class="label">该视频热度</span>
            <div class="bar">
              <div class="bar-fill primary" :style="{ width: '75%' }"></div>
            </div>
            <span class="value">{{ heatInfo.text }}</span>
          </div>
          <div class="comparison-item">
            <span class="label">同领域平均</span>
            <div class="bar">
              <div class="bar-fill secondary" :style="{ width: '50%' }"></div>
            </div>
            <span class="value">50.0</span>
          </div>
          <div class="ranking">
            该视频在同领域中排名 <strong>Top 15%</strong>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMessage } from 'naive-ui'
import type { Video } from '@/types/video'
import { videoApi } from '@/api/video'
import { formatNumber, formatDate, formatHeatScore, formatSentiment } from '@/utils/format'
import { normalizeCover } from '@/utils/media'

const message = useMessage()

const props = defineProps<{
  video: Video | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const generating = ref(false)

async function handleGenerateSummary() {
  if (!props.video?.id) return
  generating.value = true
  try {
    await videoApi.generateSummary(props.video.id)
    message.success('摘要生成中,10 秒后自动刷新')
    setTimeout(() => {
      emit('refresh')
      generating.value = false
    }, 10000)
  } catch (error: any) {
    message.error(error.message || '生成摘要失败')
    generating.value = false
  }
}

const originalUrl = computed(() => {
  if (!props.video) return '#'
  return props.video.video_url || '#'
})

const heatInfo = computed(() => formatHeatScore(props.video?.heat_score ?? null))
const sentimentInfo = computed(() =>
  formatSentiment(props.video?.comment_summary?.sentiment || 'neutral')
)

// 评论摘要生成时间,格式:YYYY/MM/DD HH:mm
const generatedAtText = computed(() => {
  const raw = props.video?.comment_summary?.generated_at
  if (!raw) return '-'
  const d = new Date(raw)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
})
</script>

<style scoped>
.dashboard {
  height: 100%;
  overflow-y: auto;
  background-color: var(--bg-secondary);
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  color: var(--text-secondary);
  text-align: center;
  padding: var(--spacing-xl);
}

.empty-icon {
  color: var(--text-tertiary);
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 14px;
  color: var(--text-tertiary);
}

.dashboard-content {
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.section {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  border: 1px solid var(--border-color);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.coming-soon {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-tertiary);
  padding: 2px 8px;
  background-color: var(--bg-secondary);
  border-radius: 10px;
}

.video-detail {
  display: flex;
  gap: var(--spacing-xl);
}

.video-player-container {
  flex: 0 0 480px;
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-color: var(--bg-tertiary);
}

.video-player {
  width: 100%;
  aspect-ratio: 16 / 9;
  background-color: #000;
}

.video-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
}

.video-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.45);
}

.open-douyin-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-xl);
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
  text-decoration: none;
  border-radius: var(--radius-lg);
  font-size: 14px;
  font-weight: 600;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all var(--transition-fast);
}

.open-douyin-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
  transform: scale(1.04);
}

.no-video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.no-video-overlay svg {
  opacity: 0.6;
}

.video-cover {
  flex: 0 0 280px;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-color: var(--bg-tertiary);
}

.video-cover img {
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
  font-size: 32px;
  font-weight: 600;
}

.video-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.video-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: var(--spacing-sm);
}

.video-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.external-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  padding: 6px 12px;
  background-color: var(--bg-secondary);
  color: var(--primary-color);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-fast);
  border: 1px solid var(--border-color);
}

.external-link:hover {
  background-color: var(--bg-tertiary);
  border-color: var(--primary-color);
}

.external-link svg {
  opacity: 0.7;
}

.divider {
  color: var(--text-tertiary);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-top: auto;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.metric-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.heat-metric .heat-red {
  color: var(--error-color);
}

.heat-metric .heat-orange {
  color: var(--warning-color);
}

.heat-metric .heat-gray {
  color: var(--text-secondary);
}

.chart-placeholder {
  width: 100%;
}

.mock-chart {
  width: 100%;
  height: 200px;
}

.chart-legend {
  display: flex;
  gap: var(--spacing-lg);
  justify-content: center;
  margin-top: var(--spacing-md);
  font-size: 13px;
  color: var(--text-secondary);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.comment-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.summary-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.summary-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.keyword-tag {
  padding: 4px 10px;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: 12px;
  font-size: 12px;
}

.sentiment {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
}

.sentiment-green {
  background-color: rgba(52, 199, 89, 0.1);
  color: var(--success-color);
}

.sentiment-red {
  background-color: rgba(255, 59, 48, 0.1);
  color: var(--error-color);
}

.sentiment-gray {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
}

.no-data {
  color: var(--text-tertiary);
  font-size: 13px;
}

.generate-summary {
  padding: var(--spacing-lg);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.generate-summary .hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.generate-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(0, 122, 255, 0.18);
  background: linear-gradient(180deg, #2997ff 0%, #007aff 100%);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s ease, opacity 0.15s ease;
}

.generate-btn:hover:not(:disabled) {
  filter: brightness(1.05);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.regenerate-summary {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.generated-at {
  font-size: 12px;
  color: var(--text-tertiary);
}

.regenerate-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.regenerate-btn:hover:not(:disabled) {
  color: var(--primary-color);
  border-color: var(--primary-color);
  background: rgba(0, 122, 255, 0.05);
}

.regenerate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-analysis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.analysis-card {
  padding: var(--spacing-lg);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
}

.analysis-card h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.analysis-card .placeholder {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.trend-comparison {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.comparison-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.comparison-item .label {
  flex: 0 0 100px;
  font-size: 13px;
  color: var(--text-secondary);
}

.bar {
  flex: 1;
  height: 8px;
  background-color: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width var(--transition-base);
}

.bar-fill.primary {
  background-color: var(--primary-color);
}

.bar-fill.secondary {
  background-color: var(--text-tertiary);
}

.comparison-item .value {
  flex: 0 0 60px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.ranking {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}

.ranking strong {
  color: var(--primary-color);
  font-weight: 600;
}

@media (max-width: 768px) {
  .dashboard-content {
    padding: var(--spacing-md);
    gap: var(--spacing-md);
  }

  .section {
    padding: var(--spacing-md);
  }

  .video-detail {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .video-player-container {
    flex: 0 0 auto;
    width: 100%;
  }

  .video-title {
    font-size: 16px;
  }

  .metrics {
    grid-template-columns: repeat(2, 1fr);
  }

  .ai-analysis {
    grid-template-columns: 1fr;
  }
}
</style>
