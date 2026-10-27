import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { REFRESH_KEY, TOKEN_KEY, USER_KEY } from '@/api/http'
import { login as apiLogin, register as apiRegister } from '@/api/auth'
import type { LoginPayload, RegisterPayload } from '@/api/auth'
import { getMe } from '@/api/user'
import type { UserInfo } from '@/api/user'

function readStoredUser(): UserInfo | null {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<UserInfo | null>(readStoredUser())

  const isLoggedIn = computed(() => Boolean(token.value))
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setSession(newToken: string, newUser: UserInfo, refreshToken?: string) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem(TOKEN_KEY, newToken)
    if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken)
    localStorage.setItem(USER_KEY, JSON.stringify(newUser))
  }

  async function login(payload: LoginPayload) {
    const res = await apiLogin(payload)
    setSession(res.access_token, res.user, res.refresh_token)
  }

  async function register(payload: RegisterPayload) {
    const res = await apiRegister(payload)
    setSession(res.access_token, res.user, res.refresh_token)
  }

  async function fetchMe() {
    user.value = await getMe()
    localStorage.setItem(USER_KEY, JSON.stringify(user.value))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return { token, user, isLoggedIn, isAdmin, login, register, fetchMe, logout }
})
