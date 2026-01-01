<template>
  <v-app>
    <!-- Header -->
    <v-app-bar flat density="comfortable">
      <v-app-bar-title class="brand">
        <img
          src="@/assets/branding/hms/header/hms-logo-header.png"
          alt="HMS"
          class="brand-logo"
        />
        <span class="brand-text">HMS</span>
      </v-app-bar-title>

      <v-spacer />

      <!-- Logged out -->
      <v-btn
        v-if="!isAuthenticated"
        variant="text"
        @click="goLogin"
      >
        Login
      </v-btn>

      <!-- Logged in -->
      <template v-else>
        <v-btn
          v-if="isAdmin"
          variant="text"
          @click="goAdmin"
        >
          Admin
        </v-btn>

        <v-btn
          variant="text"
          color="error"
          @click="logout"
        >
          Logout
        </v-btn>
      </template>
    </v-app-bar>

    <!-- Page content -->
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"

/* -----------------------
   STATE
------------------------ */
const isAuthenticated = ref(false)
const isAdmin = ref(false)

const router = useRouter()

/* -----------------------
   TOKEN CHECK
------------------------ */
function evaluateAuth() {
  const token = localStorage.getItem("hms_token")

  if (!token) {
    isAuthenticated.value = false
    isAdmin.value = false
    return
  }

  try {
    const parts = token.split(".")

    if (parts.length !== 3 || !parts[1]) {
      throw new Error("Invalid JWT")
    }

    const decoded = atob(
      parts[1].replace(/-/g, "+").replace(/_/g, "/")
    )

    const payload = JSON.parse(decoded)

    isAuthenticated.value = true
    isAdmin.value = payload.role === "admin"
  } catch {
    isAuthenticated.value = false
    isAdmin.value = false
  }
}

/* -----------------------
   NAV ACTIONS
------------------------ */
function goLogin() {
  router.push("/login")
}

function goAdmin() {
  router.push("/admin")
}

function logout() {
  localStorage.removeItem("hms_token")
  isAuthenticated.value = false
  isAdmin.value = false
  router.replace("/login")
}

/* -----------------------
   INIT
------------------------ */
onMounted(() => {
  evaluateAuth()
})
</script>

<style scoped>
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  height: 30px;
  width: auto;
}

.brand-text {
  font-weight: 600;
  letter-spacing: 0.5px;
}
</style>
