<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { getItems } from '@/api/items'
import type { Item } from '@/api/items'
import { analyzeItem, confirmMatch, getRecommendations } from '@/api/matches'
import type { MatchInfo } from '@/api/matches'

const route = useRoute()
const router = useRouter()

const myItems = ref<Item[]>([])
const selectedId = ref<number | null>(null)
const matches = ref<MatchInfo[]>([])
const loading = ref(false)
const analyzing = ref(false)

const selectedItem = computed(() => myItems.value.find((i) => i.id === selectedId.value) || null)

function scoreColor(score: number): string {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#409eff'
  if (score >= 45) return '#e6a23c'
  return '#909399'
}

function scoreText(score: number): string {
  if (score >= 80) return '极可能匹配'
  if (score >= 60) return '很可能匹配'
  if (score >= 45) return '可能匹配'
  return '匹配度较低'
}

async function loadItems() {
  const res = await getItems({ mine: true, page: 1, size: 100 })
  myItems.value = res.items
  const fromRoute = Number(route.params.id)
  if (fromRoute && res.items.some((i) => i.id === fromRoute)) {
    selectedId.value = fromRoute
    await loadMatches()
  }
}

async function loadMatches() {
  if (!selectedId.value) {
    matches.value = []
    return
  }
  loading.value = true
  try {
    const res = await getRecommendations(selectedId.value)
    matches.value = res.items
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '加载匹配结果失败')
  } finally {
    loading.value = false
  }
}

async function onAnalyze() {
  if (!selectedId.value) return
  analyzing.value = true
  try {
    const res = await analyzeItem(selectedId.value)
    matches.value = res.items
    ElMessage.success(res.total > 0 ? `分析完成，发现 ${res.total} 条匹配` : '分析完成，暂无高匹配度信息')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '分析失败')
  } finally {
    analyzing.value = false
  }
}

function openItem(id: number) {
  router.push(`/items/${id}`)
}

const confirmingId = ref<number | null>(null)

async function onConfirm(m: MatchInfo) {
  confirmingId.value = m.id
  try {
    const updated = await confirmMatch(m.id)
    m.status = updated.status
    ElMessage.success('已确认！已通知拾获者，请尽快联系完成交接')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '确认失败')
  } finally {
    confirmingId.value = null
  }
}

onMounted(loadItems)
</script>

<template>
  <div class="matches-page">
    <el-card shadow="never">
      <template #header>
        <div class="matches-page__header">
          <span>🤖 智能匹配</span>
          <div class="matches-page__tools">
            <el-select v-model="selectedId" placeholder="选择我发布的物品" clearable style="width: 260px" @change="loadMatches">
              <el-option v-for="item in myItems" :key="item.id" :label="`[${item.item_type === 'lost' ? '失物' : '招领'}] ${item.title}`" :value="item.id" />
            </el-select>
            <el-button type="primary" :loading="analyzing" :disabled="!selectedId" @click="onAnalyze">立即分析</el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="selectedItem"
        type="info"
        :closable="false"
        show-icon
        class="matches-page__alert"
        :title="`正在分析「${selectedItem.title}」（${selectedItem.item_type === 'lost' ? '失物' : '招领'}），Agent 将综合类别、名称、颜色、品牌、时间、地点和特征计算匹配度`"
      />

      <div v-loading="loading || analyzing" class="matches-page__list">
        <el-empty v-if="!loading && !analyzing && matches.length === 0" description="暂无匹配结果，点击「立即分析」运行 Agent" />
        <div v-for="m in matches" :key="m.id || `${m.lost_item_id}-${m.found_item_id}`" class="match-card">
          <div class="match-card__main">
            <div class="match-card__item" @click="openItem(m.lost_item_id)">
              <el-tag size="small" type="danger">失物</el-tag>
              <span>{{ m.lost_title }}</span>
            </div>
            <div class="match-card__score" :style="{ color: scoreColor(m.match_score) }">
              <div class="match-card__score-num">{{ m.match_score }}</div>
              <div class="match-card__score-text">{{ scoreText(m.match_score) }}</div>
            </div>
            <div class="match-card__item" @click="openItem(m.found_item_id)">
              <el-tag size="small" type="success">招领</el-tag>
              <span>{{ m.found_title }}</span>
            </div>
          </div>
          <el-progress
            :percentage="Math.min(m.match_score, 100)"
            :color="scoreColor(m.match_score)"
            :stroke-width="8"
            :show-text="false"
          />
          <div class="match-card__reasons">
            <el-tag v-for="(reason, idx) in m.match_reason" :key="idx" size="small" type="info" effect="plain" class="match-card__reason">
              {{ reason }}
            </el-tag>
          </div>
          <div
            v-if="selectedItem && selectedItem.item_type === 'lost' && m.lost_item_id === selectedItem.id"
            class="match-card__confirm"
          >
            <el-tag v-if="m.status === 'confirmed'" type="success" effect="dark" size="small">
              ✅ 已确认是我的物品
            </el-tag>
            <el-button
              v-else-if="m.id > 0"
              type="success"
              size="small"
              class="glow-btn"
              :loading="confirmingId === m.id"
              @click="onConfirm(m)"
            >
              确认这是我的物品
            </el-button>
            <span v-else class="match-card__hint">运行「立即分析」保存匹配记录后可确认</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.matches-page {
  max-width: 900px;
  margin: 0 auto;
}
.matches-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.matches-page__tools {
  display: flex;
  gap: 10px;
}
.matches-page__alert {
  margin-bottom: 16px;
}
.match-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 14px;
}
.match-card__main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.match-card__item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 600;
}
.match-card__item:last-child {
  justify-content: flex-end;
  text-align: right;
}
.match-card__score {
  text-align: center;
  min-width: 90px;
}
.match-card__score-num {
  font-size: 26px;
  font-weight: 700;
}
.match-card__score-text {
  font-size: 12px;
}
.match-card__reasons {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.match-card__confirm {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
}
.match-card__hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
