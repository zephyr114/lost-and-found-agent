import http from './http'

export type ItemType = 'lost' | 'found'

export interface Item {
  id: number
  user_id: number
  item_type: ItemType
  title: string
  category: string
  description: string | null
  color: string | null
  brand: string | null
  location: string
  latitude: number | null
  longitude: number | null
  event_time: string
  images: string[]
  status: string
  audit_status: string
  created_at: string
  updated_at: string
  username: string | null
}

export interface ItemPayload {
  item_type: ItemType
  title: string
  category: string
  description?: string
  color?: string
  brand?: string
  location: string
  latitude?: number
  longitude?: number
  event_time: string
}

export interface ItemListParams {
  q?: string
  item_type?: ItemType
  category?: string
  location?: string
  sort?: 'newest' | 'oldest' | 'distance'
  lat?: number
  lng?: number
  page?: number
  size?: number
  mine?: boolean
}

export interface ItemListResponse {
  items: Item[]
  total: number
  page: number
  size: number
}

export async function createItem(payload: ItemPayload): Promise<Item> {
  const { data } = await http.post<Item>('/api/items', payload)
  return data
}

export async function getItems(params: ItemListParams): Promise<ItemListResponse> {
  const { data } = await http.get<ItemListResponse>('/api/items', { params })
  return data
}

export async function getItem(id: number): Promise<Item> {
  const { data } = await http.get<Item>(`/api/items/${id}`)
  return data
}

export async function updateItem(id: number, payload: Partial<ItemPayload>): Promise<Item> {
  const { data } = await http.put<Item>(`/api/items/${id}`, payload)
  return data
}

export async function deleteItem(id: number): Promise<void> {
  await http.delete(`/api/items/${id}`)
}

export async function uploadImages(id: number, files: File[]): Promise<Item> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const { data } = await http.post<Item>(`/api/items/${id}/images`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteImage(id: number, index: number): Promise<Item> {
  const { data } = await http.delete<Item>(`/api/items/${id}/images/${index}`)
  return data
}

export async function getCategories(): Promise<string[]> {
  const { data } = await http.get<{ categories: string[] }>('/api/items/categories')
  return data.categories
}
