<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { getUnreadCount } from '@/api/messages'
import { useUserStore } from '@/stores/user'
import ParticleBackground from '@/components/ParticleBackground.vue'

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
  const map: Record<string, string> = {
    profile: '/profile',
    myItems: '/my/items',
    myClaims: '/my/claims',
    receivedClaims: '/my/claims/received',
    messages: '/messages',
    admin: '/admin',
    publishLost: '/publish/lost',
    publishFound: '/publish/found',
  }
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/')
    return
  }
  if (map[cmd]) router.push(map[cmd])
}
</script>

<template>
  <div class="app-shell">
    <ParticleBackground />
    <div class="hdu-watermark" aria-hidden="true">HDU</div>

    <header class="app-header">
      <div class="app-header__inner">
        <router-link to="/" class="app-logo">
          <span class="hdu-badge">HDU</span>
          <span class="app-logo__text">杭州电子科技大学 <em class="app-logo__dot">·</em> 智能失物招领</span>
        </router-link>

        <nav class="app-nav">
          <router-link to="/" class="app-nav__link">首页</router-link>
          <router-link to="/items?type=lost" class="app-nav__link">失物信息</router-link>
          <router-link to="/items?type=found" class="app-nav__link">招领信息</router-link>
          <router-link to="/stats" class="app-nav__link">数据看板</router-link>
          <router-link v-if="userStore.isLoggedIn" to="/matches" class="app-nav__link">智能匹配</router-link>
        </nav>

        <div class="app-header__right">
          <template v-if="userStore.isLoggedIn">
            <el-badge :value="unread" :hidden="unread === 0" :max="99">
              <el-button text class="msg-btn" @click="router.push('/messages')">💬 <span class="hide-sm">消息</span></el-button>
            </el-badge>
            <el-dropdown @command="handleCommand">
              <el-button type="primary" size="small" class="glow-btn">＋ 发布</el-button>
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
                <el-tag v-if="userStore.isAdmin" size="small" type="warning">管理员</el-tag>
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
              <el-button type="primary" size="small" class="glow-btn">注册</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </header>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <footer class="app-footer">
      <div class="app-footer__motto">笃学 · 力行 · 守正 · 求新</div>
      <div class="app-footer__copy">© 2026 杭州电子科技大学 · 智能失物招领 · Lost-and-Found Intelligent Platform</div>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.bg-grid {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(0, 229, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 229, 255, 0.035) 1px, transparent 1px);
  background-size: 96px 96px;
  mask-image: radial-gradient(ellipse at 50% 0%, #000 30%, transparent 75%);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid rgba(0, 229, 255, 0.14);
  background: rgba(5, 10, 20, 0.72);
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
}

.app-header__inner {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 18px;
}

.app-logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  white-space: nowrap;
}

.hdu-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #001018;
  background: linear-gradient(135deg, #00e5ff, #0088ff 70%, #005bac);
  box-shadow: 0 0 18px rgba(0, 229, 255, 0.45);
}

.app-logo__text {
  font-size: 15px;
  font-weight: 700;
  color: #e8f3ff;
}

.app-logo__dot {
  color: #00e5ff;
  font-style: normal;
  margin: 0 2px;
}

.app-nav {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.app-nav::-webkit-scrollbar {
  display: none;
}

.app-nav__link {
  position: relative;
  padding: 6px 12px;
  border-radius: 8px;
  color: #8fb3d9;
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
  transition: color 0.2s, background 0.2s;
}

.app-nav__link:hover {
  color: #00e5ff;
  background: rgba(0, 229, 255, 0.08);
}

.app-nav__link.router-link-exact-active {
  color: #00e5ff;
  background: rgba(0, 229, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(0, 229, 255, 0.28);
}

.app-header__right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.msg-btn {
  color: #b9d4f0;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(0, 229, 255, 0.22);
  background: rgba(0, 229, 255, 0.06);
  color: #e8f3ff;
  font-size: 13px;
  cursor: pointer;
}

.app-main {
  position: relative;
  z-index: 1;
  flex: 1;
  width: 100%;
  padding: 24px 20px 40px;
}

.app-footer {
  position: relative;
  z-index: 1;
  padding: 18px 20px 26px;
  text-align: center;
  border-top: 1px solid rgba(0, 229, 255, 0.1);
  background: rgba(5, 10, 20, 0.6);
  backdrop-filter: blur(12px);
}

.app-footer__motto {
  font-size: 14px;
  letter-spacing: 0.28em;
  color: #00e5ff;
  text-shadow: 0 0 16px rgba(0, 229, 255, 0.35);
  margin-bottom: 6px;
}

.app-footer__copy {
  font-size: 12px;
  color: #6f8cb0;
}

@media (max-width: 860px) {
  .app-header__inner {
    padding: 8px 12px;
    gap: 10px;
    flex-wrap: wrap;
  }
  .app-nav {
    order: 3;
    width: 100%;
  }
  .app-logo__text {
    font-size: 13px;
  }
  .hdu-badge {
    width: 32px;
    height: 32px;
    font-size: 11px;
  }
  .app-main {
    padding: 16px 12px 32px;
  }
}

@media (max-width: 480px) {
  .app-logo__text {
    max-width: 190px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .app-footer__motto {
    letter-spacing: 0.18em;
  }
}
</style>
