<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getHealth } from '@/api/health'
import type { HealthInfo } from '@/api/health'
import { getActiveAnnouncements } from '@/api/announcements'
import type { Announcement } from '@/api/admin'
import { getItems } from '@/api/items'
import type { Item } from '@/api/items'
import { getOverview } from '@/api/stats'
import type { Overview } from '@/api/stats'
import { useUserStore } from '@/stores/user'
import ItemCard from '@/components/ItemCard.vue'
import NumberRoll from '@/components/NumberRoll.vue'

type Status = 'loading' | 'ok' | 'degraded' | 'error'

const router = useRouter()
const userStore = useUserStore()

const status = ref<Status>('loading')
const health = ref<HealthInfo | null>(null)
const announcements = ref<Announcement[]>([])
const overview = ref<Overview | null>(null)
const latest = ref<Item[]>([])

onMounted(async () => {
  const [overviewRes, announcementsRes, healthRes, latestRes] = await Promise.allSettled([
    getOverview(),
    getActiveAnnouncements(),
    getHealth(),
    getItems({ sort: 'newest', page: 1, size: 4 }),
  ])
  if (overviewRes.status === 'fulfilled') overview.value = overviewRes.value
  if (announcementsRes.status === 'fulfilled') announcements.value = announcementsRes.value
  if (latestRes.status === 'fulfilled') latest.value = latestRes.value.items
  if (healthRes.status === 'fulfilled') {
    health.value = healthRes.value
    status.value = healthRes.value.status === 'ok' ? 'ok' : 'degraded'
  } else {
    status.value = 'error'
  }
})

const stats = computed(() => {
  const o = overview.value
  return [
    { label: '物品总数', value: o?.items_total ?? 0, color: '#00e5ff' },
    { label: '失物信息', value: o?.items_lost ?? 0, color: '#ff6b81' },
    { label: '招领信息', value: o?.items_found ?? 0, color: '#3ddc97' },
    { label: '匹配记录', value: o?.matches_total ?? 0, color: '#7c9cff' },
  ]
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
      <div class="hero__badge">
        <span class="hero__badge-dot" />
        HDU · 杭州电子科技大学
      </div>
      <h1 class="hero__title">
        <span class="glow-text">智能失物招领</span>
      </h1>
      <p class="hero__subtitle">让每一件失物，都能找到回家的路</p>
      <div class="hero__actions">
        <el-button type="primary" size="large" class="glow-btn" @click="router.push('/publish/lost')">
          发布失物
        </el-button>
        <el-button size="large" plain class="hero__secondary" @click="router.push('/publish/found')">
          发布招领
        </el-button>
        <el-button size="large" text @click="router.push('/stats')">📊 查看数据看板 →</el-button>
      </div>

      <div class="stats-strip">
        <div v-for="s in stats" :key="s.label" class="stats-strip__item">
          <div class="stats-strip__value" :style="{ color: s.color }">
            <NumberRoll :value="s.value" />
          </div>
          <div class="stats-strip__label">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <section class="latest">
      <div class="section-title">
        <span>最新发布</span>
        <router-link to="/items" class="latest__more">查看全部 →</router-link>
      </div>
      <div v-if="latest.length" class="latest__grid">
        <ItemCard v-for="item in latest" :key="item.id" :item="item" />
      </div>
      <el-empty v-else description="还没有已审核的物品，发布第一条吧" />
    </section>

    <section class="features">
      <div class="section-title"><span>功能入口</span></div>
      <div class="features__grid">
        <div v-for="f in features" :key="f.title" class="feature glass" @click="open(f.path)">
          <div class="feature__icon">{{ f.icon }}</div>
          <h3 class="feature__title">{{ f.title }}</h3>
          <p class="feature__desc">{{ f.desc }}</p>
          <span class="feature__arrow">→</span>
        </div>
      </div>
    </section>

    <section class="flow-section">
      <div class="section-title"><span>匹配流程</span></div>
      <div class="flow glass">
        <div class="flow__step">
          <div class="flow__icon">📝</div>
          <div class="flow__label">发布失物</div>
          <div class="flow__desc">描述物品特征与地点</div>
        </div>
        <div class="flow__arrow"><span class="flow__dot" /></div>
        <div class="flow__step flow__step--ai">
          <div class="flow__icon">🤖</div>
          <div class="flow__label">AI 智能匹配</div>
          <div class="flow__desc">多维打分 · 生成理由</div>
        </div>
        <div class="flow__arrow"><span class="flow__dot flow__dot--delay" /></div>
        <div class="flow__step">
          <div class="flow__icon">🎯</div>
          <div class="flow__label">找到招领</div>
          <div class="flow__desc">确认匹配 · 联系拾获者</div>
        </div>
      </div>
    </section>

    <el-card v-if="announcements.length" class="home-card" shadow="never">
      <template #header><span>📢 系统公告</span></template>
      <div v-for="a in announcements" :key="a.id" class="announcement">
        <div class="announcement__title">{{ a.title }}</div>
        <div class="announcement__content">{{ a.content }}</div>
        <div class="announcement__time">{{ new Date(a.created_at).toLocaleString('zh-CN') }}</div>
      </div>
    </el-card>

    <el-card class="home-card" shadow="never">
      <template #header><span>系统状态</span></template>
      <el-skeleton v-if="status === 'loading'" :rows="2" animated />
      <el-alert
        v-else-if="status === 'error'"
        type="error"
        title="无法连接后端服务"
        description="请确认后端已启动：cd backend && uvicorn app.main:app --reload"
        show-icon
        :closable="false"
      />
      <div v-else class="status-row">
        <el-tag :type="status === 'ok' ? 'success' : 'warning'">服务 {{ health?.status }}</el-tag>
        <el-tag type="info">数据库 {{ health?.database }}</el-tag>
        <el-tag type="info">版本 v{{ health?.version }}</el-tag>
        <span class="status-row__time">检查时间 {{ health?.time }}</span>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.home {
  max-width: 1120px;
  margin: 0 auto;
}

/* ---- Hero ---- */
.hero {
  text-align: center;
  padding: 56px 16px 36px;
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(0, 229, 255, 0.3);
  background: rgba(0, 229, 255, 0.07);
  color: #9fe8ff;
  font-size: 13px;
  letter-spacing: 0.04em;
}

.hero__badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #00e5ff;
  box-shadow: 0 0 10px #00e5ff;
  animation: pulse 1.8s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(0.8); }
}

.hero__title {
  font-size: clamp(32px, 5vw, 54px);
  margin: 18px 0 10px;
  letter-spacing: 0.04em;
  font-weight: 800;
}

.hero__subtitle {
  color: #8fb3d9;
  font-size: clamp(14px, 1.6vw, 17px);
  margin: 0 0 26px;
}

.hero__actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
}

.hero__secondary {
  --el-button-bg-color: rgba(0, 229, 255, 0.06);
  --el-button-border-color: rgba(0, 229, 255, 0.35);
  --el-button-text-color: #9fe8ff;
}

/* ---- 数据条 ---- */
.stats-strip {
  margin: 40px auto 0;
  max-width: 760px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.stats-strip__item {
  padding: 16px 10px;
  border-radius: 14px;
  border: 1px solid rgba(0, 229, 255, 0.14);
  background: rgba(255, 255, 255, 0.035);
  backdrop-filter: blur(10px);
  transition: border-color 0.25s, box-shadow 0.25s;
}

.stats-strip__item:hover {
  border-color: rgba(0, 229, 255, 0.45);
  box-shadow: 0 0 20px rgba(0, 229, 255, 0.18);
}

.stats-strip__value {
  font-size: 26px;
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 0 18px currentColor;
}

.stats-strip__label {
  margin-top: 4px;
  font-size: 12px;
  color: #8fb3d9;
}

/* ---- 区块标题 ---- */
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 34px 4px 16px;
  color: #cfe6ff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, #00e5ff, #005bac);
  box-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
}

/* ---- 最新发布 ---- */
.latest__more {
  margin-left: auto;
  color: #00e5ff;
  font-size: 13px;
  text-decoration: none;
  letter-spacing: 0.02em;
}

.latest__more:hover {
  text-shadow: 0 0 12px rgba(0, 229, 255, 0.5);
}

.latest__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .latest__grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 560px) {
  .latest__grid {
    grid-template-columns: 1fr;
  }
}

/* ---- 功能卡 ---- */
.features__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.feature {
  position: relative;
  padding: 22px 18px;
  cursor: pointer;
  overflow: hidden;
}

.feature::before {
  content: '';
  position: absolute;
  inset: -40% -60% auto auto;
  width: 160px;
  height: 160px;
  background: radial-gradient(circle, rgba(0, 229, 255, 0.18), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s;
}

.feature:hover::before {
  opacity: 1;
}

.feature__icon {
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 24px;
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.16), rgba(0, 91, 172, 0.24));
  border: 1px solid rgba(0, 229, 255, 0.22);
  margin-bottom: 14px;
}

.feature__title {
  margin: 0 0 6px;
  font-size: 15px;
  color: #e8f3ff;
}

.feature__desc {
  margin: 0;
  font-size: 13px;
  color: #8fb3d9;
  line-height: 1.6;
}

.feature__arrow {
  position: absolute;
  right: 16px;
  bottom: 14px;
  color: #00e5ff;
  opacity: 0.5;
  transition: transform 0.25s, opacity 0.25s;
}

.feature:hover .feature__arrow {
  opacity: 1;
  transform: translateX(4px);
}

/* ---- 匹配流程 ---- */
.flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 30px 22px;
}

.flow__step {
  flex: 0 1 220px;
  text-align: center;
  padding: 18px 12px;
  border-radius: 14px;
  border: 1px solid rgba(0, 229, 255, 0.14);
  background: rgba(255, 255, 255, 0.03);
}

.flow__step--ai {
  border-color: rgba(0, 229, 255, 0.5);
  box-shadow: 0 0 26px rgba(0, 229, 255, 0.16);
  animation: aiGlow 2.6s ease-in-out infinite;
}

@keyframes aiGlow {
  0%, 100% { box-shadow: 0 0 18px rgba(0, 229, 255, 0.12); }
  50% { box-shadow: 0 0 34px rgba(0, 229, 255, 0.32); }
}

.flow__icon {
  font-size: 30px;
  margin-bottom: 8px;
}

.flow__label {
  font-size: 15px;
  font-weight: 700;
  color: #e8f3ff;
  margin-bottom: 4px;
}

.flow__desc {
  font-size: 12px;
  color: #8fb3d9;
}

.flow__arrow {
  position: relative;
  width: 84px;
  height: 2px;
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.08), rgba(0, 229, 255, 0.55), rgba(0, 229, 255, 0.08));
  border-radius: 2px;
}

.flow__dot {
  position: absolute;
  top: -3px;
  left: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00e5ff;
  box-shadow: 0 0 12px #00e5ff;
  animation: flowMove 2.6s linear infinite;
}

.flow__dot--delay {
  animation-delay: 1.3s;
}

@keyframes flowMove {
  from { left: 0; }
  to { left: calc(100% - 8px); }
}

/* ---- 公告 / 状态 ---- */
.home-card {
  margin-top: 22px;
}

.announcement {
  padding: 10px 0;
  border-bottom: 1px dashed rgba(0, 229, 255, 0.1);
}

.announcement:last-child {
  border-bottom: none;
}

.announcement__title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #e8f3ff;
}

.announcement__content {
  font-size: 13px;
  color: #b9d4f0;
  white-space: pre-wrap;
}

.announcement__time {
  margin-top: 4px;
  font-size: 12px;
  color: #6f8cb0;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-row__time {
  color: #6f8cb0;
  font-size: 12px;
}

/* ---- 响应式 ---- */
@media (max-width: 860px) {
  .features__grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .flow {
    flex-direction: column;
    gap: 12px;
  }
  .flow__arrow {
    width: 2px;
    height: 44px;
    background: linear-gradient(180deg, rgba(0, 229, 255, 0.08), rgba(0, 229, 255, 0.55), rgba(0, 229, 255, 0.08));
  }
  .flow__dot {
    left: -3px;
    top: 0;
    animation: flowDown 2.6s linear infinite;
  }
  .flow__dot--delay {
    animation-delay: 1.3s;
  }
  @keyframes flowDown {
    from { top: 0; }
    to { top: calc(100% - 8px); }
  }
}

@media (max-width: 560px) {
  .stats-strip {
    grid-template-columns: repeat(2, 1fr);
  }
  .hero {
    padding: 36px 8px 24px;
  }
  .hero__actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
