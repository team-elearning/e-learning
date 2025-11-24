import api from '@/config/axios'

export interface MediaUploadResponse {
  id: string
  url?: string
}

export const mediaService = {
  async upload(file: File, component: string = 'user_avatar'): Promise<MediaUploadResponse> {
    const form = new FormData()
    form.append('file', file)
    form.append('component', component)
    form.append('content_type_str', 'custom_account.User') // Backend yêu cầu field này
    const { data } = await api.post('/media/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return { id: data.id ?? data.media_id ?? data.pk ?? '', url: data.url ?? data.file ?? data.path }
  },
}
