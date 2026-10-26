import http from './http'

export interface Overview {
  items_total: number
  items_lost: number
  items_found: number
  items_claimed: number
  claims_total: number
  matches_total: number
  matches_confirmed: number
  users_total: number
}

export async function getOverview(): Promise<Overview> {
  const { data } = await http.get<Overview>('/api/stats/overview')
  return data
}
