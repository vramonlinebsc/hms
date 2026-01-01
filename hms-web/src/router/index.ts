import { createRouter, createWebHistory } from "vue-router"
import BaseLayout from "../layouts/BaseLayout.vue"
import Login from "../pages/Login.vue"

/* -----------------------
   ROUTES
------------------------ */
const routes = [
  {
    path: "/",
    component: BaseLayout,
    children: [
      { path: "", redirect: "/login" },
      { path: "login", component: Login },

      {
        path: "admin",
        component: () => import("../pages/admin/AdminDashboard.vue"),
        meta: { requiresAdmin: true },
      },

      {
        path: "admin/appointments",
        component: () => import("../pages/admin/Appointments.vue"),
        meta: { requiresAdmin: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/* -----------------------
   ROUTE GUARD (ADMIN ONLY)
------------------------ */
router.beforeEach((to) => {
  if (!to.meta.requiresAdmin) {
    return true
  }

  const token = localStorage.getItem("hms_token")
  const role = localStorage.getItem("hms_role")

  if (!token || role !== "admin") {
    return "/login"
  }

  return true
})

export default router
