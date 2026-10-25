import http from './http'
import type { UserInfo } from './user'
import type { Claim } from './claims'

export interface Statistics {
  users_total: number
  users_active: number
  users_disabled: number
  items_total: number
  items_lost: number
  items_found: number
  items_pending_audit: number
  items_claimed: number
  claims_total: number
  claims_pending: number
  matches_total: number
  reports_pending: number
  announcements_active: number
}

export interface PendingItem {
  id: number
  item_type: string
  title: string
  category: string
  location: string
  description: string | null
  images: string[]
  event_time: string
  created_at: string
  username: string | null
}

export interface AdminUser extends UserInfo {
  // 同 UserInfo
}

export interface AdminReport {
  id: number
  reporter_id: number
  reporter_name: string | null
  target_type: string
  target_id: number
  reason: string
  description: string | null
  status: string
  handler_id: number | null
  handler_comment: string | null
  created_at: string
}

export interface Announcement {
  id: number
  title: string
  content: string
  status: string
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface AgentLogRow {
  id: number
  user_id: number | null
  task_type: string
  tool_name: string
  input_data: unknown
  tool_result: unknown
  execution_time_ms: number
  status: string
  created_at: string
}

export interface OperationLogRow {
  id: number
  admin_id: number
  admin_name: string | null
  action: string
  target_type: string
  target_id: number | null
  detail: unknown
  created_at: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export async function getStatistics(): Promise<Statistics> {
  const { data } = await http.get<Statistics>('/api/admin/statistics')
  return data
}

export async function getPendingItems(page = 1, size = 20): Promise<Page<PendingItem>> {
  const { data } = await http.get<Page<PendingItem>>('/api/admin/items/pending', { params: { page, size } })
  return data
}

export async function auditItem(itemId: number, decision: 'approve' | 'reject', comment?: string): Promise<void> {
  await http.put(`/api/admin/items/${itemId}/audit`, { decision, comment: comment || null })
}

export async function adminDeleteItem(itemId: number): Promise<void> {
  await http.delete(`/api/admin/items/${itemId}`)
}

export async function listUsers(page = 1, size = 50): Promise<Page<AdminUser>> {
  const { data } = await http.get<Page<AdminUser>>('/api/admin/users', { params: { page, size } })
  return data
}

export async function setUserStatus(userId: number, status: 'active' | 'disabled'): Promise<void> {
  await http.put(`/api/admin/users/${userId}/status`, { status })
}

export async function listAllClaims(page = 1, size = 20): Promise<Page<Claim>> {
  const { data } = await http.get<Page<Claim>>('/api/admin/claims', { params: { page, size } })
  return data
}

export async function listReports(page = 1, size = 20, status?: string): Promise<Page<AdminReport>> {
  const { data } = await http.get<Page<AdminReport>>('/api/admin/reports', { params: { page, size, status } })
  return data
}

export async function handleReport(reportId: number, action: 'handled' | 'dismissed', comment?: string): Promise<void> {
  await http.put(`/api/admin/reports/${reportId}/handle`, { action, comment: comment || null })
}

export async function adminListAnnouncements(): Promise<Announcement[]> {
  const { data } = await http.get<Announcement[]>('/api/admin/announcements')
  return data
}

export async function createAnnouncement(payload: { title: string; content: string }): Promise<Announcement> {
  const { data } = await http.post<Announcement>('/api/admin/announcements', payload)
  return data
}

export async function updateAnnouncement(id: number, payload: Partial<Announcement>): Promise<Announcement> {
  const { data } = await http.put<Announcement>(`/api/admin/announcements/${id}`, payload)
  return data
}

export async function deleteAnnouncement(id: number): Promise<void> {
  await http.delete(`/api/admin/announcements/${id}`)
}

export async function listAgentLogs(page = 1, size = 50): Promise<Page<AgentLogRow>> {
  const { data } = await http.get<Page<AgentLogRow>>('/api/admin/agent-logs', { params: { page, size } })
  return data
}

export async function listOperationLogs(page = 1, size = 50): Promise<Page<OperationLogRow>> {
  const { data } = await http.get<Page<OperationLogRow>>('/api/admin/operation-logs', { params: { page, size } })
  return data
}
