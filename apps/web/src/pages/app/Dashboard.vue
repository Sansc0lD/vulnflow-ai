<template>
  <AppLayout>
    <template #header-title>
      <div class="flex items-center gap-3 min-w-0">
        <div class="min-w-0">
          <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
            Overview
          </h1>
          <p class="text-xs text-[#8A8D96] truncate">
            {{
              activeProject
                ? `${activeProject.name} · ${activeProject.client_name}`
                : 'Select or create a project'
            }}
          </p>
        </div>
        <span v-if="loading" class="inline-flex items-center gap-1.5 text-xs text-[#8A8D96] shrink-0">
          <Loader2 class="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          <span class="hidden sm:inline">Syncing...</span>
        </span>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <PipelineStepper @open-cli="cliDrawerOpen = true" />

      <!-- Empty State when no project -->
      <EmptyState
        v-if="!activeProject"
        :icon="FolderPlus"
        title="No active project selected"
        description="Create a project and set its authorized targets to start importing Nmap or Nuclei scans or adding manual findings."
        action-label="Create first project"
        action-to="/app/projects"
      />

      <template v-else>
        <!-- Unified 4-Column Hairline KPI Ledger (Zero Card Clutter) -->
        <SkeletonBlock v-if="loading && !hasLoadedOnce" variant="kpi" :count="4" />

        <div
          v-else
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border border-white/[0.11] divide-y sm:divide-y-0 sm:divide-x divide-white/[0.11] bg-[#08080B]"
        >
          <div class="p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Total Findings</span>
              <AlertTriangle class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
            </div>
            <div class="text-3xl font-display font-bold text-[#F5F5F3] font-mono tabular-nums">
              {{ summary.total }}
            </div>
            <p class="text-xs text-[#8A8D96]">From CLI scans and manual entries</p>
          </div>

          <div class="p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Scope Compliance</span>
              <ShieldCheck class="h-4 w-4 text-emerald-400" aria-hidden="true" />
            </div>
            <div
              :class="[
                'text-2xl sm:text-3xl font-display font-bold tabular-nums',
                summary.total === 0 ? 'text-[#8A8D96]' : 'text-emerald-400',
              ]"
            >
              {{ summary.total === 0 ? '—' : `${roeCompliancePct}% In Scope` }}
            </div>
            <p class="text-xs text-[#8A8D96]">
              {{
                summary.total === 0
                  ? 'No findings imported yet'
                  : `${summary.quarantined} out-of-scope held back`
              }}
            </p>
          </div>

          <div class="p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Selected for Report</span>
              <BookmarkCheck class="h-4 w-4 text-[#F5F5F3]" aria-hidden="true" />
            </div>
            <div class="text-3xl font-display font-bold text-[#F5F5F3] font-mono tabular-nums">
              {{ summary.curated }}
            </div>
            <p class="text-xs text-[#8A8D96]">
              {{ falsePositiveCount }} marked false positive
            </p>
          </div>

          <div class="p-5 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">Report Draft</span>
              <Sparkles class="h-4 w-4 text-[#F5F5F3]" aria-hidden="true" />
            </div>
            <div class="text-2xl sm:text-3xl font-display font-bold text-[#F5F5F3]">
              {{ formatDraftStatus(latestNarrative?.approval_status) }}
            </div>
            <p class="text-xs text-[#8A8D96]">
              {{
                latestNarrative
                  ? `${latestNarrative.tokens_consumed} tokens · ${latestNarrative.is_fallback ? 'Standard template' : 'AI draft'}`
                  : 'Ready to generate'
              }}
            </p>
          </div>
        </div>

        <!-- Charts & Recent Findings -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Left: Severity Breakdown + Status Summary (7 cols) -->
          <div class="lg:col-span-7 space-y-6">
            <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-5">
              <div class="flex items-center justify-between border-b border-white/[0.08] pb-3.5">
                <h2 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
                  <BarChart3 class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
                  <span>Severity Breakdown</span>
                </h2>
                <span class="text-xs text-[#8A8D96]">Click a row to filter</span>
              </div>

              <div class="space-y-3">
                <router-link
                  v-for="bar in severityBars"
                  :key="bar.key"
                  :to="{ path: '/app/triage', query: { severity: bar.key } }"
                  class="block py-2 hover:bg-white/[0.03] px-2 -mx-2 transition-colors space-y-1.5 group"
                >
                  <div class="flex justify-between text-xs">
                    <span :class="['font-medium flex items-center gap-2', bar.textClass]">
                      <span :class="['h-2 w-2 rounded-full', bar.dotClass]" aria-hidden="true"></span>
                      <span class="group-hover:underline underline-offset-4">{{ bar.label }}</span>
                    </span>
                    <span class="text-[#F5F5F3] font-mono font-semibold tabular-nums">
                      {{ bar.count }} ({{ bar.pctLabel }})
                    </span>
                  </div>
                  <div class="h-1.5 bg-[#050507] border border-white/[0.08] overflow-hidden">
                    <div
                      :class="['h-full transition-all duration-500', bar.barClass]"
                      :style="{ width: `${bar.pct}%` }"
                    ></div>
                  </div>
                </router-link>
              </div>
            </div>

            <!-- Ruled Status Summary Grid -->
            <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
              <div class="flex items-center justify-between border-b border-white/[0.08] pb-3.5">
                <h2 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
                  <ListChecks class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
                  <span>Findings by Status</span>
                </h2>
                <router-link to="/app/triage" class="text-xs text-[#F5F5F3] underline underline-offset-4 hover:text-white font-medium">
                  View all →
                </router-link>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-3 border border-white/[0.09] divide-y sm:divide-y-0 divide-x divide-white/[0.09] text-xs">
                <router-link
                  v-for="st in statusCards"
                  :key="st.key"
                  :to="{ path: '/app/triage', query: { status: st.key } }"
                  class="p-3 bg-[#050507] hover:bg-white/[0.04] transition-colors flex items-center justify-between gap-2 border-b border-white/[0.08]"
                >
                  <StatusBadge :status="st.key" />
                  <span class="text-base font-mono font-bold text-[#F5F5F3] tabular-nums">{{ st.count }}</span>
                </router-link>
              </div>
            </div>
          </div>

          <!-- Right: Recent Activity & Exported Reports (5 cols) -->
          <div class="lg:col-span-5 border border-white/[0.11] bg-[#08080B] p-6 space-y-5 flex flex-col">
            <div class="flex items-center justify-between border-b border-white/[0.08] pb-3.5">
              <h2 class="text-sm font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
                <Activity class="h-4 w-4 text-emerald-400" aria-hidden="true" />
                <span>Recent Activity</span>
              </h2>
              <router-link to="/app/triage" class="text-xs text-[#F5F5F3] underline underline-offset-4 hover:text-white font-medium">
                Open Findings →
              </router-link>
            </div>

            <SkeletonBlock v-if="loading && !hasLoadedOnce" variant="text" :count="4" />

            <EmptyState
              v-else-if="recentFindings.length === 0"
              :icon="Terminal"
              title="No findings yet"
              description="Import scan results with the CLI or add findings manually to get started."
              action-label="Open import guide"
              @action="cliDrawerOpen = true"
            />

            <div v-else class="divide-y divide-white/[0.08] border-y border-white/[0.08] text-xs">
              <router-link
                v-for="f in recentFindings.slice(0, 5)"
                :key="f.id"
                :to="{ path: '/app/triage', query: { severity: f.severity } }"
                class="block py-3 hover:bg-white/[0.03] px-2 -mx-2 transition-colors space-y-1.5"
              >
                <div class="flex justify-between items-center gap-2">
                  <SeverityBadge :severity="f.severity" :score="f.cvss_score" />
                  <StatusBadge :status="f.status" />
                </div>
                <div class="text-[#F5F5F3] font-medium truncate">{{ f.title }}</div>
                <div class="text-[11px] text-[#8A8D96] font-mono truncate">
                  {{ f.source_tool }} · {{ f.target_host }}{{ f.endpoint_path }} ({{ f.cwe_id }})
                </div>
              </router-link>
            </div>

            <!-- Exported Reports List -->
            <div v-if="recentReports.length > 0" class="border-t border-white/[0.1] pt-4 mt-auto space-y-3">
              <div class="flex items-center justify-between">
                <span class="font-mono text-[11px] uppercase tracking-wider text-[#8A8D96] tabular-nums">
                  Exported PDFs ({{ recentReports.length }})
                </span>
                <router-link to="/app/theme" class="text-xs text-[#F5F5F3] underline underline-offset-4">
                  View all
                </router-link>
              </div>
              <div class="divide-y divide-white/[0.08] border-y border-white/[0.08]">
                <div
                  v-for="rep in recentReports.slice(0, 3)"
                  :key="rep.id"
                  class="flex items-center justify-between py-2.5 text-xs gap-2"
                >
                  <div class="min-w-0">
                    <div class="font-medium text-[#F5F5F3] truncate">
                      {{ rep.report_title }} ({{ rep.version }})
                    </div>
                    <div class="font-mono text-[11px] text-[#8A8D96]">
                      {{ rep.watermark_applied ? 'Free watermark' : 'White-label' }}
                    </div>
                  </div>
                  <button
                    type="button"
                    @click="handleDownload(rep)"
                    class="btn-glass shrink-0 px-3 py-1.5 text-xs"
                  >
                    <FileDown class="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Download</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <CliIngestDrawer :open="cliDrawerOpen" @close="cliDrawerOpen = false" />
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookmarkCheck,
  FileDown,
  FolderPlus,
  ListChecks,
  Loader2,
  ShieldCheck,
  Sparkles,
  Terminal,
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import CliIngestDrawer from '@/components/ui/CliIngestDrawer.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PipelineStepper from '@/components/ui/PipelineStepper.vue'
import SeverityBadge from '@/components/ui/SeverityBadge.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import {
  api,
  type AINarrativeResponse,
  type Finding,
  type FindingStatus,
  type FindingSummaryMetrics,
  type ReportSummary,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'
import { getSeverityStyle } from '@/utils/cvss'

const activeProject = session.activeProject

const loading = ref(false)
const hasLoadedOnce = ref(false)
const cliDrawerOpen = ref(false)
const summary = ref<FindingSummaryMetrics>({
  total: 0,
  curated: 0,
  quarantined: 0,
  by_severity: {},
  by_status: {},
})
const recentFindings = ref<Finding[]>([])
const narratives = ref<AINarrativeResponse[]>([])
const recentReports = ref<ReportSummary[]>([])

const latestNarrative = computed(() => narratives.value[0] ?? null)
const falsePositiveCount = computed(() => summary.value.by_status['FALSE_POSITIVE'] ?? 0)
const roeCompliancePct = computed(() => {
  if (summary.value.total === 0) return 0
  return Math.round(((summary.value.total - summary.value.quarantined) / summary.value.total) * 100)
})

const formatDraftStatus = (status?: string | null): string => {
  if (!status) return 'Not started'
  if (status === 'APPROVED') return 'Approved'
  if (status === 'DRAFT') return 'Draft'
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
}

const severityBars = computed(() => {
  const total = summary.value.total
  const defs: Array<{ key: string; label: string }> = [
    { key: 'CRITICAL', label: 'Critical (9.0 – 10.0)' },
    { key: 'HIGH', label: 'High (7.0 – 8.9)' },
    { key: 'MEDIUM', label: 'Medium (4.0 – 6.9)' },
    { key: 'LOW', label: 'Low (0.1 – 3.9)' },
    { key: 'INFO', label: 'Info (0.0)' },
  ]
  return defs.map((def) => {
    const style = getSeverityStyle(def.key)
    const count = summary.value.by_severity[def.key] ?? 0
    const pct = total > 0 ? (count / total) * 100 : 0
    return {
      ...def,
      ...style,
      count,
      pct: Number(pct.toFixed(1)),
      pctLabel: `${pct.toFixed(1)}%`,
    }
  })
})

const statusKeys: FindingStatus[] = [
  'OPEN',
  'IN_REVIEW',
  'REMEDIATED',
  'REOPENED',
  'FALSE_POSITIVE',
  'ACCEPTED_RISK',
]

const statusCards = computed(() =>
  statusKeys.map((key) => ({
    key,
    count: summary.value.by_status[key] ?? 0,
  }))
)

async function loadDashboard(): Promise<void> {
  const wId = session.state.activeWorkspaceId
  const pId = session.state.activeProjectId
  if (!wId || !pId) {
    recentFindings.value = []
    narratives.value = []
    recentReports.value = []
    summary.value = { total: 0, curated: 0, quarantined: 0, by_severity: {}, by_status: {} }
    hasLoadedOnce.value = true
    return
  }

  loading.value = true
  try {
    const [findingsRes, narrativeList, reportList] = await Promise.all([
      api.findings.list(wId, pId, { limit: 10 }),
      api.ai.listNarratives(wId, pId),
      api.reports.list(wId, pId),
    ])
    recentFindings.value = findingsRes.items
    summary.value = findingsRes.summary
    narratives.value = narrativeList
    recentReports.value = reportList
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to load project metrics.')
  } finally {
    hasLoadedOnce.value = true
    loading.value = false
  }
}

watch(
  [() => session.state.activeWorkspaceId, () => session.state.activeProjectId],
  () => {
    hasLoadedOnce.value = false
    void loadDashboard()
  },
  { immediate: true }
)

const handleDownload = async (report: ReportSummary) => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  try {
    const { download_url } = await api.reports.getDownloadUrl(wId, report.id)
    window.open(download_url, '_blank', 'noopener')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to fetch PDF download link.')
  }
}
</script>
