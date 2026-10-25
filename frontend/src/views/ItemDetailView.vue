<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

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

onMounted(load)
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
            <h2 class="detail-page__title">
              <el-tag :type="item.item_type === 'lost' ? 'danger' : 'success'" size="large">
                {{ typeText(item.item_type) }}
              </el-tag>
              {{ item.title }}
            </h2>
            <div class="detail-page__tags">
              <el-tag v-if="item.audit_status === 'pending'" type="warning" size="small">待审核（仅自己和管理员可见）</el-tag>
              <el-tag v-if="item.status === 'claimed'" type="info" size="small">已被认领</el-tag>
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

        <el-descriptions :column="2" border class="detail-page__desc">
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
