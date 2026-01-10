import { createRouter, createWebHistory } from "vue-router"
import BaseLayout from "../layouts/BaseLayout.vue"
import Login from "../pages/Login.vue"
import { auth } from "../services/auth"

/* -----------------------
   ROUTES
------------------------ */
const routes = [
  {
    path: "/login",
    component: Login,
  },

  {
    path: "/",
    component: BaseLayout,
    children: [
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
   ROUTE GUARD (ADMIN)
------------------------ */
router.beforeEach(async (to) => {
  if (!to.meta.requiresAdmin) {
    return true
  }

  try {
    await auth.adminMe()
    return true
  } catch {
    return "/login"
  }
})

export default router

