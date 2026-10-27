<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getMessages, markAllRead, markRead, messageTypeText, sendMessage } from '@/api/messages'
import type { Message } from '@/api/messages'
import { getUnreadCount } from '@/api/messages'

const box = ref<'inbox' | 'sent'>('inbox')
const messages = ref<Message[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 20
const unread = ref(0)

// 回复
const replyDialog = ref(false)
const replyTarget = ref<Message | null>(null)
const replyContent = ref('')
const replying = ref(false)

function openReply(msg: Message) {
  if (!msg.sender_id) return
  replyTarget.value = msg
  replyContent.value = ''
  replyDialog.value = true
}

async function submitReply() {
  if (!replyTarget.value?.sender_id) return
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  replying.value = true
  try {
    await sendMessage(replyTarget.value.sender_id, replyContent.value.trim())
    replyDialog.value = false
    ElMessage.success('回复已发送')
  } catch {
    ElMessage.error('发送失败')
  } finally {
    replying.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await getMessages(box.value, page.value, size)
    messages.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function refreshUnread() {
  unread.value = await getUnreadCount()
}

async function onRead(msg: Message) {
  if (msg.is_read) return
  try {
    await markRead(msg.id)
    msg.is_read = true
    await refreshUnread()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function onReadAll() {
  try {
    await markAllRead()
    await Promise.all([load(), refreshUnread()])
    ElMessage.success('已全部标记为已读')
  } catch {
    ElMessage.error('操作失败')
  }
}

function switchBox(value: 'inbox' | 'sent') {
  box.value = value
  page.value = 1
  load()
}

onMounted(async () => {
  await Promise.all([load(), refreshUnread()])
})
</script>

<template>
  <div class="messages-page">
    <el-card shadow="never">
      <template #header>
        <div class="messages-page__header">
          <span>消息中心</span>
          <div>
            <el-button v-if="box === 'inbox'" size="small" @click="onReadAll">全部已读</el-button>
            <el-radio-group v-model="box" size="small" @change="switchBox">
              <el-radio-button value="inbox">收到的消息（未读 {{ unread }}）</el-radio-button>
              <el-radio-button value="sent">发出的消息</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="messages-page__list">
        <el-empty v-if="!loading && messages.length === 0" description="暂无消息" />
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-item"
          :class="{ 'message-item--unread': !msg.is_read }"
          @click="onRead(msg)"
        >
          <div class="message-item__head">
            <el-tag size="small" type="info">{{ messageTypeText[msg.message_type] || msg.message_type }}</el-tag>
            <span class="message-item__from">
              {{ box === 'inbox' ? (msg.sender_name || '系统') : '发给用户 #' + msg.receiver_id }}
            </span>
            <span class="message-item__time">{{ new Date(msg.created_at).toLocaleString('zh-CN') }}</span>
            <el-badge v-if="!msg.is_read && box === 'inbox'" is-dot />
          </div>
          <div class="message-item__content">{{ msg.content }}</div>
          <div v-if="box === 'inbox' && msg.sender_id" class="message-item__actions">
            <el-button size="small" text type="primary" @click.stop="openReply(msg)">回复</el-button>
          </div>
        </div>
      </div>

      <div class="messages-page__pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="load"
        />
      </div>
    </el-card>

    <el-dialog v-model="replyDialog" title="回复消息" width="420px">
      <p class="reply-hint">回复给：{{ replyTarget?.sender_name || '用户' }}</p>
      <el-input v-model="replyContent" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="输入回复内容" />
      <template #footer>
        <el-button @click="replyDialog = false">取消</el-button>
        <el-button type="primary" :loading="replying" @click="submitReply">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.messages-page {
  max-width: 860px;
  margin: 0 auto;
}
.messages-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.messages-page__list {
  min-height: 200px;
}
.message-item {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
}
.message-item:hover {
  background: var(--el-fill-color-light);
}
.message-item--unread {
  background: var(--el-color-primary-light-9);
}
.message-item__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.message-item__from {
  font-weight: 600;
  font-size: 13px;
}
.message-item__time {
  margin-left: auto;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.message-item__content {
  font-size: 14px;
  white-space: pre-wrap;
}
.message-item__actions {
  margin-top: 6px;
  display: flex;
  justify-content: flex-end;
}
.reply-hint {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.messages-page__pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
</style>
