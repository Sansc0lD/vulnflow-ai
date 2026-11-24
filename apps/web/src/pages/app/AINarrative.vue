<template>
  <AppLayout :pipeline-step="4">
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
          Report Draft
        </h1>
        <p class="text-xs text-[#8A8D96] truncate">
          {{ activeProject ? activeProject.name : 'Select a project' }}
        </p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <EmptyState
        v-if="!activeProject"
        :icon="FolderGit2"
        title="No active project"
        description="Select a project first to generate and review executive summaries."
        action-label="Open Projects"
        action-to="/app/projects"
      />

      <template v-else>
        <!-- Toolbar -->
        <div
          class="flex flex-wrap items-center justify-between gap-4 p-4 border border-white/[0.11] bg-[#08080B]"
        >
          <div class="flex flex-wrap items-center gap-2.5 text-xs">
            <label for="ai-lang" class="sr-only">Draft language</label>
            <select
              id="ai-lang"
              v-model="language"
              :disabled="generating"
              class="input-glass px-2.5 py-1.5 text-xs"
            >
              <option value="en">English (Executive)</option>
              <option value="id">Bahasa Indonesia</option>
            </select>

            <label for="ai-tone" class="sr-only">Writing tone</label>
            <select
              id="ai-tone"
              v-model="tone"
              :disabled="generating"
              class="input-glass px-2.5 py-1.5 text-xs"
            >
              <option value="formal_executive">Executive Formal</option>
              <option value="board_summary">Board Summary</option>
              <option value="technical_brief">Technical Brief</option>
            </select>

            <span
              class="font-mono text-[10px] uppercase tracking-wider px-2 py-1 bg-emerald-500/10 text-emerald-300 border border-emerald-400/25 font-medium"
            >
              Privacy protected
            </span>

            <StatusBadge
              v-if="currentNarrative"
              :status="currentNarrative.approval_status"
            />

            <span
              v-if="currentNarrative?.is_fallback"
              class="font-mono text-[10px] uppercase tracking-wider px-2 py-1 bg-amber-500/10 text-amber-300 border border-amber-400/25 font-medium"
            >
              Standard template
            </span>

            <span
              v-if="isDirty"
              class="font-mono text-[10px] uppercase tracking-wider px-2 py-1 bg-amber-500/10 text-amber-300 border border-amber-400/35"
            >
              Unsaved changes
            </span>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <!-- Edit / Preview Mode Toggle -->
            <div
              v-if="currentNarrative"
              class="inline-flex border border-white/[0.14] divide-x divide-white/[0.14] bg-[#050507] text-xs font-medium"
            >
              <button
                type="button"
                @click="previewMode = false"
                :class="[
                  'px-3 py-1.5 transition-colors',
                  !previewMode
                    ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
                    : 'text-[#8A8D96] hover:text-[#F5F5F3]',
                ]"
              >
                Edit
              </button>
              <button
                type="button"
                @click="previewMode = true"
                :class="[
                  'px-3 py-1.5 transition-colors',
                  previewMode
                    ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
                    : 'text-[#8A8D96] hover:text-[#F5F5F3]',
                ]"
              >
                Preview
              </button>
            </div>

            <template v-if="canEdit">
              <button
                type="button"
                @click="promptGenerate"
                :disabled="generating || selectedFindingIds.length === 0"
                class="btn-glass px-3.5 py-1.5 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw
                  :class="['h-3.5 w-3.5', generating ? 'animate-spin' : '']"
                  aria-hidden="true"
                />
                <span>
                  {{ generating ? 'Generating...' : currentNarrative ? 'Regenerate' : 'Generate Draft' }}
                </span>
              </button>

              <button
                v-if="currentNarrative?.id"
                type="button"
                @click="handleSaveNarrative('DRAFT')"
                :disabled="saving || generating"
                class="btn-glass px-3.5 py-1.5 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save class="h-3.5 w-3.5" aria-hidden="true" />
                <span>Save Draft</span>
              </button>

              <button
                v-if="currentNarrative?.id"
                type="button"
                @click="handleSaveNarrative('APPROVED')"
                :disabled="saving || generating"
                class="btn-glass px-4 py-1.5 text-xs border-emerald-400/35 text-emerald-300 hover:bg-emerald-500/20 hover:text-emerald-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckCircle2 class="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
                <span>Approve Draft</span>
              </button>
            </template>

            <router-link
              v-if="currentNarrative"
              to="/app/theme"
              class="btn-platinum px-3.5 py-1.5 text-xs"
            >
              <span>Export PDF</span>
              <ArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
            </router-link>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div class="lg:col-span-8 space-y-4">
            <SkeletonBlock variant="text" :count="6" />
          </div>
          <div class="lg:col-span-4 space-y-4">
            <SkeletonBlock variant="text" :count="5" />
          </div>
        </div>

        <!-- Main Grid -->
        <div v-else class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Editor / Preview Canvas (8 cols) -->
          <div class="lg:col-span-8 space-y-6">
            <div
              v-if="generating && generationStage"
              role="status"
              class="border border-white/[0.14] bg-[#08080B] p-4 space-y-2.5 text-xs"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="font-medium text-[#F5F5F3]">{{ generationStage }}</span>
                <span class="font-mono text-[#8A8D96] tabular-nums">{{ generationProgress }}%</span>
              </div>
              <div class="h-1.5 bg-[#050507] border border-white/[0.1] overflow-hidden">
                <div
                  class="h-full bg-[#F5F5F3] transition-all duration-300"
                  :style="{ width: `${generationProgress}%` }"
                ></div>
              </div>
            </div>

            <EmptyState
              v-if="!currentNarrative"
              :icon="FileText"
              title="No report draft yet"
              description="Select findings on the right and click Generate Draft to create an executive summary, business impact analysis, and fix guidance."
              :action-label="canEdit && selectedFindingIds.length > 0 ? 'Generate Draft' : ''"
              @action="promptGenerate"
            />

            <!-- Preview Mode -->
            <div
              v-else-if="previewMode"
              class="border border-white/[0.11] bg-[#08080B] p-6 sm:p-8 space-y-6"
            >
              <div class="border-b border-white/[0.1] pb-4 flex items-center justify-between gap-2">
                <div>
                  <span class="font-mono text-[11px] uppercase tracking-wider text-[#8A8D96]">Report Draft Preview</span>
                  <h2 class="text-lg font-display font-semibold text-[#F5F5F3] mt-0.5">{{ activeProject.name }}</h2>
                </div>
                <StatusBadge :status="currentNarrative.approval_status" />
              </div>

              <div class="space-y-2 max-w-2xl">
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96]">01. Executive Summary</h3>
                <p class="text-base text-[#F5F5F3] leading-7 whitespace-pre-line">
                  {{ editor.executive_summary || '—' }}
                </p>
              </div>

              <div class="space-y-2 max-w-2xl">
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-red-300">02. Business Impact</h3>
                <p class="text-base text-[#D4D4D8] leading-7 whitespace-pre-line">
                  {{ editor.business_impact || '—' }}
                </p>
              </div>

              <div class="space-y-3 border-t border-white/[0.08] pt-5">
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-emerald-400">
                  03. Remediation Guidance ({{ editor.remediations.length }})
                </h3>
                <ul class="divide-y divide-white/[0.08] border-y border-white/[0.08]">
                  <li
                    v-for="(rem, idx) in editor.remediations"
                    :key="idx"
                    class="py-4 space-y-1.5"
                  >
                    <div class="text-xs font-mono font-semibold text-[#F5F5F3]">
                      {{ rem.cwe_id }} — {{ rem.vuln_title }}
                    </div>
                    <p class="text-sm text-[#D4D4D8] leading-relaxed whitespace-pre-line max-w-2xl">
                      {{ rem.remediation_guidance }}
                    </p>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Edit Mode -->
            <template v-else>
              <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-3">
                <div class="flex items-center justify-between border-b border-white/[0.08] pb-2.5 gap-2">
                  <label
                    for="ai-exec-summary"
                    class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2"
                  >
                    <FileText class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
                    <span>1. Executive Summary</span>
                  </label>
                  <span class="font-mono text-xs text-[#8A8D96] tabular-nums">
                    {{ wordCount(editor.executive_summary) }} words
                  </span>
                </div>
                <textarea
                  id="ai-exec-summary"
                  v-model="editor.executive_summary"
                  :readonly="!canEdit || generating"
                  rows="6"
                  class="input-glass w-full p-3.5 text-sm leading-relaxed"
                ></textarea>
              </div>

              <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-3">
                <div class="flex items-center justify-between border-b border-white/[0.08] pb-2.5 gap-2">
                  <label
                    for="ai-biz-impact"
                    class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2"
                  >
                    <AlertCircle class="h-4 w-4 text-red-400" aria-hidden="true" />
                    <span>2. Business Impact</span>
                  </label>
                  <span class="font-mono text-xs text-[#8A8D96] tabular-nums">
                    {{ wordCount(editor.business_impact) }} words
                  </span>
                </div>
                <textarea
                  id="ai-biz-impact"
                  v-model="editor.business_impact"
                  :readonly="!canEdit || generating"
                  rows="5"
                  class="input-glass w-full p-3.5 text-sm leading-relaxed"
                ></textarea>
              </div>

              <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
                <div class="flex flex-wrap items-center justify-between border-b border-white/[0.08] pb-2.5 gap-2">
                  <h3 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
                    <CheckCircle2 class="h-4 w-4 text-emerald-400" aria-hidden="true" />
                    <span>3. Remediation Guidance ({{ editor.remediations.length }})</span>
                  </h3>
                  <button
                    v-if="canEdit"
                    type="button"
                    :disabled="generating"
                    @click="addRemediationItem"
                    class="btn-glass px-2.5 py-1 text-xs disabled:opacity-50"
                  >
                    <Plus class="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Add item</span>
                  </button>
                </div>

                <div v-if="editor.remediations.length === 0" class="text-xs text-[#8A8D96]">
                  No remediation items yet. Click Add item to include specific guidance.
                </div>

                <div class="divide-y divide-white/[0.08] border-t border-white/[0.08]">
                  <div
                    v-for="(rem, index) in editor.remediations"
                    :key="index"
                    class="py-4 space-y-2.5"
                  >
                    <div class="flex flex-wrap items-center gap-2">
                      <input
                        v-model.trim="rem.cwe_id"
                        :readonly="!canEdit || generating"
                        type="text"
                        aria-label="CWE identifier"
                        placeholder="CWE-89"
                        class="input-glass w-24 px-2.5 py-1.5 text-xs font-mono font-semibold text-[#F5F5F3]"
                      />
                      <input
                        v-model="rem.vuln_title"
                        :readonly="!canEdit || generating"
                        type="text"
                        aria-label="Finding title"
                        placeholder="Finding title..."
                        class="input-glass flex-1 min-w-[180px] px-3 py-1.5 text-xs sm:text-sm font-medium"
                      />
                      <button
                        v-if="canEdit"
                        type="button"
                        :disabled="generating"
                        @click="removeRemediationItem(index)"
                        class="p-1.5 text-[#8A8D96] hover:text-red-300 hover:bg-red-500/15 transition-colors"
                        aria-label="Remove remediation item"
                      >
                        <Trash2 class="h-4 w-4" />
                      </button>
                    </div>
                    <textarea
                      v-model="rem.remediation_guidance"
                      :readonly="!canEdit || generating"
                      rows="3"
                      aria-label="Fix steps"
                      placeholder="Recommended fix steps..."
                      class="input-glass w-full p-3 text-xs sm:text-sm leading-relaxed"
                    ></textarea>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- Sidebar: Draft Info, Version Switcher & Eligible Findings (4 cols) -->
          <div class="lg:col-span-4 space-y-6">
            <div class="border border-white/[0.11] bg-[#08080B] p-5 space-y-4 text-xs">
              <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] border-b border-white/[0.08] pb-2.5">
                Draft Overview
              </h3>

              <div class="space-y-2.5 text-[#D4D4D8]">
                <div class="flex justify-between">
                  <span class="text-[#8A8D96]">Saved versions</span>
                  <span class="text-[#F5F5F3] font-semibold tabular-nums">{{ narratives.length }}</span>
                </div>

                <div v-if="narratives.length > 0" class="space-y-1">
                  <label for="narrative-version-select" class="text-xs text-[#8A8D96] block">
                    Select version
                  </label>
                  <select
                    id="narrative-version-select"
                    :value="selectedNarrativeId"
                    @change="handleVersionSelectChange"
                    class="input-glass w-full px-2.5 py-1.5 text-xs"
                  >
                    <option
                      v-for="(n, idx) in narratives"
                      :key="n.id || idx"
                      :value="n.id || String(idx)"
                    >
                      v{{ narratives.length - idx }} · {{ n.approval_status === 'APPROVED' ? 'Approved' : 'Draft' }} ({{ n.tokens_consumed }} tokens)
                    </option>
                  </select>
                </div>

                <div class="flex justify-between">
                  <span class="text-[#8A8D96]">Token usage</span>
                  <span class="text-[#F5F5F3] font-mono font-semibold tabular-nums">
                    {{ currentNarrative?.tokens_consumed ?? 0 }}
                  </span>
                </div>

                <div class="flex justify-between">
                  <span class="text-[#8A8D96]">Engine</span>
                  <span :class="currentNarrative?.is_fallback ? 'text-amber-300' : 'text-emerald-400'">
                    {{ currentNarrative?.is_fallback ? 'Standard CWE template' : 'AI Ghostwriter' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Included Findings Checklist -->
            <div class="border border-white/[0.11] bg-[#08080B] p-5 space-y-3 text-xs">
              <div class="flex items-center justify-between border-b border-white/[0.08] pb-2.5 gap-2">
                <span class="font-semibold text-[#F5F5F3] tabular-nums">
                  Included Findings ({{ selectedFindingIds.length }}/{{ eligibleFindings.length }})
                </span>
                <div class="flex items-center gap-2 text-xs">
                  <button type="button" @click="selectCuratedOnly" class="text-[#F5F5F3] underline underline-offset-4">
                    Report only
                  </button>
                  <button type="button" @click="selectAllEligible" class="text-[#D4D4D8] hover:text-white underline underline-offset-4">
                    All
                  </button>
                  <button
                    v-if="selectedFindingIds.length > 0"
                    type="button"
                    @click="selectedFindingIds = []"
                    class="text-[#8A8D96] hover:text-white"
                  >
                    Clear
                  </button>
                </div>
              </div>

              <p class="text-xs text-[#8A8D96] leading-relaxed">
                Only valid, in-scope findings are included in sanitized report generation.
              </p>

              <EmptyState
                v-if="eligibleFindings.length === 0"
                :icon="CheckSquare"
                title="No eligible findings"
                description="Make sure your project has valid in-scope findings."
                action-label="Open Findings"
                action-to="/app/triage"
              />

              <div v-else class="divide-y divide-white/[0.08] border-y border-white/[0.08] max-h-80 overflow-y-auto">
                <label
                  v-for="f in eligibleFindings"
                  :key="f.id"
                  class="flex items-start gap-2.5 py-2.5 cursor-pointer hover:bg-white/[0.03] px-1 transition-colors"
                >
                  <input
                    v-model="selectedFindingIds"
                    :value="f.id"
                    type="checkbox"
                    class="mt-0.5 bg-[#050507] border-white/30 text-[#F5F5F3]"
                  />
                  <div class="min-w-0 flex-1 space-y-1">
                    <div class="font-medium text-[#F5F5F3] truncate">{{ f.title }}</div>
                    <div class="flex items-center justify-between gap-2 text-[11px] font-mono text-[#8A8D96]">
                      <span>{{ f.severity }} · {{ f.cwe_id }}</span>
                      <span v-if="f.is_curated_for_report" class="font-sans text-emerald-400">Selected</span>
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Regenerate Confirmation Dialog -->
    <ConfirmDialog
      :open="showWarningModal"
      title="Generate new draft version?"
      message="Generating a new draft saves the result as your latest version. Earlier versions remain available in the version selector."
      confirm-text="Generate new draft"
      variant="primary"
      :loading="generating"
      @confirm="executeGenerate"
      @cancel="showWarningModal = false"
    />

    <!-- Unsaved Dirty Guard Dialog -->
    <ConfirmDialog
      :open="Boolean(pendingVersionId)"
      title="Discard unsaved changes?"
      message="You have unsaved edits on the current draft. Switching versions will discard them."
      confirm-text="Discard & switch"
      variant="warning"
      @confirm="confirmVersionSwitch"
      @cancel="cancelVersionSwitch"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  CheckSquare,
  FileText,
  FolderGit2,
  Plus,
  RefreshCw,
  Save,
  Trash2,
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {
  api,
  type AINarrativeResponse,
  type Finding,
  type RemediationItem,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const activeProject = session.activeProject
const canEdit = computed(() => session.activeRole.value !== 'VIEWER')

const loading = ref(false)
const previewMode = ref(false)
const language = ref<'id' | 'en'>('en')
const tone = ref('formal_executive')
const generating = ref(false)
const generationStage = ref('')
const generationProgress = ref(0)
const saving = ref(false)
const showWarningModal = ref(false)
const pendingVersionId = ref<string | null>(null)

const eligibleFindings = ref<Finding[]>([])
const selectedFindingIds = ref<string[]>([])
const narratives = ref<AINarrativeResponse[]>([])
const selectedNarrativeId = ref<string>('')

const editor = ref<{
  executive_summary: string
  business_impact: string
  remediations: RemediationItem[]
}>({
  executive_summary: '',
  business_impact: '',
  remediations: [],
})

const currentNarrative = computed(() => {
  return (
    narratives.value.find((n, idx) => (n.id || String(idx)) === selectedNarrativeId.value) ??
    narratives.value[0] ??
    null
  )
})

const isDirty = computed(() => {
  const n = currentNarrative.value
  if (!n) return false
  return (
    editor.value.executive_summary !== n.narratives.executive_summary ||
    editor.value.business_impact !== n.narratives.business_impact ||
    JSON.stringify(editor.value.remediations) !== JSON.stringify(n.narratives.remediations)
  )
})

const wordCount = (text: string): number => {
  const trimmed = text.trim()
  return trimmed ? trimmed.split(/\s+/).length : 0
}

function syncEditorFromNarrative(n: AINarrativeResponse | null): void {
  if (!n) {
    editor.value = { executive_summary: '', business_impact: '', remediations: [] }
    return
  }
  editor.value = {
    executive_summary: n.narratives.executive_summary,
    business_impact: n.narratives.business_impact,
    remediations: n.narratives.remediations.map((r) => ({ ...r })),
  }
}

watch(currentNarrative, (n) => {
  syncEditorFromNarrative(n)
})

const handleVersionSelectChange = (event: Event) => {
  const selectEl = event.target as HTMLSelectElement
  const nextId = selectEl.value
  if (isDirty.value) {
    pendingVersionId.value = nextId
    selectEl.value = selectedNarrativeId.value
    return
  }
  selectedNarrativeId.value = nextId
}

const confirmVersionSwitch = () => {
  if (pendingVersionId.value !== null) {
    selectedNarrativeId.value = pendingVersionId.value
  }
  pendingVersionId.value = null
}

const cancelVersionSwitch = () => {
  pendingVersionId.value = null
}

onBeforeRouteLeave(() => {
  if (!isDirty.value) return true
  return window.confirm(
    'You have unsaved changes to this draft. Leave the page and discard them?'
  )
})

const addRemediationItem = () => {
  editor.value.remediations.push({
    cwe_id: 'CWE-0',
    vuln_title: '',
    remediation_guidance: '',
  })
}

const removeRemediationItem = (index: number) => {
  editor.value.remediations.splice(index, 1)
}

let aiComponentUnmounted = false
let aiLoadSeq = 0
let aiGenSeq = 0

onUnmounted(() => {
  aiComponentUnmounted = true
  aiLoadSeq += 1
  aiGenSeq += 1
})

async function loadData(): Promise<void> {
  const seq = ++aiLoadSeq
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) {
    eligibleFindings.value = []
    selectedFindingIds.value = []
    narratives.value = []
    selectedNarrativeId.value = ''
    return
  }

  loading.value = true
  try {
    const [findingsRes, narrativeList] = await Promise.all([
      api.findings.list(wId, pId, { is_quarantined: false, limit: 200 }),
      api.ai.listNarratives(wId, pId),
    ])
    if (
      aiComponentUnmounted ||
      seq !== aiLoadSeq ||
      session.state.activeWorkspaceId !== wId ||
      session.state.activeProjectId !== pId
    ) {
      return
    }
    const eligible = findingsRes.items.filter(
      (f) => !f.is_quarantined && f.status !== 'FALSE_POSITIVE'
    )
    eligibleFindings.value = eligible
    selectedFindingIds.value = eligible
      .filter((f) => f.is_curated_for_report)
      .map((f) => f.id)
    if (selectedFindingIds.value.length === 0) {
      selectedFindingIds.value = eligible.map((f) => f.id)
    }

    narratives.value = narrativeList
    selectedNarrativeId.value = narrativeList[0]?.id || (narrativeList[0] ? '0' : '')
    syncEditorFromNarrative(currentNarrative.value)
  } catch (err: unknown) {
    if (!aiComponentUnmounted && seq === aiLoadSeq) {
      toast.error(err instanceof Error ? err.message : 'Unable to load report draft data.')
    }
  } finally {
    if (!aiComponentUnmounted && seq === aiLoadSeq) {
      loading.value = false
    }
  }
}

watch(
  [() => session.state.activeWorkspaceId, () => session.state.activeProjectId],
  () => {
    aiGenSeq += 1
    generating.value = false
    generationStage.value = ''
    generationProgress.value = 0
    void loadData()
  },
  { immediate: true }
)

const selectCuratedOnly = () => {
  const curated = eligibleFindings.value.filter((f) => f.is_curated_for_report).map((f) => f.id)
  selectedFindingIds.value = curated
  if (curated.length === 0) {
    toast.info('No findings are selected for report yet.')
  }
}

const selectAllEligible = () => {
  selectedFindingIds.value = eligibleFindings.value.map((f) => f.id)
}

const promptGenerate = () => {
  if (selectedFindingIds.value.length === 0) {
    toast.warning('Select at least one finding first.')
    return
  }
  if (currentNarrative.value) {
    showWarningModal.value = true
  } else {
    void executeGenerate()
  }
}

const executeGenerate = async () => {
  showWarningModal.value = false
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return
  const genSeq = ++aiGenSeq

  const isStale = () =>
    aiComponentUnmounted ||
    genSeq !== aiGenSeq ||
    session.state.activeWorkspaceId !== wId ||
    session.state.activeProjectId !== pId

  generating.value = true
  generationStage.value = 'Queueing AI draft job...'
  generationProgress.value = 10
  try {
    const accepted = await api.ai.generateNarrativeAsync(wId, pId, {
      tone: tone.value,
      language: language.value,
      sections_requested: ['executive_summary', 'business_impact', 'remediations'],
      finding_ids: selectedFindingIds.value,
    })
    if (isStale()) return

    let generated: AINarrativeResponse | null = null
    for (let attempt = 0; attempt < 90; attempt++) {
      if (isStale()) return
      const job = await api.ai.getJobStatus(wId, pId, accepted.job_id)
      if (isStale()) return
      generationStage.value = job.stage || 'Generating draft...'
      generationProgress.value = job.progress_percentage ?? 50
      if (job.status === 'COMPLETED' && job.narrative) {
        generated = job.narrative
        break
      }
      if (job.status === 'COMPLETED') {
        const latest = await api.ai.listNarratives(wId, pId)
        if (isStale()) return
        generated = latest[0] ?? null
        break
      }
      if (job.status === 'FAILED') {
        throw new Error(job.error_message || 'AI draft generation failed.')
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1200))
    }

    if (isStale()) return
    if (!generated) {
      throw new Error('AI draft generation is still running. Refresh in a moment to view it.')
    }

    narratives.value = [generated, ...narratives.value]
    selectedNarrativeId.value = generated.id || '0'
    syncEditorFromNarrative(generated)
    previewMode.value = false
    void session.refreshProjectProgress()
    if (generated.is_fallback) {
      toast.warning('Draft generated using standard CWE templates because the AI service is unavailable.')
    } else {
      toast.success(`Report draft generated (${generated.tokens_consumed} tokens).`)
    }
  } catch (err: unknown) {
    if (!isStale()) {
      toast.error(err instanceof Error ? err.message : 'Unable to generate report draft.')
    }
  } finally {
    if (!aiComponentUnmounted && genSeq === aiGenSeq) {
      generating.value = false
      generationStage.value = ''
      generationProgress.value = 0
    }
  }
}

const handleSaveNarrative = async (approvalStatus: 'DRAFT' | 'APPROVED') => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  const narrativeId = currentNarrative.value?.id
  if (!wId || !pId || !narrativeId) return

  saving.value = true
  try {
    const updated = await api.ai.updateNarrative(wId, pId, narrativeId, {
      executive_summary: editor.value.executive_summary,
      business_impact: editor.value.business_impact,
      remediations: editor.value.remediations,
      approval_status: approvalStatus,
    })
    const idx = narratives.value.findIndex((n) => n.id === narrativeId)
    if (idx !== -1) {
      narratives.value[idx] = updated
    }
    syncEditorFromNarrative(updated)
    void session.refreshProjectProgress()
    toast.success(
      approvalStatus === 'APPROVED'
        ? 'Draft approved and ready for PDF export.'
        : 'Draft saved.'
    )
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to save draft.')
  } finally {
    saving.value = false
  }
}
</script>
