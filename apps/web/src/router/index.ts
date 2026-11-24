import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { authStorage } from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

// Public Pages
const Home = () => import('@/pages/public/Home.vue')
const About = () => import('@/pages/public/About.vue')
const Solutions = () => import('@/pages/public/Solutions.vue')
const SolutionDetail = () => import('@/pages/public/SolutionDetail.vue')
const Contact = () => import('@/pages/public/Contact.vue')
const VerifyReport = () => import('@/pages/public/VerifyReport.vue')

// Auth Pages
const Login = () => import('@/pages/app/Login.vue')
const Register = () => import('@/pages/app/Register.vue')
const ForgotPassword = () => import('@/pages/app/ForgotPassword.vue')
const ResetPassword = () => import('@/pages/app/ResetPassword.vue')

// Authenticated SaaS App Pages
const Dashboard = () => import('@/pages/app/Dashboard.vue')
const Projects = () => import('@/pages/app/Projects.vue')
const Triage = () => import('@/pages/app/Triage.vue')
const AINarrative = () => import('@/pages/app/AINarrative.vue')
const ThemeStudio = () => import('@/pages/app/ThemeStudio.vue')
const Billing = () => import('@/pages/app/Billing.vue')
const Settings = () => import('@/pages/app/Settings.vue')
const AdminConsole = () => import('@/pages/app/AdminConsole.vue')

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
  {
    path: '/verify/:code?',
    name: 'verify-report',
    component: VerifyReport,
    meta: { title: 'Verify Report — VulnFlow' },
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
      if (!authStorage.getToken()) {
        next({
          path: '/app/login',
          query: { reason: 'session_expired', redirect: to.fullPath },
        })
        return
      }
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
    if (
      to.name === 'register' &&
      !session.state.user?.is_superadmin &&
      typeof to.query.invite === 'string' &&
      to.query.invite.trim()
    ) {
      next({ path: '/app/settings', query: { invite: to.query.invite.trim() } })
      return
    }
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
