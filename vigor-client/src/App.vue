<template>
  <n-message-provider>
    <n-dialog-provider>
      <router-view />
    </n-dialog-provider>
  </n-message-provider>
</template>

<script setup lang="ts">
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { useThemeStore } from '@/stores/theme'

useThemeStore()
</script>

<style>
html,
body,
#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
