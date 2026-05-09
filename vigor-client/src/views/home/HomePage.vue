<template>
  <div class="home-page">
    <TopNavBar
      :categories="categoryStore.categories"
      :active-category-id="categoryStore.activeCategoryId"
      @change-category="handleCategoryChange"
    />

    <div class="main-content" :class="{ 'mobile-detail': isMobile && videoStore.selectedVideo }">
      <div class="list-panel">
        <VideoList
          :videos="videoStore.videos"
          :loading="videoStore.loading"
          :selected-id="videoStore.selectedVideo?.id ?? null"
          :initial-platform="videoStore.currentPlatform"
          :initial-sort-by="videoStore.sortBy"
          :initial-time-window="videoStore.timeWindow"
          @select="handleVideoSelect"
          @change-sort="handleSortChange"
          @change-time-window="handleTimeWindowChange"
          @change-platform="handlePlatformChange"
        />
      </div>

      <div class="dashboard-panel">
        <div v-if="isMobile && videoStore.selectedVideo" class="mobile-back" @click="handleBack">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
          </svg>
          <span>返回列表</span>
        </div>
        <DataDashboard :video="videoStore.selectedVideo" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue'
import { useCategoryStore } from '@/stores/category'
import { useVideoStore } from '@/stores/video'
import TopNavBar from '@/components/common/TopNavBar.vue'
import VideoList from '@/components/video/VideoList.vue'
import DataDashboard from '@/components/dashboard/DataDashboard.vue'

const categoryStore = useCategoryStore()
const videoStore = useVideoStore()

const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

function handleCategoryChange(id: number) {
  categoryStore.setActiveCategory(id)
  videoStore.setCategoryId(id)
}

function handleVideoSelect(id: number) {
  videoStore.selectVideo(id)
}

function handleSortChange(sort: 'heat_score' | 'publish_time') {
  videoStore.setSortBy(sort)
}

function handleTimeWindowChange(window: '1d' | '3d' | '7d' | '15d' | '30d' | null) {
  videoStore.setTimeWindow(window)
}

function handlePlatformChange(platform: string | null) {
  videoStore.setPlatform(platform)
}

function handleBack() {
  videoStore.selectedVideo = null
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  await categoryStore.fetchCategories()
  // fetchCategories 后 activeCategoryId 已经是真实 ID,现在才设置
  if (categoryStore.activeCategoryId) {
    videoStore.setCategoryId(categoryStore.activeCategoryId)
  } else {
    // 如果没有领域,直接拉全部视频
    videoStore.fetchVideos()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.list-panel {
  flex: 0 0 40%;
  max-width: 500px;
  min-width: 320px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dashboard-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.mobile-back {
  display: none;
  align-items: center;
  gap: 4px;
  padding: var(--spacing-md);
  color: var(--primary-color);
  font-size: 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-primary);
}

@media (max-width: 768px) {
  .main-content {
    position: relative;
  }

  .list-panel {
    flex: 1;
    max-width: none;
    min-width: 0;
    width: 100%;
    border-right: none;
  }

  .dashboard-panel {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--bg-primary);
    transform: translateX(100%);
    transition: transform var(--transition-base);
  }

  .main-content.mobile-detail .list-panel {
    display: none;
  }

  .main-content.mobile-detail .dashboard-panel {
    transform: translateX(0);
  }

  .mobile-back {
    display: flex;
  }
}
</style>
