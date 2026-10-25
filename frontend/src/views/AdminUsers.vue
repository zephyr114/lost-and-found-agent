<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listUsers } from '@/api/admin'
import type { UserInfo } from '@/api/user'

const users = ref<UserInfo[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    users.value = await listUsers()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="admin-page">
    <el-card shadow="never">
      <template #header>
        <span>用户管理（第二阶段演示：仅管理员可访问，完整后台见第六阶段）</span>
      </template>
      <el-table v-loading="loading" :data="users" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" min-width="120" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'admin' ? 'warning' : 'info'">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="credit_score" label="信用分" width="90" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="created_at" label="注册时间" min-width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1080px;
  margin: 0 auto;
}
</style>
