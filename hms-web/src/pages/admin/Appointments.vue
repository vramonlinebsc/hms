<template>
  <v-container fluid>
    <!-- Back Navigation -->
    <v-row class="mb-2">
      <v-col cols="12">
        <v-btn
          variant="text"
          color="primary"
          @click="goBack"
        >
          ← Back to Dashboard
        </v-btn>
      </v-col>
    </v-row>

    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="page-title">Appointments</h1>
        <p class="page-subtitle">
          Read-only view of all appointments in the system
        </p>
      </v-col>
    </v-row>

    <!-- Table -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-table>
            <thead>
              <tr>
                <th>Appointment ID</th>
                <th>Date</th>
                <th>Doctor ID</th>
                <th>Patient ID</th>
                <th>Start</th>
                <th>End</th>
                <th>Status</th>
		<th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="appointments.length === 0">
                <td colspan="8" class="text-center py-6">
                  No appointments found
                </td>
              </tr>

              <tr v-for="appt in appointments" :key="appt.appointment_id">
                <td>{{ appt.appointment_id }}</td>
                <td>{{ appt.appt_date }}</td>
                <td>{{ appt.doctor_id }}</td>
                <td>{{ appt.patient_id }}</td>
                <td>{{ appt.start_datetime }}</td>
                <td>{{ appt.end_datetime }}</td>
                <td>
                  <v-chip
				  v-if="appt.status"
                    size="small"
                    :color="statusColor(appt.status)"
                    variant="flat"
                  >
                    {{ appt.status }}
                  </v-chip>
                </td>
		<td>
			<v-btn
					size="small"
					color="error"
					variant="outlined"
					@click.stop="onCancel(appt)"
					>
					Cancel
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

interface Appointment {
  appointment_id: number
  patient_id: number
  doctor_id: number
  start_datetime: string
  end_datetime: string
  status: string
  appt_date: string
}

const appointments = ref<Appointment[]>([])

/* -----------------------------
   Navigation
----------------------------- */

const goBack = () => {
  router.push("/admin")
}

/* -----------------------------
   Admin Actions (UI ONLY)
----------------------------- */

const onCancel = async (appt: Appointment) => {
  try {
    const token = localStorage.getItem("hms_token")

    const res = await fetch(
      `http://127.0.0.1:5000/admin/appointments/${appt.appointment_id}/cancel`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    if (!res.ok) {
      throw new Error("Cancel failed")
    }

    // refresh appointments after cancel
    const refreshed = await fetch(
      "http://127.0.0.1:5000/admin/appointments",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    appointments.value = await refreshed.json()
  } catch (err) {
    console.error("Failed to cancel appointment", err)
  }
}


/* -----------------------------
   Status → Color (UI ONLY)
----------------------------- */

const statusColor = (status: string) => {
  switch (status) {
    case "BOOKED":
      return "primary"
    case "COMPLETED":
      return "success"
    case "CANCELLED":
      return "error"
    case "NO_SHOW":
      return "warning"
    default:
      return "default"
  }
}

/* -----------------------------
   Lifecycle
----------------------------- */

onMounted(async () => {
  try {
    const token = localStorage.getItem("hms_token")

    const res = await fetch(
      "http://127.0.0.1:5000/admin/appointments",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    appointments.value = await res.json()
  } catch (err) {
    console.error("Failed to fetch appointments", err)
  }
})
</script>

