import http from './http'

export interface Claim {
  id: number
  item_id: number
  applicant_id: number
  applicant_name: string | null
  proof_description: string
  proof_images: string[]
  contact: string | null
  status: string
  review_comment: string | null
  created_at: string
  updated_at: string
  item_title: string | null
  item_type: string | null
}

export interface ClaimListResponse {
  items: Claim[]
  total: number
  page: number
  size: number
}

export async function createClaim(
  itemId: number,
  data: { proof_description: string; contact?: string; files: File[] },
): Promise<Claim> {
  const form = new FormData()
  form.append('proof_description', data.proof_description)
  if (data.contact) form.append('contact', data.contact)
  data.files.forEach((f) => form.append('files', f))
  const { data: res } = await http.post<Claim>(`/api/items/${itemId}/claims`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res
}

export async function getMyClaims(page = 1, size = 20): Promise<ClaimListResponse> {
  const { data } = await http.get<ClaimListResponse>('/api/claims/my', { params: { page, size } })
  return data
}

export async function getReceivedClaims(page = 1, size = 20): Promise<ClaimListResponse> {
  const { data } = await http.get<ClaimListResponse>('/api/claims/received', { params: { page, size } })
  return data
}

export async function addClaimImages(claimId: number, files: File[]): Promise<Claim> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const { data } = await http.post<Claim>(`/api/claims/${claimId}/images`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function reviewClaim(claimId: number, action: 'approve' | 'reject' | 'request-proof', reviewComment?: string): Promise<Claim> {
  const { data } = await http.put<Claim>(`/api/claims/${claimId}/${action}`, { review_comment: reviewComment || null })
  return data
}

export async function cancelClaim(claimId: number): Promise<Claim> {
  const { data } = await http.delete<Claim>(`/api/claims/${claimId}`)
  return data
}

export const claimStatusText: Record<string, string> = {
  pending: '待处理',
  approved: '已通过',
  rejected: '已拒绝',
  need_more_proof: '待补充证明',
  cancelled: '已撤回',
}

export const claimStatusTag: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  need_more_proof: 'info',
  cancelled: 'info',
}
