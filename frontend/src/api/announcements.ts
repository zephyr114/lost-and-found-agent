import http from './http'
import type { Announcement } from './admin'

export async function getActiveAnnouncements(): Promise<Announcement[]> {
  const { data } = await http.get<Announcement[]>('/api/announcements')
  return data
}
