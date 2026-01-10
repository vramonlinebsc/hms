<template>
  <div class="viewport">
    <div class="ambient"></div>

    <section class="panel">
      <header class="brand">
        <div class="logo">HMS</div>
        <div class="subtitle">Hospital Management System</div>
      </header>

      <div class="form">
        <!-- Username -->
        <v-text-field
          v-model="username"
          variant="solo"
          density="comfortable"
          placeholder="Username"
          autocomplete="username"
          hide-details
          class="input-field"
          data-testid="login-username"
        />

        <!-- Password -->
        <v-text-field
          v-model="password"
          variant="solo"
          density="comfortable"
          placeholder="Password"
          autocomplete="current-password"
          :type="showPassword ? 'text' : 'password'"
          hide-details
          class="input-field"
          data-testid="login-password"
        >
          <template #append-inner>
            <v-icon
              class="cursor-pointer eye-icon"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'mdi-eye-off' : 'mdi-eye' }}
            </v-icon>
          </template>
        </v-text-field>

        <!-- Login Button -->
        <v-btn
          class="login-btn"
          height="54"
          block
          :loading="loading"
          @click="handleLogin"
          data-testid="login-submit"
        >
          Continue
        </v-btn>
      </div>
    </section>

    <v-snackbar v-model="showError" color="error" :timeout="3000">
      {{ errorMessage }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { auth } from "../services/auth"

const username = ref("")
const password = ref("")
const showPassword = ref(false)

const loading = ref(false)
const errorMessage = ref("")
const showError = ref(false)

const router = useRouter()

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMessage.value = "Username and password required"
    showError.value = true
    return
  }

  loading.value = true
  showError.value = false

  try {
    await auth.adminLogin(username.value, password.value)
    console.log("ADMIN LOGIN SUCCESS")
    await router.push("/admin")
  } catch (err: any) {
    errorMessage.value = err?.message || "Invalid credentials"
    showError.value = true
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ---------- Layout ---------- */

.viewport {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: radial-gradient(
    circle at 20% 20%,
    #f2f5ff,
    #e6ebf5 40%,
    #dfe4ee
  );
  overflow: hidden;
  font-size: 18px;
}

.ambient {
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(circle at 70% 30%, rgba(120, 140, 255, 0.35), transparent 40%),
    radial-gradient(circle at 30% 70%, rgba(120, 200, 255, 0.25), transparent 45%);
  filter: blur(90px);
}

.panel {
  position: relative;
  width: 100%;
  max-width: 460px;
  padding: 40px 36px 42px;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(20px);
  box-shadow:
    0 35px 70px rgba(0, 0, 0, 0.14),
    0 14px 30px rgba(0, 0, 0, 0.10);
}

/* ---------- Branding ---------- */

.brand {
  margin-bottom: 34px;
}

.logo {
  font-size: 2.1rem;
  font-weight: 600;
  letter-spacing: 0.6px;
}

.subtitle {
  margin-top: 8px;
  font-size: 1.05rem;
  color: #555;
}

/* ---------- Form ---------- */

.form {
  display: grid;
  gap: 22px;
}

/* ---------- Inputs ---------- */

.input-field {
  font-size: 1.05rem;
}

:deep(.v-field--variant-solo) {
  border-radius: 16px;
  transition:
    box-shadow 0.22s ease,
    transform 0.22s ease,
    background-color 0.22s ease;
}

:deep(.v-field--variant-solo:hover) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.v-field--variant-solo.v-field--active) {
  box-shadow: 0 10px 28px rgba(90, 110, 255, 0.35);
  transform: translateY(-2px);
}

.eye-icon {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}
.eye-icon:hover {
  opacity: 1;
}

/* ---------- Button ---------- */

.login-btn {
  margin-top: 6px;
  border-radius: 18px;
  font-size: 1.05rem;
  font-weight: 500;
  text-transform: none;
  background: linear-gradient(
    135deg,
    #6f7dff,
    #5aa6ff
  );
  color: white;
  box-shadow:
    0 12px 28px rgba(90, 110, 255, 0.35);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    filter 0.18s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow:
    0 18px 36px rgba(90, 110, 255, 0.45);
  filter: brightness(1.08);
}
</style>

