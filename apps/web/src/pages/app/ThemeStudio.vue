<template>
  <AppLayout :pipeline-step="5">
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
          Branding &amp; PDF Export
        </h1>
        <p class="text-xs text-[#8A8D96] truncate">
          {{ activeProject ? activeProject.name : 'Workspace branding & reports' }}
        </p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Quota Exhausted Persistent Banner -->
      <div
        v-if="quotaExhausted"
        role="alert"
        class="border border-red-400/35 bg-red-500/10 p-4 flex flex-wrap items-center justify-between gap-3"
      >
        <div class="flex items-center gap-2.5 text-xs sm:text-sm text-red-200">
          <AlertTriangle class="h-5 w-5 text-red-400 shrink-0" aria-hidden="true" />
          <span>
            Monthly PDF quota reached. Upgrade to <strong>Pro</strong> for 30 white-label exports per month.
          </span>
        </div>
        <router-link
          to="/app/billing"
          class="btn-platinum px-4 py-2 text-xs shrink-0"
        >
          Upgrade in Billing →
        </router-link>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- Settings & Export Controls (5 cols) -->
        <div class="lg:col-span-5 space-y-6">
          <!-- Branding Panel -->
          <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-5">
            <div class="border-b border-white/[0.08] pb-3.5 flex items-start justify-between gap-2">
              <div>
                <h2 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
                  <Palette class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
                  <span>Brand Identity</span>
                </h2>
                <p class="text-xs text-[#8A8D96] mt-1">
                  Applied to cover pages, headers, and footers of exported PDFs.
                </p>
              </div>
              <span
                :class="[
                  'font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 border font-medium shrink-0',
                  isProTier
                    ? 'bg-[#F5F5F3] text-[#050507] border-[#F5F5F3] font-semibold'
                    : 'bg-transparent text-[#8A8D96] border-white/[0.14]',
                ]"
              >
                {{ isProTier ? 'Pro White-Label' : 'Free Preview' }}
              </span>
            </div>

            <div
              v-if="!isManager"
              class="p-3 bg-[#050507] border border-white/[0.1] text-xs text-[#D4D4D8]"
            >
              View-only: only Workspace Managers can change branding settings.
            </div>

            <!-- Logo Upload -->
            <div class="space-y-2">
              <span class="text-xs font-medium text-[#D4D4D8] block">
                Agency logo (PNG, JPEG, or SVG, max 2 MB)
              </span>
              <div class="flex flex-wrap items-center gap-3">
                <div
                  class="h-12 w-12 bg-[#050507] border border-white/[0.14] flex items-center justify-center overflow-hidden font-mono font-semibold text-xs text-[#F5F5F3] shrink-0"
                >
                  <img
                    v-if="workspace?.custom_logo_url"
                    :src="workspace.custom_logo_url"
                    alt="Agency logo"
                    class="h-full w-full object-contain"
                  />
                  <span v-else>{{ workspaceInitials }}</span>
                </div>

                <label
                  v-if="isManager && isProTier"
                  :class="[
                    'btn-glass px-3 py-2 text-xs',
                    !uploadingLogo
                      ? 'cursor-pointer'
                      : 'cursor-not-allowed opacity-50',
                  ]"
                >
                  <span>{{ uploadingLogo ? 'Uploading...' : 'Upload logo' }}</span>
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/svg+xml"
                    class="hidden"
                    :disabled="uploadingLogo"
                    @change="handleLogoUpload"
                  />
                </label>

                <router-link
                  v-else-if="isManager && !isProTier"
                  to="/app/billing"
                  class="btn-glass px-3 py-2 text-xs"
                >
                  Unlock custom logo with Pro →
                </router-link>
              </div>
            </div>

            <!-- Brand Presets -->
            <div v-if="isManager" class="space-y-1.5">
              <span class="text-xs font-medium text-[#D4D4D8] block">PDF color presets</span>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="preset in colorPresets"
                  :key="preset.name"
                  type="button"
                  @click="applyColorPreset(preset.primary, preset.secondary)"
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 border border-white/[0.12] bg-[#050507] text-xs text-[#D4D4D8] hover:border-white/30 hover:text-[#F5F5F3] transition-colors"
                >
                  <span class="h-3 w-3 rounded-full border border-white/30" :style="{ backgroundColor: preset.primary }" />
                  <span>{{ preset.name }}</span>
                </button>
              </div>
            </div>

            <!-- Hex Color Pickers -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label for="brand-primary-hex" class="text-xs font-medium text-[#D4D4D8] block">
                  Primary color
                </label>
                <div class="flex items-center gap-2">
                  <input
                    aria-label="Pick primary color"
                    :value="isValidHex(primaryColor) ? primaryColor : '#1e40af'"
                    @input="primaryColor = ($event.target as HTMLInputElement).value"
                    :disabled="!isManager"
                    type="color"
                    class="h-9 w-9 border border-white/[0.14] bg-[#050507] cursor-pointer p-0.5 shrink-0"
                  />
                  <input
                    id="brand-primary-hex"
                    v-model.trim="primaryColor"
                    :readonly="!isManager"
                    type="text"
                    class="input-glass w-full px-2.5 py-1.5 text-xs font-mono"
                  />
                </div>
                <p v-if="!isValidHex(primaryColor)" class="text-[11px] text-amber-300">
                  Use #RRGGBB hex format
                </p>
              </div>

              <div class="space-y-1.5">
                <label for="brand-secondary-hex" class="text-xs font-medium text-[#D4D4D8] block">
                  Accent color
                </label>
                <div class="flex items-center gap-2">
                  <input
                    aria-label="Pick accent color"
                    :value="isValidHex(secondaryColor) ? secondaryColor : '#0d9488'"
                    @input="secondaryColor = ($event.target as HTMLInputElement).value"
                    :disabled="!isManager"
                    type="color"
                    class="h-9 w-9 border border-white/[0.14] bg-[#050507] cursor-pointer p-0.5 shrink-0"
                  />
                  <input
                    id="brand-secondary-hex"
                    v-model.trim="secondaryColor"
                    :readonly="!isManager"
                    type="text"
                    class="input-glass w-full px-2.5 py-1.5 text-xs font-mono"
                  />
                </div>
                <p v-if="!isValidHex(secondaryColor)" class="text-[11px] text-amber-300">
                  Use #RRGGBB hex format
                </p>
              </div>
            </div>

            <div
              class="text-xs text-[#D4D4D8] flex items-center justify-between px-3 py-2 bg-[#050507] border border-white/[0.1] tabular-nums font-mono"
            >
              <span class="font-sans text-[#8A8D96]">Cover contrast</span>
              <span :class="primaryContrast >= 4.5 ? 'text-emerald-400 font-medium' : 'text-amber-300 font-medium'">
                {{ primaryContrast.toFixed(2) }}:1 (Text: {{ accessibleCoverText }})
              </span>
            </div>

            <div class="space-y-1.5">
              <label for="brand-nda-text" class="text-xs font-medium text-[#D4D4D8] block">
                Confidentiality notice
              </label>
              <textarea
                id="brand-nda-text"
                v-model="confidentialityText"
                :readonly="!isManager"
                rows="3"
                class="input-glass w-full p-2.5 text-xs sm:text-sm"
              ></textarea>
            </div>

            <button
              v-if="isManager"
              type="button"
              @click="handleSaveBranding"
              :disabled="savingBranding || !isValidHex(primaryColor) || !isValidHex(secondaryColor)"
              class="btn-glass w-full py-2.5 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="savingBranding" class="h-3.5 w-3.5 animate-spin" />
              <span>
                {{
                  savingBranding
                    ? 'Saving branding...'
                    : brandingDirty
                      ? 'Save branding'
                      : 'Branding saved'
                }}
              </span>
            </button>
          </div>

          <!-- Async PDF Export Panel -->
          <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
            <h3 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2 border-b border-white/[0.08] pb-2.5">
              <FileDown class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
              <span>Export PDF Report</span>
            </h3>

            <EmptyState
              v-if="!activeProject"
              :icon="FolderGit2"
              title="No active project"
              description="Create or select a project first to export a PDF report."
              action-label="Open Projects"
              action-to="/app/projects"
            />

            <SkeletonBlock v-else-if="loadingData" variant="text" :count="4" />

            <template v-else>
              <div class="text-xs space-y-2">
                <div class="flex justify-between items-center text-[#D4D4D8] tabular-nums">
                  <span>Selected findings ({{ selectedFindingIds.length }}/{{ reportEligibleFindings.length }})</span>
                  <button
                    type="button"
                    @click="selectCuratedFindings"
                    class="text-[#F5F5F3] underline underline-offset-4 font-medium"
                  >
                    Select report items
                  </button>
                </div>

                <div
                  v-if="reportEligibleFindings.length === 0"
                  class="text-xs text-amber-200 bg-amber-500/10 border border-amber-400/25 p-3 space-y-1.5"
                >
                  <div>No eligible in-scope findings in this project yet.</div>
                  <router-link to="/app/triage" class="text-[#F5F5F3] underline font-medium inline-block">
                    Review findings →
                  </router-link>
                </div>

                <div v-else class="max-h-44 overflow-y-auto border-y border-white/[0.1] divide-y divide-white/[0.08]">
                  <label
                    v-for="f in reportEligibleFindings"
                    :key="f.id"
                    class="flex items-center gap-2.5 py-2 px-1.5 cursor-pointer hover:bg-white/[0.03] transition-colors"
                  >
                    <input
                      v-model="selectedFindingIds"
                      :value="f.id"
                      type="checkbox"
                      class="bg-[#050507] border-white/30 text-[#F5F5F3]"
                    />
                    <span class="truncate flex-1 text-[#F5F5F3]">{{ f.title }}</span>
                    <SeverityBadge :severity="f.severity" />
                  </label>
                </div>
              </div>

              <!-- Compile Options + Draft Readiness -->
              <div class="space-y-2.5 text-xs text-[#D4D4D8] border-t border-white/[0.08] pt-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="includeAiNarratives"
                      type="checkbox"
                      class="bg-[#050507] border-white/30 text-[#F5F5F3]"
                    />
                    <span>Include AI executive summary &amp; guidance</span>
                  </label>

                  <router-link
                    to="/app/ai-review"
                    class="inline-flex items-center gap-1.5 text-xs hover:underline"
                  >
                    <StatusBadge
                      v-if="latestNarrative"
                      :status="latestNarrative.approval_status"
                    />
                    <span v-else class="text-amber-300">No draft yet →</span>
                  </router-link>
                </div>

                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    v-model="showCoverPage"
                    type="checkbox"
                    class="bg-[#050507] border-white/30 text-[#F5F5F3]"
                  />
                  <span>Include cover page</span>
                </label>

                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    v-model="showCvssRadar"
                    type="checkbox"
                    class="bg-[#050507] border-white/30 text-[#F5F5F3]"
                  />
                  <span>Include CVSS risk radar chart</span>
                </label>
              </div>

              <!-- Job Status Progress -->
              <div
                v-if="activeJob"
                class="p-4 bg-[#050507] border border-white/[0.1] space-y-2.5 text-xs"
              >
                <div class="flex justify-between items-center gap-2">
                  <span class="text-[#F5F5F3] font-medium">{{ jobStageText }}</span>
                  <span class="text-[#F5F5F3] font-mono font-semibold tabular-nums">{{ activeJob.progress_percentage ?? 0 }}%</span>
                </div>
                <div class="h-1.5 bg-[#08080B] overflow-hidden border border-white/[0.1]">
                  <div
                    :class="[
                      'h-full transition-all duration-300',
                      activeJob.status === 'FAILED'
                        ? 'bg-red-500'
                        : activeJob.status === 'COMPLETED'
                          ? 'bg-emerald-500'
                          : 'bg-[#F5F5F3]',
                    ]"
                    :style="{ width: `${activeJob.progress_percentage ?? 10}%` }"
                  ></div>
                </div>
                <p v-if="activeJob.error_message" class="text-xs text-red-300">
                  {{ activeJob.error_message }}
                </p>
                <button
                  v-if="activeJob.status === 'COMPLETED' && (activeJob.report_id || activeJob.download_url)"
                  type="button"
                  @click="downloadCompletedJob"
                  class="btn-glass w-full py-2 text-xs border-emerald-400/35 text-emerald-300 hover:bg-emerald-500/20"
                >
                  <FileDown class="h-4 w-4" />
                  <span>Download PDF</span>
                </button>
              </div>

              <button
                v-if="canCompile"
                type="button"
                @click="compilePDF"
                :disabled="isCompiling || selectedFindingIds.length === 0 || quotaExhausted"
                class="btn-platinum w-full py-2.5 text-xs sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Loader2 v-if="isCompiling" class="h-4 w-4 animate-spin" />
                <FileDown v-else class="h-4 w-4" aria-hidden="true" />
                <span>{{ isCompiling ? 'Generating PDF...' : 'Export PDF Report' }}</span>
              </button>
            </template>
          </div>
        </div>

        <!-- Live Cover / Interior Preview & Report History (7 cols) -->
        <div class="lg:col-span-7 space-y-6">
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-mono text-xs uppercase tracking-wider text-[#8A8D96]">
                {{ showCoverPage ? 'Live Cover Preview (A4)' : 'Executive Page Preview' }}
              </span>
              <span class="font-mono text-[11px] text-[#8A8D96]">Print specimen</span>
            </div>

            <!-- A4 Mock Cover Canvas -->
            <div
              v-if="showCoverPage"
              class="relative overflow-hidden border border-white/20 p-8 sm:p-10 shadow-2xl aspect-[1/1.414] max-w-md mx-auto flex flex-col justify-between transition-colors"
              :style="{ backgroundColor: safePrimaryColor, color: accessibleCoverText }"
            >
              <!-- Watermark overlay on Free plan -->
              <div
                v-if="!isProTier"
                class="pointer-events-none select-none absolute inset-0 flex items-center justify-center z-20"
              >
                <span
                  class="-rotate-30 px-5 py-2 bg-black/65 border border-white/30 text-white text-xl font-display font-bold tracking-widest uppercase shadow-lg"
                >
                  Free Tier Preview
                </span>
              </div>

              <!-- Header on Paper -->
              <div
                class="flex justify-between items-start pb-4 relative z-10 border-b"
                :style="{ borderColor: coverDividerColor }"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="h-10 w-10 flex items-center justify-center overflow-hidden font-bold text-xs border"
                    :style="{ backgroundColor: coverFrameBg, borderColor: coverDividerColor }"
                  >
                    <img
                      v-if="workspace?.custom_logo_url"
                      :src="workspace.custom_logo_url"
                      alt="Agency logo"
                      class="h-full w-full object-contain"
                    />
                    <span v-else>{{ workspaceInitials }}</span>
                  </div>
                  <div>
                    <div class="font-bold text-xs">{{ workspace?.name || 'Security Team' }}</div>
                    <div class="text-[10px] opacity-80">Confidential Audit Report</div>
                  </div>
                </div>

                <span
                  class="text-[10px] font-medium px-2 py-0.5"
                  :style="{ backgroundColor: safeSecondaryColor, color: accessibleAccentText }"
                >
                  {{ isProTier ? 'White-Label' : 'Preview' }}
                </span>
              </div>

              <!-- Title Section on Paper -->
              <div class="space-y-4 my-auto relative z-10">
                <div class="text-[10px] tracking-widest opacity-80 uppercase">
                  Security Assessment Report
                </div>
                <h2 class="font-display text-2xl font-bold leading-tight">
                  {{ activeProject?.name || 'Application Security Assessment' }}
                </h2>
                <div class="space-y-1 text-xs opacity-90">
                  <div><strong>Client:</strong> {{ activeProject?.client_name || 'Client Name' }}</div>
                  <div>
                    <strong>Scope:</strong>
                    {{ activeProject?.target_scope.slice(0, 3).join(', ') || 'Authorized Targets' }}
                  </div>
                </div>
              </div>

              <!-- Footer on Paper -->
              <div
                class="pt-4 space-y-2 relative z-10 border-t"
                :style="{ borderColor: coverDividerColor }"
              >
                <p class="text-[10px] opacity-85 italic leading-snug">
                  {{ confidentialityText || 'Confidential document prepared for authorized stakeholders.' }}
                </p>
                <div class="flex justify-between items-center text-[9px] font-mono opacity-75">
                  <span>{{ workspace?.name || 'VulnFlow' }}</span>
                  <span>v1.{{ reports.length }}</span>
                </div>
              </div>
            </div>

            <!-- Executive Interior Preview when Cover Page unchecked -->
            <div
              v-else
              class="border border-white/20 bg-white text-slate-900 p-8 shadow-2xl max-w-md mx-auto aspect-[1/1.414] flex flex-col justify-between"
            >
              <div class="space-y-4">
                <div
                  class="flex items-center justify-between pb-3 border-b-2"
                  :style="{ borderColor: safePrimaryColor }"
                >
                  <span class="font-display font-bold text-sm" :style="{ color: safePrimaryColor }">
                    {{ workspace?.name || 'Security Team' }}
                  </span>
                  <span class="text-[10px] text-slate-500 uppercase tracking-wider">Executive Summary</span>
                </div>

                <h3 class="font-display font-bold text-lg text-slate-900">
                  {{ activeProject?.name || 'Security Assessment Summary' }}
                </h3>
                <p class="text-xs text-slate-700 leading-relaxed line-clamp-6">
                  {{
                    latestNarrative?.narratives.executive_summary ||
                    'This report summarizes ' +
                      selectedFindingIds.length +
                      ' selected security findings with CVSS risk scoring and recommended remediation steps.'
                  }}
                </p>
                <div class="p-3 bg-slate-100 border border-slate-200 text-xs text-slate-700">
                  Included findings: {{ selectedFindingIds.length }} · Risk radar: {{ showCvssRadar ? 'Enabled' : 'Hidden' }}
                </div>
              </div>

              <div class="pt-3 border-t border-slate-200 text-[10px] text-slate-500 flex justify-between">
                <span>Cover page hidden</span>
                <span>{{ isProTier ? 'White-label' : 'Free watermark' }}</span>
              </div>
            </div>
          </div>

          <!-- Exported Reports History -->
          <div class="border border-white/[0.11] bg-[#08080B] p-5 space-y-3">
            <h3 class="font-mono text-xs uppercase tracking-wider text-[#F5F5F3] border-b border-white/[0.08] pb-2.5 tabular-nums">
              Exported Reports ({{ reports.length }})
            </h3>

            <SkeletonBlock v-if="loadingData" variant="table-row" :count="2" />

            <div v-else-if="reports.length === 0" class="text-xs text-[#8A8D96] py-3">
              No PDF reports have been generated for this project yet.
            </div>

            <ul v-else class="divide-y divide-white/[0.08] border-t border-white/[0.08]">
              <li
                v-for="rep in reports"
                :key="rep.id"
                class="flex flex-wrap items-center justify-between gap-2 py-3 text-xs"
              >
                <div class="min-w-0">
                  <div class="font-medium text-[#F5F5F3]">
                    {{ rep.report_title }} <span class="font-mono text-[#8A8D96]">({{ rep.version }})</span>
                  </div>
                  <div class="font-mono text-[11px] text-[#8A8D96]">
                    {{ formatDate(rep.generated_at) }} ·
                    {{ rep.watermark_applied ? 'Free watermark' : 'White-label' }}
                  </div>
                </div>
                <button
                  type="button"
                  @click="downloadReport(rep.id)"
                  class="btn-glass px-3 py-1.5 text-xs"
                >
                  <FileDown class="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Download PDF</span>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { AlertTriangle, FileDown, FolderGit2, Loader2, Palette } from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SeverityBadge from '@/components/ui/SeverityBadge.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {
  api,
  ApiError,
  type AINarrativeResponse,
  type Finding,
  type ReportJobStatusResponse,
  type ReportSummary,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'
import { computeContrastRatio, pickAccessibleTextColor } from '@/utils/colors'
import { readFileAsBase64 } from '@/utils/files'

const workspace = computed(() => session.state.activeWorkspace)
const activeProject = session.activeProject
const isManager = computed(() => session.activeRole.value === 'MANAGER')
const canCompile = computed(() => session.activeRole.value !== 'VIEWER')
const isProTier = computed(() => {
  const tier = session.state.subscription?.tier
  return tier === 'PRO' || tier === 'ENTERPRISE'
})
const quotaHitApi = ref(false)
const quotaExhausted = computed(() => {
  if (quotaHitApi.value) return true
  const sub = session.state.subscription
  return Boolean(sub && sub.remaining_reports <= 0)
})

const workspaceInitials = computed(() => {
  const name = workspace.value?.name || 'VF'
  return name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

const colorPresets = [
  { name: 'Deep Navy', primary: '#1e3a8a', secondary: '#06b6d4' },
  { name: 'Obsidian Slate', primary: '#0f172a', secondary: '#3b82f6' },
  { name: 'Forest Emerald', primary: '#064e3b', secondary: '#10b981' },
  { name: 'Crimson', primary: '#7f1d1d', secondary: '#f97316' },
]

const primaryColor = ref('#1e40af')
const secondaryColor = ref('#0d9488')
const confidentialityText = ref('')
const savingBranding = ref(false)
const uploadingLogo = ref(false)

const loadingData = ref(false)
const reportEligibleFindings = ref<Finding[]>([])
const selectedFindingIds = ref<string[]>([])
const narratives = ref<AINarrativeResponse[]>([])
const includeAiNarratives = ref(true)
const showCoverPage = ref(true)
const showCvssRadar = ref(true)
const reports = ref<ReportSummary[]>([])
const activeJob = ref<ReportJobStatusResponse | null>(null)
const isCompiling = ref(false)

const latestNarrative = computed(() => narratives.value[0] ?? null)

const isValidHex = (val: string) => /^#[0-9A-Fa-f]{6}$/.test(val)
const safePrimaryColor = computed(() => (isValidHex(primaryColor.value) ? primaryColor.value : '#1e40af'))
const safeSecondaryColor = computed(() =>
  isValidHex(secondaryColor.value) ? secondaryColor.value : '#0d9488'
)

const brandingDirty = computed(() => {
  const ws = workspace.value
  if (!ws) return false
  return (
    primaryColor.value !== (ws.brand_primary_color || '#1e40af') ||
    secondaryColor.value !== (ws.brand_secondary_color || '#0d9488') ||
    confidentialityText.value !== (ws.confidentiality_text || '')
  )
})

const applyColorPreset = (p: string, s: string) => {
  primaryColor.value = p
  secondaryColor.value = s
}

let pollTimer: number | undefined
onUnmounted(() => {
  window.clearInterval(pollTimer)
})

const accessibleCoverText = computed(() => pickAccessibleTextColor(safePrimaryColor.value))
const accessibleAccentText = computed(() => pickAccessibleTextColor(safeSecondaryColor.value))
const primaryContrast = computed(() =>
  computeContrastRatio(accessibleCoverText.value, safePrimaryColor.value)
)
const coverDividerColor = computed(() =>
  accessibleCoverText.value === '#FFFFFF' ? 'rgba(255,255,255,0.22)' : 'rgba(15,23,42,0.22)'
)
const coverFrameBg = computed(() =>
  accessibleCoverText.value === '#FFFFFF' ? 'rgba(255,255,255,0.14)' : 'rgba(15,23,42,0.08)'
)

const jobStageText = computed(() => {
  const j = activeJob.value
  if (!j) return ''
  switch (j.status) {
    case 'QUEUED':
      return 'Waiting for export queue...'
    case 'PROCESSING':
      return 'Rendering layout, charts, and PDF...'
    case 'COMPLETED':
      return 'PDF report is ready to download'
    case 'FAILED':
      return 'PDF export failed'
    default:
      return j.status
  }
})

watch(
  workspace,
  (ws) => {
    if (!ws) return
    primaryColor.value = ws.brand_primary_color || '#1e40af'
    secondaryColor.value = ws.brand_secondary_color || '#0d9488'
    confidentialityText.value = ws.confidentiality_text || ''
  },
  { immediate: true }
)

async function loadProjectReportingData(): Promise<void> {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) {
    reportEligibleFindings.value = []
    selectedFindingIds.value = []
    narratives.value = []
    reports.value = []
    return
  }

  loadingData.value = true
  try {
    const [findingsRes, reportList, narrativeList] = await Promise.all([
      api.findings.list(wId, pId, { is_quarantined: false, limit: 200 }),
      api.reports.list(wId, pId),
      api.ai.listNarratives(wId, pId),
    ])
    const eligible = findingsRes.items.filter(
      (f) => !f.is_quarantined && f.status !== 'FALSE_POSITIVE'
    )
    reportEligibleFindings.value = eligible
    selectedFindingIds.value = eligible
      .filter((f) => f.is_curated_for_report)
      .map((f) => f.id)
    reports.value = reportList
    narratives.value = narrativeList
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to load project reporting data.')
  } finally {
    loadingData.value = false
  }
}

watch(
  [() => session.state.activeWorkspaceId, () => session.state.activeProjectId],
  () => {
    window.clearInterval(pollTimer)
    activeJob.value = null
    isCompiling.value = false
    quotaHitApi.value = false
    void loadProjectReportingData()
  },
  { immediate: true }
)

const selectCuratedFindings = () => {
  selectedFindingIds.value = reportEligibleFindings.value
    .filter((f) => f.is_curated_for_report)
    .map((f) => f.id)
}

const handleSaveBranding = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  savingBranding.value = true
  try {
    await api.workspaces.update(wId, {
      brand_primary_color: safePrimaryColor.value,
      brand_secondary_color: safeSecondaryColor.value,
      confidentiality_text: confidentialityText.value,
    })
    await session.refreshWorkspace()
    toast.success('Workspace branding saved.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to save workspace branding.')
  } finally {
    savingBranding.value = false
  }
}

const handleLogoUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const wId = session.state.activeWorkspaceId
  if (!wId) return

  uploadingLogo.value = true
  try {
    const encoded = await readFileAsBase64(file, {
      maxBytes: 2 * 1024 * 1024,
      allowedTypes: ['image/png', 'image/jpeg', 'image/svg+xml'] as const,
    })
    await api.workspaces.uploadLogo(wId, encoded)
    await session.refreshWorkspace()
    toast.success('Agency logo updated.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to upload agency logo.')
  } finally {
    uploadingLogo.value = false
  }
}

const compilePDF = async () => {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) return

  isCompiling.value = true
  window.clearInterval(pollTimer)
  try {
    const accepted = await api.reports.compilePdf(wId, pId, {
      finding_ids: selectedFindingIds.value,
      include_ai_narratives: includeAiNarratives.value,
      theme_options: {
        primary_color: safePrimaryColor.value,
        secondary_color: safeSecondaryColor.value,
        show_cover_page: showCoverPage.value,
        show_cvss_radar: showCvssRadar.value,
        confidentiality_notice: confidentialityText.value,
      },
    })
    activeJob.value = {
      job_id: accepted.job_id,
      status: accepted.status,
      progress_percentage: 10,
    }
    toast.info('PDF export started...')

    pollTimer = window.setInterval(async () => {
      try {
        const jobStatus = await api.reports.getJobStatus(wId, accepted.job_id)
        activeJob.value = jobStatus
        if (jobStatus.status === 'COMPLETED') {
          window.clearInterval(pollTimer)
          isCompiling.value = false
          await Promise.all([loadProjectReportingData(), session.refreshSubscription()])
          toast.success('PDF report is ready to download.')
        } else if (jobStatus.status === 'FAILED') {
          window.clearInterval(pollTimer)
          isCompiling.value = false
          toast.error(jobStatus.error_message || 'PDF export failed.')
        }
      } catch (pollErr: unknown) {
        window.clearInterval(pollTimer)
        isCompiling.value = false
        toast.error(pollErr instanceof Error ? pollErr.message : 'Unable to check PDF export progress.')
      }
    }, 1500)
  } catch (err: unknown) {
    isCompiling.value = false
    if (err instanceof ApiError && err.status === 402) {
      quotaHitApi.value = true
      toast.warning('Monthly PDF quota reached. Upgrade your plan in Billing.')
      return
    }
    toast.error(err instanceof Error ? err.message : 'Unable to start PDF export.')
  }
}

const downloadCompletedJob = async () => {
  if (!activeJob.value) return
  if (activeJob.value.report_id) {
    await downloadReport(activeJob.value.report_id)
    return
  }
  if (activeJob.value.download_url) {
    window.open(activeJob.value.download_url, '_blank', 'noopener')
  }
}

const downloadReport = async (reportId: string) => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  try {
    const { download_url } = await api.reports.getDownloadUrl(wId, reportId)
    window.open(download_url, '_blank', 'noopener')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to generate PDF download link.')
  }
}

const formatDate = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('en-US')
}
</script>
