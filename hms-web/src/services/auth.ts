import axios from "axios"

const API_BASE = "http://localhost:5000"

type Role = "admin" | "doctor" | "patient" | null

class AuthService {
  private tokenKey = "hms_token"

  /* ---------------- Token helpers ---------------- */

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

  private authHeaders() {
    const token = this.getToken()
    if (!token) {
      throw new Error("No token")
    }
    return {
      Authorization: `Bearer ${token}`,
    }
  }

  /* ---------------- Session resolution ---------------- */

  async resolveRole(): Promise<Role> {
    try {
      await this.adminMe()
      return "admin"
    } catch {}

    try {
      await this.doctorMe()
      return "doctor"
    } catch {}

    try {
      await this.patientMe()
      return "patient"
    } catch {}

    this.clear()
    return null
  }

  /* ---------------- Explicit session checks ---------------- */

  async adminMe() {
    const res = await axios.get(`${API_BASE}/admin/me`, {
      headers: this.authHeaders(),
    })
    return res.data
  }

  async doctorMe() {
    const res = await axios.get(`${API_BASE}/doctor/me`, {
      headers: this.authHeaders(),
    })
    return res.data
  }

  async patientMe() {
    const res = await axios.get(`${API_BASE}/patient/me`, {
      headers: this.authHeaders(),
    })
    return res.data
  }

  /* ---------------- Login / Logout ---------------- */

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

  adminLogout() {
    this.clear()
  }
}

export const auth = new AuthService()

