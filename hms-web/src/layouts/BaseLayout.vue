<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter, onBeforeRouteUpdate } from "vue-router"

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

onBeforeRouteUpdate(() => {
  evaluateAuth()
})
</script>

