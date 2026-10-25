<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listAllClaims } from '@/api/admin'
import { claimStatusTag, claimStatusText } from '@/api/claims'
import type { Claim } from '@/api/claims'

const claims = ref<Claim[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 20

async function load() {
  loading.value = true
  try {
    const res = await listAllClaims(page.value, size)
    claims.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <template #header><span>认领申请管理（全部 {{ total }} 条）</span></template>
    <el-table v-loading="loading" :data="claims" border stripe>
      <el-table-column prop="id" label="编号" width="80" />
      <el-table-column prop="item_title" label="物品" min-width="140" />
      <el-table-column prop="applicant_name" label="申请人" width="110" />
      <el-table-column label="特征说明" min-width="180">
        <template #default="{ row }">{{ row.proof_description }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="claimStatusTag[row.status]">{{ claimStatusText[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="处理意见" min-width="140">
        <template #default="{ row }">{{ row.review_comment || '—' }}</template>
      </el-table-column>
      <el-table-column label="申请时间" width="170">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="prev, pager, next, total" @current-change="load" />
    </div>
  </el-card>
</template>

<style scoped>
.pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
</style>
