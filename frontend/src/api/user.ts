import http from './http'

export interface UserInfo {
  id: number
  username: string
  email: string
  phone: string | null
  avatar: string | null
  credit_score: number
  role: 'user' | 'admin'
  status: string
  created_at: string
}

export interface UpdateProfilePayload {
  username?: string
  email?: string
  phone?: string
  avatar?: string
}

export async function getMe(): Promise<UserInfo> {
  const { data } = await http.get<UserInfo>('/api/users/me')
  return data
}

export async function updateMe(payload: UpdateProfilePayload): Promise<UserInfo> {
  const { data } = await http.put<UserInfo>('/api/users/me', payload)
  return data
}

export async function changePassword(old_password: string, new_password: string): Promise<void> {
  await http.put('/api/users/me/password', { old_password, new_password })
}
