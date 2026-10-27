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
  source?: string
  category?: string
  brand?: string
  description?: string
}

export async function extractAttributes(text: string): Promise<ExtractedAttributes> {
  const { data } = await http.post<ExtractedAttributes>('/api/agent/extract', { text })
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
