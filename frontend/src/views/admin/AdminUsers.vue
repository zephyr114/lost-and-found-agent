<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { listUsers, setUserStatus } from '@/api/admin'
import type { AdminUser } from '@/api/admin'

const users = ref<AdminUser[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 20

async function load() {
  loading.value = true
  try {
    const res = await listUsers(page.value, size)
    users.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function onToggle(user: AdminUser) {
  const next = user.status === 'active' ? 'disabled' : 'active'
  const actionText = next === 'disabled' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${actionText}用户「${user.username}」吗？`, `${actionText}确认`, { type: 'warning' })
    await setUserStatus(user.id, next)
    ElMessage.success(`已${actionText}`)
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
  <el-card shadow="never">
    <template #header><span>用户管理</span></template>
    <el-table v-loading="loading" :data="users" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="手机号" width="130">
        <template #default="{ row }">{{ row.phone || '—' }}</template>
      </el-table-column>
      <el-table-column label="角色" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.role === 'admin' ? 'warning' : 'info'">{{ row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="credit_score" label="信用分" width="90" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'active' ? 'success' : 'danger'">{{ row.status === 'active' ? '正常' : '已禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="170">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.role !== 'admin'"
            size="small"
            :type="row.status === 'active' ? 'danger' : 'success'"
            plain
            @click="onToggle(row)"
          >
            {{ row.status === 'active' ? '禁用' : '启用' }}
          </el-button>
          <span v-else>—</span>
        </template>
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
