<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()

function handleCommand(cmd: string) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'admin') {
    router.push('/admin/users')
  } else if (cmd === 'logout') {
    userStore.logout()
    router.push('/')
  }
}
</script>

<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-header__inner">
        <router-link to="/" class="app-logo">
          🔍 失物招领智能平台
        </router-link>
        <span class="app-tagline">Lost-and-Found Intelligent Platform</span>
        <div class="app-header__right">
          <template v-if="userStore.isLoggedIn">
            <el-dropdown @command="handleCommand">
              <span class="user-chip">
                {{ userStore.user?.username }}
                <el-tag v-if="userStore.isAdmin" size="small" type="warning" class="user-chip__tag">
                  管理员
                </el-tag>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item v-if="userStore.isAdmin" command="admin">管理后台</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <router-link to="/login">
              <el-button text type="primary">登录</el-button>
            </router-link>
            <router-link to="/register">
              <el-button type="primary">注册</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </el-header>
    <el-main class="app-main">
      <RouterView />
    </el-main>
    <el-footer class="app-footer">
      Lost-and-Found Intelligent Platform · 第二阶段：用户系统
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
  align-items: center;
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
.app-header__right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--el-text-color-primary);
  font-size: 14px;
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
