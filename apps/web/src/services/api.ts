/**
 * VulnFlow AI API Client — strictly aligned with packages/contracts Pydantic v2 schemas.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')

export type WorkspaceRole = 'MANAGER' | 'PENTESTER' | 'VIEWER'
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
export type FindingStatus =
  | 'OPEN'
  | 'IN_REVIEW'
  | 'REMEDIATED'
  | 'REOPENED'
  | 'FALSE_POSITIVE'
  | 'ACCEPTED_RISK'
export type Protocol = 'tcp' | 'udp' | 'http' | 'https' | 'icmp' | 'sctp' | 'other'
export type ImageContentType = 'image/png' | 'image/jpeg' | 'image/svg+xml'

export interface ErrorDetail {
  field?: string
  message?: string
}

export class ApiError extends Error {
  status: number
  code: string
  details: ErrorDetail[]
  requestId?: string

  constructor(
    message: string,
    opts: { status: number; code: string; details?: ErrorDetail[]; requestId?: string }
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = opts.status
    this.code = opts.code
    this.details = opts.details ?? []
    this.requestId = opts.requestId
  }
}

export interface UserDTO {
  id: string
  email: string
  full_name: string
  is_superadmin: boolean
  mfa_enabled: boolean
}

export interface WorkspaceMembership {
  id: string
  name: string
  role: WorkspaceRole
  tier?: string | null
}

export interface RegisterResponse {
  user_id: string
  email: string
  full_name: string
  workspace_id: string
  access_token: string
  token_type: string
  expires_in: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserDTO
  workspaces: WorkspaceMembership[]
}

export interface MeResponse {
  user: UserDTO
  workspaces: WorkspaceMembership[]
}

export interface MFASetupResponse {
  secret: string
  otpauth_uri: string
  enabled: boolean
}

export interface Workspace {
  id: string
  name: string
  custom_logo_url?: string | null
  brand_primary_color: string
  brand_secondary_color: string
  confidentiality_text?: string | null
  created_at: string
}

export interface WorkspaceMember {
  user_id: string
  email: string
  full_name: string
  role: WorkspaceRole
}

export interface InviteMemberResponse {
  invitation_token: string
  expires_in: number
}

export interface APIKeyCreateResponse {
  id: string
  label: string
  api_key: string
}

export interface APIKeySummary {
  id: string
  label: string
  is_active: boolean
  last_used_at?: string | null
  created_by_user_id: string
}

export interface LogoUploadResponse {
  custom_logo_url: string
  storage_path: string
}

export interface AuditLogEntry {
  id: string
  created_at: string
  workspace_id: string
  actor_user_id?: string | null
  action: string
  target_entity: string
  ip_address: string
  details: Record<string, unknown>
}

export interface PaginatedAuditLogs {
  items: AuditLogEntry[]
  total: number
  limit: number
  offset: number
}

export interface ProjectTechStack {
  language?:
    | 'python'
    | 'typescript'
    | 'javascript'
    | 'go'
    | 'java'
    | 'php'
    | 'csharp'
    | 'ruby'
    | 'other'
    | null
  framework?:
    | 'fastapi'
    | 'django'
    | 'flask'
    | 'express'
    | 'nestjs'
    | 'nextjs'
    | 'laravel'
    | 'spring_boot'
    | 'aspnet'
    | 'rails'
    | 'gin'
    | 'other'
    | null
  database?: 'postgresql' | 'mysql' | 'mongodb' | 'mssql' | 'sqlite' | 'redis' | 'other' | null
}

export interface Project {
  id: string
  workspace_id: string
  name: string
  client_name: string
  target_scope: string[]
  roe_start_date: string
  roe_end_date: string
  timezone: string
  status: 'ACTIVE' | 'ARCHIVED'
  lead_pentester_id?: string | null
  tech_stack?: ProjectTechStack | null
}

export interface ProjectCreatePayload {
  name: string
  client_name: string
  target_scope: string[]
  roe_start_date: string
  roe_end_date: string
  timezone?: string
  tech_stack?: ProjectTechStack | null
}

export interface ProjectUpdatePayload {
  name?: string
  client_name?: string
  target_scope?: string[]
  roe_start_date?: string
  roe_end_date?: string
  timezone?: string
  status?: 'ACTIVE' | 'ARCHIVED'
  tech_stack?: ProjectTechStack | null
}

export interface Finding {
  id: string
  project_id: string
  title: string
  severity: Severity
  cvss_score: number
  cvss_version: string
  cvss_vector: string
  cwe_id: string
  target_host: string
  target_port?: number | null
  endpoint_path: string
  protocol: string
  source_tool: string
  status: FindingStatus
  is_curated_for_report: boolean
  is_quarantined: boolean
  version: number
  created_at: string
}

export interface FindingSummaryMetrics {
  total: number
  curated: number
  quarantined: number
  by_severity: Record<string, number>
  by_status: Record<string, number>
}

export interface FindingListResponse {
  items: Finding[]
  total: number
  limit: number
  offset: number
  summary: FindingSummaryMetrics
}

export interface ManualFindingPayload {
  title: string
  severity: Severity
  cvss_vector: string
  cwe_id: string
  target_host: string
  target_port?: number | null
  endpoint_path?: string
  protocol: Protocol
  proof_of_concept: {
    raw_evidence: string
    reproduction_steps?: string[]
    attachment_urls?: string[]
  }
}

export interface ManualFindingResponse {
  id: string
  project_id: string
  title: string
  severity: Severity
  cvss_score: number
  cvss_vector: string
  cwe_id: string
  source_tool: 'manual'
  status: FindingStatus
  is_quarantined: boolean
  created_at: string
}

export interface FindingStatusResponse {
  id: string
  status: FindingStatus
  version: number
  is_curated_for_report: boolean
}

export interface FindingPoC {
  finding_id: string
  raw_evidence: string
  reproduction_steps: string[]
  attachment_file_urls: string[]
  key_version: number
}

export interface PoCAttachmentResponse {
  attachment_url: string
  storage_path: string
}

export interface RemediationItem {
  cwe_id: string
  vuln_title: string
  remediation_guidance: string
}

export interface NarrativeContent {
  executive_summary: string
  business_impact: string
  remediations: RemediationItem[]
}

export interface AINarrativeResponse {
  id?: string | null
  approval_status: 'DRAFT' | 'APPROVED'
  narratives: NarrativeContent
  tokens_consumed: number
  generated_at: string
  is_fallback: boolean
}

export interface AINarrativeAcceptedResponse {
  job_id: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  message: string
  status_url: string
}

export interface AINarrativeJobStatusResponse {
  job_id: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  progress_percentage?: number | null
  stage?: string | null
  narrative_id?: string | null
  narrative?: AINarrativeResponse | null
  error_message?: string | null
}

export interface ThemeOptionsPayload {
  primary_color: string
  secondary_color: string
  show_cover_page?: boolean
  show_cvss_radar?: boolean
  show_toc?: boolean
  show_methodology?: boolean
  show_poc_attachments?: boolean
  report_language?: 'en' | 'id'
  methodology_framework?: string
  confidentiality_notice?: string
}

export interface ReportSummary {
  id: string
  project_id: string
  report_title: string
  version: string
  watermark_applied: boolean
  verification_code?: string | null
  sha256_hash?: string | null
  is_rasterized?: boolean
  is_signed?: boolean
  generated_at: string
  download_url: string
}

export interface PublicReportVerifyResponse {
  valid: boolean
  verification_code: string
  report_version?: string | null
  agency_name?: string | null
  generated_at?: string | null
  watermark_applied: boolean
  is_rasterized: boolean
  is_signed: boolean
  sha256_hash?: string | null
}

export interface CompilePDFAcceptedResponse {
  job_id: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  message: string
  status_url: string
}

export interface ReportJobStatusResponse {
  job_id: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  progress_percentage?: number | null
  report_id?: string | null
  download_url?: string | null
  expires_in_seconds?: number | null
  error_message?: string | null
}

export interface ReportDownloadResponse {
  download_url: string
  expires_in_seconds: number
}

export interface SubscriptionStatus {
  workspace_id: string
  tier: 'FREE' | 'PRO' | 'ENTERPRISE' | string
  status: string
  monthly_report_quota: number
  is_unlimited?: boolean
  custom_batch_limit?: number | null
  reports_used_this_month: number
  remaining_reports: number
  quota_reset_date: string
  payment_status: string
  payment_type?: string | null
  midtrans_order_id?: string | null
}

export type EnterpriseInquiryStatus = 'NEW' | 'CONTACTED' | 'PROVISIONED' | 'DECLINED'

export interface EnterpriseInquiryCreatePayload {
  company_name: string
  contact_name: string
  contact_email: string
  team_size: string
  estimated_monthly_reports?: number | null
  requirements: string
}

export interface EnterpriseInquiryResponse {
  id: string
  workspace_id?: string | null
  submitted_by_user_id?: string | null
  company_name: string
  contact_name: string
  contact_email: string
  team_size: string
  estimated_monthly_reports?: number | null
  requirements: string
  status: EnterpriseInquiryStatus
  admin_notes?: string | null
  created_at: string
  updated_at: string
}

export interface AdminWorkspaceSubscriptionSummary {
  workspace_id: string
  workspace_name: string
  tier: string
  status: string
  monthly_report_quota: number
  is_unlimited: boolean
  reports_used_this_month: number
  custom_batch_limit?: number | null
  quota_reset_date: string
  payment_status: string
  manager_emails: string[]
  created_at: string
}

export interface AdminSubscriptionOverridePayload {
  tier: 'FREE' | 'PRO' | 'ENTERPRISE'
  monthly_report_quota: number
  custom_batch_limit?: number | null
  reason: string
}

export interface MidtransCheckoutResponse {
  order_id: string
  gross_amount: number
  snap_token: string
  redirect_url: string
}

export interface WorkspaceTokenUsage {
  workspace_id: string
  workspace_name: string
  total_tokens: number
  narrative_count: number
  fallback_count: number
  estimated_cost_usd: number
  estimated_cost_idr: number
}

export interface AITelemetryResponse {
  total_tokens: number
  total_narratives: number
  fallback_count: number
  fallback_ratio: number
  estimated_cost_usd: number
  estimated_cost_idr: number
  monthly_spend_ceiling_usd: number
  circuit_breaker_active: boolean
  by_workspace: WorkspaceTokenUsage[]
}

export interface AdminUserSummary {
  id: string
  email: string
  full_name: string
  status: string
  is_superadmin: boolean
  mfa_enabled: boolean
  created_at: string
  workspace_count: number
}

const STORAGE_KEYS = {
  token: 'vulnflow_token',
  user: 'vulnflow_user',
  workspaceId: 'vulnflow_active_workspace_id',
  workspace: 'vulnflow_active_workspace',
  projectId: 'vulnflow_active_project_id',
} as const

function safeParseJson<T>(raw: string | null): T | null {
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export const authStorage = {
  getToken: (): string | null => localStorage.getItem(STORAGE_KEYS.token),
  setToken: (token: string): void => localStorage.setItem(STORAGE_KEYS.token, token),
  removeToken: (): void => localStorage.removeItem(STORAGE_KEYS.token),

  getUser: (): UserDTO | null => safeParseJson<UserDTO>(localStorage.getItem(STORAGE_KEYS.user)),
  setUser: (user: UserDTO): void => localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user)),
  removeUser: (): void => localStorage.removeItem(STORAGE_KEYS.user),

  getActiveWorkspaceId: (): string | null => {
    const direct = localStorage.getItem(STORAGE_KEYS.workspaceId)
    if (direct) return direct
    const legacy = safeParseJson<{ id?: string }>(localStorage.getItem(STORAGE_KEYS.workspace))
    return legacy?.id ?? null
  },
  setActiveWorkspaceId: (workspaceId: string | null): void => {
    if (workspaceId) {
      localStorage.setItem(STORAGE_KEYS.workspaceId, workspaceId)
    } else {
      localStorage.removeItem(STORAGE_KEYS.workspaceId)
      localStorage.removeItem(STORAGE_KEYS.workspace)
    }
  },

  getActiveWorkspace: (): Workspace | null =>
    safeParseJson<Workspace>(localStorage.getItem(STORAGE_KEYS.workspace)),
  setActiveWorkspace: (workspace: Workspace): void => {
    localStorage.setItem(STORAGE_KEYS.workspace, JSON.stringify(workspace))
    localStorage.setItem(STORAGE_KEYS.workspaceId, workspace.id)
  },

  getActiveProjectId: (): string | null => localStorage.getItem(STORAGE_KEYS.projectId),
  setActiveProjectId: (projectId: string | null): void => {
    if (projectId) {
      localStorage.setItem(STORAGE_KEYS.projectId, projectId)
    } else {
      localStorage.removeItem(STORAGE_KEYS.projectId)
    }
  },

  clear: (): void => {
    localStorage.removeItem(STORAGE_KEYS.token)
    localStorage.removeItem(STORAGE_KEYS.user)
    localStorage.removeItem(STORAGE_KEYS.workspaceId)
    localStorage.removeItem(STORAGE_KEYS.workspace)
    localStorage.removeItem(STORAGE_KEYS.projectId)
  },
}

const PUBLIC_AUTH_PATHS = new Set([
  '/auth/login',
  '/auth/register',
  '/auth/forgot-password',
  '/auth/reset-password',
])

const DEFAULT_REQUEST_TIMEOUT_MS = 15_000
const RETRYABLE_GATEWAY_STATUSES = new Set([502, 503, 504])
let isRedirectingToLogin = false

function delayMs(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const sp = new URLSearchParams()
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null && val !== '') {
      sp.set(key, String(val))
    }
  }
  const qs = sp.toString()
  return qs ? `?${qs}` : ''
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController()
  const externalSignal = options.signal
  const onExternalAbort = () => controller.abort()
  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort()
    } else {
      externalSignal.addEventListener('abort', onExternalAbort, { once: true })
    }
  }
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    })
  } finally {
    window.clearTimeout(timer)
    if (externalSignal) {
      externalSignal.removeEventListener('abort', onExternalAbort)
    }
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  config: { skipAuthRedirect?: boolean; timeoutMs?: number } = {}
): Promise<T> {
  const token = authStorage.getToken()
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const method = (options.method || 'GET').toUpperCase()
  const timeoutMs = config.timeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS
  const maxAttempts = method === 'GET' ? 2 : 1

  let response: Response | null = null
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const res = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`, { ...options, headers }, timeoutMs)
      if (RETRYABLE_GATEWAY_STATUSES.has(res.status) && attempt + 1 < maxAttempts) {
        await delayMs(400)
        continue
      }
      response = res
      break
    } catch (err) {
      if (attempt + 1 < maxAttempts) {
        await delayMs(400)
        continue
      }
      const isTimeout = err instanceof DOMException && err.name === 'AbortError'
      throw new ApiError(
        isTimeout
          ? 'API request timed out. Please retry.'
          : 'Unable to reach the VulnFlow API server.',
        {
          status: 0,
          code: 'NETWORK_ERROR',
        }
      )
    }
  }

  if (!response) {
    throw new ApiError('Unable to reach the VulnFlow API server.', {
      status: 0,
      code: 'NETWORK_ERROR',
    })
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const code = typeof data.code === 'string' ? data.code : `HTTP_${response.status}`
    const message =
      (typeof data.message === 'string' && data.message) ||
      (typeof data.detail === 'string' && data.detail) ||
      `Request failed (HTTP ${response.status}).`
    const details = Array.isArray(data.details) ? (data.details as ErrorDetail[]) : []

    if (
      response.status === 401 &&
      !config.skipAuthRedirect &&
      !PUBLIC_AUTH_PATHS.has(endpoint) &&
      code !== 'MFA_REQUIRED'
    ) {
      authStorage.clear()
      if (
        !isRedirectingToLogin &&
        window.location.pathname.startsWith('/app') &&
        !window.location.pathname.startsWith('/app/login')
      ) {
        isRedirectingToLogin = true
        window.location.href = `/app/login?reason=session_expired&redirect=${encodeURIComponent(window.location.pathname)}`
      }
    }

    throw new ApiError(message, {
      status: response.status,
      code,
      details,
      requestId: typeof data.request_id === 'string' ? data.request_id : undefined,
    })
  }

  return data as T
}

export const api = {
  auth: {
    login: (credentials: { email: string; password: string; totp_code?: string | null }) =>
      request<TokenResponse>(
        '/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
            ...(credentials.totp_code ? { totp_code: credentials.totp_code } : {}),
          }),
        },
        { skipAuthRedirect: true }
      ),
    register: (payload: {
      email: string
      password: string
      full_name: string
      workspace_name: string
      invitation_token?: string | null
    }) =>
      request<RegisterResponse>(
        '/auth/register',
        {
          method: 'POST',
          body: JSON.stringify({
            email: payload.email,
            password: payload.password,
            full_name: payload.full_name,
            workspace_name: payload.workspace_name,
            ...(payload.invitation_token ? { invitation_token: payload.invitation_token } : {}),
          }),
        },
        { skipAuthRedirect: true }
      ),
    me: () => request<MeResponse>('/auth/me'),
    logout: () => request<{ status: string }>('/auth/logout', { method: 'POST' }),
    forgotPassword: (email: string) =>
      request<{ message: string }>(
        '/auth/forgot-password',
        { method: 'POST', body: JSON.stringify({ email }) },
        { skipAuthRedirect: true }
      ),
    resetPassword: (token: string, newPassword: string) =>
      request<{ status: string }>(
        '/auth/reset-password',
        { method: 'POST', body: JSON.stringify({ token, new_password: newPassword }) },
        { skipAuthRedirect: true }
      ),
    setupMfa: () => request<MFASetupResponse>('/auth/mfa/setup', { method: 'POST' }),
    verifyMfa: (totpCode: string) =>
      request<{ valid: boolean }>(
        '/auth/mfa/verify',
        { method: 'POST', body: JSON.stringify({ totp_code: totpCode }) },
        { skipAuthRedirect: true }
      ),
    deleteMe: (password: string) =>
      request<{ status: string }>(
        '/auth/me',
        { method: 'DELETE', body: JSON.stringify({ password }) },
        { skipAuthRedirect: true }
      ),
  },

  workspaces: {
    list: () => request<Workspace[]>('/workspaces'),
    get: (workspaceId: string) => request<Workspace>(`/workspaces/${workspaceId}`),
    create: (name: string) =>
      request<Workspace>('/workspaces', {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),
    update: (
      workspaceId: string,
      payload: {
        name?: string
        custom_logo_url?: string
        brand_primary_color?: string
        brand_secondary_color?: string
        confidentiality_text?: string
      }
    ) =>
      request<Workspace>(`/workspaces/${workspaceId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    delete: (workspaceId: string, password: string, confirmWorkspaceName: string) =>
      request<{ status: string }>(
        `/workspaces/${workspaceId}`,
        {
          method: 'DELETE',
          body: JSON.stringify({
            password,
            confirm_workspace_name: confirmWorkspaceName,
          }),
        },
        { skipAuthRedirect: true }
      ),
    uploadLogo: (
      workspaceId: string,
      payload: { filename: string; content_type: ImageContentType; data_base64: string }
    ) =>
      request<LogoUploadResponse>(`/workspaces/${workspaceId}/logo`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    listMembers: (workspaceId: string) =>
      request<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`),
    inviteMember: (workspaceId: string, email: string, role: WorkspaceRole) =>
      request<InviteMemberResponse>(`/workspaces/${workspaceId}/members`, {
        method: 'POST',
        body: JSON.stringify({ email, role }),
      }),
    acceptInvitation: (invitationToken: string) =>
      request<WorkspaceMembership>('/workspaces/invitations/accept', {
        method: 'POST',
        body: JSON.stringify({ invitation_token: invitationToken }),
      }),
    updateMemberRole: (workspaceId: string, userId: string, role: WorkspaceRole) =>
      request<WorkspaceMember>(`/workspaces/${workspaceId}/members/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ role }),
      }),
    removeMember: (workspaceId: string, userId: string) =>
      request<{ status: string }>(`/workspaces/${workspaceId}/members/${userId}`, {
        method: 'DELETE',
      }),
    listApiKeys: (workspaceId: string) =>
      request<APIKeySummary[]>(`/workspaces/${workspaceId}/api-keys`),
    createApiKey: (workspaceId: string, label: string) =>
      request<APIKeyCreateResponse>(`/workspaces/${workspaceId}/api-keys`, {
        method: 'POST',
        body: JSON.stringify({ label }),
      }),
    revokeApiKey: (workspaceId: string, keyId: string) =>
      request<{ status: string }>(`/workspaces/${workspaceId}/api-keys/${keyId}`, {
        method: 'DELETE',
      }),
    listAuditLogs: (
      workspaceId: string,
      params: { action?: string; actor_user_id?: string; limit?: number; offset?: number } = {}
    ) =>
      request<PaginatedAuditLogs>(
        `/workspaces/${workspaceId}/audit-logs${buildQuery(params)}`
      ),
  },

  projects: {
    list: (workspaceId: string) => request<Project[]>(`/workspaces/${workspaceId}/projects`),
    get: (workspaceId: string, projectId: string) =>
      request<Project>(`/workspaces/${workspaceId}/projects/${projectId}`),
    create: (workspaceId: string, payload: ProjectCreatePayload) =>
      request<Project>(`/workspaces/${workspaceId}/projects`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    update: (workspaceId: string, projectId: string, payload: ProjectUpdatePayload) =>
      request<Project>(`/workspaces/${workspaceId}/projects/${projectId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    assignLead: (workspaceId: string, projectId: string, leadPentesterId: string) =>
      request<Project>(`/workspaces/${workspaceId}/projects/${projectId}/lead`, {
        method: 'PATCH',
        body: JSON.stringify({ lead_pentester_id: leadPentesterId }),
      }),
  },

  findings: {
    list: (
      workspaceId: string,
      projectId: string,
      params: {
        severity?: Severity | ''
        status?: FindingStatus | ''
        is_quarantined?: boolean | null
        search?: string
        limit?: number
        offset?: number
      } = {}
    ) =>
      request<FindingListResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings${buildQuery(params)}`
      ),
    createManual: (workspaceId: string, projectId: string, payload: ManualFindingPayload) =>
      request<ManualFindingResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings/manual`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        }
      ),
    updateStatus: (
      workspaceId: string,
      projectId: string,
      findingId: string,
      status: FindingStatus,
      version: number
    ) =>
      request<FindingStatusResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings/${findingId}/status`,
        {
          method: 'PATCH',
          body: JSON.stringify({ status, version }),
        }
      ),
    updateCuration: (
      workspaceId: string,
      projectId: string,
      findingId: string,
      payload: { is_curated_for_report: boolean; unquarantine?: boolean }
    ) =>
      request<FindingStatusResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings/${findingId}/curation`,
        {
          method: 'PATCH',
          body: JSON.stringify(payload),
        }
      ),
    getPoC: (workspaceId: string, projectId: string, findingId: string) =>
      request<FindingPoC>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings/${findingId}/poc`
      ),
    uploadAttachment: (
      workspaceId: string,
      projectId: string,
      findingId: string,
      payload: { filename: string; content_type: 'image/png' | 'image/jpeg'; data_base64: string }
    ) =>
      request<PoCAttachmentResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/findings/${findingId}/attachments`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        }
      ),
  },

  ai: {
    listNarratives: (workspaceId: string, projectId: string) =>
      request<AINarrativeResponse[]>(
        `/workspaces/${workspaceId}/projects/${projectId}/reports/ai-narratives`
      ),
    generateNarrative: (
      workspaceId: string,
      projectId: string,
      payload: {
        tone?: string
        language: 'id' | 'en'
        sections_requested: string[]
        finding_ids: string[]
      }
    ) =>
      request<AINarrativeResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/reports/ai-narratives`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        }
      ),
    generateNarrativeAsync: (
      workspaceId: string,
      projectId: string,
      payload: {
        tone?: string
        language: 'id' | 'en'
        sections_requested: string[]
        finding_ids: string[]
      }
    ) =>
      request<AINarrativeAcceptedResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/reports/ai-narratives/async`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        }
      ),
    getJobStatus: (workspaceId: string, projectId: string, jobId: string) =>
      request<AINarrativeJobStatusResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/reports/ai-narratives/jobs/${jobId}`
      ),
    updateNarrative: (
      workspaceId: string,
      projectId: string,
      narrativeId: string,
      payload: {
        executive_summary: string
        business_impact: string
        remediations: RemediationItem[]
        approval_status: 'DRAFT' | 'APPROVED'
      }
    ) =>
      request<AINarrativeResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/reports/ai-narratives/${narrativeId}`,
        {
          method: 'PUT',
          body: JSON.stringify(payload),
        }
      ),
  },

  reports: {
    list: (workspaceId: string, projectId: string) =>
      request<ReportSummary[]>(`/workspaces/${workspaceId}/projects/${projectId}/reports`),
    compilePdf: (
      workspaceId: string,
      projectId: string,
      payload: {
        finding_ids: string[]
        include_ai_narratives?: boolean
        theme_options?: ThemeOptionsPayload | null
      }
    ) =>
      request<CompilePDFAcceptedResponse>(
        `/workspaces/${workspaceId}/projects/${projectId}/reports/compile-pdf`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        }
      ),
    getJobStatus: (workspaceId: string, jobId: string) =>
      request<ReportJobStatusResponse>(`/workspaces/${workspaceId}/reports/jobs/${jobId}`),
    getDownloadUrl: (workspaceId: string, reportId: string) =>
      request<ReportDownloadResponse>(
        `/workspaces/${workspaceId}/reports/${reportId}/download?format=json`
      ),
  },

  billing: {
    getSubscription: (workspaceId: string) =>
      request<SubscriptionStatus>(`/workspaces/${workspaceId}/billing/subscription`),
    checkoutPro: (workspaceId: string) =>
      request<MidtransCheckoutResponse>(`/workspaces/${workspaceId}/billing/checkout`, {
        method: 'POST',
        body: JSON.stringify({ tier: 'PRO', billing_cycle: 'MONTHLY' }),
      }),
    syncStatus: (workspaceId: string) =>
      request<SubscriptionStatus>(`/workspaces/${workspaceId}/billing/sync`, {
        method: 'POST',
      }),
    submitEnterpriseInquiry: (workspaceId: string, payload: EnterpriseInquiryCreatePayload) =>
      request<EnterpriseInquiryResponse>(
        `/workspaces/${workspaceId}/billing/enterprise-inquiry`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        }
      ),
  },

  public: {
    verifyReport: (verificationCode: string) =>
      request<PublicReportVerifyResponse>(
        `/public/verify/${encodeURIComponent(verificationCode)}`,
        {},
        { skipAuthRedirect: true }
      ),
    submitEnterpriseInquiry: (payload: EnterpriseInquiryCreatePayload) =>
      request<EnterpriseInquiryResponse>(
        '/public/enterprise-inquiries',
        {
          method: 'POST',
          body: JSON.stringify(payload),
        },
        { skipAuthRedirect: true }
      ),
  },

  admin: {
    getAiTelemetry: () => request<AITelemetryResponse>('/admin/telemetry/ai'),
    updateSpendCeiling: (monthlySpendCeilingUsd: number) =>
      request<AITelemetryResponse>('/admin/telemetry/ai/ceiling', {
        method: 'PATCH',
        body: JSON.stringify({ monthly_spend_ceiling_usd: monthlySpendCeilingUsd }),
      }),
    listUsers: (params: { status?: string; limit?: number; offset?: number } = {}) =>
      request<AdminUserSummary[]>(`/admin/users${buildQuery(params)}`),
    suspendUser: (userId: string, reason: string) =>
      request<AdminUserSummary>(`/admin/users/${userId}/suspend`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
    activateUser: (userId: string) =>
      request<AdminUserSummary>(`/admin/users/${userId}/activate`, {
        method: 'POST',
      }),
    listAuditLogs: (
      params: { workspace_id?: string; action?: string; limit?: number; offset?: number } = {}
    ) => request<PaginatedAuditLogs>(`/admin/audit-logs${buildQuery(params)}`),
    listWorkspaces: (params: { tier?: string; limit?: number; offset?: number } = {}) =>
      request<AdminWorkspaceSubscriptionSummary[]>(`/admin/workspaces${buildQuery(params)}`),
    overrideWorkspaceSubscription: (
      workspaceId: string,
      payload: AdminSubscriptionOverridePayload
    ) =>
      request<AdminWorkspaceSubscriptionSummary>(`/admin/workspaces/${workspaceId}/subscription`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    listEnterpriseInquiries: (params: { status?: string; limit?: number; offset?: number } = {}) =>
      request<EnterpriseInquiryResponse[]>(`/admin/enterprise-inquiries${buildQuery(params)}`),
    updateEnterpriseInquiry: (
      inquiryId: string,
      payload: { status: EnterpriseInquiryStatus; admin_notes?: string | null }
    ) =>
      request<EnterpriseInquiryResponse>(`/admin/enterprise-inquiries/${inquiryId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
  },
}
