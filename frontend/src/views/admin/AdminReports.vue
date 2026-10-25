<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { handleReport, listReports } from '@/api/admin'
import type { AdminReport } from '@/api/admin'

const reports = ref<AdminReport[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 20
const statusFilter = ref<string>('')

async function load() {
  loading.value = true
  try {
    const res = await listReports(page.value, size, statusFilter.value || undefined)
    reports.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function onHandle(report: AdminReport, action: 'handled' | 'dismissed') {
  const actionText = action === 'handled' ? '处理（举报成立）' : '驳回（举报不成立）'
  try {
    const { value } = await ElMessageBox.prompt(
      `对举报「${report.reason}」执行：${actionText}。可填写处理说明`,
      '处理举报',
      { confirmButtonText: '确定', cancelButtonText: '取消', inputPlaceholder: '处理说明' },
    )
    await handleReport(report.id, action, value || undefined)
    ElMessage.success('已处理')
    await load()
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '操作失败')
  }
}

const targetText: Record<string, string> = { item: '物品', user: '用户', claim: '认领申请' }
const statusText: Record<string, string> = { pending: '待处理', handled: '已处理', dismissed: '已驳回' }

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>举报处理</span>
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="handled" />
          <el-option label="已驳回" value="dismissed" />
        </el-select>
      </div>
    </template>
    <el-table v-loading="loading" :data="reports" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="举报对象" width="110">
        <template #default="{ row }">{{ targetText[row.target_type] || row.target_type }} #{{ row.target_id }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="举报原因" min-width="120" />
      <el-table-column label="补充说明" min-width="150">
        <template #default="{ row }">{{ row.description || '—' }}</template>
      </el-table-column>
      <el-table-column prop="reporter_name" label="举报人" width="100" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'pending' ? 'warning' : row.status === 'handled' ? 'success' : 'info'">
            {{ statusText[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button size="small" type="success" @click="onHandle(row, 'handled')">成立</el-button>
            <el-button size="small" type="info" plain @click="onHandle(row, 'dismissed')">驳回</el-button>
          </template>
          <span v-else>{{ row.handler_comment || '—' }}</span>
        </template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="prev, pager, next, total" @current-change="load" />
    </div>
  </el-card>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
</style>
