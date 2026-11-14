import http from './http'

export interface ExtractedAttributes {
  title: string
  category: string
  color: string
  brand: string
  location: string
}

export interface ImageAnalysis {
  image_url: string
  color: string | null
  brightness: number | null
  dominant_rgb: number[] | null
  top_colors?: { name: string; ratio: number }[]
  orientation?: string | null
  aspect_ratio?: number | null
  tags?: string[]
  source?: string
  category?: string
  brand?: string
  description?: string
}

export interface DialogDraft {
  title: string
  category: string
  color: string
  brand: string
  location: string
  event_time: string
  description: string
}

export interface DialogResult {
  reply: string
  draft: DialogDraft
  missing: string[]
  next_field: string | null
  options: string[]
  done: boolean
  progress: number
}

export interface PrecheckResult {
  level: 'low' | 'medium' | 'high'
  score: number
  reasons: string[]
  suggestion: string
}

export interface ClaimCheckResult {
  score: number
  verdict: 'high' | 'medium' | 'low'
  reasons: string[]
  suggestions: { field: string; label: string; current: string; suggestion: string; gain: number; score_after: number }[]
}

export async function claimCheck(itemId: number, description: string): Promise<ClaimCheckResult> {
  const { data } = await http.post<ClaimCheckResult>('/api/agent/claim-check', { item_id: itemId, description })
  return data
}

export async function extractAttributes(text: string): Promise<ExtractedAttributes> {
  const { data } = await http.post<ExtractedAttributes>('/api/agent/extract', { text })
  return data
}

export async function dialogStep(payload: {
  text: string
  draft: Partial<DialogDraft>
  item_type: 'lost' | 'found'
}): Promise<DialogResult> {
  const { data } = await http.post<DialogResult>('/api/agent/dialog', payload)
  return data
}

export async function precheckItem(payload: {
  title: string
  description?: string
  location?: string
}): Promise<PrecheckResult> {
  const { data } = await http.post<PrecheckResult>('/api/agent/precheck', payload)
  return data
}

export async function analyzeImage(file: File): Promise<ImageAnalysis> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post<ImageAnalysis>('/api/agent/analyze-image', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
