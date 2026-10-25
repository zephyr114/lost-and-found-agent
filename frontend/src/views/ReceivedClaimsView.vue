<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { claimStatusTag, claimStatusText, getReceivedClaims, reviewClaim } from '@/api/claims'
import type { Claim } from '@/api/claims'

const router = useRouter()
const claims = ref<Claim[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 10

async function load() {
  loading.value = true
  try {
    const res = await getReceivedClaims(page.value, size)
    claims.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function onApprove(claim: Claim) {
  try {
    await ElMessageBox.confirm('同意后该物品将标记为已认领，其余申请自动拒绝。确定同意？', '同意认领', { type: 'warning' })
    await reviewClaim(claim.id, 'approve')
    ElMessage.success('已同意认领')
    await load()
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '操作失败')
  }
}

async function onReject(claim: Claim) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因（可留空）', '拒绝认领', {
      confirmButtonText: '拒绝',
      cancelButtonText: '取消',
      inputPlaceholder: '如：特征不符',
    })
    await reviewClaim(claim.id, 'reject', value || undefined)
    ElMessage.success('已拒绝该申请')
    await load()
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '操作失败')
  }
}

async function onRequestProof(claim: Claim) {
  try {
    const { value } = await ElMessageBox.prompt('请填写需要补充的证明内容', '要求补充证明', {
      confirmButtonText: '发送要求',
      cancelButtonText: '取消',
      inputPlaceholder: '如：请提供购买凭证照片',
    })
    await reviewClaim(claim.id, 'request-proof', value || undefined)
    ElMessage.success('已通知申请人补充证明')
    await load()
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '操作失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="claims-page">
    <el-card shadow="never">
      <template #header><span>收到我物品的认领申请</span></template>
      <el-table v-loading="loading" :data="claims" border stripe>
        <el-table-column label="申请编号" width="90">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column label="物品" min-width="140">
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/items/${row.item_id}`)">{{ row.item_title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="applicant_name" label="申请人" width="110" />
        <el-table-column label="特征说明" min-width="200">
          <template #default="{ row }">
            <div>{{ row.proof_description }}</div>
            <div v-if="row.proof_images.length" class="claims-page__imgs">
              <el-image
                v-for="img in row.proof_images"
                :key="img"
                :src="img"
                :preview-src-list="row.proof_images"
                fit="cover"
                class="claims-page__img"
              />
            </div>
            <div v-if="row.contact" class="claims-page__contact">📞 {{ row.contact }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="claimStatusTag[row.status]">{{ claimStatusText[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button size="small" type="success" @click="onApprove(row)">同意</el-button>
              <el-button size="small" type="danger" plain @click="onReject(row)">拒绝</el-button>
              <el-button size="small" type="primary" plain @click="onRequestProof(row)">要求补充证明</el-button>
            </template>
            <span v-else>—</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="claims-page__pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.claims-page {
  max-width: 1080px;
  margin: 0 auto;
}
.claims-page__pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
.claims-page__imgs {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}
.claims-page__img {
  width: 48px;
  height: 48px;
  border-radius: 4px;
}
.claims-page__contact {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
