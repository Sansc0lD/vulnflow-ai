/**
 * VulnFlow AI API Client
 * Interfaces with FastAPI backend and manages stateless JWT auth tokens.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export interface User {
  id: string
  email: string
  full_name: string
  status: string
}

export interface Workspace {
  id: string
  name: string
  custom_logo_url?: string | null
  primary_color_hex?: string | null
  accent_color_hex?: string | null
  confidentiality_text?: string | null
}

export interface Project {
  id: string
  workspace_id: string
  name: string
  client_name: string
  target_scope: string[]
  roe_start_date: string
  roe_end_date: string
}

export interface Finding {
  id: string
  project_id: string
  title: string
  cwe_id: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
  cvss_score: number
  cvss_vector: string
  status: 'OPEN' | 'IN_REVIEW' | 'REMEDIATED' | 'REOPENED' | 'FALSE_POSITIVE' | 'ACCEPTED_RISK'
  is_quarantined: boolean
  is_curated_for_report: boolean
  target_host: string
  target_port?: number | null
  endpoint_path?: string | null
  version: number
  created_at: string
}

export const authStorage = {
  getToken: () => localStorage.getItem('vulnflow_token'),
  setToken: (token: string) => localStorage.setItem('vulnflow_token', token),
  removeToken: () => localStorage.removeItem('vulnflow_token'),
  getUser: (): User | null => {
    const raw = localStorage.getItem('vulnflow_user')
    return raw ? JSON.parse(raw) : null
  },
  setUser: (user: User) => localStorage.setItem('vulnflow_user', JSON.stringify(user)),
  removeUser: () => localStorage.removeItem('vulnflow_user'),
  clear: () => {
    localStorage.removeItem('vulnflow_token')
    localStorage.removeItem('vulnflow_user')
    localStorage.removeItem('vulnflow_active_workspace')
  },
  getActiveWorkspace: (): Workspace | null => {
    const raw = localStorage.getItem('vulnflow_active_workspace')
    return raw ? JSON.parse(raw) : null
  },
  setActiveWorkspace: (w: Workspace) =>
    localStorage.setItem('vulnflow_active_workspace', JSON.stringify(w)),
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = authStorage.getToken()
  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    authStorage.clear()
    if (!window.location.pathname.startsWith('/app/login')) {
      window.location.href = '/app/login'
    }
    throw new Error('Sesi telah berakhir. Silakan login kembali.')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.message || `HTTP ${response.status}: Permintaan gagal diproses.`)
  }

  return data as T
}

export const api = {
  auth: {
    login: (credentials: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
    register: (payload: {
      email: string
      password: string
      full_name: string
      workspace_name: string
      invitation_token?: string
    }) =>
      request<{ access_token: string; workspace_id: string; user: User }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
  workspaces: {
    list: () => request<Workspace[]>('/workspaces'),
    get: (id: string) => request<Workspace>(`/workspaces/${id}`),
    updateTheme: (
      id: string,
      theme: { primary_color_hex?: string; accent_color_hex?: string; confidentiality_text?: string }
    ) =>
      request<Workspace>(`/workspaces/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(theme),
      }),
  },
  projects: {
    list: (workspaceId: string) => request<Project[]>(`/workspaces/${workspaceId}/projects`),
    create: (workspaceId: string, payload: Omit<Project, 'id' | 'workspace_id'>) =>
      request<Project>(`/workspaces/${workspaceId}/projects`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
  findings: {
    list: (workspaceId: string, projectId: string) =>
      request<Finding[]>(`/workspaces/${workspaceId}/projects/${projectId}/findings`),
    updateStatus: (
      workspaceId: string,
      projectId: string,
      findingId: string,
      status: Finding['status'],
      version: number
    ) =>
      request<Finding>(`/workspaces/${workspaceId}/projects/${projectId}/findings/${findingId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, version }),
      }),
    decryptPoC: (workspaceId: string, projectId: string, findingId: string) =>
      request<{ raw_evidence: string; reproduction_steps: string[] }>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings/${findingId}/poc`
      ),
  },
  ai: {
    generateNarrative: (
      workspaceId: string,
      projectId: string,
      payload: { language: string; finding_ids: string[]; sections_requested: string[] }
    ) =>
      request<{
        narratives: { executive_summary: string; business_impact: string; remediations: any[] }
        is_fallback: boolean
        tokens_consumed: number
      }>(`/workspaces/${workspaceId}/projects/${projectId}/reports/ai-narratives`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
  billing: {
    getSubscription: (workspaceId: string) =>
      request<{ tier: string; reports_used_this_month: number; max_reports: number }>(
        `/workspaces/${workspaceId}/billing/subscription`
      ),
    checkoutPro: (workspaceId: string) =>
      request<{ snap_token: string; redirect_url: string; order_id: string }>(
        `/workspaces/${workspaceId}/billing/checkout`,
        { method: 'POST', body: JSON.stringify({ tier: 'PRO' }) }
      ),
  },
}
