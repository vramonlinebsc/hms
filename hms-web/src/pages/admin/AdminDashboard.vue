i<template>
  <v-container fluid>
    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="page-title">Admin Dashboard</h1>
        <p class="page-subtitle">
          Hospital administration overview
        </p>
      </v-col>
    </v-row>

    <!-- Skeleton Cards -->
    <v-row class="mt-6" dense>
      <v-col cols="12" md="3" v-for="label in cards" :key="label">
        <v-card height="120" class="d-flex align-center justify-center">
          <div class="skeleton-card">
            <div class="skeleton-title">{{ label }}</div>
            <div class="skeleton-value">—</div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Navigation -->
    <v-row class="mt-8">
      <v-col cols="12">
        <v-btn
          color="primary"
          variant="flat"
          @click="goToAppointments"
        >
          Manage Appointments
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"

const router = useRouter()

const cards = [
  "Doctors",
  "Patients",
  "Appointments Today",
  "No-Shows",
  "Cancelled",
]

function goToAppointments() {
  router.push("/admin/appointments")
}
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

.skeleton-card {
  text-align: center;
}

.skeleton-title {
  font-size: 0.95rem;
  color: #777;
}

.skeleton-value {
  font-size: 1.6rem;
  font-weight: 500;
  margin-top: 6px;
}
</style>

