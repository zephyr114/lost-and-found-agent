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
  <div class="item-card glass" @click="openDetail(item.id)">
    <div class="item-card__img">
      <el-image v-if="item.images && item.images.length" :src="item.images[0]" fit="cover" class="item-card__cover" />
      <div v-else class="item-card__placeholder">📦</div>
      <span class="item-card__type" :class="`item-card__type--${item.item_type}`">{{ typeText(item.item_type) }}</span>
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
      <div v-else-if="item.status === 'resolved'" class="item-card__status">
        <el-tag size="small" type="success">已找回</el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.item-card {
  cursor: pointer;
  margin-bottom: 16px;
  overflow: hidden;
  border-radius: var(--radius-md);
}

.item-card__img {
  position: relative;
  height: 160px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-card__cover {
  width: 100%;
  height: 100%;
  transition: transform 0.45s ease;
}

.item-card:hover .item-card__cover {
  transform: scale(1.06);
}

.item-card__placeholder {
  font-size: 48px;
  opacity: 0.55;
}

.item-card__type {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(8px);
}

.item-card__type--lost {
  color: #ffb3c0;
  background: rgba(255, 93, 115, 0.18);
  border: 1px solid rgba(255, 93, 115, 0.45);
}

.item-card__type--found {
  color: #a9f5d0;
  background: rgba(61, 220, 151, 0.16);
  border: 1px solid rgba(61, 220, 151, 0.45);
}

.item-card__body {
  padding: 12px 14px 14px;
}

.item-card__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.item-card__name {
  font-weight: 600;
  color: #e8f3ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-card__meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #8fb3d9;
  font-size: 12px;
}

.item-card__status {
  margin-top: 8px;
}
</style>
