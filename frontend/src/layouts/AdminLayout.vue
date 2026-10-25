<script setup lang="ts">
import { RouterView, useRoute, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const menus = [
  { path: '/admin', label: '📊 数据统计' },
  { path: '/admin/items', label: '✅ 信息审核' },
  { path: '/admin/users', label: '👥 用户管理' },
  { path: '/admin/claims', label: '📋 认领申请' },
  { path: '/admin/reports', label: '🚨 举报处理' },
  { path: '/admin/announcements', label: '📢 系统公告' },
  { path: '/admin/agent-logs', label: '🤖 Agent 日志' },
  { path: '/admin/logs', label: '🗂 操作日志' },
]

function activePath(path: string): boolean {
  if (path === '/admin') return route.path === '/admin'
  return route.path.startsWith(path)
}

function logout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="admin-shell">
    <el-aside width="220px" class="admin-aside">
      <div class="admin-aside__brand">🛡️ 管理后台</div>
      <el-menu :default-active="route.path" class="admin-aside__menu">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path" :class="{ 'is-active': activePath(m.path) }" @click="router.push(m.path)">
          {{ m.label }}
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="admin-header">
        <span>{{ menus.find((m) => activePath(m.path))?.label || '管理后台' }}</span>
        <div class="admin-header__right">
          <span>{{ userStore.user?.username }}（管理员）</span>
          <el-button size="small" text @click="router.push('/')">返回前台</el-button>
          <el-button size="small" text type="danger" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-shell {
  min-height: 100vh;
}
.admin-aside {
  background: var(--el-bg-color-page);
  border-right: 1px solid var(--el-border-color-light);
}
.admin-aside__brand {
  padding: 18px 16px;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.admin-aside__menu {
  border-right: none;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  font-weight: 600;
}
.admin-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.admin-main {
  background: var(--el-bg-color-page);
}
</style>
