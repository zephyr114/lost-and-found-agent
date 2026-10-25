<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listOperationLogs } from '@/api/admin'
import type { OperationLogRow } from '@/api/admin'

const logs = ref<OperationLogRow[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 20

async function load() {
  loading.value = true
  try {
    const res = await listOperationLogs(page.value, size)
    logs.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <template #header><span>🗂 操作审计日志（最近 {{ total }} 条）</span></template>
    <el-table v-loading="loading" :data="logs" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="admin_name" label="操作人" width="110" />
      <el-table-column prop="action" label="操作" min-width="170" />
      <el-table-column label="对象" width="140">
        <template #default="{ row }">{{ row.target_type }} #{{ row.target_id ?? '—' }}</template>
      </el-table-column>
      <el-table-column label="详情" min-width="220">
        <template #default="{ row }">
          {{ row.detail ? JSON.stringify(row.detail) : '—' }}
        </template>
      </el-table-column>
      <el-table-column label="时间" width="170">
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
