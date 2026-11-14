import http from './http'

export interface MatchSuggestion {
  field: string
  label: string
  current: string
  suggestion: string
  gain: number
  score_after: number
}

export interface MatchInfo {
  id: number
  lost_item_id: number
  found_item_id: number
  match_score: number
  match_reason: string[]
  dimensions?: Record<string, number> | null
  suggestions?: MatchSuggestion[]
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
  story?: string
}

export interface HandoverItem {
  id: number
  title: string
  category: string
  location: string
  images: string[]
  username: string | null
}

export interface HandoverInfo extends MatchInfo {
  code_valid: boolean
  lost_item: HandoverItem
  found_item: HandoverItem
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

export async function getHandoverInfo(matchId: number, code: string): Promise<HandoverInfo> {
  const { data } = await http.get<HandoverInfo>(`/api/matches/${matchId}/handover-info`, { params: { code } })
  return data
}

export async function getStories(): Promise<{ items: StoryItem[]; total: number }> {
  const { data } = await http.get<{ items: StoryItem[]; total: number }>('/api/matches/stories')
  return data
}
