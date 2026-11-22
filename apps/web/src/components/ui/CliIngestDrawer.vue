<template>
  <BaseModal
    :open="open"
    title="Import Scan Results"
    subtitle="Run Nmap or Nuclei locally on your workstation, then push structured findings directly into this project."
    max-width="xl"
    @close="emit('close')"
  >
    <div class="space-y-5">
      <!-- Active Project Callout -->
      <div class="pb-4 border-b border-white/[0.1] flex flex-wrap items-center justify-between gap-3">
        <div class="min-w-0">
          <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96] block">Active Project</span>
          <span class="text-sm font-semibold text-[#F5F5F3] truncate block mt-0.5">
            {{ targetProject ? `${targetProject.name} · ${targetProject.client_name}` : 'No project selected' }}
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <div
            role="group"
            aria-label="CLI invocation mode"
            class="inline-flex border border-white/[0.14] divide-x divide-white/[0.14] bg-[#050507] text-[11px] font-mono"
          >
            <button
              type="button"
              @click="useUvRunPrefix = false"
              :class="[
                'px-2.5 py-1 transition-colors',
                !useUvRunPrefix
                  ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
                  : 'text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              vulnflow
            </button>
            <button
              type="button"
              @click="useUvRunPrefix = true"
              :class="[
                'px-2.5 py-1 transition-colors',
                useUvRunPrefix
                  ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
                  : 'text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              uv run
            </button>
          </div>
          <button
            v-if="effectiveProjectId !== '<PROJECT_ID>'"
            type="button"
            @click="copyText(effectiveProjectId, 'Project ID')"
            class="btn-glass px-3 py-1.5 text-xs font-mono"
          >
            <Copy class="h-3.5 w-3.5" />
            <span>Copy Project ID</span>
          </button>
        </div>
      </div>

      <p class="text-[11px] text-[#8A8D96] leading-relaxed">
        Running from the source repo without an activated <code class="font-mono text-[#D4D4D8]">.venv</code> or global install? Switch the toggle above to <code class="font-mono text-[#D4D4D8]">uv run</code> (run <code class="font-mono text-[#D4D4D8]">uv run vulnflow setup-tools</code> once if Nuclei is not installed).
      </p>

      <!-- 3-Step Hairline CLI Guide -->
      <ol class="border-y border-white/[0.1] divide-y divide-white/[0.08]">
        <li class="py-4 space-y-2.5">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2.5">
              <span class="font-mono text-xs font-bold text-[#F5F5F3]">01</span>
              <h4 class="text-xs font-semibold text-[#F5F5F3]">Connect the CLI</h4>
            </div>
            <router-link
              to="/app/settings"
              @click="emit('close')"
              class="text-xs font-medium text-[#F5F5F3] underline underline-offset-4 hover:text-zinc-300 flex items-center gap-1"
            >
              <Key class="h-3 w-3" />
              <span>Create API Key</span>
            </router-link>
          </div>
          <div class="relative border border-white/[0.11] bg-[#050507] p-3 pr-20 font-mono text-xs text-emerald-300 overflow-x-auto">
            <code>{{ cmdConfigure }}</code>
            <button
              type="button"
              @click="copyText(cmdConfigure, 'Configure command')"
              class="btn-glass absolute right-2 top-2 px-2.5 py-1 text-[11px]"
            >
              Copy
            </button>
          </div>
        </li>

        <li class="py-4 space-y-2.5">
          <div class="flex items-center gap-2.5">
            <span class="font-mono text-xs font-bold text-[#F5F5F3]">02</span>
            <h4 class="text-xs font-semibold text-[#F5F5F3]">Run your local scan</h4>
          </div>
          <p class="text-xs text-[#8A8D96]">
            Scans run locally on your workstation, never from external cloud servers. Existing Nuclei JSONL or Nmap XML files work identically.
          </p>
          <div class="relative border border-white/[0.11] bg-[#050507] p-3 pr-20 font-mono text-xs text-[#F5F5F3] overflow-x-auto">
            <code>{{ cmdScan }}</code>
            <button
              type="button"
              @click="copyText(cmdScan, 'Scan command')"
              class="btn-glass absolute right-2 top-2 px-2.5 py-1 text-[11px]"
            >
              Copy
            </button>
          </div>
        </li>

        <li class="py-4 space-y-2.5">
          <div class="flex items-center gap-2.5">
            <span class="font-mono text-xs font-bold text-[#F5F5F3]">03</span>
            <h4 class="text-xs font-semibold text-[#F5F5F3]">Upload to this project</h4>
          </div>
          <p class="text-xs text-[#8A8D96]">
            Authorized targets go straight to Findings for review; out-of-scope hosts are set aside automatically.
          </p>
          <div class="relative border border-white/[0.11] bg-[#050507] p-3 pr-20 font-mono text-xs text-[#D4D4D8] overflow-x-auto">
            <code>{{ cmdPush }}</code>
            <button
              type="button"
              @click="copyText(cmdPush, 'Upload command')"
              class="btn-glass absolute right-2 top-2 px-2.5 py-1 text-[11px]"
            >
              Copy
            </button>
          </div>
        </li>
      </ol>

      <!-- Alternative Manual Entry -->
      <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
        <div class="text-xs text-[#8A8D96]">
          Prefer adding manual findings and proof directly in the browser?
        </div>
        <router-link
          to="/app/triage"
          @click="emit('close')"
          class="btn-platinum px-3.5 py-1.5 text-xs shrink-0"
        >
          <span>Open Findings</span>
          <ArrowRight class="h-3.5 w-3.5" />
        </router-link>
      </div>
    </div>

    <template #footer>
      <button
        type="button"
        :disabled="refreshing || !targetProject"
        @click="handleRefreshFindings"
        class="btn-platinum px-4 py-2 text-xs disabled:opacity-50"
      >
        <RefreshCw :class="['h-3.5 w-3.5', refreshing ? 'animate-spin' : '']" />
        <span>{{ refreshing ? 'Refreshing...' : 'Refresh Findings' }}</span>
      </button>
      <button type="button" @click="emit('close')" class="btn-glass px-4 py-2 text-xs">
        Close
      </button>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowRight, Copy, Key, RefreshCw } from 'lucide-vue-next'
import BaseModal from '@/components/ui/BaseModal.vue'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const props = withDefaults(
  defineProps<{
    open: boolean
    projectId?: string | null
  }>(),
  {
    projectId: null,
  }
)

const emit = defineEmits<{
  (e: 'close'): void
}>()

const refreshing = ref(false)
const useUvRunPrefix = ref(false)
const cliBin = computed(() => (useUvRunPrefix.value ? 'uv run vulnflow' : 'vulnflow'))

const targetProject = computed(() => {
  if (props.projectId) {
    return session.state.projects.find((p) => p.id === props.projectId) ?? session.activeProject.value
  }
  return session.activeProject.value
})

const effectiveWorkspaceId = computed(() => session.state.activeWorkspaceId || '<WORKSPACE_ID>')
const effectiveProjectId = computed(() => targetProject.value?.id || '<PROJECT_ID>')
const sampleTarget = computed(() => targetProject.value?.target_scope[0] || 'app.example.com')
const apiOrigin = computed(() => import.meta.env.VITE_API_PUBLIC_URL || window.location.origin)

const handleRefreshFindings = async () => {
  refreshing.value = true
  try {
    await session.refreshProjectProgress()
    const total = session.state.projectProgress.totalFindings
    toast.success(`Synced project telemetry: ${total} finding${total === 1 ? '' : 's'} recorded.`)
  } finally {
    refreshing.value = false
  }
}

const cmdConfigure = computed(
  () =>
    `${cliBin.value} configure --token <YOUR_API_KEY> --workspace ${effectiveWorkspaceId.value} --api-url ${apiOrigin.value}`
)
const cmdScan = computed(
  () => `${cliBin.value} scan --target ${sampleTarget.value} --output scan_results.jsonl`
)
const cmdPush = computed(
  () =>
    `${cliBin.value} push --project ${effectiveProjectId.value} --type nuclei --file scan_results.jsonl`
)

const copyText = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`${label} copied to clipboard.`)
  } catch {
    toast.info(text, label)
  }
}
</script>
