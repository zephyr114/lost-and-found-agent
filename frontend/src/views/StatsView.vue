<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getOverview } from '@/api/stats'
import type { Overview } from '@/api/stats'
import NumberRoll from '@/components/NumberRoll.vue'

const router = useRouter()
const overview = ref<Overview | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    overview.value = await getOverview()
  } finally {
    loading.value = false
  }
})

const cards = computed(() => {
  const o = overview.value
  return [
    { label: '物品总数', value: o?.items_total ?? 0, icon: '📦', color: '#00e5ff' },
    { label: '失物信息', value: o?.items_lost ?? 0, icon: '🔍', color: '#ff6b81' },
    { label: '招领信息', value: o?.items_found ?? 0, icon: '🎯', color: '#3ddc97' },
    { label: '认领申请', value: o?.claims_total ?? 0, icon: '🤝', color: '#00b8ff' },
    { label: '匹配记录', value: o?.matches_total ?? 0, icon: '🤖', color: '#7c9cff' },
    { label: '确认匹配', value: o?.matches_confirmed ?? 0, icon: '✅', color: '#ffb020' },
    { label: '已认领物品', value: o?.items_claimed ?? 0, icon: '🏷️', color: '#ff8f6b' },
    { label: '活跃用户', value: o?.users_total ?? 0, icon: '👥', color: '#b58cff' },
  ]
})

const maxValue = computed(() => {
  const o = overview.value
  if (!o) return 1
  return Math.max(o.items_lost, o.items_found, o.claims_total, o.matches_total, o.users_total, 1)
})

const bars = computed(() => {
  const o = overview.value
  if (!o) return []
  return [
    { label: '失物信息', value: o.items_lost, color: '#ff6b81' },
    { label: '招领信息', value: o.items_found, color: '#3ddc97' },
    { label: '认领申请', value: o.claims_total, color: '#00b8ff' },
    { label: '匹配记录', value: o.matches_total, color: '#7c9cff' },
    { label: '活跃用户', value: o.users_total, color: '#ffb020' },
  ]
})

const lostPct = computed(() => {
  const o = overview.value
  if (!o) return 0
  const total = o.items_lost + o.items_found || 1
  return Math.round((o.items_lost / total) * 100)
})

const donutStyle = computed(() => ({
  background: `conic-gradient(#ff6b81 0 ${lostPct.value}%, #3ddc97 ${lostPct.value}% 100%)`,
}))
</script>

<template>
  <div class="stats-page">
    <div class="stats-page__head">
      <div>
        <h1 class="stats-page__title"><span class="glow-text">数据看板</span></h1>
        <p class="stats-page__sub">实时统计 · 杭州电子科技大学智能失物招领</p>
      </div>
      <el-button text @click="router.push('/')">← 返回首页</el-button>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated class="glass stats-page__skeleton" />

    <template v-else>
      <div class="stat-cards">
        <div v-for="c in cards" :key="c.label" class="stat-card glass">
          <div class="stat-card__icon">{{ c.icon }}</div>
          <div class="stat-card__value" :style="{ color: c.color }">
            <NumberRoll :value="c.value" />
          </div>
          <div class="stat-card__label">{{ c.label }}</div>
        </div>
      </div>

      <div class="charts">
        <div class="chart-card glass">
          <h3 class="chart-card__title">失物 / 招领占比</h3>
          <div class="donut-wrap">
            <div class="donut" :style="donutStyle">
              <div class="donut__hole">
                <span class="donut__value">{{ lostPct }}%</span>
                <span class="donut__label">失物占比</span>
              </div>
            </div>
            <div class="donut-legend">
              <div class="donut-legend__item">
                <i class="dot" style="background: #ff6b81" />
                失物 {{ overview?.items_lost ?? 0 }} 条
              </div>
              <div class="donut-legend__item">
                <i class="dot" style="background: #3ddc97" />
                招领 {{ overview?.items_found ?? 0 }} 条
              </div>
            </div>
          </div>
        </div>

        <div class="chart-card glass">
          <h3 class="chart-card__title">核心数据对比</h3>
          <div class="bars">
            <div v-for="b in bars" :key="b.label" class="bar-row">
              <span class="bar-row__label">{{ b.label }}</span>
              <div class="bar-row__track">
                <div
                  class="bar-row__fill"
                  :style="{ width: `${Math.min((b.value / maxValue) * 100, 100)}%`, background: `linear-gradient(90deg, ${b.color}66, ${b.color})`, boxShadow: `0 0 12px ${b.color}66` }"
                />
              </div>
              <span class="bar-row__value">{{ b.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.stats-page {
  max-width: 1120px;
  margin: 0 auto;
}

.stats-page__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 22px;
}

.stats-page__title {
  font-size: clamp(26px, 4vw, 38px);
  margin: 0 0 6px;
  letter-spacing: 0.04em;
}

.stats-page__sub {
  margin: 0;
  color: #8fb3d9;
  font-size: 13px;
}

.stats-page__skeleton {
  padding: 22px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 18px 16px;
  text-align: center;
}

.stat-card__icon {
  font-size: 22px;
  margin-bottom: 8px;
  opacity: 0.9;
}

.stat-card__value {
  font-size: 30px;
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 0 20px currentColor;
}

.stat-card__label {
  margin-top: 4px;
  font-size: 12px;
  color: #8fb3d9;
}

.charts {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 16px;
}

.chart-card {
  padding: 20px;
}

.chart-card__title {
  margin: 0 0 18px;
  font-size: 15px;
  color: #cfe6ff;
  letter-spacing: 0.06em;
}

.donut-wrap {
  display: flex;
  align-items: center;
  gap: 26px;
  flex-wrap: wrap;
  justify-content: center;
}

.donut {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.12);
}

.donut__hole {
  width: 126px;
  height: 126px;
  border-radius: 50%;
  background: #081226;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(0, 229, 255, 0.18);
}

.donut__value {
  font-size: 26px;
  font-weight: 800;
  color: #e8f3ff;
}

.donut__label {
  font-size: 12px;
  color: #8fb3d9;
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
  color: #b9d4f0;
}

.donut-legend__item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-row__label {
  flex: 0 0 76px;
  font-size: 13px;
  color: #b9d4f0;
}

.bar-row__track {
  flex: 1;
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.bar-row__fill {
  height: 100%;
  border-radius: 999px;
  transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
}

.bar-row__value {
  flex: 0 0 44px;
  text-align: right;
  font-size: 13px;
  font-weight: 700;
  color: #e8f3ff;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 900px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .stats-page__head {
    flex-direction: column;
    align-items: flex-start;
  }
  .stat-card__value {
    font-size: 24px;
  }
}
</style>
