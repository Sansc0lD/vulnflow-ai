<template>
  <PublicLayout>
    <!-- Header -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-10">
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div class="max-w-2xl space-y-2.5">
            <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
              Interactive Catalog
            </span>
            <h1 class="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F5F3]">
              Sample Finding Workbench
            </h1>
            <p class="text-sm text-[#8A8D96] leading-relaxed">
              Filter imported findings, inspect CVSS severity, and review executive and remediation prose before compiling the final report.
            </p>
          </div>

          <router-link to="/app/register" class="btn-platinum px-4 py-2.5 text-xs shrink-0 self-start md:self-auto">
            <span>Start a real project</span>
            <ArrowRight class="h-3.5 w-3.5" />
          </router-link>
        </div>
      </div>
    </section>

    <!-- Monograph Finding Workbench (UC-03) -->
    <section class="py-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
      <div class="border border-white/[0.12] bg-[#08080B] grid grid-cols-1 lg:grid-cols-12 lg:min-h-[720px] divide-y lg:divide-y-0 lg:divide-x divide-white/[0.1]">
        <!-- Narrow Master Index (4 cols) -->
        <div class="lg:col-span-4 flex flex-col">
          <!-- Search & Ruled Filter Tabs -->
          <div class="p-4 border-b border-white/[0.1] space-y-3 shrink-0 bg-[#050507]">
            <div class="relative">
              <Search
                class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8A8D96]"
                aria-hidden="true"
              />
              <label for="demo-triage-search" class="sr-only">Search findings, CWE, or host</label>
              <input
                id="demo-triage-search"
                ref="searchInputRef"
                v-model.trim="searchQuery"
                type="text"
                placeholder="Search findings, CWE, or host..."
                class="w-full input-glass pl-9 pr-3 py-2 text-xs"
              />
            </div>

            <div class="flex items-center gap-3 overflow-x-auto pb-0.5 text-xs border-t border-white/[0.08] pt-2.5">
              <button
                v-for="sev in severityFilters"
                :key="sev.key"
                type="button"
                @click="selectedSeverity = sev.key"
                :aria-pressed="selectedSeverity === sev.key"
                :class="[
                  'pb-0.5 border-b transition-colors whitespace-nowrap inline-flex items-center gap-1 tabular-nums',
                  selectedSeverity === sev.key
                    ? 'border-[#F5F5F3] text-[#F5F5F3] font-semibold'
                    : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3]',
                ]"
              >
                <span>{{ sev.label }}</span>
                <span class="font-mono text-[10px] opacity-70">{{ severityCounts[sev.key] }}</span>
              </button>
            </div>
          </div>

          <!-- Clean Mono-Indexed Finding Rows -->
          <div class="flex-1 overflow-y-auto divide-y divide-white/[0.08]">
            <button
              v-for="item in filteredFindings"
              :key="item.id"
              type="button"
              @click="selectedId = item.id"
              :aria-current="selectedFinding?.id === item.id ? 'true' : undefined"
              :class="[
                'w-full px-4 py-3.5 transition-colors text-left space-y-1 block border-l-2',
                selectedFinding?.id === item.id
                  ? 'bg-white/[0.05] border-l-[#F5F5F3]'
                  : 'border-l-transparent hover:bg-white/[0.02]',
              ]"
            >
              <div class="flex items-baseline justify-between gap-2.5">
                <span class="text-xs sm:text-sm font-medium text-[#F5F5F3] truncate">
                  {{ item.title }}
                </span>
                <span class="font-mono text-xs tabular-nums shrink-0 inline-flex items-center gap-1.5 text-[#F5F5F3]">
                  <span :class="['h-1.5 w-1.5 rounded-full', severityDotClass(item.severity)]" aria-hidden="true" />
                  <span>{{ item.cvss.toFixed(1) }}</span>
                </span>
              </div>

              <div class="flex items-center justify-between text-[11px] font-mono text-[#8A8D96]">
                <span class="truncate">{{ item.id }} · {{ item.cwe }} · {{ item.host }}</span>
                <span class="font-sans text-[#D4D4D8] shrink-0">{{ formatStatusLabel(effectiveStatus(item)) }}</span>
              </div>
            </button>

            <div v-if="filteredFindings.length === 0" class="p-6">
              <EmptyState
                :icon="Search"
                title="No matching findings"
                description="Adjust your search term or severity filter to view more results."
                action-label="Reset filters"
                @action="resetFilters"
              />
            </div>
          </div>
        </div>

        <!-- Wide Monograph Detail Sheet (8 cols) -->
        <div class="lg:col-span-8 p-6 sm:p-10 flex flex-col overflow-y-auto space-y-7">
          <EmptyState
            v-if="!selectedFinding"
            :icon="ShieldAlert"
            title="Select a finding to inspect"
            description="Choose an item from the index or reset filters to inspect details and remediation guidance."
            action-label="Reset filters"
            @action="resetFilters"
          />

          <template v-else>
            <!-- Top Header with Oversized CVSS Score Anchor -->
            <div class="border-b border-white/[0.1] pb-6 flex flex-col sm:flex-row sm:items-start justify-between gap-6">
              <div class="space-y-3">
                <div class="flex flex-wrap items-center gap-2">
                  <SeverityBadge :severity="selectedFinding.severity" :score="selectedFinding.cvss" size="md" />
                  <StatusBadge :status="effectiveStatus(selectedFinding)" />
                </div>

                <h2 class="text-2xl sm:text-3xl font-display font-bold text-[#F5F5F3] leading-tight">
                  {{ selectedFinding.title }}
                </h2>

                <!-- Single-line Hairline Spec Metadata -->
                <div class="flex flex-wrap items-center gap-3 font-mono text-xs text-[#8A8D96]">
                  <span>{{ selectedFinding.id }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.cwe }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.host }} ({{ selectedFinding.protocol }}:{{ selectedFinding.port }})</span>
                  <span>·</span>
                  <span class="text-[#F5F5F3]">{{ selectedFinding.endpoint }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.scanner }}</span>
                </div>
              </div>

              <div class="shrink-0 sm:text-right">
                <div class="font-display text-5xl font-bold tracking-tighter text-[#F5F5F3] tabular-nums leading-none">
                  {{ selectedFinding.cvss.toFixed(1) }}
                </div>
                <div class="mt-2 font-mono text-[10px] uppercase tracking-wider text-[#8A8D96]">
                  CVSS v3.1 Score
                </div>
              </div>
            </div>

            <!-- Action Bar -->
            <div class="flex flex-wrap items-center gap-3">
              <router-link :to="`/solutions/${selectedFinding.id}`" class="btn-platinum px-4 py-2 text-xs">
                <span>Inspect CVSS &amp; Proof</span>
                <ArrowRight class="h-3.5 w-3.5" />
              </router-link>

              <button
                type="button"
                @click="toggleFalsePositive(selectedFinding)"
                :class="[
                  'px-4 py-2 border text-xs font-medium transition-colors',
                  effectiveStatus(selectedFinding) === 'FALSE_POSITIVE'
                    ? 'border-emerald-400/40 bg-emerald-500/10 text-emerald-300'
                    : 'btn-glass',
                ]"
              >
                {{
                  effectiveStatus(selectedFinding) === 'FALSE_POSITIVE'
                    ? 'Restore finding'
                    : 'Exclude from report'
                }}
              </button>
            </div>

            <!-- Spacious Monograph Reading Prose -->
            <div class="space-y-6 text-base leading-7 text-[#D4D4D8] max-w-2xl">
              <div>
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Overview</h3>
                <p>{{ selectedFinding.description }}</p>
              </div>

              <div>
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Business Impact</h3>
                <p>{{ selectedFinding.businessImpact }}</p>
              </div>

              <div>
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Recommended Fix</h3>
                <p>{{ selectedFinding.remediation }}</p>
              </div>
            </div>
          </template>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ArrowRight, Search, ShieldAlert } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SeverityBadge from '@/components/ui/SeverityBadge.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { mockFindings, type MockFinding } from '@/services/mockData'
import { toast } from '@/stores/toast'

const severityFilters = [
  { key: 'ALL', label: 'All' },
  { key: 'CRITICAL', label: 'Critical' },
  { key: 'HIGH', label: 'High' },
  { key: 'MEDIUM', label: 'Medium' },
  { key: 'LOW', label: 'Low' },
] as const

type SeverityFilterKey = (typeof severityFilters)[number]['key']

const searchInputRef = ref<HTMLInputElement | null>(null)
const searchQuery = ref('')
const selectedSeverity = ref<SeverityFilterKey>('ALL')
const selectedId = ref<string>(mockFindings[0]?.id ?? '')
const statusOverrides = reactive<Record<string, string>>({})

const severityCounts = computed<Record<SeverityFilterKey, number>>(() => ({
  ALL: mockFindings.length,
  CRITICAL: mockFindings.filter((f) => f.severity === 'CRITICAL').length,
  HIGH: mockFindings.filter((f) => f.severity === 'HIGH').length,
  MEDIUM: mockFindings.filter((f) => f.severity === 'MEDIUM').length,
  LOW: mockFindings.filter((f) => f.severity === 'LOW').length,
}))

const filteredFindings = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return mockFindings.filter((item) => {
    const matchQuery =
      !q ||
      item.title.toLowerCase().includes(q) ||
      item.cwe.toLowerCase().includes(q) ||
      item.host.toLowerCase().includes(q) ||
      item.cve.toLowerCase().includes(q)
    const matchSev = selectedSeverity.value === 'ALL' || item.severity === selectedSeverity.value
    return matchQuery && matchSev
  })
})

watch(filteredFindings, (list) => {
  if (list.length > 0 && !list.some((f) => f.id === selectedId.value)) {
    selectedId.value = list[0]?.id ?? ''
  }
})

const selectedFinding = computed<MockFinding | null>(() => {
  if (filteredFindings.value.length === 0) return null
  return (
    filteredFindings.value.find((f) => f.id === selectedId.value) ??
    filteredFindings.value[0] ??
    null
  )
})

const effectiveStatus = (f: MockFinding): string => statusOverrides[f.id] ?? f.status

const formatStatusLabel = (status: string): string => {
  switch (status.toUpperCase()) {
    case 'OPEN':
      return 'Open'
    case 'IN_REVIEW':
      return 'In Review'
    case 'REMEDIATED':
      return 'Remediated'
    case 'FALSE_POSITIVE':
      return 'False Positive'
    case 'ACCEPTED_RISK':
      return 'Accepted Risk'
    default:
      return status
  }
}

const severityDotClass = (severity: string) => {
  switch (severity.toUpperCase()) {
    case 'CRITICAL':
      return 'bg-red-500'
    case 'HIGH':
      return 'bg-orange-400'
    case 'MEDIUM':
      return 'bg-amber-400'
    default:
      return 'bg-zinc-400'
  }
}

const toggleFalsePositive = (f: MockFinding) => {
  const current = effectiveStatus(f)
  if (current === 'FALSE_POSITIVE') {
    delete statusOverrides[f.id]
    toast.info(`Finding ${f.id} restored to ${formatStatusLabel(f.status)}.`)
  } else {
    statusOverrides[f.id] = 'FALSE_POSITIVE'
    toast.success(`${f.id} excluded from the demo report as False Positive.`)
  }
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedSeverity.value = 'ALL'
}

const handleShortcut = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    searchInputRef.value?.focus()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleShortcut)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleShortcut)
})
</script>
