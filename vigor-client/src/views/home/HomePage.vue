<template>
  <div class="home-page">
    <div class="content">
      <h1>Vigor 数据分析平台</h1>
      <p>正在开发中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useKeywordStore } from '@/stores/keyword'
import { useVideoStore } from '@/stores/video'

const keywordStore = useKeywordStore()
const videoStore = useVideoStore()

onMounted(() => {
  keywordStore.fetchKeywords()
  videoStore.fetchVideos()
})
</script>

<style scoped>
.home-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content {
  text-align: center;
}

h1 {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

p {
  color: var(--text-secondary);
}
</style>
