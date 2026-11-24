<template>
  <AppLayout :pipeline-step="1">
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
          Projects
        </h1>
        <p class="text-xs text-[#8A8D96] truncate">
          {{ session.state.activeWorkspace?.name || 'Workspace' }}
        </p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Top Action & Filter Row -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.1] pb-5">
        <div>
          <h2 class="text-lg font-display font-semibold text-[#F5F5F3] tracking-tight">Projects &amp; Scope</h2>
          <p class="text-xs sm:text-sm text-[#8A8D96]">
            Manage authorized target scopes, engagement schedules, and project leads.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2.5">
          <div class="relative min-w-[200px]">
            <Search
              class="h-3.5 w-3.5 text-[#8A8D96] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              aria-hidden="true"
            />
            <label for="project-search" class="sr-only">Search projects or clients</label>
            <input
              id="project-search"
              v-model.trim="searchQuery"
              type="text"
              placeholder="Search projects or clients..."
              class="input-glass w-full pl-8 pr-3 py-2 text-xs"
            />
          </div>

          <label for="project-status-filter" class="sr-only">Filter project status</label>
          <select
            id="project-status-filter"
            v-model="statusFilter"
            class="input-glass px-3 py-2 text-xs text-[#F5F5F3]"
          >
            <option value="ALL">All ({{ session.state.projects.length }})</option>
            <option value="ACTIVE">Active</option>
            <option value="ARCHIVED">Archived</option>
          </select>

          <button
            v-if="canManageProjects"
            type="button"
            @click="openCreateModal"
            class="btn-platinum px-4 py-2 text-xs"
          >
            <Plus class="h-3.5 w-3.5" aria-hidden="true" />
            <span>New project</span>
          </button>
        </div>
      </div>

      <!-- Post-Create Guided Next-Step Banner -->
      <div
        v-if="recentlyCreatedProject"
        class="border border-emerald-400/35 bg-emerald-500/10 p-4 flex flex-wrap items-center justify-between gap-3"
      >
        <div class="space-y-0.5">
          <div class="text-xs font-semibold text-emerald-300 flex items-center gap-1.5">
            <CheckCircle2 class="h-4 w-4" aria-hidden="true" />
            <span>Project "{{ recentlyCreatedProject.name }}" is ready for findings</span>
          </div>
          <p class="text-xs text-[#D4D4D8]">
            Next step: import Nmap or Nuclei scans via CLI or log findings manually.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            @click="openCliForProject(recentlyCreatedProject)"
            class="btn-glass px-3 py-1.5 text-xs"
          >
            <Terminal class="h-3.5 w-3.5" />
            <span>Import via CLI</span>
          </button>
          <router-link
            to="/app/triage"
            class="btn-platinum px-3 py-1.5 text-xs"
          >
            <span>Open Findings</span>
            <ArrowRight class="h-3.5 w-3.5" />
          </router-link>
          <button
            type="button"
            @click="recentlyCreatedProject = null"
            class="p-1.5 text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.06] transition-colors"
            aria-label="Dismiss guide"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <EmptyState
        v-if="filteredProjects.length === 0"
        :icon="FolderGit2"
        :title="session.state.projects.length === 0 ? 'No projects yet' : 'No matching projects'"
        :description="
          session.state.projects.length === 0
            ? 'Create your first project to set authorized target scopes and engagement dates.'
            : 'Adjust your search query or status filter to view more projects.'
        "
        :action-label="
          session.state.projects.length === 0 && canManageProjects
            ? 'New project'
            : session.state.projects.length > 0
              ? 'Reset filters'
              : ''
        "
        @action="session.state.projects.length === 0 ? openCreateModal() : resetFilters()"
      />

      <!-- Ruled Project Ledger Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-t border-l border-white/[0.11] bg-[#08080B]">
        <div
          v-for="p in filteredProjects"
          :key="p.id"
          :class="[
            'p-6 flex flex-col justify-between space-y-5 border-r border-b border-white/[0.11]',
            p.id === session.state.activeProjectId
              ? 'bg-white/[0.03] border-t-2 border-t-[#F5F5F3]'
              : '',
          ]"
        >
          <div class="space-y-4">
            <div class="flex items-start justify-between border-b border-white/[0.08] pb-3.5 gap-2">
              <div class="space-y-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span
                    v-if="p.id === session.state.activeProjectId"
                    class="font-mono text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 bg-[#F5F5F3] text-[#050507]"
                  >
                    Active
                  </span>
                  <span class="font-mono text-[11px] text-[#8A8D96] truncate">{{ p.client_name }}</span>
                </div>
                <h3 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] truncate">
                  {{ p.name }}
                </h3>
              </div>
              <StatusBadge :status="getRoeState(p)" />
            </div>

            <div class="space-y-3 text-xs">
              <div>
                <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96] block">
                  Schedule ({{ p.timezone }})
                </span>
                <span class="text-[#D4D4D8] font-mono text-[11px] block mt-0.5 tabular-nums">
                  {{ formatDateTime(p.roe_start_date) }} – {{ formatDateTime(p.roe_end_date) }}
                </span>
              </div>

              <div>
                <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96] block">
                  Authorized Targets ({{ p.target_scope.length }})
                </span>
                <div class="flex flex-wrap gap-1.5 mt-1.5 font-mono">
                  <span
                    v-for="(target, i) in visibleScopes(p)"
                    :key="i"
                    class="px-2 py-0.5 bg-[#050507] border border-white/[0.1] text-[11px] text-[#D4D4D8]"
                  >
                    {{ target }}
                  </span>
                  <button
                    v-if="p.target_scope.length > 4"
                    type="button"
                    @click="toggleScopeExpand(p.id)"
                    class="px-2 py-0.5 border border-white/[0.16] text-[11px] font-sans text-[#F5F5F3] hover:bg-white/[0.06] transition-colors"
                  >
                    {{ expandedScopes[p.id] ? 'Show less' : `+${p.target_scope.length - 4} more` }}
                  </button>
                </div>
              </div>

              <div v-if="formatTechStackTags(p.tech_stack).length > 0">
                <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96] block">
                  Target Architecture
                </span>
                <div class="flex flex-wrap gap-1.5 mt-1 font-mono">
                  <span
                    v-for="tag in formatTechStackTags(p.tech_stack)"
                    :key="tag"
                    class="px-2 py-0.5 bg-white/[0.04] border border-white/[0.12] text-[10px] text-[#D4D4D8] uppercase"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>

              <div>
                <label
                  :for="`lead-select-${p.id}`"
                  class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96] block mb-1"
                >
                  Project Lead
                </label>
                <select
                  v-if="isManager"
                  :id="`lead-select-${p.id}`"
                  :value="p.lead_pentester_id || ''"
                  @change="handleAssignLead(p, $event)"
                  class="input-glass w-full px-2.5 py-1.5 text-xs"
                >
                  <option value="" disabled>Select project lead...</option>
                  <option v-for="m in eligibleLeads" :key="m.user_id" :value="m.user_id">
                    {{ m.full_name }} ({{ formatRole(m.role) }})
                  </option>
                </select>
                <span v-else class="text-[#D4D4D8] text-xs">
                  {{ resolveMemberName(p.lead_pentester_id) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Card Footer Actions -->
          <div class="border-t border-white/[0.08] pt-3.5 flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2.5">
              <button
                type="button"
                @click="openInTriage(p)"
                class="text-xs font-medium text-[#F5F5F3] underline underline-offset-4 hover:text-white inline-flex items-center gap-1 transition-colors"
              >
                <span>Open Findings</span>
                <ArrowRight class="h-3.5 w-3.5" />
              </button>

              <button
                v-if="p.id !== session.state.activeProjectId"
                type="button"
                @click="activateProject(p)"
                class="text-xs text-[#D4D4D8] hover:text-[#F5F5F3] px-2.5 py-1 border border-white/[0.12] hover:border-white/[0.25] transition-colors"
              >
                Set Active
              </button>
            </div>

            <div class="flex items-center gap-1.5">
              <button
                type="button"
                @click="openCliForProject(p)"
                class="text-xs text-[#F5F5F3] px-2.5 py-1 border border-white/[0.12] hover:bg-[#F5F5F3] hover:text-[#050507] inline-flex items-center gap-1 transition-colors"
                title="Show CLI upload commands for this project"
              >
                <Terminal class="h-3 w-3" aria-hidden="true" />
                <span>CLI</span>
              </button>
              <button
                type="button"
                @click="copyProjectId(p.id)"
                class="text-xs text-[#D4D4D8] px-2.5 py-1 border border-white/[0.12] hover:bg-white/[0.06] transition-colors"
                title="Copy Project ID"
              >
                ID
              </button>
              <button
                v-if="canManageProjects"
                type="button"
                @click="openEditModal(p)"
                class="text-xs text-[#D4D4D8] px-2.5 py-1 border border-white/[0.12] hover:bg-white/[0.06] transition-colors"
              >
                Edit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create / Edit Project Modal -->
    <BaseModal
      :open="showModal"
      :title="editingProjectId ? 'Edit Project & Scope' : 'New Project'"
      subtitle="Define authorized targets and engagement dates to keep scan imports within scope."
      max-width="lg"
      @close="showModal = false"
    >
      <form id="project-form" @submit.prevent="handleSaveProject" class="space-y-4 text-xs">
        <div class="space-y-1.5">
          <label for="proj-name" class="font-medium text-[#D4D4D8] block">Project name</label>
          <input
            id="proj-name"
            v-model.trim="form.name"
            type="text"
            required
            placeholder="Core Web Platform Assessment"
            class="input-glass w-full px-3 py-2 text-xs"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label for="proj-client" class="font-medium text-[#D4D4D8] block">
              Client name
            </label>
            <input
              id="proj-client"
              v-model.trim="form.client_name"
              type="text"
              required
              placeholder="Acme Corp"
              class="input-glass w-full px-3 py-2 text-xs"
            />
          </div>

          <div class="space-y-1.5">
            <label for="proj-timezone" class="font-medium text-[#D4D4D8] block">Timezone</label>
            <select
              id="proj-timezone"
              v-model="form.timezone"
              class="input-glass w-full px-3 py-2 text-xs"
            >
              <option value="Asia/Jakarta">Asia/Jakarta (WIB)</option>
              <option value="Asia/Makassar">Asia/Makassar (WITA)</option>
              <option value="Asia/Jayapura">Asia/Jayapura (WIT)</option>
              <option value="Asia/Singapore">Asia/Singapore</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label for="proj-roe-start" class="font-medium text-[#D4D4D8] block">Start date &amp; time</label>
            <input
              id="proj-roe-start"
              v-model="form.roeStartLocal"
              type="datetime-local"
              required
              class="input-glass w-full px-3 py-2 text-xs"
            />
          </div>
          <div class="space-y-1.5">
            <label for="proj-roe-end" class="font-medium text-[#D4D4D8] block">End date &amp; time</label>
            <input
              id="proj-roe-end"
              v-model="form.roeEndLocal"
              type="datetime-local"
              required
              class="input-glass w-full px-3 py-2 text-xs"
            />
          </div>
        </div>

        <div v-if="editingProjectId" class="space-y-1.5">
          <label for="proj-status" class="font-medium text-[#D4D4D8] block">Project status</label>
          <select
            id="proj-status"
            v-model="form.status"
            class="input-glass w-full px-3 py-2 text-xs"
          >
            <option value="ACTIVE">Active (Accepts imports)</option>
            <option value="ARCHIVED">Archived (Imports paused)</option>
          </select>
        </div>

        <div class="space-y-1.5">
          <label for="proj-scope" class="font-medium text-[#D4D4D8] block">
            Authorized target scope (one domain, IP, or CIDR per line)
          </label>
          <textarea
            id="proj-scope"
            v-model="form.scopeRaw"
            rows="3"
            required
            placeholder="*.example.com&#10;10.20.0.0/24"
            class="input-glass w-full p-3 font-mono text-xs"
          ></textarea>
        </div>

        <div class="border border-white/[0.1] bg-[#050507] p-3.5 space-y-3">
          <div>
            <div class="text-xs font-medium text-[#F5F5F3]">
              Target Tech Stack (Optional, Stack-Aware Remediation)
            </div>
            <p class="text-[11px] text-[#8A8D96] mt-0.5 leading-relaxed">
              Only abstract enum tags are shared with the AI Ghostwriter to tailor fix examples. Raw PoC and source code never leave your database.
            </p>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <select v-model="form.stackLanguage" aria-label="Primary language" class="input-glass px-2.5 py-1.5 text-xs">
              <option value="">Language (Any)</option>
              <option value="python">Python</option>
              <option value="typescript">TypeScript</option>
              <option value="javascript">JavaScript</option>
              <option value="go">Go</option>
              <option value="java">Java</option>
              <option value="php">PHP</option>
              <option value="csharp">C# / .NET</option>
              <option value="ruby">Ruby</option>
              <option value="other">Other</option>
            </select>
            <select v-model="form.stackFramework" aria-label="Framework" class="input-glass px-2.5 py-1.5 text-xs">
              <option value="">Framework (Any)</option>
              <option value="fastapi">FastAPI</option>
              <option value="django">Django</option>
              <option value="flask">Flask</option>
              <option value="express">Express</option>
              <option value="nestjs">NestJS</option>
              <option value="nextjs">Next.js</option>
              <option value="laravel">Laravel</option>
              <option value="spring_boot">Spring Boot</option>
              <option value="aspnet">ASP.NET</option>
              <option value="rails">Rails</option>
              <option value="gin">Gin</option>
              <option value="other">Other</option>
            </select>
            <select v-model="form.stackDatabase" aria-label="Database" class="input-glass px-2.5 py-1.5 text-xs">
              <option value="">Database (Any)</option>
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="mongodb">MongoDB</option>
              <option value="mssql">SQL Server</option>
              <option value="sqlite">SQLite</option>
              <option value="redis">Redis</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
      </form>

      <template #footer>
        <div class="w-full flex flex-wrap items-center justify-between gap-3">
          <router-link to="/app/settings" class="text-xs text-[#F5F5F3] underline underline-offset-4 hover:text-white">
            Manage CLI API keys in Settings
          </router-link>
          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="showModal = false"
              class="btn-glass px-4 py-2 text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              form="project-form"
              :disabled="saving"
              class="btn-platinum px-4 py-2 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="saving" class="h-3.5 w-3.5 animate-spin" />
              <span>{{ saving ? 'Saving...' : editingProjectId ? 'Save changes' : 'Create project' }}</span>
            </button>
          </div>
        </div>
      </template>
    </BaseModal>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, inject, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  CheckCircle2,
  FolderGit2,
  Loader2,
  Plus,
  Search,
  Terminal,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { api, type Project, type ProjectTechStack, type WorkspaceMember } from '@/services/api'
import { OPEN_CLI_DRAWER_KEY, session } from '@/stores/session'
import { toast } from '@/stores/toast'

const router = useRouter()
const openCliDrawer = inject(OPEN_CLI_DRAWER_KEY, () => {})

const statusFilter = ref<'ALL' | 'ACTIVE' | 'ARCHIVED'>('ALL')
const searchQuery = ref('')
const members = ref<WorkspaceMember[]>([])
const showModal = ref(false)
const saving = ref(false)
const editingProjectId = ref<string | null>(null)
const recentlyCreatedProject = ref<Project | null>(null)
const expandedScopes = reactive<Record<string, boolean>>({})

const isManager = computed(() => session.activeRole.value === 'MANAGER')
const canManageProjects = computed(() => session.activeRole.value !== 'VIEWER')
const eligibleLeads = computed(() => members.value.filter((m) => m.role !== 'VIEWER'))

const filteredProjects = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return session.state.projects.filter((p) => {
    const matchStatus = statusFilter.value === 'ALL' || p.status === statusFilter.value
    const matchQuery =
      !q || p.name.toLowerCase().includes(q) || p.client_name.toLowerCase().includes(q)
    return matchStatus && matchQuery
  })
})

const formatRole = (role: string): string => {
  if (!role) return 'Member'
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase()
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'ALL'
}

const visibleScopes = (p: Project): string[] => {
  if (expandedScopes[p.id] || p.target_scope.length <= 4) {
    return p.target_scope
  }
  return p.target_scope.slice(0, 4)
}

const toggleScopeExpand = (projectId: string) => {
  expandedScopes[projectId] = !expandedScopes[projectId]
}

function toLocalInputValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const form = ref({
  name: '',
  client_name: '',
  timezone: 'Asia/Jakarta',
  roeStartLocal: '',
  roeEndLocal: '',
  scopeRaw: '',
  status: 'ACTIVE' as 'ACTIVE' | 'ARCHIVED',
  stackLanguage: '' as NonNullable<ProjectTechStack['language']> | '',
  stackFramework: '' as NonNullable<ProjectTechStack['framework']> | '',
  stackDatabase: '' as NonNullable<ProjectTechStack['database']> | '',
})

const formatTechStackTags = (stack?: ProjectTechStack | null): string[] => {
  if (!stack) return []
  return [stack.language, stack.framework, stack.database]
    .filter((v) => Boolean(v))
    .map((v) => String(v))
}

watch(
  () => session.state.activeWorkspaceId,
  async (wId) => {
    recentlyCreatedProject.value = null
    if (!wId) {
      members.value = []
      return
    }
    try {
      members.value = await api.workspaces.listMembers(wId)
    } catch {
      members.value = []
    }
  },
  { immediate: true }
)

function resolveMemberName(userId?: string | null): string {
  if (!userId) return 'Unassigned'
  return members.value.find((m) => m.user_id === userId)?.full_name ?? userId
}

function formatDateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getRoeState(p: Project): string {
  if (p.status === 'ARCHIVED') return 'ARCHIVED'
  const now = Date.now()
  const start = new Date(p.roe_start_date).getTime()
  const end = new Date(p.roe_end_date).getTime()
  if (now < start) return 'UPCOMING'
  if (now > end) return 'EXPIRED'
  return 'ACTIVE'
}

const openCreateModal = () => {
  const now = new Date()
  const end = new Date(now.getTime() + 14 * 24 * 3600 * 1000)
  editingProjectId.value = null
  form.value = {
    name: '',
    client_name: '',
    timezone: 'Asia/Jakarta',
    roeStartLocal: toLocalInputValue(now),
    roeEndLocal: toLocalInputValue(end),
    scopeRaw: '127.0.0.1\nlocalhost',
    status: 'ACTIVE',
    stackLanguage: '',
    stackFramework: '',
    stackDatabase: '',
  }
  showModal.value = true
}

const openEditModal = (p: Project) => {
  editingProjectId.value = p.id
  form.value = {
    name: p.name,
    client_name: p.client_name,
    timezone: p.timezone || 'UTC',
    roeStartLocal: toLocalInputValue(new Date(p.roe_start_date)),
    roeEndLocal: toLocalInputValue(new Date(p.roe_end_date)),
    scopeRaw: p.target_scope.join('\n'),
    status: p.status,
    stackLanguage: p.tech_stack?.language || '',
    stackFramework: p.tech_stack?.framework || '',
    stackDatabase: p.tech_stack?.database || '',
  }
  showModal.value = true
}

const buildTechStackPayload = (): ProjectTechStack | null => {
  const stack: ProjectTechStack = {}
  if (form.value.stackLanguage) stack.language = form.value.stackLanguage
  if (form.value.stackFramework) stack.framework = form.value.stackFramework
  if (form.value.stackDatabase) stack.database = form.value.stackDatabase
  return Object.keys(stack).length > 0 ? stack : null
}

const handleSaveProject = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return

  const scopeList = form.value.scopeRaw
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
  if (scopeList.length === 0) {
    toast.warning('Please enter at least one authorized target.')
    return
  }

  const startIso = new Date(form.value.roeStartLocal).toISOString()
  const endIso = new Date(form.value.roeEndLocal).toISOString()
  if (new Date(endIso) <= new Date(startIso)) {
    toast.warning('End date must be after start date.')
    return
  }

  saving.value = true
  const techStack = buildTechStackPayload()
  try {
    if (editingProjectId.value) {
      await api.projects.update(wId, editingProjectId.value, {
        name: form.value.name,
        client_name: form.value.client_name,
        target_scope: scopeList,
        roe_start_date: startIso,
        roe_end_date: endIso,
        timezone: form.value.timezone,
        status: form.value.status,
        tech_stack: techStack ?? {},
      })
      toast.success('Project updated.')
    } else {
      const created = await api.projects.create(wId, {
        name: form.value.name,
        client_name: form.value.client_name,
        target_scope: scopeList,
        roe_start_date: startIso,
        roe_end_date: endIso,
        timezone: form.value.timezone,
        ...(techStack ? { tech_stack: techStack } : {}),
      })
      session.selectProject(created.id)
      recentlyCreatedProject.value = created
      toast.success('Project created and activated.')
    }
    await session.refreshProjects()
    void session.refreshProjectProgress()
    showModal.value = false
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to save project.')
  } finally {
    saving.value = false
  }
}

const handleAssignLead = async (project: Project, event: Event) => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  const selectEl = event.target as HTMLSelectElement
  const leadId = selectEl.value
  if (!leadId) return
  try {
    await api.projects.assignLead(wId, project.id, leadId)
    await session.refreshProjects()
    toast.success('Project lead updated.')
  } catch (err: unknown) {
    selectEl.value = project.lead_pentester_id || ''
    toast.error(err instanceof Error ? err.message : 'Unable to update project lead.')
  }
}

const activateProject = (project: Project) => {
  session.selectProject(project.id)
  toast.info(`Active project switched to ${project.name}.`)
}

const openInTriage = async (project: Project) => {
  session.selectProject(project.id)
  await router.push('/app/triage')
}

const openCliForProject = (project: Project) => {
  session.selectProject(project.id)
  openCliDrawer(project.id)
}

const copyProjectId = async (projectId: string) => {
  try {
    await navigator.clipboard.writeText(projectId)
    toast.success(`Project ID copied: ${projectId}`)
  } catch {
    toast.info(projectId, 'Project ID')
  }
}
</script>
