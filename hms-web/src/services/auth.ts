import axios from "axios"

const API_BASE = "http://localhost:5000" // adjust if needed

type Role = "admin" | "doctor" | "patient" | null

class AuthService {
  private tokenKey = "hms_token"

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey)
  }

  setToken(token: string) {
    localStorage.setItem(this.tokenKey, token)
  }

  clear() {
    localStorage.removeItem(this.tokenKey)
  }

  isAuthenticated(): boolean {
    return !!this.getToken()
  }

  async resolveRole(): Promise<Role> {
    const token = this.getToken()
    if (!token) return null

    const headers = {
      Authorization: `Bearer ${token}`,
    }

    try {
      // Try admin first
      await axios.get(`${API_BASE}/admin/me`, { headers })
      return "admin"
    } catch {}

    try {
      await axios.get(`${API_BASE}/doctor/me`, { headers })
      return "doctor"
    } catch {}

    try {
      await axios.get(`${API_BASE}/patient/me`, { headers })
      return "patient"
    } catch {}

    // Token invalid or expired
    this.clear()
    return null
  }

  async adminLogin(username: string, password: string): Promise<void> {
  const res = await axios.post(`${API_BASE}/admin/login`, {
    username,
    password,
  })

  const token = res.data.token
  if (!token) {
    throw new Error("No token received")
  }

  this.setToken(token)
  }

}

export const auth = new AuthService()
