import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { authStorage } from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

// Public Pages
import Home from '@/pages/public/Home.vue'
import About from '@/pages/public/About.vue'
import Solutions from '@/pages/public/Solutions.vue'
import SolutionDetail from '@/pages/public/SolutionDetail.vue'
import Contact from '@/pages/public/Contact.vue'

// Auth Pages
import Login from '@/pages/app/Login.vue'
import Register from '@/pages/app/Register.vue'
import ForgotPassword from '@/pages/app/ForgotPassword.vue'
import ResetPassword from '@/pages/app/ResetPassword.vue'

// Authenticated SaaS App Pages
import Dashboard from '@/pages/app/Dashboard.vue'
import Projects from '@/pages/app/Projects.vue'
import Triage from '@/pages/app/Triage.vue'
import AINarrative from '@/pages/app/AINarrative.vue'
import ThemeStudio from '@/pages/app/ThemeStudio.vue'
import Billing from '@/pages/app/Billing.vue'
import Settings from '@/pages/app/Settings.vue'
import AdminConsole from '@/pages/app/AdminConsole.vue'

const routes: RouteRecordRaw[] = [
  // Public Routes
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { title: 'VulnFlow — Automated Security Reporting' },
  },
  {
    path: '/about',
    name: 'about',
    component: About,
    meta: { title: 'How It Works — VulnFlow' },
  },
  {
    path: '/solutions',
    name: 'solutions',
    component: Solutions,
    meta: { title: 'Interactive Demo — VulnFlow' },
  },
  {
    path: '/solutions/:id',
    name: 'solution-detail',
    component: SolutionDetail,
    meta: { title: 'Finding Details — VulnFlow' },
  },
  {
    path: '/contact',
    name: 'contact',
    component: Contact,
    meta: { title: 'Pricing & Estimator — VulnFlow' },
  },

  // Auth Routes
  {
    path: '/app/login',
    name: 'login',
    component: Login,
    meta: { guestOnly: true, title: 'Sign In — VulnFlow' },
  },
  {
    path: '/app/register',
    name: 'register',
    component: Register,
    meta: { guestOnly: true, title: 'Create Workspace — VulnFlow' },
  },
  {
    path: '/app/forgot-password',
    name: 'forgot-password',
    component: ForgotPassword,
    meta: { guestOnly: true, title: 'Reset Password — VulnFlow' },
  },
  {
    path: '/app/reset-password',
    name: 'reset-password',
    component: ResetPassword,
    meta: { guestOnly: true, title: 'Set New Password — VulnFlow' },
  },

  // Authenticated App Routes
  { path: '/app', redirect: '/app/dashboard' },
  {
    path: '/app/dashboard',
    name: 'app-dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, tenantOnly: true, title: 'Overview — VulnFlow' },
  },
  {
    path: '/app/projects',
    name: 'app-projects',
    component: Projects,
    meta: { requiresAuth: true, tenantOnly: true, title: 'Projects — VulnFlow' },
  },
  {
    path: '/app/triage',
    name: 'app-triage',
    component: Triage,
    meta: { requiresAuth: true, tenantOnly: true, title: 'Findings — VulnFlow' },
  },
  {
    path: '/app/ai-review',
    name: 'app-ai-review',
    component: AINarrative,
    meta: { requiresAuth: true, tenantOnly: true, title: 'Report Draft — VulnFlow' },
  },
  {
    path: '/app/theme',
    name: 'app-theme',
    component: ThemeStudio,
    meta: { requiresAuth: true, tenantOnly: true, title: 'Branding & PDF — VulnFlow' },
  },
  {
    path: '/app/billing',
    name: 'app-billing',
    component: Billing,
    meta: { requiresAuth: true, tenantOnly: true, title: 'Billing — VulnFlow' },
  },
  {
    path: '/app/settings',
    name: 'app-settings',
    component: Settings,
    meta: { requiresAuth: true, title: 'Settings — VulnFlow' },
  },
  {
    path: '/app/admin',
    name: 'app-admin',
    component: AdminConsole,
    meta: { requiresAuth: true, requiresSuperadmin: true, title: 'Admin Console — VulnFlow' },
  },

  // Catch-all redirects
  { path: '/app/:pathMatch(.*)*', redirect: '/app/dashboard' },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to, _from, next) => {
  const token = authStorage.getToken()
  const requiresAuth = Boolean(to.meta.requiresAuth)

  if (requiresAuth && !token) {
    next({ path: '/app/login', query: { redirect: to.fullPath } })
    return
  }

  if (requiresAuth && token && !session.state.initialized) {
    try {
      await session.hydrate()
    } catch {
      next({ path: '/app/login', query: { redirect: to.fullPath } })
      return
    }
  }

  if (to.meta.tenantOnly && session.state.user?.is_superadmin) {
    next('/app/admin')
    return
  }

  if (to.meta.requiresSuperadmin && !session.state.user?.is_superadmin) {
    toast.warning('Administrator access is required to open the Admin Console.')
    next('/app/dashboard')
    return
  }

  if (to.meta.guestOnly && token) {
    next(session.state.user?.is_superadmin ? '/app/admin' : '/app/dashboard')
    return
  }

  next()
})

router.afterEach((to) => {
  const pageTitle = typeof to.meta.title === 'string' ? to.meta.title : 'VulnFlow'
  document.title = pageTitle
})

export default router
