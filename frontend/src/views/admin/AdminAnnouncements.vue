<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  adminListAnnouncements,
  createAnnouncement,
  deleteAnnouncement,
  updateAnnouncement,
} from '@/api/admin'
import type { Announcement } from '@/api/admin'

const announcements = ref<Announcement[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)

const form = reactive({
  title: '',
  content: '',
})

async function load() {
  loading.value = true
  try {
    announcements.value = await adminListAnnouncements()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.title = ''
  form.content = ''
  dialogVisible.value = true
}

function openEdit(ann: Announcement) {
  editingId.value = ann.id
  form.title = ann.title
  form.content = ann.content
  dialogVisible.value = true
}

async function onSubmit() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  try {
    if (editingId.value) {
      await updateAnnouncement(editingId.value, { title: form.title, content: form.content })
      ElMessage.success('公告已更新')
    } else {
      await createAnnouncement({ title: form.title, content: form.content })
      ElMessage.success('公告已发布')
    }
    dialogVisible.value = false
    await load()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '操作失败')
  }
}

async function onToggle(ann: Announcement) {
  const next = ann.status === 'active' ? 'archived' : 'active'
  try {
    await updateAnnouncement(ann.id, { status: next })
    await load()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function onDelete(ann: Announcement) {
  try {
    await ElMessageBox.confirm(`确定删除公告「${ann.title}」吗？`, '删除确认', { type: 'warning' })
    await deleteAnnouncement(ann.id)
    ElMessage.success('已删除')
    await load()
  } catch (e: unknown) {
    if (e === 'cancel' || (e as { name?: string })?.name === 'ElMessageBoxError') return
    ElMessage.error('删除失败')
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="header">
        <span>系统公告管理</span>
        <el-button type="primary" size="small" @click="openCreate">发布公告</el-button>
      </div>
    </template>
    <el-table v-loading="loading" :data="announcements" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'">{{ row.status === 'active' ? '生效中' : '已归档' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" width="170">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" plain @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="onToggle(row)">{{ row.status === 'active' ? '归档' : '恢复' }}</el-button>
          <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑公告' : '发布公告'" width="560px">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="5" maxlength="5000" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">{{ editingId ? '保存' : '发布' }}</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
