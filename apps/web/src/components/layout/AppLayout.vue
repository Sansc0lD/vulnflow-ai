<template>
  <div class="flex h-screen bg-background text-zinc-100 overflow-hidden font-sans">
    <!-- Sidebar -->
    <aside class="w-64 border-r border-border bg-surface flex flex-col justify-between shrink-0">
      <div>
        <!-- Brand / Header -->
        <div class="h-16 border-b border-border px-5 flex items-center justify-between">
          <router-link to="/app/dashboard" class="flex items-center space-x-2.5">
            <div class="h-8 w-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
              <ShieldAlert class="h-4 w-4" />
            </div>
            <div>
              <span class="font-bold text-sm text-white flex items-center gap-1">
                VulnFlow <span class="text-[10px] px-1 py-0.2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">AI</span>
              </span>
              <span class="text-[10px] text-zinc-400 block font-mono">AGENCY DASHBOARD</span>
            </div>
          </router-link>
        </div>

        <!-- Workspace Info Card -->
        <div class="p-3 mx-3 mt-3 rounded-lg border border-border/80 bg-surface-elevated flex items-center justify-between">
          <div class="truncate">
            <span class="text-[10px] text-zinc-400 font-mono block">WORKSPACE AKTIF</span>
            <span class="text-xs font-semibold text-white truncate block">{{ activeWorkspace?.name || 'Agensi Utama' }}</span>
          </div>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
            FREE TIER
          </span>
        </div>

        <!-- Navigation Links -->
        <nav class="p-3 space-y-1 text-xs font-medium">
          <router-link
            to="/app/dashboard"
            class="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-elevated transition-colors"
            active-class="!bg-blue-600/10 !text-blue-400 !border !border-blue-500/20 font-semibold"
          >
            <LayoutDashboard class="h-4 w-4" />
            <span>Dasbor Utama (WF1)</span>
          </router-link>

          <router-link
            to="/app/projects"
            class="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-elevated transition-colors"
            active-class="!bg-blue-600/10 !text-blue-400 !border !border-blue-500/20 font-semibold"
          >
            <FolderGit2 class="h-4 w-4" />
            <span>Proyek & Scope ROE</span>
          </router-link>

          <router-link
            to="/app/triage"
            class="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-elevated transition-colors"
            active-class="!bg-blue-600/10 !text-blue-400 !border !border-blue-500/20 font-semibold"
          >
            <CheckSquare class="h-4 w-4" />
            <span>Papan Triase & PoC (WF2)</span>
          </router-link>

          <router-link
            to="/app/ai-review"
            class="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-elevated transition-colors"
            active-class="!bg-blue-600/10 !text-blue-400 !border !border-blue-500/20 font-semibold"
          >
            <Sparkles class="h-4 w-4" />
            <span>Review Narasi AI (WF3)</span>
          </router-link>

          <router-link
            to="/app/theme"
            class="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-elevated transition-colors"
            active-class="!bg-blue-600/10 !text-blue-400 !border !border-blue-500/20 font-semibold"
          >
            <Palette class="h-4 w-4" />
            <span>Theme Studio (WF4)</span>
          </router-link>

          <router-link
            to="/app/billing"
            class="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-elevated transition-colors"
            active-class="!bg-blue-600/10 !text-blue-400 !border !border-blue-500/20 font-semibold"
          >
            <CreditCard class="h-4 w-4" />
            <span>Billing & Kuota (WF5)</span>
          </router-link>
        </nav>
      </div>

      <!-- Footer / User Info -->
      <div class="p-3 border-t border-border">
        <div class="flex items-center justify-between p-2 rounded-lg bg-surface-elevated">
          <div class="truncate mr-2">
            <span class="text-xs font-medium text-white truncate block">{{ currentUser?.email || 'pentester@vulnflow.ai' }}</span>
            <span class="text-[10px] text-zinc-400 font-mono block">ROLE: PENTESTER</span>
          </div>
          <button
            @click="handleLogout"
            class="p-1.5 rounded text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Keluar"
          >
            <LogOut class="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Header -->
      <header class="h-16 border-b border-border bg-surface flex items-center justify-between px-6 shrink-0">
        <div class="flex items-center space-x-3">
          <slot name="header-title">
            <h1 class="text-base font-semibold text-white">Dasbor Auditor</h1>
          </slot>
        </div>

        <div class="flex items-center space-x-3">
          <router-link
            to="/"
            class="text-xs text-zinc-400 hover:text-white transition-colors flex items-center space-x-1"
          >
            <span>Kembali ke Halaman Publik</span>
            <ExternalLink class="h-3.5 w-3.5" />
          </router-link>
        </div>
      </header>

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ShieldAlert,
  LayoutDashboard,
  FolderGit2,
  CheckSquare,
  Sparkles,
  Palette,
  CreditCard,
  LogOut,
  ExternalLink,
} from 'lucide-vue-next'
import { authStorage, User, Workspace } from '@/services/api'

const router = useRouter()
const currentUser = ref<User | null>(null)
const activeWorkspace = ref<Workspace | null>(null)

onMounted(() => {
  currentUser.value = authStorage.getUser()
  activeWorkspace.value = authStorage.getActiveWorkspace()
})

const handleLogout = () => {
  authStorage.clear()
  router.push('/app/login')
}
</script>
