<template>
  <div class="dashboard soft-scrollbar">
    <DomainHomePage
      v-if="!video"
      :category="category"
      :videos="videos"
      :platform="platform"
      :sort-by="sortBy"
      :time-window="timeWindow"
      @select-video="emit('selectVideo', $event)"
    />

    <div v-else class="dashboard-content">
      <!-- 视频详情 -->
      <section class="section video-detail">
        <button
          type="button"
          class="close-detail-btn"
          aria-label="关闭视频详情"
          title="关闭视频详情"
          @click="emit('close')"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path
              d="M18.3 5.71 12 12l6.3 6.29-1.41 1.41L10.59 13.41 4.29 19.7 2.88 18.29 9.17 12 2.88 5.71 4.29 4.3l6.3 6.29 6.3-6.29z"
            />
          </svg>
        </button>
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
          <h1 class="video-title">
            <span
              v-if="video.platform === 'bilibili'"
              class="platform-icon platform-bilibili"
              title="B站"
            >
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                <path
                  d="M18.223 3.086a1.25 1.25 0 0 1 0 1.768L17.08 5.996h1.17A3.75 3.75 0 0 1 22 9.747v7.5a3.75 3.75 0 0 1-3.75 3.75H5.75A3.75 3.75 0 0 1 2 17.247v-7.5a3.75 3.75 0 0 1 3.75-3.75h1.166L5.775 4.855a1.25 1.25 0 1 1 1.767-1.768l2.652 2.652a.984.984 0 0 1 .131.258h3.348a.984.984 0 0 1 .131-.258l2.652-2.652a1.25 1.25 0 0 1 1.768 0zM18.25 8.496H5.75a1.25 1.25 0 0 0-1.247 1.158l-.003.093v7.5c0 .659.51 1.198 1.157 1.246l.093.004h12.5a1.25 1.25 0 0 0 1.247-1.157l.003-.093v-7.5a1.25 1.25 0 0 0-1.157-1.247l-.093-.003zM8.5 11.499a1.25 1.25 0 0 1 1.25 1.25v1.25a1.25 1.25 0 1 1-2.5 0v-1.25a1.25 1.25 0 0 1 1.25-1.25zm7 0a1.25 1.25 0 0 1 1.25 1.25v1.25a1.25 1.25 0 1 1-2.5 0v-1.25a1.25 1.25 0 0 1 1.25-1.25z"
                />
              </svg>
            </span>
            <span
              v-else-if="video.platform === 'douyin'"
              class="platform-icon platform-douyin"
              title="抖音"
            >
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                <path
                  d="M19.321 5.562a5.124 5.124 0 0 1-.443-.258 6.228 6.228 0 0 1-1.137-.966c-.849-.971-1.166-1.957-1.282-2.647h.005A3.844 3.844 0 0 1 16.4 1h-3.27v12.638c0 .17 0 .337-.007.502a5.196 5.196 0 1 1-.717-2.7 5.196 5.196 0 0 1 .717 1.13V8.275a8.42 8.42 0 0 0-7.97 1.49C3.547 11.34 2.62 13.86 2.93 16.297c.31 2.437 1.78 4.485 3.94 5.49a8.481 8.481 0 0 0 7.96-.69 8.514 8.514 0 0 0 3.79-7.061V8.275a10.354 10.354 0 0 0 6.06 1.94V6.94a6.16 6.16 0 0 1-5.36-1.378z"
                />
              </svg>
            </span>
            <span class="video-title-text">{{ video.title }}</span>
          </h1>
          <div class="video-meta">
            <span class="author">{{ video.author_name || '匿名作者' }}</span>
            <span class="divider">·</span>
            <span class="publish-time">{{ formatDate(video.publish_time) }}</span>
            <a class="external-link" :href="originalUrl" target="_blank" rel="noopener">
              查看原视频
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path
                  d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"
                />
              </svg>
            </a>
          </div>
          <div v-if="video.tags && video.tags.length > 0" class="video-tags">
            <span v-for="tag in video.tags" :key="tag" class="tag-item">{{ tag }}</span>
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

      <!-- 评论摘要 -->
      <section class="section">
        <h2 class="section-title">评论摘要</h2>
        <div v-if="generating" class="generating-summary">
          <div class="generating-spinner"></div>
          <p class="generating-text">正在生成评论摘要…</p>
          <p class="generating-hint">AI 处理约需 1 分钟,完成后会自动刷新</p>
        </div>
        <div v-else-if="video.comment_summary" class="comment-summary">
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
            <span class="generated-at"> 生成于 {{ generatedAtText }} </span>
            <div class="summary-actions">
              <button type="button" class="toggle-btn" @click="toggleComments">
                {{ showComments ? '收起评论' : '查看评论' }}
                <svg
                  viewBox="0 0 24 24"
                  width="12"
                  height="12"
                  fill="currentColor"
                  :class="{ 'icon-flipped': showComments }"
                >
                  <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
                </svg>
              </button>
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
          <div v-if="showComments" class="comments-list soft-scrollbar">
            <div v-if="loadingComments" class="comments-state">加载中...</div>
            <div v-else-if="comments.length === 0" class="comments-state">暂无评论</div>
            <div v-else class="comment-items">
              <div v-for="comment in comments" :key="comment.id" class="comment-item">
                <div class="comment-header">
                  <div class="comment-meta">
                    <span class="comment-author">{{ comment.author_name || '匿名' }}</span>
                    <span v-if="comment.publish_time" class="comment-time">
                      {{ formatDate(comment.publish_time) }}
                    </span>
                  </div>
                  <span class="comment-likes">👍 {{ formatNumber(comment.like_count) }}</span>
                </div>
                <p class="comment-content">{{ comment.content }}</p>
              </div>
            </div>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'
import type { Category } from '@/api/category'
import type { Video, Comment } from '@/types/video'
import { videoApi } from '@/api/video'
import { formatNumber, formatDate, formatHeatScore, formatSentiment } from '@/utils/format'
import { normalizeCover } from '@/utils/media'
import DomainHomePage from './DomainHomePage.vue'

const message = useMessage()

const props = defineProps<{
  video: Video | null
  category: Category | null
  videos: Video[]
  platform: string | null
  sortBy: 'heat_score' | 'publish_time'
  timeWindow: '1d' | '3d' | '7d' | '15d' | '30d' | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'selectVideo', id: number): void
  (e: 'close'): void
}>()

const generating = ref(false)
let pollTimer: number | null = null

const showComments = ref(false)
const comments = ref<Comment[]>([])
const loadingComments = ref(false)

async function toggleComments() {
  showComments.value = !showComments.value
  if (showComments.value && comments.value.length === 0) {
    await loadComments()
  }
}

async function loadComments() {
  if (!props.video?.id) return
  loadingComments.value = true
  try {
    comments.value = await videoApi.getComments(props.video.id, { limit: 50 })
  } catch {
    message.error('加载评论失败')
  } finally {
    loadingComments.value = false
  }
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function handleGenerateSummary() {
  if (!props.video?.id) return
  generating.value = true
  // 重新生成场景:先停掉旧的 interval
  stopPolling()
  // 记录当前摘要生成时间,用来判断新摘要是否真的产生(重新生成时必须 > 此值)
  const baselineGeneratedAt = props.video.comment_summary?.generated_at || null
  try {
    await videoApi.generateSummary(props.video.id)
    message.success('摘要生成中,生成完成后会自动刷新')
    pollForSummary(props.video.id, baselineGeneratedAt)
  } catch (error: any) {
    message.error(error.message || '生成摘要失败')
    generating.value = false
  }
}

function pollForSummary(videoId: number, baselineGeneratedAt: string | null) {
  let attempts = 0
  const maxAttempts = 24 // 最多 120s (24 * 5s)
  pollTimer = window.setInterval(async () => {
    attempts++
    try {
      const detail = await videoApi.getSummary(videoId)
      const cs = detail.comment_summary
      // 重新生成:要求 generated_at 严格晚于基线时间戳;首次生成:有摘要即可
      const isReady = cs && (!baselineGeneratedAt || cs.generated_at > baselineGeneratedAt)
      if (isReady) {
        stopPolling()
        generating.value = false
        emit('refresh')
        return
      }
    } catch {
      // 网络错误不中断轮询,继续重试直到 maxAttempts
    }
    if (attempts >= maxAttempts) {
      stopPolling()
      generating.value = false
      message.warning('生成时间较长,请稍后手动刷新')
    }
  }, 5000)
}

onUnmounted(() => {
  stopPolling()
})

// 切换视频时重置本地状态,避免残留上个视频的评论列表 / 摘要生成状态
watch(
  () => props.video?.id,
  (newId, oldId) => {
    if (newId === oldId) return
    stopPolling()
    comments.value = []
    showComments.value = false
    loadingComments.value = false
    generating.value = false
  }
)

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
  position: relative;
  display: flex;
  gap: var(--spacing-xl);
}

.close-detail-btn {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  z-index: 2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  border-radius: 50%;
  background-color: color-mix(in srgb, var(--bg-primary) 88%, transparent);
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast),
    transform var(--transition-fast);
}

.close-detail-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-tertiary);
  background-color: var(--bg-secondary);
  transform: scale(1.04);
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
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.platform-icon {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-top: 2px;
}

.platform-bilibili {
  color: #00a1d6;
}

.platform-douyin {
  color: #fe2c55;
}

.video-title-text {
  flex: 1;
  min-width: 0;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--spacing-lg);
}

.tag-item {
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.tag-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
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
  transition:
    filter 0.15s ease,
    opacity 0.15s ease;
}

.generate-btn:hover:not(:disabled) {
  filter: brightness(1.05);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.generating-summary {
  padding: var(--spacing-xl);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.generating-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.generating-text {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.generating-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-tertiary);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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

.summary-actions {
  display: flex;
  gap: 8px;
}

.toggle-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.toggle-btn:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
  background: rgba(0, 122, 255, 0.05);
}

.toggle-btn .icon-flipped {
  transform: rotate(180deg);
}

.comments-list {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  max-height: 400px;
  overflow-y: auto;
}

.comments-state {
  padding: var(--spacing-md);
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}

.comment-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.comment-item {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
}

.comment-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.comment-author {
  color: var(--text-secondary);
  font-weight: 500;
}

.comment-time {
  color: var(--text-tertiary);
  font-size: 11px;
}

.comment-likes {
  color: var(--text-tertiary);
}

.comment-content {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
  margin: 0;
  word-break: break-word;
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
