<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listAgentLogs } from '@/api/admin'
import type { AgentLogRow } from '@/api/admin'

const logs = ref<AgentLogRow[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 20

async function load() {
  loading.value = true
  try {
    const res = await listAgentLogs(page.value, size)
    logs.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function pretty(obj: unknown): string {
  if (obj === null || obj === undefined) return '—'
  const text = JSON.stringify(obj)
  return text.length > 200 ? text.slice(0, 200) + '…' : text
}

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <template #header><span>🤖 Agent 运行日志（最近 {{ total }} 条）</span></template>
    <el-table v-loading="loading" :data="logs" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="task_type" label="任务类型" width="130" />
      <el-table-column prop="tool_name" label="工具" width="200" />
      <el-table-column label="输入" min-width="180">
        <template #default="{ row }">{{ pretty(row.input_data) }}</template>
      </el-table-column>
      <el-table-column label="结果" min-width="200">
        <template #default="{ row }">{{ pretty(row.tool_result) }}</template>
      </el-table-column>
      <el-table-column prop="execution_time_ms" label="耗时(ms)" width="100" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">{{ row.status }}</el-tag>
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
