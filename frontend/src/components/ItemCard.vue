<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Item } from '@/api/items'

defineProps<{ item: Item }>()

const router = useRouter()

function typeText(t: string): string {
  return t === 'lost' ? '失物' : '招领'
}

function typeTag(t: string): 'danger' | 'success' {
  return t === 'lost' ? 'danger' : 'success'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('zh-CN')
}

function openDetail(id: number) {
  router.push(`/items/${id}`)
}
</script>

<template>
  <el-card class="item-card" shadow="hover" @click="openDetail(item.id)">
    <div class="item-card__img">
      <el-image v-if="item.images && item.images.length" :src="item.images[0]" fit="cover" class="item-card__cover" />
      <div v-else class="item-card__placeholder">📦</div>
    </div>
    <div class="item-card__body">
      <div class="item-card__title">
        <el-tag size="small" :type="typeTag(item.item_type)">{{ typeText(item.item_type) }}</el-tag>
        <span class="item-card__name">{{ item.title }}</span>
      </div>
      <div class="item-card__meta">
        <span>📍 {{ item.location }}</span>
        <span>🕐 {{ formatDate(item.event_time) }}</span>
      </div>
      <div v-if="item.audit_status === 'pending'" class="item-card__status">
        <el-tag size="small" type="warning">待审核</el-tag>
      </div>
      <div v-else-if="item.status === 'claimed'" class="item-card__status">
        <el-tag size="small" type="info">已认领</el-tag>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.item-card {
  cursor: pointer;
  margin-bottom: 16px;
}
.item-card__img {
  height: 160px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
}
.item-card__cover {
  width: 100%;
  height: 100%;
}
.item-card__placeholder {
  font-size: 48px;
}
.item-card__body {
  padding-top: 10px;
}
.item-card__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.item-card__name {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-card__meta {
  display: flex;
  justify-content: space-between;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.item-card__status {
  margin-top: 8px;
}
</style>
