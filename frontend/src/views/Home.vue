<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getHealth } from '@/api/health'
import type { HealthInfo } from '@/api/health'
import { getActiveAnnouncements } from '@/api/announcements'
import type { Announcement } from '@/api/admin'
import { useUserStore } from '@/stores/user'

type Status = 'loading' | 'ok' | 'degraded' | 'error'

const router = useRouter()
const userStore = useUserStore()

const status = ref<Status>('loading')
const health = ref<HealthInfo | null>(null)
const announcements = ref<Announcement[]>([])

onMounted(async () => {
  try {
    health.value = await getHealth()
    status.value = health.value.status === 'ok' ? 'ok' : 'degraded'
  } catch {
    status.value = 'error'
  }
  try {
    announcements.value = await getActiveAnnouncements()
  } catch {
    announcements.value = []
  }
})

const features = [
  { icon: '📝', title: '发布失物 / 招领', desc: '填写丢失或捡到物品的详细信息', path: '/publish/lost' },
  { icon: '🔍', title: '物品搜索', desc: '按关键词、类别、地点和时间筛选', path: '/items' },
  { icon: '🤖', title: '智能匹配', desc: 'AI Agent 自动推荐可能匹配的物品', path: '/matches' },
  { icon: '🛡️', title: '审核管理', desc: '管理员审核信息、处理举报', path: '/admin' },
]

function open(path: string) {
  if (path.startsWith('/admin') && !userStore.isAdmin) {
    router.push('/login')
    return
  }
  router.push(path)
}
</script>

<template>
  <div class="home">
    <section class="hero">
      <h1 class="hero__title">失物招领智能平台</h1>
      <p class="hero__subtitle">Lost-and-Found Intelligent Platform · 让每一件失物早日回家</p>
    </section>

    <el-row :gutter="16" class="features">
      <el-col v-for="f in features" :key="f.title" :xs="12" :sm="6">
        <el-card class="feature-card" shadow="hover" @click="open(f.path)">
          <div class="feature-card__icon">{{ f.icon }}</div>
          <h3 class="feature-card__title">{{ f.title }}</h3>
          <p class="feature-card__desc">{{ f.desc }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="announcements.length" class="home-card" shadow="never">
      <template #header><span>📢 系统公告</span></template>
      <div v-for="a in announcements" :key="a.id" class="announcement">
        <div class="announcement__title">· {{ a.title }}</div>
        <div class="announcement__content">{{ a.content }}</div>
        <div class="announcement__time">{{ new Date(a.created_at).toLocaleString('zh-CN') }}</div>
      </div>
    </el-card>

    <el-card class="home-card" shadow="never">
      <template #header>
        <span>系统状态（后端 /health 健康检查）</span>
      </template>

      <el-skeleton v-if="status === 'loading'" :rows="2" animated />

      <el-alert
        v-else-if="status === 'error'"
        type="error"
        title="无法连接后端服务"
        description="请确认后端已启动：cd backend && uvicorn app.main:app --reload（默认 8000 端口）"
        show-icon
        :closable="false"
      />

      <el-descriptions v-else :column="2" border>
        <el-descriptions-item label="服务状态">
          <el-tag :type="status === 'ok' ? 'success' : 'warning'">{{ health?.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据库">{{ health?.database }}</el-descriptions-item>
        <el-descriptions-item label="服务名称">{{ health?.service }}</el-descriptions-item>
        <el-descriptions-item label="版本">v{{ health?.version }}</el-descriptions-item>
        <el-descriptions-item label="运行环境">{{ health?.environment }}</el-descriptions-item>
        <el-descriptions-item label="检查时间">{{ health?.time }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.home {
  max-width: 1080px;
  margin: 0 auto;
}
.hero {
  text-align: center;
  padding: 48px 16px 32px;
}
.hero__title {
  font-size: 36px;
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
}
.hero__subtitle {
  color: var(--el-text-color-secondary);
  margin: 0;
}
.features {
  margin-bottom: 24px;
}
.feature-card {
  text-align: center;
  height: 100%;
  margin-bottom: 16px;
  cursor: pointer;
}
.feature-card__icon {
  font-size: 40px;
  margin-bottom: 8px;
}
.feature-card__title {
  margin: 0 0 8px;
  font-size: 15px;
}
.feature-card__desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin: 0;
}
.home-card {
  margin-bottom: 24px;
}
.announcement {
  padding: 10px 0;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}
.announcement:last-child {
  border-bottom: none;
}
.announcement__title {
  font-weight: 600;
  margin-bottom: 4px;
}
.announcement__content {
  font-size: 13px;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
}
.announcement__time {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
