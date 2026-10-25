<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="placeholder-page">
    <el-result
      icon="info"
      title="发布功能将在第三阶段上线"
      sub-title="本页面用于验证路由守卫：未登录访问会自动跳转到登录页"
    >
      <template #extra>
        <el-button type="primary" @click="router.push('/')">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<style scoped>
.placeholder-page {
  display: flex;
  justify-content: center;
  padding: 48px 16px;
}
</style>
