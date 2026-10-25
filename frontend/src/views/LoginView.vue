<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = reactive({
  account: '',
  password: '',
})
const loading = ref(false)

async function onSubmit() {
  if (!form.account || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login({ account: form.account, password: form.password })
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '登录失败，请检查账号和密码')
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
          <h2>登录</h2>
          <p>支持用户名 / 邮箱 / 手机号</p>
        </div>
      </template>
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="账号">
          <el-input v-model="form.account" placeholder="用户名 / 邮箱 / 手机号" clearable />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-button type="primary" class="auth-card__submit" :loading="loading" native-type="submit">
          登 录
        </el-button>
        <div class="auth-card__footer">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 48px 16px;
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
