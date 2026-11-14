<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { getHandoverInfo, handoverMatch } from '@/api/matches'
import type { HandoverInfo } from '@/api/matches'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const info = ref<HandoverInfo | null>(null)
const loading = ref(true)
const error = ref('')
const submitting = ref(false)
const done = ref(false)

const matchId = Number(route.params.id)
const code = String(route.query.code || '')

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    router.replace(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    return
  }
  try {
    info.value = await getHandoverInfo(matchId, code)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = detail || '无法加载交接信息'
  } finally {
    loading.value = false
  }
})

async function confirmHandover() {
  if (!info.value?.code_valid) return
  submitting.value = true
  try {
    await handoverMatch(matchId, code)
    done.value = true
    ElMessage.success('交接完成，物品已标记为「已找回」')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '交接失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="handover-page" v-loading="loading">
    <el-result v-if="error" icon="warning" title="交接信息不可用" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="router.push('/')">返回首页</el-button>
      </template>
    </el-result>

    <el-result v-else-if="done" icon="success" title="交接完成" sub-title="物品已标记为「已找回」，感谢你的配合！">
      <template #extra>
        <el-button type="primary" @click="router.push('/items')">继续浏览</el-button>
        <el-button @click="router.push('/matches')">返回匹配</el-button>
      </template>
    </el-result>

    <template v-else-if="info">
      <div class="handover-page__head">
        <h1 class="handover-page__title"><span class="glow-text">扫码交接</span></h1>
        <p class="handover-page__sub">请双方当面确认物品无误，再点击「确认交接」</p>
      </div>

      <el-alert
        v-if="!info.code_valid"
        type="error"
        :closable="false"
        show-icon
        title="交接码无效"
        description="二维码可能已过期或链接不完整，请让对方向你重新出示交接码。"
        class="handover-page__alert"
      />

      <div class="handover-page__pair">
        <el-card shadow="never" class="handover-card">
          <template #header><span>🔍 失物信息</span></template>
          <el-image v-if="info.lost_item.images?.length" :src="info.lost_item.images[0]" fit="cover" class="handover-card__img" />
          <h3 class="handover-card__title">{{ info.lost_item.title }}</h3>
          <p class="handover-card__meta">{{ info.lost_item.category }} · {{ info.lost_item.location }}</p>
          <p class="handover-card__meta">发布者：{{ info.lost_item.username || '匿名' }}</p>
        </el-card>

        <div class="handover-page__link">
          <span class="handover-page__score">{{ info.match_score }}</span>
          <span class="handover-page__score-label">匹配分</span>
          <span class="handover-page__arrow">⇄</span>
        </div>

        <el-card shadow="never" class="handover-card">
          <template #header><span>🎯 招领信息</span></template>
          <el-image v-if="info.found_item.images?.length" :src="info.found_item.images[0]" fit="cover" class="handover-card__img" />
          <h3 class="handover-card__title">{{ info.found_item.title }}</h3>
          <p class="handover-card__meta">{{ info.found_item.category }} · {{ info.found_item.location }}</p>
          <p class="handover-card__meta">发布者：{{ info.found_item.username || '匿名' }}</p>
        </el-card>
      </div>

      <div class="handover-page__actions">
        <el-tag v-if="info.code_valid" type="success" effect="dark">交接码已核验 ✓</el-tag>
        <el-tag v-else type="danger" effect="dark">交接码不匹配</el-tag>
        <el-button
          type="success"
          size="large"
          class="glow-btn"
          :disabled="!info.code_valid"
          :loading="submitting"
          @click="confirmHandover"
        >
          确认完成交接
        </el-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.handover-page {
  max-width: 900px;
  margin: 0 auto;
}
.handover-page__head {
  margin-bottom: 18px;
}
.handover-page__title {
  margin: 0 0 6px;
  font-size: clamp(24px, 4vw, 34px);
}
.handover-page__sub {
  margin: 0;
  color: #8fb3d9;
  font-size: 13px;
}
.handover-page__alert {
  margin-bottom: 16px;
}
.handover-page__pair {
  display: flex;
  align-items: center;
  gap: 14px;
}
.handover-card {
  flex: 1;
  min-width: 0;
  background: rgba(8, 25, 43, 0.7);
}
.handover-card__img {
  width: 100%;
  height: 150px;
  border-radius: 8px;
  margin-bottom: 10px;
}
.handover-card__title {
  margin: 0 0 6px;
  font-size: 17px;
}
.handover-card__meta {
  margin: 2px 0;
  color: #8fb3d9;
  font-size: 13px;
}
.handover-page__link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 68px;
}
.handover-page__score {
  font-size: 24px;
  font-weight: 800;
  color: #00e5ff;
}
.handover-page__score-label {
  font-size: 11px;
  color: #8fb3d9;
}
.handover-page__arrow {
  font-size: 22px;
  color: #00e5ff;
}
.handover-page__actions {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
@media (max-width: 720px) {
  .handover-page__pair {
    flex-direction: column;
    align-items: stretch;
  }
  .handover-page__link {
    flex-direction: row;
  }
}
</style>
