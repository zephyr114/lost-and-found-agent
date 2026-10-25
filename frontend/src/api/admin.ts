import http from './http'
import type { UserInfo } from './user'

export async function listUsers(): Promise<UserInfo[]> {
  const { data } = await http.get<UserInfo[]>('/api/admin/users')
  return data
}
