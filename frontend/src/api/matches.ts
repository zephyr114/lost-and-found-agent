import http from './http'

export interface MatchInfo {
  id: number
  lost_item_id: number
  found_item_id: number
  match_score: number
  match_reason: string[]
  dimensions?: Record<string, number> | null
  handover_code?: string | null
  status: string
  created_at: string
  lost_title: string | null
  found_title: string | null
}

export interface StoryItem {
  id: number
  title: string
  item_type: string
  category: string
  location: string
  resolved_at: string
}

export interface MatchListResponse {
  items: MatchInfo[]
  total: number
}

export async function analyzeItem(itemId: number): Promise<MatchListResponse> {
  const { data } = await http.post<MatchListResponse>('/api/matches/analyze', { item_id: itemId })
  return data
}

export async function getRecommendations(itemId: number): Promise<MatchListResponse> {
  const { data } = await http.get<MatchListResponse>('/api/matches/recommendations', { params: { item_id: itemId } })
  return data
}

export async function confirmMatch(matchId: number): Promise<MatchInfo> {
  const { data } = await http.post<MatchInfo>(`/api/matches/${matchId}/confirm`)
  return data
}

export async function getHandoverCode(matchId: number): Promise<string> {
  const { data } = await http.get<{ handover_code: string }>(`/api/matches/${matchId}/code`)
  return data.handover_code
}

export async function handoverMatch(matchId: number, code: string): Promise<MatchInfo> {
  const { data } = await http.post<MatchInfo>(`/api/matches/${matchId}/handover`, { code })
  return data
}

export async function getStories(): Promise<{ items: StoryItem[]; total: number }> {
  const { data } = await http.get<{ items: StoryItem[]; total: number }>('/api/matches/stories')
  return data
}
