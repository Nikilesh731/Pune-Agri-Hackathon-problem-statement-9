const API_BASE = import.meta.env.VITE_API_URL 

export const farmerService = {
  async getFarmers() {
    const res = await fetch(`${API_BASE}/api/applications/farmers`)
    if (!res.ok) throw new Error('Failed to fetch farmers')
    return res.json()
  },

  async getFarmerById(farmerId: string) {
    const res = await fetch(`${API_BASE}/api/applications/farmers/${farmerId}`)
    if (!res.ok) throw new Error('Failed to fetch farmer')
    return res.json()
  },

  async getFarmerApplicationTimeline(farmerId: string) {
    const res = await fetch(`${API_BASE}/api/applications/farmers/${farmerId}/timeline`)
    if (!res.ok) throw new Error('Failed to fetch farmer timeline')
    return res.json()
  }
}
