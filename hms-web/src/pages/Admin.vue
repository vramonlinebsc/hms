<template>
  <div class="admin-page">
    <h2 class="title">Admin Dashboard</h2>

    <!-- Identity -->
    <div class="identity">
      <div><strong>Role:</strong> {{ role }}</div>
      <div><strong>User ID:</strong> {{ userId }}</div>
    </div>

    <!-- Doctors Section -->
    <section class="section">
      <h3>Doctors</h3>

      <div v-if="loadingDoctors" class="muted">
        Loading doctors…
      </div>

      <div v-else-if="doctorError" class="error">
        {{ doctorError }}
      </div>

      <ul v-else-if="doctors.length" class="list">
        <li v-for="doc in doctors" :key="doc.id" class="list-item">
          <div class="name">{{ doc.name }}</div>
          <div class="meta">{{ doc.specialization }}</div>
        </li>
      </ul>

      <div v-else class="muted">
        No doctors found.
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"

/* -----------------------
   TYPES
------------------------ */
type Doctor = {
  id: number
  name: string
  specialization: string
}

/* -----------------------
   STATE
------------------------ */
const role = ref<string | null>(null)
const userId = ref<string | null>(null)

const doctors = ref<Doctor[]>([])
const loadingDoctors = ref(false)
const doctorError = ref<string | null>(null)

/* -----------------------
   INIT
------------------------ */
onMounted(() => {
  const token = localStorage.getItem("hms_token")
  if (!token) return

  try {
    const parts = token.split(".")
    if (parts.length !== 3 || !parts[1]) return

    const decoded = atob(
      parts[1].replace(/-/g, "+").replace(/_/g, "/")
    )

    const payload = JSON.parse(decoded)
    role.value = payload.role ?? null
    userId.value = payload.sub ?? null
  } catch {
    return
  }

  fetchDoctors()
})

/* -----------------------
   API: FETCH DOCTORS
------------------------ */
async function fetchDoctors() {
  const token = localStorage.getItem("hms_token")
  if (!token) return

  loadingDoctors.value = true
  doctorError.value = null

  try {
    const response = await fetch(
      "http://127.0.0.1:5000/admin/doctors",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    if (!response.ok) {
      throw new Error(
        response.status === 404
          ? "Doctors endpoint not available yet"
          : "Failed to load doctors"
      )
    }

    const data = await response.json()
    doctors.value = data
  } catch (err: any) {
    doctorError.value = err.message || "Unexpected error"
  } finally {
    loadingDoctors.value = false
  }
}
</script>

<style scoped>
.admin-page {
  padding: 32px;
}

.title {
  margin-bottom: 12px;
}

.identity {
  margin-bottom: 24px;
  padding: 12px 16px;
  background: #f6f7fb;
  border-radius: 10px;
  max-width: 360px;
}

.section {
  margin-top: 24px;
}

.list {
  margin-top: 12px;
  padding: 0;
  list-style: none;
}

.list-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 8px;
}

.name {
  font-weight: 500;
}

.meta {
  font-size: 0.85rem;
  color: #666;
}

.muted {
  margin-top: 8px;
  color: #777;
}

.error {
  margin-top: 8px;
  color: #b00020;
}
</style>
