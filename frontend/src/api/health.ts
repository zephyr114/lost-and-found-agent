import http from './http'

export interface HealthInfo {
  status: string
  service: string
  version: string
  environment: string
  database: string
  time: string
}

export async function getHealth(): Promise<HealthInfo> {
  const { data } = await http.get<HealthInfo>('/health')
  return data
}
