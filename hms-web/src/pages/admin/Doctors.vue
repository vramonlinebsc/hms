<template>
  <v-container fluid>
    <!-- Top Bar -->
    <v-row class="mb-4">
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <v-btn
          variant="text"
          color="primary"
          @click="goBack"
        >
          ← Back to Dashboard
        </v-btn>

        <v-btn
          size="small"
          variant="outlined"
          color="primary"
          :loading="loading"
          @click="fetchDoctors"
        >
          Refresh
        </v-btn>
      </v-col>
    </v-row>

    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="page-title">Doctors</h1>
        <p class="page-subtitle">
          Administrative control of registered doctors
        </p>
      </v-col>
    </v-row>

    <!-- Error -->
    <v-row v-if="error" class="mt-4">
      <v-col cols="12">
        <v-alert type="error" variant="outlined">
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Table -->
    <v-row class="mt-6">
      <v-col cols="12">
        <v-card>
          <v-table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Specialization</th>
                <th>Status</th>
                <th class="text-center">Actions</th>
              </tr>
            </thead>

            <tbody>
              <!-- Loading -->
              <tr v-if="loading">
                <td colspan="5" class="text-center py-8 text-medium-emphasis">
                  Loading doctors…
                </td>
              </tr>

              <!-- Empty -->
              <tr v-else-if="doctors.length === 0">
                <td colspan="5" class="text-center py-8 text-medium-emphasis">
                  No doctors found
                </td>
              </tr>

              <!-- Rows -->
              <tr v-for="doc in doctors" :key="doc.user_id">
                <td>{{ doc.user_id }}</td>
                <td>{{ doc.name || "—" }}</td>
                <td>{{ doc.specialization || "—" }}</td>
                <td>
                  <v-chip
                    size="small"
                    variant="flat"
                    :color="doc.is_blacklisted ? 'error' : 'success'"
                  >
                    {{ doc.is_blacklisted ? "BLACKLISTED" : "ACTIVE" }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <v-btn
                    size="small"
                    variant="outlined"
                    :color="doc.is_blacklisted ? 'success' : 'error'"
                    :loading="togglingId === doc.user_id"
                    @click="toggleBlacklist(doc)"
                  >
                    {{ doc.is_blacklisted ? "Unblacklist" : "Blacklist" }}
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

/* -----------------------------
   Types
----------------------------- */

interface Doctor {
  user_id: number
  name: string | null
  specialization: string | null
  is_blacklisted: number
}

/* -----------------------------
   State
----------------------------- */

const doctors = ref<Doctor[]>([])
const loading = ref(false)
const error = ref("")
const togglingId = ref<number | null>(null)

/* -----------------------------
   Navigation
----------------------------- */

function goBack() {
  router.push("/admin")
}

/* -----------------------------
   Helpers
----------------------------- */

function getToken(): string | null {
  return localStorage.getItem("hms_token")
}

/* -----------------------------
   API
----------------------------- */

async function fetchDoctors() {
  loading.value = true
  error.value = ""

  try {
    const token = getToken()
    if (!token) {
      router.push("/login")
      return
    }

    const res = await fetch(
      "http://127.0.0.1:5000/admin/doctors",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    if (res.status === 401 || res.status === 403) {
      router.push("/login")
      return
    }

    if (!res.ok) {
      throw new Error("Fetch failed")
    }

    doctors.value = await res.json()
  } catch (e) {
    console.error(e)
    error.value = "Unable to load doctors."
  } finally {
    loading.value = false
  }
}

async function toggleBlacklist(doc: Doctor) {
  const action = doc.is_blacklisted ? "unblacklist" : "blacklist"

  if (
    !confirm(
      `${action === "blacklist" ? "Blacklist" : "Unblacklist"} doctor #${doc.user_id}?`
    )
  ) {
    return
  }

  togglingId.value = doc.user_id

  try {
    const token = getToken()
    if (!token) {
      router.push("/login")
      return
    }

    const res = await fetch(
      `http://127.0.0.1:5000/admin/doctors/${doc.user_id}/${action}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    if (!res.ok) {
      throw new Error("Toggle failed")
    }

    await fetchDoctors()
  } catch (e) {
    console.error(e)
    alert("Operation failed")
  } finally {
    togglingId.value = null
  }
}

/* -----------------------------
   Lifecycle
----------------------------- */

onMounted(fetchDoctors)
</script>

<style scoped>
.page-title {
  font-size: 1.8rem;
  font-weight: 600;
}

.page-subtitle {
  color: #666;
  margin-top: 4px;
}
</style>

