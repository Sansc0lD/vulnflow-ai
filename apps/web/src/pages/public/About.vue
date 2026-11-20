<template>
  <PublicLayout>
    <!-- Header -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-14 pb-16 lg:pt-20 lg:pb-20">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          <div class="lg:col-span-8 space-y-4">
            <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
              How it works
            </span>
            <h1 class="font-display text-4xl sm:text-5xl lg:text-6xl font-bold tracking-[-0.04em] text-[#F5F5F3] leading-[1.02]">
              Designed for clarity, built for
              <span class="font-serif italic font-normal text-white">client trust.</span>
            </h1>
          </div>
          <p class="lg:col-span-4 text-sm text-[#8A8D96] leading-relaxed">
            Follow our four-step workflow that keeps raw client evidence encrypted locally while delivering executive reports fast.
          </p>
        </div>
      </div>
    </section>

    <!-- Ruled Comparison (Zero Cards) -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/[0.1]">
        <div class="py-10 md:pr-10 space-y-3">
          <span class="font-mono text-[11px] uppercase tracking-[0.12em] text-red-300 block">
            Traditional Reporting
          </span>
          <h2 class="text-xl font-display font-semibold text-[#F5F5F3]">
            Manual spreadsheets &amp; prompt risks
          </h2>
          <p class="text-sm text-[#8A8D96] leading-relaxed max-w-md">
            Hours of engagement time go toward sorting raw XML or JSON files, recalculating risk scores by hand, and pasting evidence into document editors or public chat tools.
          </p>
        </div>

        <div class="py-10 md:pl-10 space-y-3">
          <span class="font-mono text-[11px] uppercase tracking-[0.12em] text-emerald-400 block">
            With VulnFlow
          </span>
          <h2 class="text-xl font-display font-semibold text-[#F5F5F3]">
            Private evidence &amp; instant drafts
          </h2>
          <p class="text-sm text-[#D4D4D8] leading-relaxed max-w-md">
            Scans run locally on your machine. Technical proof stays encrypted inside your workspace while only sanitized titles and scores are used to draft clean client narratives.
          </p>
        </div>
      </div>
    </section>

    <!-- Interactive 4-Step Walkthrough (UC-02) -->
    <section class="py-16 lg:py-20 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full space-y-10">
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/[0.1] pb-5">
        <div>
          <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
            Reporting Flow
          </span>
          <h2 class="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F5F3] mt-1">
            Four steps from scan to deliverable
          </h2>
        </div>
        <span class="font-mono text-xs text-[#8A8D96] tabular-nums">
          Stage {{ String(activeStepIndex + 1).padStart(2, '0') }} / {{ String(workflowSteps.length).padStart(2, '0') }}
        </span>
      </div>

      <!-- Ruled Horizontal Step Tabs -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border border-white/[0.12] divide-y sm:divide-y-0 sm:divide-x divide-white/[0.1] bg-[#08080B]">
        <button
          v-for="(step, index) in workflowSteps"
          :key="step.id"
          type="button"
          @click="activeStepIndex = index"
          :aria-pressed="activeStepIndex === index"
          :class="[
            'p-5 text-left transition-colors flex flex-col justify-between gap-4',
            activeStepIndex === index
              ? 'bg-[#F5F5F3] text-[#050507]'
              : 'text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
          ]"
        >
          <div class="flex items-center justify-between w-full font-mono text-xs">
            <span class="font-bold">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="text-[10px] uppercase tracking-wider opacity-75">
              {{ activeStepIndex === index ? 'Active' : 'Select' }}
            </span>
          </div>
          <div>
            <h3 :class="['text-sm font-display font-semibold', activeStepIndex === index ? 'text-[#050507]' : 'text-[#F5F5F3]']">
              {{ step.name }}
            </h3>
            <p :class="['text-xs mt-1', activeStepIndex === index ? 'text-[#050507]/75' : 'text-[#8A8D96]']">
              {{ step.subtitle }}
            </p>
          </div>
        </button>
      </div>

      <!-- Active Step Detail Spread (Flat Hairline Columns) -->
      <div class="border border-white/[0.14] bg-[#08080B]">
        <div class="p-6 sm:p-8 border-b border-white/[0.1] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="space-y-1">
            <h3 class="text-xl font-display font-semibold text-[#F5F5F3]">{{ activeStep.name }}</h3>
            <p class="font-mono text-xs text-[#8A8D96]">{{ activeStep.context }}</p>
          </div>
          <span class="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider px-2.5 py-1 border border-emerald-400/30 bg-emerald-500/10 text-emerald-300 self-start sm:self-auto">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
            <span>{{ activeStep.guarantee }}</span>
          </span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.1]">
          <div class="p-6 sm:p-8 space-y-4">
            <h4 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96]">What happens</h4>
            <p class="text-sm text-[#F5F5F3] leading-relaxed">{{ activeStep.description }}</p>

            <ul class="space-y-2.5 text-xs sm:text-sm text-[#D4D4D8] pt-2 border-t border-white/[0.08]">
              <li v-for="(item, i) in activeStep.highlights" :key="i" class="flex items-start gap-2.5">
                <Check class="h-4 w-4 text-[#F5F5F3] shrink-0 mt-0.5" aria-hidden="true" />
                <span>{{ item }}</span>
              </li>
            </ul>
          </div>

          <div class="p-6 sm:p-8 space-y-4">
            <h4 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96]">Privacy &amp; safeguards</h4>
            <ul class="divide-y divide-white/[0.08] border-y border-white/[0.08]">
              <li
                v-for="(rule, rIdx) in activeStep.safeguards"
                :key="rIdx"
                class="py-3.5 flex items-start gap-2.5 text-xs sm:text-sm text-[#D4D4D8] leading-relaxed"
              >
                <Shield class="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" />
                <span>{{ rule }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Ruled 4-Column Trust Foundations Ledger -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border-y border-white/[0.12] divide-y sm:divide-y-0 sm:divide-x divide-white/[0.1]">
        <div
          v-for="(item, idx) in foundations"
          :key="item.title"
          class="py-7 sm:px-6 first:sm:pl-0 last:sm:pr-0 space-y-2"
        >
          <span class="font-mono text-xs text-[#8A8D96] block">{{ String(idx + 1).padStart(2, '0') }}</span>
          <h4 class="text-sm font-display font-semibold text-[#F5F5F3]">{{ item.title }}</h4>
          <p class="text-xs text-[#8A8D96] leading-relaxed">{{ item.desc }}</p>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Shield } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'

const activeStepIndex = ref(0)

const workflowSteps = [
  {
    id: 'step1',
    name: 'Local Scan',
    subtitle: 'Run tools on your own machine',
    context: 'Works with macOS, Linux, and Windows',
    guarantee: 'No external cloud scanning',
    description:
      'Security teams run Nmap or Nuclei directly from their own authorized workstation. VulnFlow never launches active network scans from cloud servers.',
    highlights: [
      'Supports standard Nmap XML and Nuclei JSONL scan outputs.',
      'Resumable chunked uploads prevent duplicate findings on unstable networks.',
      'Local API credentials stay scoped to your team workspace.',
    ],
    safeguards: [
      'Client networks remain reachable only from your authorized test machine.',
      'Duplicate scan runs are automatically merged cleanly.',
      'API keys can be issued or revoked at any time from Settings.',
    ],
  },
  {
    id: 'step2',
    name: 'Scope Check',
    subtitle: 'Keep out-of-scope targets separate',
    context: 'Automatic target and schedule validation',
    guarantee: 'Automatic boundary guard',
    description:
      'Every imported finding is checked against the project’s approved domains, IP ranges, and testing window before appearing in report candidates.',
    highlights: [
      'Matches domains, wildcard subdomains, and CIDR IP ranges.',
      'Checks finding timestamps against project start and end windows.',
      'Holds aside unexpected targets until a manager reviews them.',
    ],
    safeguards: [
      'Out-of-scope discoveries cannot accidentally enter client reports.',
      'Only workspace managers can approve or release held findings.',
      'Full project scope rules stay clearly visible to all team members.',
    ],
  },
  {
    id: 'step3',
    name: 'Private Summary',
    subtitle: 'Clear writing without exposing proof',
    context: 'Human-reviewed report drafting',
    guarantee: 'Technical proof stays encrypted',
    description:
      'Raw evidence payloads are encrypted at rest inside your workspace. Only issue names, categories, and risk scores are used to draft readable executive narratives.',
    highlights: [
      'Removes hostnames, IP addresses, paths, and raw proof payloads automatically.',
      'Drafts plain-language business impact and fix guidance quickly.',
      'Falls back seamlessly to curated guidance templates whenever offline.',
    ],
    safeguards: [
      'Zero client secrets or exploit proof ever reach external AI services.',
      'Reviewers can edit every section and approve drafts before export.',
      'Version history preserves earlier drafts whenever you regenerate.',
    ],
  },
  {
    id: 'step4',
    name: 'Branded PDF',
    subtitle: 'Deliver clean client-ready reports',
    context: 'Asynchronous PDF generation',
    guarantee: 'Safe asset handling',
    description:
      'Generate crisp, print-ready A4 PDF reports styled with your agency logo, brand palette, CVSS risk charts, and custom confidentiality notice.',
    highlights: [
      'Automatic contrast calculation keeps cover typography legible.',
      'Include or hide cover pages and CVSS radar summaries per report.',
      'Download archived versions any time from project history.',
    ],
    safeguards: [
      'External brand assets are validated to prevent private network lookups.',
      'Viewers see approved reports without accessing sensitive raw payloads.',
      'White-label output comes standard on Pro and Enterprise plans.',
    ],
  },
]

const activeStep = computed(() => workflowSteps[activeStepIndex.value] ?? workflowSteps[0])

const foundations = [
  {
    title: 'Standardized risk scoring',
    desc: 'Consistent FIRST CVSS v3.1 calculations across scan imports, workspace review, and final PDFs.',
  },
  {
    title: 'Consistent taxonomy',
    desc: 'Uniform CWE categorization across Nmap, Nuclei, and manually logged findings.',
  },
  {
    title: 'Role-based access',
    desc: 'Separate permissions for Managers, Pentesters, and read-only Client Viewers.',
  },
  {
    title: 'Complete activity log',
    desc: 'Every status change, evidence access, and report export is logged for accountability.',
  },
]
</script>
