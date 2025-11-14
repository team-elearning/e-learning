const BASE_URL = 'https://provinces.open-api.vn/api'

export interface LocationBase {
  code: number
  name: string
  codename: string
  division_type: string
}

export interface Province extends LocationBase {
  phone_code: number
  districts?: District[]
}

export interface District extends LocationBase {
  province_code?: number
  wards?: Ward[]
}

export interface Ward extends LocationBase {
  district_code?: number
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { redirect: 'follow' })
  if (!response.ok) {
    throw new Error(`Failed to fetch location data: ${response.status}`)
  }
  return (await response.json()) as T
}

export const locationService = {
  async getProvinces(): Promise<Province[]> {
    return request<Province[]>('/p/')
  },

  async getDistricts(provinceCode: number | string): Promise<District[]> {
    if (!provinceCode) return []
    const data = await request<Province & { districts?: District[] }>(`/p/${provinceCode}?depth=2`)
    return data.districts ?? []
  },

  async getWards(districtCode: number | string): Promise<Ward[]> {
    if (!districtCode) return []
    const data = await request<District & { wards?: Ward[] }>(`/d/${districtCode}?depth=2`)
    return data.wards ?? []
  },
}
