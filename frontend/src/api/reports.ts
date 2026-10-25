import http from './http'
import type { AdminReport } from './admin'

export async function submitReport(payload: {
  target_type: 'item' | 'user' | 'claim'
  target_id: number
  reason: string
  description?: string
}): Promise<AdminReport> {
  const { data } = await http.post<AdminReport>('/api/reports', payload)
  return data
}

export async function getMyReports(page = 1, size = 20): Promise<{ items: AdminReport[]; total: number }> {
  const { data } = await http.get<{ items: AdminReport[]; total: number }>('/api/reports/my', { params: { page, size } })
  return data
}
