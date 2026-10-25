<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadRawFile, UploadUserFile } from 'element-plus'

import { createClaim } from '@/api/claims'
import { getItem } from '@/api/items'
import type { Item } from '@/api/items'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const item = ref<Item | null>(null)
const loading = ref(true)
const notFound = ref(false)
const submitting = ref(false)

const form = reactive({
  proof_description: '',
  contact: '',
})
const fileList = ref<UploadUserFile[]>([])

onMounted(async () => {
  try {
    item.value = await getItem(Number(route.params.id))
    form.contact = userStore.user?.phone || ''
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})

async function onSubmit() {
  if (!form.proof_description.trim()) {
    ElMessage.warning('请说明物品的特殊特征或证明')
    return
  }
  if (!item.value) return
  submitting.value = true
  try {
    await createClaim(item.value.id, {
      proof_description: form.proof_description,
      contact: form.contact || undefined,
      files: fileList.value
        .map((f) => f.raw)
        .filter((f): f is UploadRawFile => Boolean(f)),
    })
    ElMessage.success('认领申请已提交，请等待物品发布者处理')
    router.push('/my/claims')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="claim-form-page" v-loading="loading">
    <el-result v-if="notFound" icon="info" title="物品不存在或不可认领">
      <template #extra>
        <el-button type="primary" @click="router.push('/items?type=found')">返回招领列表</el-button>
      </template>
    </el-result>

    <el-card v-else-if="item" shadow="never">
      <template #header>
        <span>认领申请 —— {{ item.title }}</span>
      </template>
      <el-alert type="info" :closable="false" show-icon class="claim-form-page__alert">
        请描述只有物主才知道的物品特征（如内部物品、划痕、编号等），并上传证明图片，以提高认领成功率。
      </el-alert>
      <el-form label-position="top" class="claim-form-page__form">
        <el-form-item label="物品特殊特征 / 证明说明 *">
          <el-input
            v-model="form.proof_description"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="例如：包内有我的校园卡，卡号后四位 1234；耳机盒底部有刻字 XX"
          />
        </el-form-item>
        <el-form-item label="联系方式（选填，便于发布者联系你）">
          <el-input v-model="form.contact" maxlength="100" placeholder="手机号或微信" />
        </el-form-item>
        <el-form-item label="证明图片（选填，最多 6 张）">
          <el-upload
            v-model:file-list="fileList"
            list-type="picture-card"
            :auto-upload="false"
            accept=".jpg,.jpeg,.png,.webp,.gif"
            :limit="6"
          >
            <div>
              <div style="font-size: 24px">＋</div>
              <div style="font-size: 12px">上传证明</div>
            </div>
          </el-upload>
        </el-form-item>
        <div class="claim-form-page__actions">
          <el-button @click="router.back()">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="onSubmit">提交申请</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.claim-form-page {
  max-width: 720px;
  margin: 0 auto;
}
.claim-form-page__alert {
  margin-bottom: 16px;
}
.claim-form-page__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
