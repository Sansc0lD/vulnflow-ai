import { computed, reactive } from 'vue'
import {
  api,
  authStorage,
  type Project,
  type RegisterResponse,
  type SubscriptionStatus,
  type TokenResponse,
  type UserDTO,
  type Workspace,
  type WorkspaceMembership,
  type WorkspaceRole,
} from '@/services/api'

interface SessionState {
  hasToken: boolean
  user: UserDTO | null
  memberships: WorkspaceMembership[]
  activeWorkspaceId: string | null
  activeWorkspace: Workspace | null
  subscription: SubscriptionStatus | null
  projects: Project[]
  activeProjectId: string | null
  initialized: boolean
  hydrating: boolean
}

const state = reactive<SessionState>({
  hasToken: Boolean(authStorage.getToken()),
  user: authStorage.getUser(),
  memberships: [],
  activeWorkspaceId: authStorage.getActiveWorkspaceId(),
  activeWorkspace: authStorage.getActiveWorkspace(),
  subscription: null,
  projects: [],
  activeProjectId: authStorage.getActiveProjectId(),
  initialized: false,
  hydrating: false,
})

let inFlightHydration: Promise<void> | null = null

const isAuthenticated = computed(() => state.hasToken)
const isSuperadmin = computed(() => Boolean(state.user?.is_superadmin))

const activeRole = computed<WorkspaceRole>(() => {
  const match = state.memberships.find((m) => m.id === state.activeWorkspaceId)
  return match?.role ?? 'VIEWER'
})

const activeProject = computed<Project | null>(() => {
  return state.projects.find((p) => p.id === state.activeProjectId) ?? null
})

async function loadWorkspaceContext(workspaceId: string): Promise<void> {
  const [ws, sub, projList] = await Promise.all([
    api.workspaces.get(workspaceId),
    api.billing.getSubscription(workspaceId),
    api.projects.list(workspaceId),
  ])

  state.activeWorkspace = ws
  authStorage.setActiveWorkspace(ws)
  state.subscription = sub
  state.projects = projList

  const existingValid = projList.some((p) => p.id === state.activeProjectId)
  if (!existingValid) {
    const firstActive = projList.find((p) => p.status === 'ACTIVE') ?? projList[0] ?? null
    state.activeProjectId = firstActive?.id ?? null
    authStorage.setActiveProjectId(state.activeProjectId)
  }
}

function clearWorkspaceContext(): void {
  state.activeWorkspace = null
  state.subscription = null
  state.projects = []
  state.activeProjectId = null
  authStorage.setActiveProjectId(null)
}

async function hydrate(force = false): Promise<void> {
  if (!authStorage.getToken()) {
    resetState()
    return
  }
  state.hasToken = true
  if (state.initialized && !force) {
    return
  }
  if (inFlightHydration) {
    return inFlightHydration
  }

  state.hydrating = true
  inFlightHydration = (async () => {
    try {
      const me = await api.auth.me()
      state.user = me.user
      authStorage.setUser(me.user)
      state.memberships = me.workspaces

      const preferredId = state.activeWorkspaceId || authStorage.getActiveWorkspaceId()
      const validMembership = me.workspaces.find((m) => m.id === preferredId) ?? me.workspaces[0]

      if (me.user.is_superadmin) {
        state.activeWorkspaceId = null
        authStorage.setActiveWorkspaceId(null)
        clearWorkspaceContext()
      } else if (validMembership) {
        state.activeWorkspaceId = validMembership.id
        authStorage.setActiveWorkspaceId(validMembership.id)
        await loadWorkspaceContext(validMembership.id)
      } else {
        state.activeWorkspaceId = null
        clearWorkspaceContext()
      }
      state.initialized = true
    } catch (err) {
      authStorage.clear()
      resetState()
      throw err
    } finally {
      state.hydrating = false
      inFlightHydration = null
    }
  })()

  return inFlightHydration
}

function resetState(): void {
  state.hasToken = false
  state.user = null
  state.memberships = []
  state.activeWorkspaceId = null
  state.activeWorkspace = null
  state.subscription = null
  state.projects = []
  state.activeProjectId = null
  state.initialized = false
  state.hydrating = false
}

async function applyLogin(res: TokenResponse): Promise<void> {
  authStorage.setToken(res.access_token)
  authStorage.setUser(res.user)
  state.hasToken = true
  state.user = res.user
  state.memberships = res.workspaces
  if (res.user.is_superadmin) {
    state.activeWorkspaceId = null
    authStorage.setActiveWorkspaceId(null)
    clearWorkspaceContext()
  } else {
    const firstWs = res.workspaces[0]?.id ?? null
    if (firstWs) {
      state.activeWorkspaceId = firstWs
      authStorage.setActiveWorkspaceId(firstWs)
    }
  }
  await hydrate(true)
}

async function applyRegister(res: RegisterResponse): Promise<void> {
  authStorage.setToken(res.access_token)
  authStorage.setActiveWorkspaceId(res.workspace_id)
  state.hasToken = true
  state.activeWorkspaceId = res.workspace_id
  await hydrate(true)
}

async function switchWorkspace(workspaceId: string): Promise<void> {
  if (!workspaceId) return
  state.activeWorkspaceId = workspaceId
  authStorage.setActiveWorkspaceId(workspaceId)
  state.activeProjectId = null
  authStorage.setActiveProjectId(null)
  await loadWorkspaceContext(workspaceId)
}

function selectProject(projectId: string | null): void {
  state.activeProjectId = projectId
  authStorage.setActiveProjectId(projectId)
}

async function refreshWorkspace(): Promise<void> {
  if (!state.activeWorkspaceId) return
  const ws = await api.workspaces.get(state.activeWorkspaceId)
  state.activeWorkspace = ws
  authStorage.setActiveWorkspace(ws)
  const membership = state.memberships.find((m) => m.id === state.activeWorkspaceId)
  if (membership) {
    membership.name = ws.name
  }
}

async function refreshProjects(): Promise<void> {
  if (!state.activeWorkspaceId) return
  const list = await api.projects.list(state.activeWorkspaceId)
  state.projects = list
  const stillValid = list.some((p) => p.id === state.activeProjectId)
  if (!stillValid) {
    const next = list.find((p) => p.status === 'ACTIVE') ?? list[0] ?? null
    state.activeProjectId = next?.id ?? null
    authStorage.setActiveProjectId(state.activeProjectId)
  }
}

async function refreshSubscription(): Promise<void> {
  if (!state.activeWorkspaceId) return
  state.subscription = await api.billing.getSubscription(state.activeWorkspaceId)
}

async function logout(): Promise<void> {
  if (authStorage.getToken()) {
    try {
      await api.auth.logout()
    } catch {
      // Clear local credentials even if backend token revocation failed or expired.
    }
  }
  authStorage.clear()
  resetState()
}

export const session = {
  state,
  isAuthenticated,
  isSuperadmin,
  activeRole,
  activeProject,
  hydrate,
  applyLogin,
  applyRegister,
  switchWorkspace,
  selectProject,
  refreshWorkspace,
  refreshProjects,
  refreshSubscription,
  logout,
}
