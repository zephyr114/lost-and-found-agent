<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { RouterView, useRouter } from 'vue-router'

import { getUnreadCount } from '@/api/messages'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()
const unread = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

async function refreshUnread() {
  if (!userStore.isLoggedIn) {
    unread.value = 0
    return
  }
  try {
    unread.value = await getUnreadCount()
  } catch {
    unread.value = 0
  }
}

watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) {
      refreshUnread()
      if (!timer) timer = setInterval(refreshUnread, 30000)
    } else {
      if (timer) {
        clearInterval(timer)
        timer = null
      }
      unread.value = 0
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function handleCommand(cmd: string) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'myItems') {
    router.push('/my/items')
  } else if (cmd === 'myClaims') {
    router.push('/my/claims')
  } else if (cmd === 'receivedClaims') {
    router.push('/my/claims/received')
  } else if (cmd === 'messages') {
    router.push('/messages')
  } else if (cmd === 'admin') {
    router.push('/admin/users')
  } else if (cmd === 'publishLost') {
    router.push('/publish/lost')
  } else if (cmd === 'publishFound') {
    router.push('/publish/found')
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
        <nav class="app-nav">
          <router-link to="/" class="app-nav__link">首页</router-link>
          <router-link to="/items?type=lost" class="app-nav__link">失物信息</router-link>
          <router-link to="/items?type=found" class="app-nav__link">招领信息</router-link>
          <router-link v-if="userStore.isLoggedIn" to="/matches" class="app-nav__link">智能匹配</router-link>
        </nav>
        <div class="app-header__right">
          <template v-if="userStore.isLoggedIn">
            <el-badge :value="unread" :hidden="unread === 0" :max="99" class="app-header__msg">
              <el-button text @click="router.push('/messages')">💬 消息</el-button>
            </el-badge>
            <el-dropdown @command="handleCommand">
              <el-button type="primary" plain size="small">＋ 发布</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="publishLost">发布失物</el-dropdown-item>
                  <el-dropdown-item command="publishFound">发布招领</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
                  <el-dropdown-item command="myItems">我的发布</el-dropdown-item>
                  <el-dropdown-item command="myClaims">我的认领申请</el-dropdown-item>
                  <el-dropdown-item command="receivedClaims">收到的认领申请</el-dropdown-item>
                  <el-dropdown-item command="messages">消息中心</el-dropdown-item>
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
              <el-button type="primary" size="small">注册</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </el-header>
    <el-main class="app-main">
      <RouterView />
    </el-main>
    <el-footer class="app-footer">
      Lost-and-Found Intelligent Platform · 第五阶段：智能 Agent
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
  gap: 16px;
}
.app-logo {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-color-primary);
  text-decoration: none;
  white-space: nowrap;
}
.app-nav {
  display: flex;
  gap: 14px;
}
.app-nav__link {
  color: var(--el-text-color-regular);
  text-decoration: none;
  font-size: 14px;
}
.app-nav__link:hover {
  color: var(--el-color-primary);
}
.app-header__right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
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
