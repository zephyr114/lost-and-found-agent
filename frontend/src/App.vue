<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-header__inner">
        <router-link to="/" class="app-logo">
          🔍 失物招领智能平台
        </router-link>
        <span class="app-tagline">Lost-and-Found Intelligent Platform</span>
      </div>
    </el-header>
    <el-main class="app-main">
      <RouterView />
    </el-main>
    <el-footer class="app-footer">
      Lost-and-Found Intelligent Platform · 第一阶段项目初始化
    </el-footer>
  </el-container>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}
.app-header {
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
}
.app-header__inner {
  width: 100%;
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.app-logo {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-color-primary);
  text-decoration: none;
}
.app-tagline {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.app-main {
  flex: 1;
}
.app-footer {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  padding: 12px;
}
</style>
