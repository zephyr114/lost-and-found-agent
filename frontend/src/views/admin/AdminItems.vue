<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { auditItem, getPendingItems } from '@/api/admin'
import type { PendingItem } from '@/api/admin'

const items = ref<PendingItem[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 10

async function load() {
  loading.value = true
  try {
    const res = await getPendingItems(page.value, size)
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function onAudit(item: PendingItem, decision: 'approve' | 'reject') {
  const actionText = decision === 'approve' ? '通过' : '拒绝'
  try {
    const { value } = await ElMessageBox.prompt(
      `确定${actionText}「${item.title}」吗？可填写审核意见（可留空）`,
      `${actionText}审核`,
      { confirmButtonText: actionText, cancelButtonText: '取消', inputPlaceholder: '审核意见' },
    )
    await auditItem(item.id, decision, value || undefined)
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
    <template #header><span>信息审核（待审核 {{ total }} 条）</span></template>
    <el-table v-loading="loading" :data="items" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.item_type === 'lost' ? 'danger' : 'success'">{{ row.item_type === 'lost' ? '失物' : '招领' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="140" />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="location" label="地点" width="110" />
      <el-table-column label="描述" min-width="160">
        <template #default="{ row }">{{ row.description || '—' }}</template>
      </el-table-column>
      <el-table-column label="图片" width="80">
        <template #default="{ row }">
          <el-image v-if="row.images.length" :src="row.images[0]" :preview-src-list="row.images" fit="cover" style="width: 40px; height: 40px; border-radius: 4px" />
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="发布者" width="100" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="onAudit(row, 'approve')">通过</el-button>
          <el-button size="small" type="danger" plain @click="onAudit(row, 'reject')">拒绝</el-button>
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
