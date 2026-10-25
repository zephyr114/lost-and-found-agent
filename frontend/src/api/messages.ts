import http from './http'

export interface Message {
  id: number
  sender_id: number | null
  sender_name: string | null
  receiver_id: number
  message_type: string
  content: string
  is_read: boolean
  created_at: string
}

export interface MessageListResponse {
  items: Message[]
  total: number
  page: number
  size: number
}

export async function getMessages(box: 'inbox' | 'sent' = 'inbox', page = 1, size = 20): Promise<MessageListResponse> {
  const { data } = await http.get<MessageListResponse>('/api/messages', { params: { box, page, size } })
  return data
}

export async function getUnreadCount(): Promise<number> {
  const { data } = await http.get<{ count: number }>('/api/messages/unread-count')
  return data.count
}

export async function markRead(messageId: number): Promise<Message> {
  const { data } = await http.put<Message>(`/api/messages/${messageId}/read`)
  return data
}

export async function markAllRead(): Promise<void> {
  await http.put('/api/messages/read-all')
}

export async function sendMessage(receiverId: number, content: string): Promise<Message> {
  const { data } = await http.post<Message>('/api/messages/send', { receiver_id: receiverId, content })
  return data
}

export const messageTypeText: Record<string, string> = {
  user: '私信',
  system: '系统',
  claim: '认领',
  match: '匹配',
  audit: '审核',
  report: '举报',
  announcement: '公告',
}
