<template>
  <div class="login-page">
    <div class="login-card">
      <h1>Vigor Admin</h1>
      <p>管理员登录</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// Placeholder for admin login
</script>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
}

.login-card {
  background-color: var(--bg-primary);
  padding: 2rem;
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 16px var(--shadow);
  text-align: center;
  min-width: 320px;
}

h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

p {
  color: var(--text-secondary);
}
</style>
