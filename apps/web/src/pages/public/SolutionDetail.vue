<template>
  <PublicLayout>
    <!-- Not Found State -->
    <section
      v-if="!finding"
      class="py-16 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full flex items-center"
    >
      <div class="w-full">
        <EmptyState
          :icon="ShieldAlert"
          title="Demo finding not found"
          description="The requested demo finding is not available in the sample catalog."
          action-label="Back to demo"
          action-to="/solutions"
        />
      </div>
    </section>

    <template v-else>
      <!-- Header -->
      <section class="border-b border-white/[0.1]">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-8 space-y-5">
          <router-link
            to="/solutions"
            class="inline-flex items-center text-xs sm:text-sm text-[#8A8D96] hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors"
          >
            <ArrowLeft class="mr-1.5 h-4 w-4" />
            <span>Back to demo</span>
          </router-link>

          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-2.5">
              <div class="flex flex-wrap items-center gap-2">
                <SeverityBadge :severity="liveCvss.severity" :score="liveCvss.score" size="md" />
                <StatusBadge :status="finding.status" />
                <span class="text-xs text-[#8A8D96] font-mono">{{ finding.id }} · {{ finding.cwe }}</span>
              </div>
              <h1 class="font-display text-2xl sm:text-4xl font-bold text-[#F5F5F3] tracking-tight">
                {{ finding.title }}
              </h1>
            </div>

            <button
              type="button"
              @click="openDecryptModal"
              class="btn-platinum px-4 py-2.5 text-xs shrink-0 self-start md:self-auto"
            >
              <Key class="h-3.5 w-3.5" />
              <span>{{ pocUnlocked ? 'Evidence unlocked' : 'Unlock evidence' }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Main Detail Content (UC-04 & UC-04a) -->
      <section class="py-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8 flex-1 w-full">
        <div class="grid grid-cols-1 lg:grid-cols-12 border border-white/[0.12] bg-[#08080B] divide-y lg:divide-y-0 lg:divide-x divide-white/[0.1]">
          <!-- Interactive CVSS v3.1 Calculator & Radar (8 cols) -->
          <div class="lg:col-span-8 p-6 sm:p-7 space-y-5">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3.5">
              <div>
                <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3]">
                  Risk Score Calculator
                </h2>
                <p class="text-xs text-[#8A8D96] mt-0.5">
                  Adjust CVSS metrics to observe real-time severity recalculation.
                </p>
              </div>
              <button
                v-if="isModifiedCvss"
                type="button"
                @click="resetCvss"
                class="btn-glass px-3 py-1.5 text-xs"
              >
                Reset ({{ finding.cvss.toFixed(1) }})
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              <div class="md:col-span-5 flex flex-col items-center justify-center p-4 bg-[#050507] border border-white/[0.1]">
                <CvssRadarChart
                  :metrics="editableMetrics"
                  :score="liveCvss.score"
                  :severity="liveCvss.severity"
                  :size="220"
                />
                <div class="mt-2 text-center">
                  <SeverityBadge :severity="liveCvss.severity" :score="liveCvss.score" size="md" />
                </div>
              </div>

              <div class="md:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div v-for="def in metricDefsList" :key="def.key" class="space-y-1">
                  <label
                    :for="`cvss-${def.key}`"
                    class="text-xs font-medium text-[#D4D4D8] block"
                    :title="def.description"
                  >
                    {{ def.name }}
                  </label>
                  <select
                    :id="`cvss-${def.key}`"
                    v-model="editableMetrics[def.key]"
                    class="w-full input-glass px-2.5 py-1.5 text-xs"
                  >
                    <option v-for="opt in def.options" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <div class="p-3.5 bg-[#050507] font-mono text-xs text-[#D4D4D8] border border-white/[0.1] flex flex-wrap items-center justify-between gap-2">
              <span class="break-all">{{ liveCvss.vector }}</span>
              <span v-if="isModifiedCvss" class="text-[11px] font-sans text-amber-300">
                Modified from {{ finding.cvss.toFixed(1) }}
              </span>
            </div>
          </div>

          <!-- Hairline Target Details (4 cols) -->
          <div class="lg:col-span-4 p-6 sm:p-7 space-y-4">
            <h2 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] border-b border-white/[0.08] pb-3.5">
              Target Details
            </h2>

            <dl class="divide-y divide-white/[0.08] text-xs">
              <div class="py-3">
                <dt class="text-[#8A8D96]">Host</dt>
                <dd class="text-[#F5F5F3] font-mono font-semibold mt-1 break-all">{{ finding.host }}</dd>
              </div>
              <div class="py-3">
                <dt class="text-[#8A8D96]">Port &amp; Protocol</dt>
                <dd class="text-[#F5F5F3] font-mono mt-1 tabular-nums">{{ finding.port }} / {{ finding.protocol }}</dd>
              </div>
              <div class="py-3">
                <dt class="text-[#8A8D96]">Endpoint</dt>
                <dd class="text-[#F5F5F3] font-mono break-all mt-1">{{ finding.endpoint }}</dd>
              </div>
              <div class="pt-3">
                <dt class="text-[#8A8D96]">Scanner &amp; Reference</dt>
                <dd class="text-[#D4D4D8] mt-1">{{ finding.scanner }} · {{ finding.cve }}</dd>
              </div>
            </dl>
          </div>
        </div>

        <!-- Tabs: Overview, Fix Guidance, Technical Evidence -->
        <div class="border border-white/[0.12] bg-[#08080B]">
          <div
            role="tablist"
            aria-label="Finding details"
            class="border-b border-white/[0.1] bg-[#050507] flex overflow-x-auto text-xs sm:text-sm font-medium"
          >
            <button
              type="button"
              role="tab"
              :aria-selected="activeTab === 'description'"
              @click="activeTab = 'description'"
              :class="[
                'px-5 py-3.5 border-b-2 transition-colors whitespace-nowrap',
                activeTab === 'description'
                  ? 'border-[#F5F5F3] text-[#F5F5F3] font-semibold'
                  : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              Overview
            </button>
            <button
              type="button"
              role="tab"
              :aria-selected="activeTab === 'remediation'"
              @click="activeTab = 'remediation'"
              :class="[
                'px-5 py-3.5 border-b-2 transition-colors whitespace-nowrap',
                activeTab === 'remediation'
                  ? 'border-[#F5F5F3] text-[#F5F5F3] font-semibold'
                  : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              Fix Guidance
            </button>
            <button
              type="button"
              role="tab"
              :aria-selected="activeTab === 'poc'"
              @click="activeTab = 'poc'"
              :class="[
                'px-5 py-3.5 border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5',
                activeTab === 'poc'
                  ? 'border-[#F5F5F3] text-[#F5F5F3] font-semibold'
                  : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              <Lock v-if="!pocUnlocked" class="h-3.5 w-3.5 text-amber-300" aria-hidden="true" />
              <span>Technical Evidence</span>
            </button>
          </div>

          <div class="p-6 sm:p-8 text-sm text-[#D4D4D8] leading-relaxed">
            <!-- Tab 1 -->
            <div v-if="activeTab === 'description'" role="tabpanel" class="space-y-6 max-w-3xl">
              <div>
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Technical Explanation</h3>
                <p class="text-base leading-7 text-[#F5F5F3]">{{ finding.description }}</p>
              </div>
              <div>
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Business Impact</h3>
                <p class="text-base leading-7">{{ finding.businessImpact }}</p>
              </div>
              <div class="border-l-2 border-[#F5F5F3] pl-4 py-1 space-y-1.5">
                <div class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] flex items-center gap-1.5">
                  <FileText class="h-3.5 w-3.5 text-[#F5F5F3]" aria-hidden="true" />
                  <span>AI Executive Summary</span>
                </div>
                <p class="text-sm sm:text-base text-[#F5F5F3] leading-relaxed">{{ finding.aiExecutiveSnippet }}</p>
              </div>
            </div>

            <!-- Tab 2 -->
            <div v-else-if="activeTab === 'remediation'" role="tabpanel" class="space-y-5">
              <div class="max-w-3xl">
                <h3 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Recommended Fix</h3>
                <p class="text-base leading-7">{{ finding.remediation }}</p>
              </div>

              <div class="border border-white/[0.11] bg-[#050507] overflow-hidden">
                <div class="px-4 py-2.5 border-b border-white/[0.1] flex flex-wrap items-center justify-between gap-2">
                  <span class="font-mono text-xs text-[#D4D4D8]">Illustrative CWE Remediation Pattern</span>
                  <button
                    type="button"
                    @click="copyText(finding.patchDiff, 'Remediation pattern')"
                    class="btn-glass px-2.5 py-1 text-xs"
                  >
                    <Copy class="h-3.5 w-3.5" />
                    <span>Copy patch</span>
                  </button>
                </div>
                <div class="px-4 py-2 border-b border-white/[0.08] bg-[#08080B] font-mono text-[11px] text-[#8A8D96]">
                  Reference pattern based on CWE category: private source code and PoC payloads are never sent to AI.
                </div>
                <div class="p-4 font-mono text-xs overflow-x-auto space-y-0.5">
                  <div
                    v-for="(line, idx) in finding.patchDiff.split('\n')"
                    :key="idx"
                    :class="[
                      'px-2 py-0.5',
                      line.startsWith('+') && !line.startsWith('+++')
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : line.startsWith('-') && !line.startsWith('---')
                          ? 'bg-red-500/15 text-red-300'
                          : 'text-[#8A8D96]',
                    ]"
                  >
                    {{ line }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab 3: Optical Privacy Lens Shutter When Locked -->
            <div v-else role="tabpanel" class="space-y-4">
              <div v-if="!pocUnlocked" class="relative border border-white/[0.14] bg-[#050507] p-6 overflow-hidden min-h-[190px]">
                <div class="font-mono text-xs text-[#8A8D96] break-all select-none">
                  {{ finding.encryptedCiphertext }}
                </div>

                <div class="vf-optical-lens absolute inset-0 flex flex-col sm:flex-row items-center justify-between gap-4 p-6">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2 text-amber-300 font-mono text-xs uppercase tracking-wider">
                      <Lock class="h-3.5 w-3.5" aria-hidden="true" />
                      <span>Optical Privacy Lens Active</span>
                    </div>
                    <p class="text-xs text-[#E4E4E7]">
                      Encrypted evidence stays vaulted until unlocked with the workspace passphrase.
                    </p>
                  </div>
                  <button type="button" @click="openDecryptModal" class="btn-platinum px-4 py-2 text-xs shrink-0">
                    <Key class="h-3.5 w-3.5" />
                    <span>Unlock now</span>
                  </button>
                </div>
              </div>

              <div v-else class="space-y-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="font-mono text-xs text-emerald-400">
                    Unlocked Evidence (Authorized session)
                  </span>
                  <div class="flex items-center gap-2">
                    <button type="button" @click="copyText(finding.poc, 'Technical proof')" class="btn-glass px-3 py-1.5 text-xs">
                      Copy proof
                    </button>
                    <button type="button" @click="pocUnlocked = false" class="btn-glass px-3 py-1.5 text-xs">
                      Lock evidence
                    </button>
                  </div>
                </div>
                <div class="bg-[#050507] border border-emerald-400/30 p-4 font-mono text-xs text-[#F5F5F3] overflow-x-auto">
                  <pre>{{ finding.poc }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Interactive Evidence Unlock Modal (UC-04a) -->
      <BaseModal
        :open="showDecryptModal"
        title="Unlock Technical Evidence"
        subtitle="Enter the demo passphrase to view the protected technical proof."
        max-width="lg"
        @close="showDecryptModal = false"
      >
        <div class="space-y-4">
          <div class="p-3 bg-[#050507] border border-white/[0.1] font-mono text-[11px] text-[#8A8D96] break-all">
            <span class="text-[#F5F5F3] font-sans block mb-1 font-medium">Encrypted Payload:</span>
            {{ finding.encryptedCiphertext }}
          </div>

          <form @submit.prevent="attemptDecrypt" class="space-y-3">
            <div class="flex items-center justify-between gap-2">
              <label for="poc-passphrase" class="text-xs font-medium text-[#D4D4D8]">
                Passphrase
              </label>
              <button
                type="button"
                @click="passphraseInput = finding.demoPassphrase"
                class="text-xs text-[#F5F5F3] underline underline-offset-4 hover:text-white"
              >
                Fill demo passphrase ({{ finding.demoPassphrase }})
              </button>
            </div>

            <input
              id="poc-passphrase"
              v-model.trim="passphraseInput"
              type="text"
              required
              placeholder="Enter passphrase..."
              class="w-full input-glass px-3 py-2 text-xs font-mono"
            />

            <div
              v-if="decryptError"
              role="alert"
              class="p-2.5 bg-red-500/15 border border-red-400/35 text-red-200 text-xs"
            >
              {{ decryptError }}
            </div>

            <div class="flex justify-end gap-2">
              <button type="submit" class="btn-platinum px-4 py-2 text-xs">
                Verify &amp; Unlock
              </button>
            </div>
          </form>

          <div
            v-if="pocUnlocked"
            class="p-4 bg-[#050507] border border-emerald-400/35 space-y-2 font-mono text-xs"
          >
            <div class="flex items-center justify-between">
              <span class="text-emerald-400 font-sans font-medium">Decrypted Evidence</span>
              <button
                type="button"
                @click="copyText(finding.poc, 'Technical proof')"
                class="text-[#F5F5F3] underline underline-offset-4 font-sans text-xs"
              >
                Copy
              </button>
            </div>
            <pre class="text-[#F5F5F3] overflow-x-auto whitespace-pre-wrap break-all">{{ finding.poc }}</pre>
          </div>
        </div>

        <template #footer>
          <button type="button" @click="showDecryptModal = false" class="btn-glass px-4 py-2 text-xs">
            Close
          </button>
        </template>
      </BaseModal>
    </template>
  </PublicLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Copy, FileText, Key, Lock, ShieldAlert } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import CvssRadarChart from '@/components/ui/CvssRadarChart.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SeverityBadge from '@/components/ui/SeverityBadge.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { mockFindings } from '@/services/mockData'
import { toast } from '@/stores/toast'
import {
  computeCvss31,
  CVSS_METRIC_DEFS,
  parseCvssVector,
  type CvssMetrics,
} from '@/utils/cvss'

const route = useRoute()

const finding = computed(() => {
  const id = String(route.params.id || '')
  return mockFindings.find((f) => f.id === id) ?? null
})

const editableMetrics = reactive<CvssMetrics>(parseCvssVector(finding.value?.vector))

const syncMetricsFromFinding = () => {
  const parsed = parseCvssVector(finding.value?.vector)
  Object.assign(editableMetrics, parsed)
}

watch(
  () => finding.value?.id,
  () => {
    syncMetricsFromFinding()
    activeTab.value = 'description'
    pocUnlocked.value = false
    passphraseInput.value = ''
    decryptError.value = ''
  }
)

const metricDefsList = Object.values(CVSS_METRIC_DEFS)
const liveCvss = computed(() => computeCvss31(editableMetrics))
const isModifiedCvss = computed(
  () => Boolean(finding.value && liveCvss.value.vector !== finding.value.vector)
)

const resetCvss = () => {
  syncMetricsFromFinding()
  toast.info('Risk score metrics reset to baseline values.')
}

const activeTab = ref<'description' | 'remediation' | 'poc'>('description')
const showDecryptModal = ref(false)
const pocUnlocked = ref(false)
const passphraseInput = ref('')
const decryptError = ref('')

const openDecryptModal = () => {
  decryptError.value = ''
  showDecryptModal.value = true
}

const attemptDecrypt = () => {
  if (!finding.value) return
  if (passphraseInput.value !== finding.value.demoPassphrase) {
    decryptError.value = 'Incorrect passphrase. Please try again or use the demo passphrase.'
    return
  }
  decryptError.value = ''
  pocUnlocked.value = true
  activeTab.value = 'poc'
  toast.success('Evidence unlocked for this session.')
}

const copyText = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`${label} copied to clipboard.`)
  } catch {
    toast.info(text, label)
  }
}
</script>
