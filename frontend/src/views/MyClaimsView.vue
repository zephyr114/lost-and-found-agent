<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { cancelClaim, claimStatusTag, claimStatusText, getMyClaims } from '@/api/claims'
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
    const res = await getMyClaims(page.value, size)
    claims.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function onCancel(claim: Claim) {
  try {
    await cancelClaim(claim.id)
    ElMessage.success('已撤回申请')
    await load()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '撤回失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="claims-page">
    <el-card shadow="never">
      <template #header><span>我的认领申请</span></template>
      <el-table v-loading="loading" :data="claims" border stripe>
        <el-table-column label="申请编号" width="90">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column label="物品" min-width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/items/${row.item_id}`)">{{ row.item_title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="170">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="claimStatusTag[row.status]">{{ claimStatusText[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="处理意见" min-width="160">
          <template #default="{ row }">{{ row.review_comment || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'need_more_proof'"
              size="small"
              type="danger"
              plain
              @click="onCancel(row)"
            >
              撤回
            </el-button>
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
</style>
