<template>
  <v-container fluid>
    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="page-title">Admin Dashboard</h1>
        <p class="page-subtitle">
          Hospital overview and administrative controls
        </p>
      </v-col>
    </v-row>

    <!-- KPI Cards -->
    <v-row class="mt-4">
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title>Total Doctors</v-card-title>
          <v-card-text class="kpi-value">
            {{ doctorCount === null ? "—" : doctorCount }}
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-title>Total Patients</v-card-title>
          <v-card-text class="kpi-value">
            {{ patientCount === null ? "—" : patientCount }}
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-title>Appointments Today</v-card-title>
          <v-card-text class="kpi-value">
            {{ appointmentsTodayCount === null ? "—" : appointmentsTodayCount }}
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-title>No-Shows</v-card-title>
          <v-card-text class="kpi-value">
            {{ noShowsCount === null ? "—" : noShowsCount }}
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-title>Cancelled</v-card-title>
          <v-card-text class="kpi-value">
            {{ cancelledCount === null ? "—" : cancelledCount }}
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Navigation -->
    <v-row class="mt-6">
      <v-col cols="12">
        <v-btn
          color="primary"
          variant="flat"
          @click="goToAppointments"
        >
          View All Appointments
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

const doctorCount = ref<number | null>(null)
const patientCount = ref<number | null>(null)
const appointmentsTodayCount = ref<number | null>(null)
const noShowsCount = ref<number | null>(null)
const cancelledCount = ref<number | null>(null)

/* -----------------------------
   Navigation
----------------------------- */

const goToAppointments = () => {
  router.push("/admin/appointments")
}

/* -----------------------------
   Fetch helpers
----------------------------- */

const fetchNoShowsCount = async () => {
  try {
    const token = localStorage.getItem("hms_token")
    const res = await fetch(
      "http://127.0.0.1:5000/admin/stats/appointments/no-shows",
      { headers: { Authorization: `Bearer ${token}` } }
    )
    const data = await res.json()
    noShowsCount.value = data.count
  } catch (err) {
    console.error("Failed to fetch no-shows count", err)
  }
}

const fetchCancelledCount = async () => {
  try {
    const token = localStorage.getItem("hms_token")
    const res = await fetch(
      "http://127.0.0.1:5000/admin/stats/appointments/cancelled",
      { headers: { Authorization: `Bearer ${token}` } }
    )
    const data = await res.json()
    cancelledCount.value = data.count
  } catch (err) {
    console.error("Failed to fetch cancelled count", err)
  }
}

/* -----------------------------
   Lifecycle
----------------------------- */

onMounted(async () => {
  const token = localStorage.getItem("hms_token")

  const doctorRes = await fetch(
    "http://127.0.0.1:5000/admin/stats/doctors/count",
    { headers: { Authorization: `Bearer ${token}` } }
  )
  doctorCount.value = (await doctorRes.json()).count

  const patientRes = await fetch(
    "http://127.0.0.1:5000/admin/stats/patients/count",
    { headers: { Authorization: `Bearer ${token}` } }
  )
  patientCount.value = (await patientRes.json()).count

  const apptRes = await fetch(
    "http://127.0.0.1:5000/admin/stats/appointments/today",
    { headers: { Authorization: `Bearer ${token}` } }
  )
  appointmentsTodayCount.value = (await apptRes.json()).count

  await fetchNoShowsCount()
  await fetchCancelledCount()
})
</script>
