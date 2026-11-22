<template>
  <div class="relative flex h-screen bg-[#050507] text-[#F5F5F3] overflow-hidden font-sans">
    <AmbientCanvas intensity="subtle" />

    <a
      href="#app-main"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[120] focus:px-4 focus:py-2 focus:rounded-none focus:bg-[#F5F5F3] focus:text-[#050507] focus:text-xs focus:font-semibold"
    >
      Skip to workspace content
    </a>

    <!-- Mobile backdrop -->
    <Transition name="vf-fade">
      <div
        v-if="mobileNavOpen"
        @click="mobileNavOpen = false"
        class="fixed inset-0 z-30 bg-black/80 backdrop-blur-sm lg:hidden"
      />
    </Transition>

    <!-- Matte Monograph Sidebar -->
    <aside
      aria-label="Workspace navigation"
      :class="[
        'fixed inset-y-0 left-0 z-40 w-64 border-r border-white/[0.1] bg-[#08080B] flex flex-col justify-between shrink-0 transition-transform duration-200 lg:static lg:translate-x-0',
        mobileNavOpen ? 'translate-x-0' : '-translate-x-full',
      ]"
    >
      <div class="overflow-y-auto flex-1">
        <!-- Brand Header -->
        <div class="h-16 border-b border-white/[0.1] px-4 flex items-center justify-between">
          <router-link :to="isSuperadmin ? '/app/admin' : '/app/dashboard'" @click="mobileNavOpen = false">
            <BrandLogo size="sm" />
          </router-link>
          <button
            type="button"
            @click="mobileNavOpen = false"
            class="lg:hidden text-[#8A8D96] hover:text-[#F5F5F3] p-1.5"
            aria-label="Close navigation"
          >
            <X class="h-4 w-4" />
          </button>
        </div>

        <!-- Superadmin Scope / Tenant Workspace Switcher Band -->
        <div v-if="isSuperadmin" class="p-3.5 border-b border-white/[0.1] space-y-1.5">
          <div class="flex items-center justify-between gap-2">
            <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">
              Platform Scope
            </span>
            <span class="font-mono text-[10px] px-2 py-0.5 border uppercase tracking-wider font-medium border-amber-400/35 bg-amber-500/15 text-amber-200">
              Superadmin
            </span>
          </div>
          <p class="text-xs text-[#D4D4D8] font-medium">Global governance &amp; AI telemetry</p>
        </div>

        <div v-else class="p-3.5 border-b border-white/[0.1] space-y-2">
          <div class="flex items-center justify-between gap-2">
            <label for="ws-switcher" class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">
              Workspace
            </label>
            <span
              :class="[
                'font-mono text-[10px] px-2 py-0.5 border uppercase tracking-wider font-medium',
                tierBadgeClass,
              ]"
            >
              {{ tierLabel }}
            </span>
          </div>

          <select
            id="ws-switcher"
            v-if="memberships.length > 0"
            :value="activeWorkspaceId || ''"
            @change="handleWorkspaceChange"
            class="w-full input-glass px-2.5 py-1.5 text-xs font-medium"
          >
            <option v-for="ws in memberships" :key="ws.id" :value="ws.id">
              {{ ws.name }} ({{ formatRole(ws.role) }})
            </option>
          </select>
          <div v-else class="text-xs text-amber-300 font-medium">
            No workspace selected yet.
          </div>

          <button
            type="button"
            @click="openCreateWorkspaceModal"
            class="w-full flex items-center justify-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium border border-white/[0.12] text-[#D4D4D8] hover:text-[#F5F5F3] hover:bg-white/[0.04] transition-colors"
          >
            <Plus class="h-3.5 w-3.5" aria-hidden="true" />
            <span>New workspace</span>
          </button>
        </div>

        <!-- Grouped Navigation -->
        <nav aria-label="Main workspace menu" class="p-3 space-y-5 text-xs font-medium">
          <template v-if="isSuperadmin">
            <div class="space-y-0.5">
              <div class="px-3 pb-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#8A8D96]">
                Platform
              </div>
              <router-link
                to="/app/admin"
                @click="mobileNavOpen = false"
                :class="[
                  'flex items-center gap-2.5 px-3 py-2 border-l-2 transition-colors',
                  route.path === '/app/admin' && (!route.query.tab || route.query.tab === 'telemetry')
                    ? 'border-[#F5F5F3] bg-white/[0.06] text-[#F5F5F3] font-semibold'
                    : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
                ]"
              >
                <BarChart3 class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>AI Usage</span>
              </router-link>

              <router-link
                :to="{ path: '/app/admin', query: { tab: 'users' } }"
                @click="mobileNavOpen = false"
                :class="[
                  'flex items-center gap-2.5 px-3 py-2 border-l-2 transition-colors',
                  route.path === '/app/admin' && route.query.tab === 'users'
                    ? 'border-[#F5F5F3] bg-white/[0.06] text-[#F5F5F3] font-semibold'
                    : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
                ]"
              >
                <Users class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Users</span>
              </router-link>

              <router-link
                :to="{ path: '/app/admin', query: { tab: 'workspaces' } }"
                @click="mobileNavOpen = false"
                :class="[
                  'flex items-center gap-2.5 px-3 py-2 border-l-2 transition-colors',
                  route.path === '/app/admin' && route.query.tab === 'workspaces'
                    ? 'border-[#F5F5F3] bg-white/[0.06] text-[#F5F5F3] font-semibold'
                    : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
                ]"
              >
                <Building2 class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Workspaces &amp; Plans</span>
              </router-link>

              <router-link
                :to="{ path: '/app/admin', query: { tab: 'audits' } }"
                @click="mobileNavOpen = false"
                :class="[
                  'flex items-center gap-2.5 px-3 py-2 border-l-2 transition-colors',
                  route.path === '/app/admin' && route.query.tab === 'audits'
                    ? 'border-[#F5F5F3] bg-white/[0.06] text-[#F5F5F3] font-semibold'
                    : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
                ]"
              >
                <ScrollText class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Audit Logs</span>
              </router-link>
            </div>

            <div class="space-y-0.5">
              <div class="px-3 pb-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#8A8D96]">
                Account
              </div>
              <router-link
                to="/app/settings"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <ShieldCheck class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Account Security</span>
              </router-link>
            </div>
          </template>

          <template v-else>
            <div class="space-y-0.5">
              <div class="px-3 pb-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#8A8D96]">
                Workspace
              </div>
              <router-link
                to="/app/dashboard"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <LayoutDashboard class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Overview</span>
              </router-link>

              <router-link
                to="/app/projects"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <FolderGit2 class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Projects</span>
              </router-link>
            </div>

            <div class="space-y-0.5">
              <div class="px-3 pb-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#8A8D96]">
                Active Project
              </div>
              <router-link
                to="/app/triage"
                @click="mobileNavOpen = false"
                class="flex items-center justify-between gap-2 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <span class="flex items-center gap-2.5 min-w-0">
                  <CheckSquare class="h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>Findings</span>
                </span>
                <span
                  v-if="projectProgress.loaded && projectProgress.totalFindings > 0"
                  class="font-mono text-[10px] tabular-nums px-1.5 py-0.5 border border-white/[0.14] text-[#D4D4D8]"
                >
                  {{ projectProgress.totalFindings }}
                </span>
              </router-link>

              <router-link
                to="/app/ai-review"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <FileText class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Report Draft</span>
              </router-link>

              <router-link
                to="/app/theme"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <Palette class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Branding &amp; PDF</span>
              </router-link>
            </div>

            <div class="space-y-0.5">
              <div class="px-3 pb-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#8A8D96]">
                Account
              </div>
              <router-link
                to="/app/billing"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <CreditCard class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Billing</span>
              </router-link>

              <router-link
                to="/app/settings"
                @click="mobileNavOpen = false"
                class="flex items-center gap-2.5 px-3 py-2 border-l-2 border-transparent text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03] transition-colors"
                active-class="!border-[#F5F5F3] !bg-white/[0.06] !text-[#F5F5F3] font-semibold"
              >
                <Settings class="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>Settings</span>
              </router-link>
            </div>
          </template>
        </nav>
      </div>

      <!-- Footer User Info -->
      <div class="p-3 border-t border-white/[0.1]">
        <div class="flex items-center justify-between p-2.5 border border-white/[0.1] bg-[#050507]">
          <div class="truncate mr-2">
            <span class="text-xs font-semibold text-[#F5F5F3] truncate block">
              {{ currentUser?.full_name || currentUser?.email || 'Account' }}
            </span>
            <div class="flex items-center gap-1.5 mt-0.5">
              <span class="text-[11px] font-mono text-[#8A8D96]">
                {{ isSuperadmin ? 'Platform Superadmin' : formatRole(activeRole) }}
              </span>
              <span
                v-if="currentUser?.is_superadmin"
                class="font-mono text-[10px] px-1.5 py-0.5 border border-white/[0.2] text-[#F5F5F3] font-medium"
              >
                Admin
              </span>
            </div>
          </div>
          <button
            type="button"
            @click="handleLogout"
            class="p-2 text-[#8A8D96] hover:text-red-300 hover:bg-red-500/15 transition-colors"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut class="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="relative z-10 flex-1 flex flex-col overflow-hidden min-w-0">
      <header class="h-16 border-b border-white/[0.1] bg-[#050507] flex items-center justify-between px-4 sm:px-6 shrink-0 gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <button
            type="button"
            @click="mobileNavOpen = true"
            class="lg:hidden min-h-[40px] min-w-[40px] flex items-center justify-center border border-white/[0.14] bg-[#08080B] text-[#F5F5F3] hover:bg-white/[0.06]"
            aria-label="Open navigation menu"
          >
            <Menu class="h-4 w-4" />
          </button>
          <div class="min-w-0 truncate">
            <slot name="header-title">
              <h1 class="text-base font-display font-semibold text-[#F5F5F3] truncate">Overview</h1>
            </slot>
          </div>
        </div>

        <div class="flex items-center gap-2.5 shrink-0">
          <div v-if="!isSuperadmin && projects.length > 0" class="hidden sm:flex items-center gap-2">
            <label for="topbar-project-desktop" class="font-mono text-[11px] uppercase tracking-wider text-[#8A8D96]">
              Project
            </label>
            <select
              id="topbar-project-desktop"
              :value="activeProjectId || ''"
              @change="handleProjectChange"
              class="max-w-[210px] input-glass px-2.5 py-1.5 text-xs"
            >
              <option v-for="proj in projects" :key="proj.id" :value="proj.id">
                {{ proj.name }} {{ proj.status === 'ARCHIVED' ? '(Archived)' : '' }}
              </option>
            </select>
          </div>

          <router-link
            v-else-if="!isSuperadmin && !activeProject"
            to="/app/projects"
            class="hidden sm:inline-flex items-center px-2 py-1.5 text-xs text-[#8A8D96] hover:text-[#F5F5F3] underline underline-offset-4 transition-colors"
          >
            No project selected
          </router-link>

          <button
            v-if="!isSuperadmin"
            type="button"
            :disabled="!activeProject"
            @click="openCliDrawer()"
            class="btn-glass px-3 py-1.5 text-xs disabled:opacity-40 disabled:cursor-not-allowed"
            :title="activeProject ? 'Import Scan Results via CLI' : 'Select or create a project first'"
            aria-label="Import Scan Results via CLI"
          >
            <Terminal class="h-3.5 w-3.5" aria-hidden="true" />
            <span class="hidden md:inline">Import CLI</span>
          </button>

          <router-link
            to="/"
            class="text-xs text-[#8A8D96] hover:text-[#F5F5F3] transition-colors inline-flex items-center gap-1 px-2.5 py-1.5"
            aria-label="View public website"
          >
            <span class="hidden md:inline">Website</span>
            <ExternalLink class="h-3.5 w-3.5" aria-hidden="true" />
          </router-link>
        </div>
      </header>

      <!-- Mobile Active Project Switcher Bar -->
      <div
        v-if="!isSuperadmin && projects.length > 0"
        class="sm:hidden border-b border-white/[0.1] bg-[#08080B] px-4 py-2 flex items-center gap-2 shrink-0"
      >
        <label for="topbar-project-mobile" class="font-mono text-[11px] text-[#8A8D96] shrink-0">
          Project
        </label>
        <select
          id="topbar-project-mobile"
          :value="activeProjectId || ''"
          @change="handleProjectChange"
          class="flex-1 min-w-0 input-glass px-2.5 py-1 text-xs"
        >
          <option v-for="proj in projects" :key="proj.id" :value="proj.id">
            {{ proj.name }} {{ proj.status === 'ARCHIVED' ? '(Archived)' : '' }}
          </option>
        </select>
      </div>

      <!-- Connection Error Banner (preserves session on transient API/network failures) -->
      <div
        v-if="connectionError"
        role="alert"
        class="border-b border-amber-400/35 bg-amber-500/10 px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs text-amber-200 shrink-0"
      >
        <span>{{ connectionError }}</span>
        <button
          type="button"
          :disabled="retryingConnection"
          @click="handleRetryConnection"
          class="btn-glass px-3 py-1 text-xs border-amber-400/40 text-amber-100 hover:bg-amber-500/20 disabled:opacity-50"
        >
          {{ retryingConnection ? 'Retrying...' : 'Retry connection' }}
        </button>
      </div>

      <!-- Scrollable Main -->
      <main id="app-main" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        <div
          v-if="!isSuperadmin && Boolean(activeProject) && (pipelineStep > 0 || showPipeline)"
          class="max-w-7xl mx-auto"
        >
          <PipelineStepper :active-step="pipelineStep" @open-cli="openCliDrawer()" />
        </div>
        <slot />
      </main>
    </div>

    <CliIngestDrawer
      v-if="!isSuperadmin"
      :open="cliDrawerOpen"
      :project-id="cliDrawerProjectId"
      @close="closeCliDrawer"
    />

    <BaseModal
      v-if="!isSuperadmin"
      :open="createWsModalOpen"
      title="Create Personal Workspace"
      subtitle="Start an isolated Free-tier workspace owned by your account (maximum 1 personal Free workspace per user)."
      max-width="md"
      @close="createWsModalOpen = false"
    >
      <form id="create-ws-modal-form" @submit.prevent="handleCreateWorkspace" class="space-y-4">
        <div
          v-if="ownsFreeWorkspace"
          class="p-3.5 border border-amber-400/35 bg-amber-500/10 text-xs text-amber-200 space-y-2 leading-relaxed"
        >
          <p>
            You already own a Free-tier workspace. Upgrade an existing workspace to Pro or Enterprise before creating another Free workspace.
          </p>
          <router-link
            to="/app/billing"
            @click="createWsModalOpen = false"
            class="inline-block font-semibold underline underline-offset-4 text-[#F5F5F3]"
          >
            Go to Billing &amp; Plans
          </router-link>
        </div>

        <div
          v-else
          class="p-3 border border-white/[0.1] bg-[#050507] text-xs text-[#8A8D96] leading-relaxed"
        >
          Your new workspace starts on the <strong class="text-[#F5F5F3]">Free</strong> plan and is completely isolated from existing workspaces. Your role in other workspaces remains unchanged.
        </div>

        <div class="space-y-1.5">
          <label for="switcher-new-ws-name" class="text-xs font-medium text-[#D4D4D8] block">
            Workspace name
          </label>
          <input
            id="switcher-new-ws-name"
            v-model.trim="newWorkspaceName"
            type="text"
            required
            :disabled="ownsFreeWorkspace || creatingWs"
            placeholder="e.g. Personal Lab or Client Assessment"
            class="w-full input-glass px-3 py-2 text-xs disabled:opacity-50"
          />
        </div>
      </form>

      <template #footer>
        <button
          type="button"
          @click="createWsModalOpen = false"
          class="btn-glass px-4 py-2 text-xs"
        >
          Cancel
        </button>
        <button
          type="submit"
          form="create-ws-modal-form"
          :disabled="ownsFreeWorkspace || creatingWs || !newWorkspaceName"
          class="btn-platinum px-4 py-2 text-xs disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {{ creatingWs ? 'Creating...' : 'Create workspace' }}
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, provide, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BarChart3,
  Building2,
  CheckSquare,
  CreditCard,
  ExternalLink,
  FileText,
  FolderGit2,
  LayoutDashboard,
  LogOut,
  Menu,
  Palette,
  Plus,
  ScrollText,
  Settings,
  ShieldCheck,
  Terminal,
  Users,
  X,
} from 'lucide-vue-next'
import AmbientCanvas from '@/components/ui/AmbientCanvas.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import CliIngestDrawer from '@/components/ui/CliIngestDrawer.vue'
import PipelineStepper from '@/components/ui/PipelineStepper.vue'
import { api } from '@/services/api'
import { OPEN_CLI_DRAWER_KEY, session } from '@/stores/session'
import { toast } from '@/stores/toast'

withDefaults(
  defineProps<{
    pipelineStep?: number
    showPipeline?: boolean
  }>(),
  {
    pipelineStep: 0,
    showPipeline: false,
  }
)

const route = useRoute()
const router = useRouter()
const mobileNavOpen = ref(false)
const cliDrawerOpen = ref(false)
const cliDrawerProjectId = ref<string | null>(null)
const createWsModalOpen = ref(false)
const newWorkspaceName = ref('')
const creatingWs = ref(false)
const retryingConnection = ref(false)

const openCreateWorkspaceModal = () => {
  newWorkspaceName.value = ''
  createWsModalOpen.value = true
  mobileNavOpen.value = false
}

const openCliDrawer = (projectId?: string | null) => {
  cliDrawerProjectId.value = projectId ?? null
  cliDrawerOpen.value = true
}

const closeCliDrawer = () => {
  cliDrawerOpen.value = false
  cliDrawerProjectId.value = null
}

provide(OPEN_CLI_DRAWER_KEY, openCliDrawer)

const currentUser = computed(() => session.state.user)
const isSuperadmin = computed(() => Boolean(currentUser.value?.is_superadmin))
const memberships = computed(() => session.state.memberships)
const activeWorkspaceId = computed(() => session.state.activeWorkspaceId)
const subscription = computed(() => session.state.subscription)
const projects = computed(() => session.state.projects)
const activeProjectId = computed(() => session.state.activeProjectId)
const activeProject = session.activeProject
const projectProgress = computed(() => session.state.projectProgress)
const activeRole = session.activeRole
const ownsFreeWorkspace = session.ownsFreeWorkspace
const connectionError = computed(() => session.state.connectionError)

const tierLabel = computed(() => {
  const tier = subscription.value?.tier
  if (tier === 'ENTERPRISE') return 'Enterprise'
  if (tier === 'PRO') return 'Pro'
  return 'Free'
})

const tierBadgeClass = computed(() => {
  const tier = subscription.value?.tier
  if (tier === 'ENTERPRISE') {
    return 'bg-white/[0.08] text-[#F5F5F3] border-white/[0.24]'
  }
  if (tier === 'PRO') {
    return 'bg-[#F5F5F3] text-[#050507] border-[#F5F5F3] font-semibold'
  }
  return 'bg-transparent text-[#8A8D96] border-white/[0.14]'
})

const formatRole = (role: string): string => {
  if (!role) return 'Member'
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase()
}

const onKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && mobileNavOpen.value) {
    mobileNavOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  if (!session.state.initialized) {
    session.hydrate().catch((err: unknown) => {
      if (err && typeof err === 'object' && 'status' in err) {
        const status = (err as { status: number }).status
        if (status === 401 || status === 403) {
          void router.push({ path: '/app/login', query: { reason: 'session_expired' } })
        }
      }
    })
  }
})

const handleRetryConnection = async () => {
  retryingConnection.value = true
  try {
    await session.retryConnection()
    toast.success('API connection restored.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Still unable to reach the API server.')
  } finally {
    retryingConnection.value = false
  }
}

const handleCreateWorkspace = async () => {
  if (!newWorkspaceName.value || ownsFreeWorkspace.value) return
  creatingWs.value = true
  try {
    const created = await api.workspaces.create(newWorkspaceName.value)
    newWorkspaceName.value = ''
    createWsModalOpen.value = false
    await session.hydrate(true)
    await session.switchWorkspace(created.id)
    toast.success(`Workspace '${created.name}' created and activated.`)
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to create workspace.')
  } finally {
    creatingWs.value = false
  }
}

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

const handleWorkspaceChange = async (event: Event) => {
  const target = event.target as HTMLSelectElement
  try {
    await session.switchWorkspace(target.value)
    toast.info('Active workspace updated.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to switch workspace.')
  }
}

const handleProjectChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  session.selectProject(target.value || null)
}

const handleLogout = async () => {
  await session.logout()
  toast.info('You have been signed out.')
  await router.push('/app/login')
}
</script>
