import { defineStore } from 'pinia'

// 占位 store：第二阶段加入 userStore（登录态、JWT、角色权限）
export const useAppStore = defineStore('app', {
  state: () => ({
    name: 'Lost-and-Found Intelligent Platform',
  }),
})
