import { defineStore } from 'pinia'

// 应用级 store：全局信息
export const useAppStore = defineStore('app', {
  state: () => ({
    name: 'Lost-and-Found Intelligent Platform',
  }),
})
