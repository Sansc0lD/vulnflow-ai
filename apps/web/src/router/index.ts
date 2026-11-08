import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { authStorage } from '@/services/api'

// Public Pages
import Home from '@/pages/public/Home.vue'
import About from '@/pages/public/About.vue'
import Solutions from '@/pages/public/Solutions.vue'
import SolutionDetail from '@/pages/public/SolutionDetail.vue'
import Contact from '@/pages/public/Contact.vue'

// App Pages
import Login from '@/pages/app/Login.vue'
import Register from '@/pages/app/Register.vue'
import Dashboard from '@/pages/app/Dashboard.vue'
import Projects from '@/pages/app/Projects.vue'
import Triage from '@/pages/app/Triage.vue'
import AINarrative from '@/pages/app/AINarrative.vue'
import ThemeStudio from '@/pages/app/ThemeStudio.vue'
import Billing from '@/pages/app/Billing.vue'

const routes: RouteRecordRaw[] = [
  // Public Routes (Desain Web requirement)
  { path: '/', name: 'home', component: Home },
  { path: '/about', name: 'about', component: About },
  { path: '/solutions', name: 'solutions', component: Solutions },
  { path: '/solutions/:id', name: 'solution-detail', component: SolutionDetail },
  { path: '/contact', name: 'contact', component: Contact },

  // Auth Routes
  { path: '/app/login', name: 'login', component: Login, meta: { guestOnly: true } },
  { path: '/app/register', name: 'register', component: Register, meta: { guestOnly: true } },

  // Authenticated App Routes (IPPL SaaS Wireframes)
  { path: '/app', redirect: '/app/dashboard' },
  { path: '/app/dashboard', name: 'app-dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/app/projects', name: 'app-projects', component: Projects, meta: { requiresAuth: true } },
  { path: '/app/triage', name: 'app-triage', component: Triage, meta: { requiresAuth: true } },
  { path: '/app/ai-review', name: 'app-ai-review', component: AINarrative, meta: { requiresAuth: true } },
  { path: '/app/theme', name: 'app-theme', component: ThemeStudio, meta: { requiresAuth: true } },
  { path: '/app/billing', name: 'app-billing', component: Billing, meta: { requiresAuth: true } },

  // Catch-all 404
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to, _from, next) => {
  const token = authStorage.getToken()
  const isAuthRoute = to.path.startsWith('/app') && !to.meta.guestOnly

  if (isAuthRoute && !token) {
    next({ path: '/app/login', query: { redirect: to.fullPath } })
  } else if (to.meta.guestOnly && token) {
    next('/app/dashboard')
  } else {
    next()
  }
})

export default router
