<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

import { getAuthConfig } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
  invite: '',
})
const inviteRequired = ref(false)
const loading = ref(false)

onMounted(async () => {
  try {
    const cfg = await getAuthConfig()
    inviteRequired.value = cfg.invite_required
    // 二维码链接可直接带邀请码：/register?invite=XXX
    const q = route.query.invite
    if (typeof q === 'string' && q) form.invite = q
  } catch {
    inviteRequired.value = false
  }
})
const agree = ref(false)

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为 2-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  phone: [{ pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 72, message: '密码长度为 8-72 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function onSubmit() {
  if (!agree.value) {
    ElMessage.warning('请先阅读并同意《用户协议》和《隐私政策》')
    return
  }
  if (inviteRequired.value && !form.invite.trim()) {
    ElMessage.warning('请输入邀请码（仅限杭电师生注册）')
    return
  }
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.register({
      username: form.username,
      email: form.email,
      phone: form.phone || undefined,
      password: form.password,
      invite_code: form.invite.trim() || undefined,
    })
    ElMessage.success('注册成功，已自动登录')
    router.push('/')
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="always">
      <template #header>
        <div class="auth-card__header">
          <h2>注册</h2>
          <p>注册成功后将自动登录</p>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="2-50 个字符" clearable />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="用于登录和找回密码" clearable />
        </el-form-item>
        <el-form-item label="手机号（选填）" prop="phone">
          <el-input v-model="form.phone" placeholder="11 位手机号" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少 8 位" show-password />
        </el-form-item>
        <el-form-item v-if="inviteRequired" label="邀请码 *">
          <el-input v-model="form.invite" placeholder="班级群 / 社团群里发的邀请码" clearable />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="agree">
            我已阅读并同意
            <router-link to="/terms" target="_blank" @click.stop>《用户协议》</router-link>
            和
            <router-link to="/privacy" target="_blank" @click.stop>《隐私政策》</router-link>
          </el-checkbox>
        </el-form-item>
        <el-button type="primary" class="auth-card__submit" :loading="loading" native-type="submit">
          注 册
        </el-button>
        <el-alert
          v-if="inviteRequired"
          type="info"
          :closable="false"
          show-icon
          class="auth-card__notice"
          title="仅限杭州电子科技大学师生注册"
          description="没有邀请码也可以直接浏览公开的失物与招领信息。"
        />
        <div class="auth-card__footer">
          已有账号？
          <router-link to="/login">去登录</router-link>
          <span class="auth-card__sep">·</span>
          <router-link to="/">先随便逛逛</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.auth-card__notice {
  margin-bottom: 12px;
}
.auth-card__sep {
  margin: 0 6px;
  color: #5f7f9e;
}

.auth-page {
  display: flex;
  justify-content: center;
  padding: 40px 16px;
}
.auth-card {
  width: 100%;
  max-width: 400px;
}
.auth-card__header {
  text-align: center;
}
.auth-card__header h2 {
  margin: 0 0 4px;
}
.auth-card__header p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.auth-card__submit {
  width: 100%;
}
.auth-card__footer {
  margin-top: 14px;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
