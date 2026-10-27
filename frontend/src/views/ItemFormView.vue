<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadRawFile, UploadUserFile } from 'element-plus'

import { analyzeImage, extractAttributes } from '@/api/agent'
import type { ExtractedAttributes } from '@/api/agent'
import { createItem, getCategories, getItem, updateItem, uploadImages } from '@/api/items'
import type { ItemType } from '@/api/items'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.name === 'itemEdit')
const itemId = computed(() => Number(route.params.id))
const itemType = ref<ItemType>('lost')
const categories = ref<string[]>([])
const loading = ref(false)
const submitting = ref(false)

const form = reactive({
  title: '',
  category: '',
  color: '',
  brand: '',
  location: '',
  latitude: null as number | null,
  longitude: null as number | null,
  event_time: '',
  description: '',
})

// 杭电校园常见地点（可选择，也可手动输入）
const campusLocations = [
  '图书馆',
  '第一教学楼',
  '第二教学楼',
  '学生活动中心',
  '体育馆',
  '宿舍区',
  '食堂',
  '校门口',
  '其他',
]

const fileList = ref<UploadUserFile[]>([])
const maxImages = 6

// ---- AI 一键填充 ----
const aiText = ref('')
const aiLoading = ref(false)
const aiResult = ref<ExtractedAttributes | null>(null)

async function onAiFill() {
  if (aiText.value.trim().length < 2) {
    ElMessage.warning('请先粘贴一段物品描述')
    return
  }
  aiLoading.value = true
  try {
    const attrs = await extractAttributes(aiText.value)
    aiResult.value = attrs
    if (attrs.title && !form.title) form.title = attrs.title
    if (attrs.category) form.category = attrs.category
    if (attrs.color) form.color = attrs.color
    if (attrs.brand) form.brand = attrs.brand
    if (attrs.location) form.location = attrs.location
    ElMessage.success('已根据描述自动填充表单')
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '识别失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

// ---- 图片识别（选图后自动识别颜色） ----
const analyzing = ref(false)
const imageTags = ref<{ color?: string; brightness?: number } | null>(null)

async function onFileChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  analyzing.value = true
  try {
    const res = await analyzeImage(raw)
    imageTags.value = { color: res.color ?? undefined, brightness: res.brightness ?? undefined }
    if (res.color && !form.color) form.color = res.color
  } catch {
    imageTags.value = null
  } finally {
    analyzing.value = false
  }
}

const pageTitle = computed(() => {
  if (isEdit.value) return '编辑信息'
  return itemType.value === 'lost' ? '发布失物' : '发布招领'
})

async function load() {
  if (!isEdit.value) {
    itemType.value = route.path.includes('/found') ? 'found' : 'lost'
    return
  }
  loading.value = true
  try {
    const item = await getItem(itemId.value)
    itemType.value = item.item_type
    form.title = item.title
    form.category = item.category
    form.color = item.color || ''
    form.brand = item.brand || ''
    form.location = item.location
    form.latitude = item.latitude
    form.longitude = item.longitude
    form.event_time = item.event_time.slice(0, 19)
    form.description = item.description || ''
  } catch {
    ElMessage.error('加载失败，物品不存在或无权访问')
    router.push('/items')
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  if (!form.title || !form.category || !form.location || !form.event_time) {
    ElMessage.warning('请填写标题、物品类别、地点和事件时间')
    return
  }
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      category: form.category,
      location: form.location,
      color: form.color || undefined,
      brand: form.brand || undefined,
      description: form.description || undefined,
      latitude: form.latitude ?? undefined,
      longitude: form.longitude ?? undefined,
      event_time: new Date(form.event_time).toISOString(),
    }
    let item
    if (isEdit.value) {
      item = await updateItem(itemId.value, payload)
    } else {
      item = await createItem({ ...payload, item_type: itemType.value })
    }
    const files = fileList.value
      .map((f) => f.raw)
      .filter((f): f is UploadRawFile => Boolean(f))
    if (files.length) {
      item = await uploadImages(item.id, files)
    }
    ElMessage.success(isEdit.value ? '已保存，内容重新进入审核' : '发布成功，等待管理员审核')
    router.push(`/items/${item.id}`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  categories.value = await getCategories()
  await load()
})
</script>

<template>
  <div class="form-page" v-loading="loading">
    <el-card shadow="never" class="ai-card">
      <template #header>
        <div class="ai-card__header">
          <span>🤖 AI 一键填充</span>
          <span class="ai-card__hint">粘贴一段物品描述，自动识别类别 / 颜色 / 品牌 / 地点</span>
        </div>
      </template>
      <div class="ai-row">
        <el-input
          v-model="aiText"
          type="textarea"
          :rows="2"
          maxlength="2000"
          show-word-limit
          placeholder="例如：我在图书馆丢了一个黑色苹果手机，外壳有点划痕"
        />
        <el-button type="primary" class="glow-btn" :loading="aiLoading" @click="onAiFill">✨ 智能识别并填充</el-button>
      </div>
      <div v-if="aiResult" class="ai-tags">
        <el-tag v-if="aiResult.category" type="success">类别：{{ aiResult.category }}</el-tag>
        <el-tag v-if="aiResult.color" type="warning">颜色：{{ aiResult.color }}</el-tag>
        <el-tag v-if="aiResult.brand" type="primary">品牌：{{ aiResult.brand }}</el-tag>
        <el-tag v-if="aiResult.location" type="info">地点：{{ aiResult.location }}</el-tag>
        <span class="ai-hint">已自动填入下方表单，可继续修改</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span>{{ pageTitle }}</span>
        <el-tag v-if="isEdit" type="warning" size="small" style="margin-left: 8px">修改后需重新审核</el-tag>
      </template>

      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <el-form-item label="物品名称 *">
              <el-input v-model="form.title" maxlength="100" show-word-limit :placeholder="itemType === 'lost' ? '如：黑色双肩包' : '如：捡到黑色双肩包'" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="物品类别 *">
              <el-select v-model="form.category" placeholder="选择类别" style="width: 100%">
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="颜色">
              <el-input v-model="form.color" maxlength="30" placeholder="如：黑色" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="品牌">
              <el-input v-model="form.brand" maxlength="50" placeholder="如：耐克（选填）" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item :label="itemType === 'lost' ? '丢失地点 *' : '拾获地点 *'">
              <el-select
                v-model="form.location"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入校园地点"
                style="width: 100%"
              >
                <el-option v-for="loc in campusLocations" :key="loc" :label="loc" :value="loc" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item :label="itemType === 'lost' ? '丢失时间 *' : '拾获时间 *'">
              <el-date-picker
                v-model="form.event_time"
                type="datetime"
                placeholder="选择时间"
                value-format="YYYY-MM-DDTHH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="纬度（选填）">
              <el-input-number v-model="form.latitude" :min="-90" :max="90" :precision="6" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="经度（选填）">
              <el-input-number v-model="form.longitude" :min="-180" :max="180" :precision="6" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="详细描述">
              <el-input v-model="form.description" type="textarea" :rows="4" maxlength="2000" show-word-limit placeholder="物品特征、包内物品、联系方式说明等" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="物品图片（选填，最多 6 张）">
              <el-upload
                v-model:file-list="fileList"
                list-type="picture-card"
                :auto-upload="false"
                accept=".jpg,.jpeg,.png,.webp,.gif"
                :limit="maxImages"
                :on-change="onFileChange"
              >
                <div>
                  <div style="font-size: 24px">＋</div>
                  <div style="font-size: 12px">选择图片</div>
                </div>
              </el-upload>
              <div v-if="analyzing || imageTags" class="vision-tags">
                <template v-if="analyzing">
                  <el-tag type="info" class="vision-tag">🔍 正在识别图片…</el-tag>
                </template>
                <template v-else-if="imageTags">
                  <el-tag v-if="imageTags.color" type="success" class="vision-tag">识别颜色：{{ imageTags.color }}</el-tag>
                  <el-tag v-if="imageTags.brightness !== undefined" type="info" class="vision-tag">
                    亮度 {{ imageTags.brightness }}
                  </el-tag>
                  <span class="ai-hint">（颜色已自动补充）</span>
                </template>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-page__actions">
          <el-button @click="router.back()">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            {{ isEdit ? '保存修改' : '发布（提交后进入审核）' }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.form-page {
  max-width: 860px;
  margin: 0 auto;
}
.form-page__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.ai-card {
  margin-bottom: 16px;
}
.ai-card__header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}
.ai-card__hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.ai-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.ai-row :deep(.el-textarea) {
  flex: 1;
}
.ai-tags {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.ai-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.vision-tags {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.vision-tag {
  animation: tagPop 0.35s ease;
}
@keyframes tagPop {
  from {
    opacity: 0;
    transform: scale(0.75);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@media (max-width: 560px) {
  .ai-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
