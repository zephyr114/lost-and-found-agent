<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteItem, getItems } from '@/api/items'
import type { Item } from '@/api/items'

const router = useRouter()
const items = ref<Item[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 10
const isMobile = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getItems({ mine: true, page: page.value, size })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function typeText(t: string): string {
  return t === 'lost' ? '失物' : '招领'
}

function auditText(s: string): string {
  return { pending: '待审核', approved: '已通过', rejected: '未通过' }[s] || s
}

function auditTag(s: string): 'warning' | 'success' | 'danger' {
  return { pending: 'warning', approved: 'success', rejected: 'danger' }[s] as 'warning' | 'success' | 'danger'
}

async function onDelete(item: Item) {
  try {
    await ElMessageBox.confirm(`确定删除「${item.title}」吗？`, '删除确认', { type: 'warning' })
    await deleteItem(item.id)
    ElMessage.success('已删除')
    await load()
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    ElMessage.error('删除失败')
  }
}

function formatTime(t: string): string {
  const d = new Date(t)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  isMobile.value = window.matchMedia('(max-width: 720px)').matches
  load()
})
</script>

<template>
  <div class="my-items-page">
    <el-card shadow="never">
      <template #header>
        <div class="my-items-page__header">
          <span>我的发布</span>
          <el-button type="primary" size="small" @click="router.push('/publish/lost')">发布失物</el-button>
        </div>
      </template>
      <el-table v-if="!isMobile" v-loading="loading" :data="items" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.item_type === 'lost' ? 'danger' : 'success'">{{ typeText(row.item_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="category" label="类别" width="110" />
        <el-table-column label="审核状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="auditTag(row.audit_status)">{{ auditText(row.audit_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="242" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" @click="router.push(`/items/${row.id}`)">查看</el-button>
              <el-button size="small" type="primary" plain @click="router.push(`/items/${row.id}/edit`)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div v-else class="my-items__cards" v-loading="loading">
        <div v-for="row in items" :key="row.id" class="my-item-card">
          <div class="my-item-card__top">
            <el-tag size="small" :type="row.item_type === 'lost' ? 'danger' : 'success'">{{ typeText(row.item_type) }}</el-tag>
            <span class="my-item-card__title">{{ row.title }}</span>
          </div>
          <div class="my-item-card__meta">
            <span>#{{ row.id }}</span>
            <span>{{ row.category }}</span>
            <el-tag size="small" :type="auditTag(row.audit_status)">{{ auditText(row.audit_status) }}</el-tag>
          </div>
          <div class="my-item-card__time">发布于 {{ formatTime(row.created_at) }}</div>
          <div class="my-item-card__actions">
            <el-button size="small" @click="router.push(`/items/${row.id}`)">查看</el-button>
            <el-button size="small" type="primary" plain @click="router.push(`/items/${row.id}/edit`)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="!items.length && !loading" description="还没有发布过信息">
          <el-button type="primary" @click="router.push('/publish/lost')">去发布失物</el-button>
        </el-empty>
      </div>
      <div class="my-items-page__pager">
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
.row-actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
}
.row-actions :deep(.el-button) {
  margin-left: 0;
}

.my-items__cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.my-item-card {
  border: 1px solid rgba(0, 229, 255, 0.18);
  border-radius: 12px;
  padding: 14px;
  background: rgba(8, 25, 43, 0.6);
}
.my-item-card__top {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}
.my-item-card__title {
  font-size: 15px;
  font-weight: 600;
  color: #eaf6ff;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}
.my-item-card__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #8fb3d9;
  margin-bottom: 6px;
}
.my-item-card__time {
  font-size: 12px;
  color: #6f8fae;
  margin-bottom: 12px;
}
.my-item-card__actions {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
}
.my-item-card__actions .el-button {
  flex: 1;
  margin: 0;
}

.my-items-page {
  max-width: 1080px;
  margin: 0 auto;
}
.my-items-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.my-items-page__pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
</style>
