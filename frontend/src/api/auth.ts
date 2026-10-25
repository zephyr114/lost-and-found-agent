import http from './http'
import type { UserInfo } from './user'

export interface RegisterPayload {
  username: string
  email: string
  phone?: string
  password: string
}

export interface LoginPayload {
  account: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export async function register(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await http.post<TokenResponse>('/api/auth/register', payload)
  return data
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await http.post<TokenResponse>('/api/auth/login', payload)
  return data
}
