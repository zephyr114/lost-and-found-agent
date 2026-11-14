<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import QRCode from 'qrcode'

import { deleteImage, deleteItem, getItem } from '@/api/items'
import type { Item } from '@/api/items'
import { submitReport } from '@/api/reports'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const item = ref<Item | null>(null)
const loading = ref(true)
const notFound = ref(false)
const reportDialog = ref(false)
const posterVisible = ref(false)
const posterLoading = ref(false)
const posterUrl = ref('')

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, maxLines: number): string[] {
  const lines: string[] = []
  let line = ''
  for (const ch of text) {
    const test = line + ch
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line)
      line = ch
    } else {
      line = test
    }
  }
  if (line) lines.push(line)
  if (lines.length > maxLines) {
    const cut = lines.slice(0, maxLines)
    cut[maxLines - 1] = cut[maxLines - 1].slice(0, -1) + '…'
    return cut
  }
  return lines
}

async function openPoster() {
  if (!item.value) return
  posterVisible.value = true
  posterLoading.value = true
  posterUrl.value = ''
  try {
    const W = 900
    const H = 1200
    const canvas = document.createElement('canvas')
    canvas.width = W
    canvas.height = H
    const ctx = canvas.getContext('2d')!
    const font = (size: number, bold = false) => `${bold ? 'bold ' : ''}${size}px "Microsoft YaHei", "PingFang SC", sans-serif`

    const bg = ctx.createLinearGradient(0, 0, W, H)
    bg.addColorStop(0, '#050a14')
    bg.addColorStop(0.55, '#071a2c')
    bg.addColorStop(1, '#0b2740')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    const glow = ctx.createRadialGradient(W * 0.82, 90, 0, W * 0.82, 90, 460)
    glow.addColorStop(0, 'rgba(0,229,255,0.25)')
    glow.addColorStop(1, 'rgba(0,229,255,0)')
    ctx.fillStyle = glow
    ctx.fillRect(0, 0, W, H)

    ctx.fillStyle = '#00e5ff'
    ctx.fillRect(0, 0, W, 10)

    ctx.fillStyle = '#00e5ff'
    ctx.font = font(30, true)
    ctx.fillText('HDU · 智能失物招领', 64, 96)
    ctx.fillStyle = '#8fb3d9'
    ctx.font = font(21)
    ctx.fillText('杭州电子科技大学 · Lost & Found', 64, 134)

    const isLost = item.value.item_type === 'lost'
    ctx.fillStyle = isLost ? '#ff6b81' : '#3ddc97'
    ctx.font = font(26, true)
    ctx.fillText(isLost ? '寻 物 启 事' : '失 物 招 领', 64, 210)

    ctx.fillStyle = '#ffffff'
    ctx.font = font(54, true)
    const titleLines = wrapText(ctx, item.value.title, W - 128, 2)
    titleLines.forEach((line, i) => ctx.fillText(line, 64, 300 + i * 70))
    let y = 300 + titleLines.length * 70 + 10

    ctx.strokeStyle = 'rgba(0,229,255,0.25)'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(64, y)
    ctx.lineTo(W - 64, y)
    ctx.stroke()
    y += 58

    const rows: [string, string][] = [
      ['类别', item.value.category],
      ['地点', item.value.location],
      ['时间', new Date(item.value.event_time).toLocaleString('zh-CN', { hour12: false })],
    ]
    ctx.font = font(26)
    for (const [k, v] of rows) {
      ctx.fillStyle = '#7fa6c9'
      ctx.fillText(k, 64, y)
      ctx.fillStyle = '#eaf6ff'
      ctx.fillText(v, 190, y)
      y += 52
    }

    if (item.value.description) {
      y += 20
      ctx.fillStyle = '#a9c6e2'
      ctx.font = font(23)
      const descLines = wrapText(ctx, item.value.description, W - 128, 4)
      descLines.forEach((line, i) => ctx.fillText(line, 64, y + i * 38))
    }

    const qrSize = 210
    const qrData = await QRCode.toDataURL(`${window.location.origin}/items/${item.value.id}`, {
      width: qrSize,
      margin: 1,
      color: { dark: '#04121f', light: '#ffffff' },
    })
    const img = new Image()
    img.src = qrData
    await img.decode()
    const qrX = W - 64 - qrSize
    const qrY = H - 64 - qrSize
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.roundRect(qrX - 16, qrY - 16, qrSize + 32, qrSize + 32, 16)
    ctx.fill()
    ctx.drawImage(img, qrX, qrY, qrSize, qrSize)

    ctx.fillStyle = '#8fb3d9'
    ctx.font = font(22)
    ctx.fillText('扫码查看详情', 64, qrY + 56)
    ctx.fillStyle = '#00e5ff'
    ctx.font = font(26, true)
    ctx.fillText('hdulosttrack.eu.cc', 64, qrY + 108)
    ctx.fillStyle = '#5f7f9e'
    ctx.font = font(20)
    ctx.fillText('杭州电子科技大学 · 智能失物招领平台', 64, H - 36)

    posterUrl.value = canvas.toDataURL('image/png')
  } catch (e) {
    ElMessage.error('海报生成失败，请重试')
  } finally {
    posterLoading.value = false
  }
}
const reportSubmitting = ref(false)
const reportReasons = ['虚假信息', '恶意认领', '违规图片', '联系方式诈骗', '重复发布', '不当内容']
const reportForm = reactive({
  reason: '虚假信息',
  description: '',
})

const isOwner = computed(() => item.value !== null && userStore.user?.id === item.value.user_id)
const canEdit = computed(() => item.value !== null && (isOwner.value || userStore.isAdmin))

async function load() {
  loading.value = true
  notFound.value = false
  try {
    item.value = await getItem(Number(route.params.id))
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
}

function typeText(t: string): string {
  return t === 'lost' ? '失物' : '招领'
}

async function onDelete() {
  if (!item.value) return
  try {
    await ElMessageBox.confirm('删除后不可恢复，确定删除这条信息吗？', '删除确认', { type: 'warning' })
    await deleteItem(item.value.id)
    ElMessage.success('已删除')
    router.push('/items')
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '删除失败')
  }
}

async function onRemoveImage(index: number) {
  if (!item.value) return
  try {
    item.value = await deleteImage(item.value.id, index)
    ElMessage.success('图片已删除')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '删除失败')
  }
}

async function onSubmitReport() {
  if (!item.value) return
  reportSubmitting.value = true
  try {
    await submitReport({
      target_type: 'item',
      target_id: item.value.id,
      reason: reportForm.reason,
      description: reportForm.description || undefined,
    })
    ElMessage.success('举报已提交，管理员会尽快处理')
    reportDialog.value = false
    reportForm.description = ''
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '提交失败')
  } finally {
    reportSubmitting.value = false
  }
}

// 小屏下表单单列展示，避免标签与内容挤压
const isMobile = ref(window.innerWidth < 640)
function onResize() {
  isMobile.value = window.innerWidth < 640
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <div class="detail-page" v-loading="loading">
    <el-result v-if="notFound" icon="info" title="物品不存在" sub-title="该物品不存在、已被删除或尚未通过审核">
      <template #extra>
        <el-button type="primary" @click="router.push('/items')">返回列表</el-button>
      </template>
    </el-result>

    <template v-else-if="item">
      <el-card shadow="never" class="detail-page__card">
        <div class="detail-page__top">
          <div>
            <h1 class="detail-page__title">
              <el-tag :type="item.item_type === 'lost' ? 'danger' : 'success'" size="large">
                {{ typeText(item.item_type) }}
              </el-tag>
              {{ item.title }}
            </h1>
            <div class="detail-page__tags">
              <el-tag v-if="item.audit_status === 'pending'" type="warning" size="small">待审核（仅自己和管理员可见）</el-tag>
              <el-tag v-if="item.status === 'claimed'" type="info" size="small">已被认领</el-tag>
              <el-tag v-if="item.status === 'resolved'" type="success" size="small">✅ 已找回</el-tag>
              <el-tag v-if="item.status === 'closed'" type="info" size="small">已关闭</el-tag>
            </div>
          </div>
          <div class="detail-page__actions">
            <el-button
              v-if="item.item_type === 'found' && item.audit_status === 'approved' && item.status === 'active' && userStore.isLoggedIn && !isOwner"
              type="success"
              @click="router.push(`/items/${item.id}/claim`)"
            >
              申请认领
            </el-button>
            <el-button
              v-if="userStore.isLoggedIn && (isOwner || userStore.isAdmin)"
              type="primary"
              plain
              @click="router.push(`/items/${item.id}/matches`)"
            >
              🤖 智能匹配
            </el-button>
            <el-button v-if="canEdit" type="primary" plain @click="router.push(`/items/${item.id}/edit`)">编辑</el-button>
            <el-button v-if="canEdit" type="danger" plain @click="onDelete">删除</el-button>
            <el-button v-if="userStore.isLoggedIn && !isOwner" type="danger" plain @click="reportDialog = true">举报</el-button>
            <el-button v-if="item.audit_status === 'approved'" plain @click="openPoster">🖼️ 生成启事海报</el-button>
          </div>
        </div>

        <div v-if="item.images && item.images.length" class="detail-page__images">
          <div v-for="(img, idx) in item.images" :key="img" class="detail-page__img-wrap">
            <el-image :src="img" fit="cover" :preview-src-list="item.images" :initial-index="idx" class="detail-page__img" />
            <el-button v-if="canEdit" size="small" type="danger" circle class="detail-page__img-del" @click="onRemoveImage(idx)">
              ✕
            </el-button>
          </div>
        </div>
        <el-empty v-else description="暂无图片" :image-size="80" />

        <el-descriptions :column="isMobile ? 1 : 2" border class="detail-page__desc">
          <el-descriptions-item label="物品类别">{{ item.category }}</el-descriptions-item>
          <el-descriptions-item label="颜色">{{ item.color || '—' }}</el-descriptions-item>
          <el-descriptions-item label="品牌">{{ item.brand || '—' }}</el-descriptions-item>
          <el-descriptions-item label="地点">{{ item.location }}</el-descriptions-item>
          <el-descriptions-item label="事件时间">{{ new Date(item.event_time).toLocaleString('zh-CN') }}</el-descriptions-item>
          <el-descriptions-item label="发布者">{{ item.username || '匿名' }}</el-descriptions-item>
          <el-descriptions-item label="坐标">
            {{ item.latitude !== null && item.longitude !== null ? `${item.latitude.toFixed(4)}, ${item.longitude.toFixed(4)}` : '未提供' }}
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ new Date(item.created_at).toLocaleString('zh-CN') }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-page__desc-block">
          <h4>详细描述</h4>
          <p>{{ item.description || '发布者未提供详细描述' }}</p>
        </div>
      </el-card>

      <el-dialog v-model="posterVisible" title="寻物启事海报" width="420px">
      <div v-loading="posterLoading" class="poster-preview">
        <img v-if="posterUrl" :src="posterUrl" alt="寻物启事海报" />
      </div>
      <template #footer>
        <a v-if="posterUrl" :href="posterUrl" :download="`启事-${item?.title || '物品'}.png`">
          <el-button type="primary">下载图片</el-button>
        </a>
        <el-button @click="posterVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reportDialog" title="举报这条信息" width="480px">
        <el-form label-position="top">
          <el-form-item label="举报原因">
            <el-select v-model="reportForm.reason" style="width: 100%">
              <el-option v-for="r in reportReasons" :key="r" :label="r" :value="r" />
            </el-select>
          </el-form-item>
          <el-form-item label="补充说明（选填）">
            <el-input v-model="reportForm.description" type="textarea" :rows="3" maxlength="1000" show-word-limit />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="reportDialog = false">取消</el-button>
          <el-button type="danger" :loading="reportSubmitting" @click="onSubmitReport">提交举报</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.poster-preview {
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.poster-preview img {
  width: 100%;
  border-radius: 12px;
  display: block;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
}

.detail-page {
  max-width: 900px;
  margin: 0 auto;
}
.detail-page__card {
  margin-bottom: 16px;
}
.detail-page__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.detail-page__title {
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.detail-page__tags {
  display: flex;
  gap: 6px;
}
.detail-page__images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.detail-page__img-wrap {
  position: relative;
}
.detail-page__img {
  width: 140px;
  height: 140px;
  border-radius: 6px;
}
.detail-page__img-del {
  position: absolute;
  top: 4px;
  right: 4px;
}
.detail-page__desc {
  margin-bottom: 16px;
}
.detail-page__desc-block h4 {
  margin: 0 0 8px;
}
.detail-page__desc-block p {
  margin: 0;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
}
</style>
