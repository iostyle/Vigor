<template>
  <div class="domain-home">
    <template v-if="isFinance">
      <section class="finance-hero">
        <div class="hero-copy">
          <div class="eyebrow">财经情报台</div>
          <h1>{{ categoryName }}</h1>
          <p>追踪政策信号、资本情绪与消费变化,从短视频热度里捕捉财经议题的传播窗口。</p>
          <div class="topic-tags">
            <span v-for="tag in hotTags" :key="tag">#{{ tag }}</span>
          </div>
        </div>
        <div class="market-panel" aria-label="财经趋势概览">
          <div class="market-header">
            <span>市场热度曲线</span>
            <strong>{{ heatIndex }}</strong>
          </div>
          <div class="market-chart">
            <span class="grid-line line-a"></span>
            <span class="grid-line line-b"></span>
            <span class="trend-line"></span>
            <span class="trend-dot dot-a"></span>
            <span class="trend-dot dot-b"></span>
            <span class="trend-dot dot-c"></span>
          </div>
          <div class="market-footer">
            <span>稳健上行</span>
            <span>{{ scopeLabel }}</span>
          </div>
        </div>
      </section>

      <section class="finance-metrics" aria-label="财经观察指标">
        <article v-for="metric in financeMetrics" :key="metric.label" class="metric-card">
          <div class="metric-topline">
            <span class="metric-icon" :class="metric.tone">{{ metric.icon }}</span>
            <span>{{ metric.label }}</span>
          </div>
          <strong>{{ metric.value }}</strong>
          <p>{{ metric.hint }}</p>
        </article>
      </section>

      <section class="content-grid">
        <article class="insight-panel">
          <div class="section-heading">
            <span>机会雷达</span>
            <small>优先关注</small>
          </div>
          <div class="radar-list">
            <div v-for="item in radarItems" :key="item.title" class="radar-item">
              <span class="radar-index">{{ item.index }}</span>
              <div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
              </div>
            </div>
          </div>
        </article>

        <article class="strategy-panel">
          <div class="section-heading">
            <span>内容策略</span>
            <small>选片前检查</small>
          </div>
          <div class="strategy-list">
            <div v-for="step in strategySteps" :key="step.title" class="strategy-item">
              <div class="check-icon">✓</div>
              <div>
                <h3>{{ step.title }}</h3>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section v-if="recommendedVideos.length > 0" class="recommend-panel">
        <div class="section-heading">
          <span>推荐先看</span>
          <small>来自当前列表</small>
        </div>
        <div class="recommend-list">
          <button
            v-for="video in recommendedVideos"
            :key="video.id"
            type="button"
            class="recommend-item"
            @click="emit('selectVideo', video.id)"
          >
            <span class="recommend-title">{{ video.title }}</span>
            <span class="recommend-meta">
              {{ video.author_name || '匿名作者' }} · 热度 {{ formatHeat(video.heat_score) }} · 评论
              {{ formatNumber(video.comment_count) }}
            </span>
          </button>
        </div>
      </section>
    </template>

    <template v-else-if="isFilm">
      <section class="film-hero">
        <div class="hero-copy film-copy">
          <div class="eyebrow film-eyebrow">影视热榜室</div>
          <h1>{{ categoryName }}</h1>
          <p>聚合国产热门剧和海外流媒体内容,用热度和讨论量判断下一批值得深看的作品。</p>
          <div class="film-nav">
            <span v-for="item in filmNavItems" :key="item">{{ item }}</span>
          </div>
        </div>
        <div class="film-scoreboard" aria-label="影视热度概览">
          <div class="scoreboard-header">
            <span>本栏热度</span>
            <strong>{{ filmPulse }}</strong>
          </div>
          <div class="scoreboard-meter">
            <span class="meter-track"></span>
            <span class="meter-fill" :style="{ width: `${filmPulse}%` }"></span>
          </div>
          <div class="scoreboard-grid">
            <div v-for="metric in filmMetrics" :key="metric.label" class="score-tile">
              <span>{{ metric.label }}</span>
              <strong>{{ metric.value }}</strong>
              <small>{{ metric.hint }}</small>
            </div>
          </div>
        </div>
      </section>

      <section class="film-rank-grid" aria-label="影视分区榜单">
        <article
          v-for="section in filmSections"
          :key="section.key"
          class="film-rank-panel"
          :class="`film-rank-panel-${section.key}`"
        >
          <div class="film-section-header">
            <div>
              <span class="section-kicker">{{ section.kicker }}</span>
              <h2>{{ section.title }}</h2>
            </div>
            <small>{{ section.subtitle }}</small>
          </div>

          <div v-if="section.items.length > 0" class="film-rank-list soft-scrollbar">
            <button
              v-for="(video, index) in section.items"
              :key="video.id"
              type="button"
              class="film-rank-row"
              @click="emit('selectVideo', video.id)"
            >
              <span class="film-rank-index">{{ index + 1 }}</span>
              <span class="film-poster">
                <span class="film-poster-initial">{{ getTitleInitial(video.title) }}</span>
                <img
                  v-if="video.cover_url"
                  :src="normalizeCover(video.cover_url)"
                  :alt="video.title"
                  referrerpolicy="no-referrer"
                  @error="handlePosterError"
                />
              </span>
              <span class="film-rank-copy">
                <strong>{{ video.title }}</strong>
                <small>{{ formatFilmMeta(video) }}</small>
              </span>
              <span class="film-score" :class="getFilmScoreTone(video)">
                <strong>{{ formatFilmScore(video) }}</strong>
                <small>热度</small>
              </span>
            </button>
          </div>

          <div v-else-if="filmRankLoading" class="film-empty">
            <strong>正在整理榜单</strong>
            <span>正在按当前筛选条件分页加载热门内容</span>
          </div>

          <div v-else class="film-empty">
            <strong>{{ section.emptyTitle }}</strong>
            <span>{{ section.emptyHint }}</span>
          </div>
        </article>
      </section>

      <section v-if="recommendedVideos.length > 0" class="film-watchlist">
        <div class="section-heading">
          <span>编辑精选</span>
          <small>来自当前视频列表</small>
        </div>
        <div class="watchlist-row">
          <button
            v-for="video in recommendedVideos"
            :key="video.id"
            type="button"
            class="watchlist-item"
            @click="emit('selectVideo', video.id)"
          >
            <span>{{ video.title }}</span>
            <strong>{{ formatFilmScore(video) }}</strong>
          </button>
        </div>
      </section>
    </template>

    <section v-else class="fallback-home">
      <div class="fallback-mark">{{ categoryInitial }}</div>
      <h1>{{ categoryName }}</h1>
      <p>从左侧选择一个视频后,这里将展示完整的数据分析、评论摘要与领域洞察。</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Category } from '@/api/category'
import { videoApi } from '@/api/video'
import type { Video } from '@/types/video'
import { formatNumber } from '@/utils/format'
import { normalizeCover } from '@/utils/media'

const FILM_PAGE_SIZE = 20
const FILM_SECTION_LIMIT = 10
const FILM_MAX_PAGES = 8

const props = defineProps<{
  category: Category | null
  videos: Video[]
  platform: string | null
  sortBy: 'heat_score' | 'publish_time'
  timeWindow: '1d' | '3d' | '7d' | '15d' | '30d' | null
}>()

const emit = defineEmits<{
  (e: 'selectVideo', id: number): void
}>()

const categoryName = computed(() => props.category?.name || '当前领域')
const isFinance = computed(() => categoryName.value.includes('财经'))
const isFilm = computed(() => /影视|电影|剧集|电视剧|娱乐/.test(categoryName.value))
const categoryInitial = computed(() => categoryName.value.slice(0, 1))
const filmRankVideos = ref<Video[]>([])
const filmRankLoading = ref(false)
let filmRankRequestId = 0
const filmMetricVideos = computed(() =>
  isFilm.value && filmRankVideos.value.length > 0 ? filmRankVideos.value : props.videos
)

const heatIndex = computed(() => {
  const scores = props.videos
    .map((video) => video.heat_score)
    .filter((score): score is number => score !== null)
  if (scores.length === 0) return 72
  return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
})

const totalInteractions = computed(() =>
  props.videos.reduce(
    (sum, video) => sum + video.like_count + video.comment_count + video.share_count,
    0
  )
)

const averageComments = computed(() => {
  if (props.videos.length === 0) return 0
  return Math.round(
    props.videos.reduce((sum, video) => sum + video.comment_count, 0) / props.videos.length
  )
})

const hotTags = computed(() => {
  const counts = new Map<string, number>()
  props.videos.forEach((video) => {
    video.tags?.forEach((tag) => counts.set(tag, (counts.get(tag) || 0) + 1))
  })
  const tags = Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([tag]) => tag)
  return tags.length > 0 ? tags : ['宏观政策', '市场情绪', '消费趋势']
})

const scopeLabel = computed(() =>
  props.videos.length > 0 ? `${props.videos.length} 条样本` : '待采集样本'
)

const financeMetrics = computed(() => [
  {
    label: '视频样本',
    value: formatNumber(props.videos.length),
    hint: '当前筛选条件下可用于分析的财经内容数量。',
    icon: 'P',
    tone: 'blue'
  },
  {
    label: '互动总量',
    value: formatNumber(totalInteractions.value),
    hint: '点赞、评论与分享合计,用于观察内容传播势能。',
    icon: 'M',
    tone: 'green'
  },
  {
    label: '平均评论',
    value: formatNumber(averageComments.value),
    hint: '评论密度越高,越适合做情绪和观点分歧分析。',
    icon: 'C',
    tone: 'orange'
  }
])

const recommendedVideos = computed(() =>
  [...props.videos]
    .sort((a, b) => {
      const aScore = (a.heat_score || 0) + a.comment_count * 0.08 + a.share_count * 0.05
      const bScore = (b.heat_score || 0) + b.comment_count * 0.08 + b.share_count * 0.05
      return bScore - aScore
    })
    .slice(0, 4)
)

const rankedFilmVideos = computed(() => {
  const source = filmRankVideos.value.length > 0 ? filmRankVideos.value : props.videos
  return [...source].sort((a, b) => getFilmRankScore(b) - getFilmRankScore(a))
})

const filmScoreMap = computed(() => {
  const scores = rankedFilmVideos.value.map((video) => getFilmRankScore(video))
  const max = Math.max(...scores, 0)
  const min = Math.min(...scores, max)
  const range = max - min
  const map = new Map<number, number>()

  rankedFilmVideos.value.forEach((video, index) => {
    if (max <= 0) {
      map.set(video.id, 0)
      return
    }

    if (range <= 0) {
      map.set(video.id, Math.max(58, 92 - index * 4))
      return
    }

    const normalized = (getFilmRankScore(video) - min) / range
    map.set(video.id, Math.round(45 + normalized * 50))
  })

  return map
})

const domesticDramaVideos = computed(() =>
  rankedFilmVideos.value.filter(
    (video) =>
      !matchesFilmKeywords(video, overseasStreamingKeywords) &&
      matchesFilmKeywords(video, domesticDramaKeywords)
  )
)

const overseasStreamingVideos = computed(() =>
  rankedFilmVideos.value.filter((video) => matchesFilmKeywords(video, overseasStreamingKeywords))
)

const filmPulse = computed(() => Math.max(0, Math.min(99, heatIndex.value)))

const filmNavItems = ['国内剧集', '海外流媒体']

const filmMetrics = computed(() => [
  {
    label: '国内剧集',
    value: formatNumber(domesticDramaVideos.value.length),
    hint: '国产剧与类型剧讨论'
  },
  {
    label: '海外流媒体',
    value: formatNumber(overseasStreamingVideos.value.length),
    hint: 'Netflix、韩剧、美剧等'
  },
  {
    label: '互动总量',
    value: formatNumber(
      filmMetricVideos.value.reduce(
        (sum, video) => sum + video.like_count + video.comment_count + video.share_count,
        0
      )
    ),
    hint: '点赞评论分享合计'
  }
])

const filmSections = computed(() => [
  {
    key: 'domestic',
    kicker: 'SERIES',
    title: '国内热门剧集',
    subtitle: '悬疑、喜剧、古装、短剧等',
    items: domesticDramaVideos.value.slice(0, FILM_SECTION_LIMIT),
    emptyTitle: '等待国内剧集数据',
    emptyHint: '采集国产剧、悬疑、喜剧等关键词后会生成榜单'
  },
  {
    key: 'overseas',
    kicker: 'STREAMING',
    title: '海外流媒体',
    subtitle: 'Netflix、HBO、Disney+、韩剧、美剧等热门内容',
    items: overseasStreamingVideos.value.slice(0, FILM_SECTION_LIMIT),
    emptyTitle: '等待海外流媒体数据',
    emptyHint: '采集 Netflix、韩剧、美剧、HBO 等关键词后会生成榜单'
  }
])

const radarItems = [
  {
    index: '01',
    title: '宏观政策解读',
    description: '关注政策发布后的第一波解释型内容,判断大众最关心的影响面。'
  },
  {
    index: '02',
    title: '公司与行业事件',
    description: '追踪财报、并购、价格战等节点,识别短期热度和长期叙事。'
  },
  {
    index: '03',
    title: '普通人的钱袋子',
    description: '把利率、房价、就业和消费变化落到生活场景,更容易形成讨论。'
  }
]

const strategySteps = [
  {
    title: '先看情绪',
    description: '优先选择评论量高且立场分化的视频,用于观察风险偏好。'
  },
  {
    title: '再看传播',
    description: '对比点赞、分享和发布时间,判断内容是知识普及还是事件爆发。'
  },
  {
    title: '最后看机会',
    description: '将高热议题沉淀为关键词,反向补充下一轮采集方向。'
  }
]

function formatHeat(score: number | null) {
  return score === null ? '-' : score.toFixed(1)
}

const domesticDramaKeywords = [
  '国产',
  '国内',
  '国剧',
  '电视剧',
  '剧集',
  '悬疑',
  '喜剧',
  '古装',
  '都市',
  '短剧',
  '大陆'
]

const overseasStreamingKeywords = [
  '韩剧',
  '韩国',
  'k-drama',
  'korea',
  'korean',
  '韩综',
  '美剧',
  '英剧',
  'netflix',
  '奈飞',
  '网飞',
  'hbo',
  'disney',
  '迪士尼',
  'apple tv',
  'prime',
  '欧美',
  '好莱坞',
  '漫威',
  'dc',
  '真人快打',
  'mortal kombat',
  '动作片',
  '恐怖片',
  '惊悚片',
  '科幻片',
  '欧美电影',
  '海外电影'
]

watch(
  () => [isFilm.value, props.category?.id ?? null, props.platform, props.sortBy, props.timeWindow],
  () => {
    loadFilmRankVideos()
  },
  { immediate: true }
)

async function loadFilmRankVideos() {
  const requestId = ++filmRankRequestId
  filmRankVideos.value = []
  if (!isFilm.value || !props.category?.id) return

  filmRankLoading.value = true
  const collected: Video[] = []
  let total = 0

  try {
    for (let page = 0; page < FILM_MAX_PAGES; page++) {
      const res = await videoApi.list({
        category_id: props.category.id,
        platform: props.platform || undefined,
        time_window: props.timeWindow || undefined,
        sort: props.sortBy,
        limit: FILM_PAGE_SIZE,
        offset: page * FILM_PAGE_SIZE
      })

      if (requestId !== filmRankRequestId) return

      total = res.total
      collected.push(...res.data)
      filmRankVideos.value = collected

      if (hasEnoughFilmSections(collected) || collected.length >= total || res.data.length === 0) {
        break
      }
    }
  } catch {
    if (requestId === filmRankRequestId) {
      filmRankVideos.value = props.videos
    }
  } finally {
    if (requestId === filmRankRequestId) {
      filmRankLoading.value = false
    }
  }
}

function hasEnoughFilmSections(videos: Video[]) {
  const ranked = [...videos].sort((a, b) => getFilmRankScore(b) - getFilmRankScore(a))
  const domesticCount = ranked.filter(
    (video) =>
      !matchesFilmKeywords(video, overseasStreamingKeywords) &&
      matchesFilmKeywords(video, domesticDramaKeywords)
  ).length
  const overseasCount = ranked.filter((video) =>
    matchesFilmKeywords(video, overseasStreamingKeywords)
  ).length
  return domesticCount >= FILM_SECTION_LIMIT && overseasCount >= FILM_SECTION_LIMIT
}

function matchesFilmKeywords(video: Video, keywords: string[]) {
  const text = [video.title, video.author_name || '', ...(video.tags || [])].join(' ').toLowerCase()
  return keywords.some((keyword) => text.includes(keyword.toLowerCase()))
}

function getFilmRankScore(video: Video) {
  return (
    (video.heat_score || 0) +
    video.comment_count * 0.08 +
    video.like_count * 0.002 +
    video.share_count * 0.04
  )
}

function formatFilmScore(video: Video) {
  return (filmScoreMap.value.get(video.id) ?? 0).toString()
}

function getFilmScoreTone(video: Video) {
  const score = Number(formatFilmScore(video))
  if (score >= 80) return 'fresh'
  if (score >= 60) return 'warm'
  return 'quiet'
}

function formatFilmMeta(video: Video) {
  const author = video.author_name || '匿名作者'
  const tags = video.tags?.slice(0, 2).join(' / ')
  const comments = `${formatNumber(video.comment_count)} 评论`
  return tags ? `${author} · ${tags} · ${comments}` : `${author} · ${comments}`
}

function getTitleInitial(title: string) {
  return title.trim().slice(0, 1) || '影'
}

function handlePosterError(event: Event) {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}
</script>

<style scoped>
.domain-home {
  min-height: 100%;
  padding: var(--spacing-xl);
  color: var(--text-primary);
}

.finance-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 360px);
  gap: var(--spacing-xl);
  align-items: stretch;
  padding: var(--spacing-xxl);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background:
    linear-gradient(135deg, rgba(0, 122, 255, 0.12), transparent 45%),
    linear-gradient(315deg, rgba(52, 199, 89, 0.12), transparent 42%), var(--bg-primary);
}

.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 640px;
}

.eyebrow {
  width: fit-content;
  margin-bottom: var(--spacing-md);
  padding: 5px 10px;
  border: 1px solid rgba(0, 122, 255, 0.24);
  border-radius: var(--radius-sm);
  color: var(--primary-color);
  font-size: 12px;
  font-weight: 600;
}

.hero-copy h1,
.fallback-home h1 {
  margin: 0;
  font-size: 36px;
  line-height: 1.12;
  font-weight: 700;
  letter-spacing: 0;
}

.hero-copy p,
.fallback-home p {
  margin: var(--spacing-lg) 0 0;
  max-width: 560px;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.8;
}

.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.topic-tags span {
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  background-color: rgba(0, 122, 255, 0.1);
  color: var(--primary-color);
  font-size: 12px;
  font-weight: 600;
}

.market-panel {
  display: flex;
  flex-direction: column;
  min-height: 220px;
  padding: var(--spacing-lg);
  border: 1px solid rgba(0, 122, 255, 0.18);
  border-radius: var(--radius-md);
  background-color: color-mix(in srgb, var(--bg-primary) 82%, var(--bg-secondary));
  box-shadow: 0 16px 44px rgba(0, 0, 0, 0.08);
}

.market-header,
.market-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.market-header strong {
  color: var(--success-color);
  font-size: 32px;
  line-height: 1;
}

.market-chart {
  position: relative;
  flex: 1;
  margin: var(--spacing-lg) 0;
  overflow: hidden;
  border-radius: var(--radius-sm);
  background:
    linear-gradient(to right, rgba(134, 134, 139, 0.14) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(134, 134, 139, 0.14) 1px, transparent 1px);
  background-size: 25% 50%;
}

.grid-line,
.trend-line,
.trend-dot {
  position: absolute;
  display: block;
}

.grid-line {
  left: 0;
  right: 0;
  height: 1px;
  background-color: rgba(134, 134, 139, 0.18);
}

.line-a {
  top: 34%;
}

.line-b {
  top: 68%;
}

.trend-line {
  left: 8%;
  right: 8%;
  top: 52%;
  height: 42%;
  border-top: 3px solid var(--success-color);
  border-right: 3px solid var(--success-color);
  transform: skewY(-13deg);
  transform-origin: left center;
}

.trend-dot {
  width: 10px;
  height: 10px;
  border: 2px solid var(--bg-primary);
  border-radius: 50%;
  background-color: var(--success-color);
  box-shadow: 0 0 0 4px rgba(52, 199, 89, 0.16);
}

.dot-a {
  left: 12%;
  bottom: 28%;
}

.dot-b {
  left: 52%;
  bottom: 46%;
}

.dot-c {
  right: 10%;
  top: 16%;
}

.finance-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.metric-card,
.insight-panel,
.strategy-panel,
.recommend-panel {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
}

.metric-card {
  padding: var(--spacing-lg);
}

.metric-topline {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-secondary);
  font-size: 13px;
}

.metric-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.metric-icon.blue {
  background-color: var(--primary-color);
}

.metric-icon.green {
  background-color: var(--success-color);
}

.metric-icon.orange {
  background-color: var(--warning-color);
}

.metric-card strong {
  display: block;
  margin-top: var(--spacing-lg);
  font-size: 24px;
  line-height: 1;
}

.metric-card p {
  margin: var(--spacing-sm) 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(280px, 0.92fr);
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.insight-panel,
.strategy-panel,
.recommend-panel {
  padding: var(--spacing-xl);
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  font-size: 16px;
  font-weight: 600;
}

.section-heading small {
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 500;
}

.radar-list,
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.radar-item,
.strategy-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
}

.radar-index {
  flex: 0 0 auto;
  color: var(--primary-color);
  font-size: 12px;
  font-weight: 700;
}

.radar-item h3,
.strategy-item h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.radar-item p,
.strategy-item p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.check-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: rgba(52, 199, 89, 0.14);
  color: var(--success-color);
  font-size: 13px;
  font-weight: 700;
}

.recommend-panel {
  margin-top: var(--spacing-lg);
}

.recommend-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.recommend-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  min-height: 96px;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    transform var(--transition-fast);
}

.recommend-item:hover {
  border-color: var(--primary-color);
  transform: translateY(-1px);
}

.recommend-title {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.recommend-meta {
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.5;
}

.film-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 420px);
  gap: var(--spacing-xl);
  align-items: stretch;
  padding: var(--spacing-xxl);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background:
    linear-gradient(135deg, rgba(255, 59, 48, 0.1), transparent 36%),
    linear-gradient(315deg, rgba(255, 204, 0, 0.13), transparent 42%), var(--bg-primary);
}

.film-eyebrow {
  border-color: rgba(255, 59, 48, 0.24);
  color: #d70015;
}

.film-copy p {
  max-width: 620px;
}

.film-nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.film-nav span {
  padding: 6px 11px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: color-mix(in srgb, var(--bg-primary) 70%, var(--bg-secondary));
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.film-scoreboard,
.film-rank-panel,
.film-watchlist {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-primary);
}

.film-scoreboard {
  padding: var(--spacing-lg);
  box-shadow: 0 16px 44px rgba(0, 0, 0, 0.08);
}

.scoreboard-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  color: var(--text-secondary);
  font-size: 13px;
}

.scoreboard-header strong {
  color: #d70015;
  font-size: 42px;
  line-height: 0.9;
}

.scoreboard-meter {
  position: relative;
  height: 10px;
  margin: var(--spacing-lg) 0;
  overflow: hidden;
  border-radius: 999px;
  background-color: var(--bg-secondary);
}

.meter-track,
.meter-fill {
  position: absolute;
  inset: 0;
}

.meter-fill {
  border-radius: inherit;
  background: linear-gradient(90deg, #ffcc00, #ff3b30);
}

.scoreboard-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.score-tile {
  min-height: 92px;
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
}

.score-tile span,
.score-tile small {
  display: block;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.4;
}

.score-tile strong {
  display: block;
  margin: 8px 0 4px;
  color: var(--text-primary);
  font-size: 22px;
  line-height: 1;
}

.film-rank-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: start;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.film-rank-panel {
  padding: var(--spacing-xl);
}

.film-section-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.film-section-header h2 {
  margin: 4px 0 0;
  color: var(--text-primary);
  font-size: 20px;
  line-height: 1.25;
  font-weight: 700;
}

.film-section-header small {
  max-width: 160px;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.5;
  text-align: right;
}

.section-kicker {
  color: #d70015;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
}

.film-rank-list {
  display: flex;
  flex-direction: column;
  max-height: 640px;
  overflow-y: auto;
  padding-right: var(--spacing-md);
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.film-rank-row {
  display: grid;
  grid-template-columns: 28px 54px minmax(0, 1fr) 52px;
  align-items: center;
  gap: var(--spacing-md);
  min-height: 78px;
  padding: var(--spacing-sm) 0;
  border: 0;
  border-top: 1px solid var(--border-color);
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.film-rank-row:hover .film-rank-copy strong {
  color: #d70015;
}

.film-rank-index {
  color: var(--text-tertiary);
  font-size: 18px;
  font-weight: 800;
  text-align: center;
}

.film-poster {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 72px;
  overflow: hidden;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-tertiary);
  font-size: 18px;
  font-weight: 700;
}

.film-poster-initial {
  color: inherit;
}

.film-poster img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.film-rank-copy {
  min-width: 0;
}

.film-rank-copy strong {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.45;
  transition: color var(--transition-fast);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.film-rank-copy small {
  display: block;
  overflow: hidden;
  margin-top: 6px;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.film-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border: 2px solid currentColor;
  border-radius: 50%;
  font-weight: 700;
}

.film-score strong {
  font-size: 17px;
  line-height: 1;
}

.film-score small {
  margin-top: 3px;
  font-size: 10px;
  line-height: 1;
}

.film-score.fresh {
  color: #d70015;
}

.film-score.warm {
  color: #ff9500;
}

.film-score.quiet {
  color: var(--text-tertiary);
}

.film-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 180px;
  padding: var(--spacing-lg);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
}

.film-empty strong {
  color: var(--text-primary);
  font-size: 15px;
}

.film-empty span {
  margin-top: var(--spacing-sm);
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

.film-watchlist {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-xl);
}

.watchlist-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.watchlist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  min-height: 64px;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.watchlist-item span {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.watchlist-item strong {
  flex: 0 0 auto;
  color: #d70015;
  font-size: 18px;
}

.fallback-home {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
  text-align: center;
}

.fallback-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  margin-bottom: var(--spacing-lg);
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 28px;
  font-weight: 700;
}

@media (max-width: 1080px) {
  .finance-hero,
  .film-hero,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .watchlist-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .domain-home {
    padding: var(--spacing-md);
  }

  .finance-hero {
    padding: var(--spacing-xl);
  }

  .film-hero,
  .film-rank-panel,
  .film-watchlist {
    padding: var(--spacing-lg);
  }

  .hero-copy h1,
  .fallback-home h1 {
    font-size: 28px;
  }

  .finance-metrics {
    grid-template-columns: 1fr;
  }

  .recommend-list {
    grid-template-columns: 1fr;
  }

  .scoreboard-grid,
  .film-rank-grid,
  .watchlist-row {
    grid-template-columns: 1fr;
  }

  .film-rank-row {
    grid-template-columns: 24px 46px minmax(0, 1fr) 46px;
    gap: var(--spacing-sm);
  }

  .film-rank-list {
    max-height: 520px;
  }

  .film-poster {
    width: 46px;
    height: 62px;
  }

  .film-score {
    width: 46px;
    height: 46px;
  }

  .market-panel {
    min-height: 190px;
  }
}
</style>
