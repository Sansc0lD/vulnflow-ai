<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-bold text-white">Editor Interaktif Tinjauan Narasi AI (WF3)</h1>
        <p class="text-xs text-zinc-400 font-mono">PROJECT PRJ-01 > AI GHOSTWRITER NARRATIVE REVIEW</p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-border bg-surface">
        <div class="flex items-center space-x-3 text-xs font-mono">
          <span class="text-zinc-400">BAHASA NARASI:</span>
          <select
            v-model="language"
            class="bg-background border border-border rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            <option value="id">Bahasa Indonesia (Manajerial)</option>
            <option value="en">English (Executive Summary)</option>
          </select>

          <span class="text-zinc-500">•</span>

          <span class="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            ZERO-POC COMPLIANT
          </span>

          <span v-if="isFallback" class="text-[11px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
            FALLBACK CWE MODE (EC-14)
          </span>
        </div>

        <div class="flex items-center space-x-2.5">
          <button
            @click="promptRegenerate"
            :disabled="generating"
            class="inline-flex items-center space-x-1.5 rounded-lg border border-border bg-surface-elevated px-3.5 py-1.5 text-xs font-semibold text-zinc-200 hover:text-white disabled:opacity-50"
          >
            <RefreshCw :class="['h-3.5 w-3.5 text-blue-400', generating ? 'animate-spin' : '']" />
            <span>{{ generating ? 'Memproses Prompt AI...' : 'Re-generate AI' }}</span>
          </button>

          <button
            @click="handleSaveNarrative"
            class="inline-flex items-center space-x-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
          >
            <Save class="h-3.5 w-3.5" />
            <span>Simpan Perubahan Narasi</span>
          </button>
        </div>
      </div>

      <!-- Narrative Review Canvas -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Main WYSIWYG Editor (8 cols) -->
        <div class="lg:col-span-8 space-y-6">
          <!-- Executive Summary Section -->
          <div class="rounded-xl border border-border bg-surface p-6 space-y-3">
            <div class="flex items-center justify-between border-b border-border pb-2.5">
              <label class="text-sm font-bold text-white flex items-center gap-2">
                <FileText class="h-4 w-4 text-blue-400" />
                <span>1. Ringkasan Eksekutif (Executive Summary)</span>
              </label>
              <span class="text-[10px] font-mono text-zinc-500">FORMAT AUDIT MANAJERIAL</span>
            </div>

            <textarea
              v-model="narrative.executiveSummary"
              rows="5"
              class="w-full bg-background border border-border rounded-lg p-3 text-xs text-zinc-200 leading-relaxed focus:outline-none focus:border-blue-500"
            ></textarea>
            <p class="text-[11px] text-zinc-500">
              Menjelaskan postur keamanan secara komprehensif bagi jajaran direksi tanpa detail eksploitasi mentah.
            </p>
          </div>

          <!-- Business Impact Section -->
          <div class="rounded-xl border border-border bg-surface p-6 space-y-3">
            <div class="flex items-center justify-between border-b border-border pb-2.5">
              <label class="text-sm font-bold text-white flex items-center gap-2">
                <AlertCircle class="h-4 w-4 text-red-400" />
                <span>2. Analisis Dampak Bisnis (Business Impact)</span>
              </label>
              <span class="text-[10px] font-mono text-zinc-500">RISK ASSESSMENT</span>
            </div>

            <textarea
              v-model="narrative.businessImpact"
              rows="5"
              class="w-full bg-background border border-border rounded-lg p-3 text-xs text-zinc-200 leading-relaxed focus:outline-none focus:border-blue-500"
            ></textarea>
          </div>

          <!-- Remediation Guidance List -->
          <div class="rounded-xl border border-border bg-surface p-6 space-y-4">
            <div class="flex items-center justify-between border-b border-border pb-2.5">
              <label class="text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 class="h-4 w-4 text-emerald-400" />
                <span>3. Panduan Remediasi Terkurasi (Per CWE)</span>
              </label>
              <span class="text-[10px] font-mono text-zinc-500">DEVELOPER ACTIONABLE</span>
            </div>

            <div class="space-y-4">
              <div
                v-for="(rem, index) in narrative.remediations"
                :key="index"
                class="p-4 rounded-lg bg-surface-elevated border border-border space-y-2"
              >
                <div class="flex items-center justify-between">
                  <span class="text-xs font-mono font-bold text-blue-400">{{ rem.cwe_id }}: {{ rem.vuln_title }}</span>
                </div>
                <textarea
                  v-model="rem.remediation_guidance"
                  rows="3"
                  class="w-full bg-background border border-border rounded-lg p-2.5 text-xs text-zinc-300 font-mono focus:outline-none focus:border-blue-500"
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar / Telemetry Info (4 cols) -->
        <div class="lg:col-span-4 space-y-6">
          <div class="rounded-xl border border-border bg-surface p-5 space-y-4 font-mono text-xs">
            <h3 class="text-xs font-bold text-white uppercase tracking-wider border-b border-border pb-2">
              Telemetri AI Ghostwriter
            </h3>

            <div class="space-y-2 text-zinc-400">
              <div class="flex justify-between">
                <span>Model AI:</span>
                <span class="text-white">Gemini 2.0 Flash</span>
              </div>
              <div class="flex justify-between">
                <span>Tokens Consumed:</span>
                <span class="text-blue-400 font-bold">482 Tokens</span>
              </div>
              <div class="flex justify-between">
                <span>Fallback In-Memory:</span>
                <span :class="isFallback ? 'text-amber-400' : 'text-emerald-400'">{{ isFallback ? 'YES' : 'NO' }}</span>
              </div>
              <div class="flex justify-between">
                <span>Zero-PoC Filter:</span>
                <span class="text-emerald-400 font-bold">100% Whitelist</span>
              </div>
            </div>
          </div>

          <div class="p-4 rounded-xl border border-blue-500/20 bg-blue-950/10 text-xs text-zinc-400 space-y-2 leading-relaxed">
            <div class="font-bold text-blue-400 flex items-center gap-1.5">
              <ShieldAlert class="h-4 w-4" />
              <span>Human-in-the-Loop Review</span>
            </div>
            <p>
              Auditor memiliki wewenang penuh untuk merevisi teks narasi yang di-generate oleh AI sebelum dicantumkan dalam laporan PDF akhir.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Regenerate Confirmation Warning Dialog (UC-12 / Wireframe 3) -->
    <div
      v-if="showWarningModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
    >
      <div class="w-full max-w-md rounded-xl border border-border bg-surface p-6 space-y-4 shadow-2xl">
        <div class="flex items-center space-x-3 text-amber-400">
          <AlertTriangle class="h-5 w-5 shrink-0" />
          <h3 class="text-sm font-bold text-white">Konfirmasi Re-generate AI</h3>
        </div>

        <p class="text-xs text-zinc-300 leading-relaxed">
          Menjalankan ulang AI Ghostwriter akan <strong>menimpa editan manual</strong> yang telah Anda buat pada Ringkasan Eksekutif dan Analisis Dampak. Apakah Anda yakin ingin melanjutkan?
        </p>

        <div class="flex justify-end space-x-2.5 pt-2">
          <button
            @click="showWarningModal = false"
            class="px-4 py-2 rounded-lg border border-border text-xs text-zinc-400 hover:text-white"
          >
            Batal
          </button>
          <button
            @click="executeRegenerate"
            class="px-4 py-2 rounded-lg bg-red-600 text-xs font-semibold text-white hover:bg-red-500"
          >
            Ya, Timpa & Generate Ulang
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import {
  FileText,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Save,
  ShieldAlert,
  AlertTriangle,
} from 'lucide-vue-next'

const language = ref('id')
const generating = ref(false)
const isFallback = ref(false)
const showWarningModal = ref(false)

const narrative = ref({
  executiveSummary:
    'Berdasarkan hasil asesmen penetrasi terhadap sistem perbankan PT Bank Bukopin Tbk pada rentang waktu Oktober 2026, tim auditor menemukan 19 kerentanan teknis. Dari jumlah tersebut, ditemukan 2 kerentanan kritis berupa SQL Injection pada antarmuka autentikasi dan tereksposnya port Redis ke jaringan publik. Postur keamanan saat ini membutuhkan mitigasi segera pada lapisan input validation serta segmentasi jaringan private.',
  businessImpact:
    'Eksploitasi atas temuan kritis memungkinkan pelaku ancaman membobol kerahasiaan data nasabah, memodifikasi saldo rekening, dan mengekstraksi kredensial administratif. Hal ini dapat menimbulkan kerugian finansial langsung, denda sanksi regulasi OJK/BI, serta degradasi reputasi agensi.',
  remediations: [
    {
      cwe_id: 'CWE-89',
      vuln_title: 'SQL Injection',
      remediation_guidance:
        'Terapkan parameter binding (prepared statements) secara konsisten di seluruh lapisan data access layer ORM.',
    },
    {
      cwe_id: 'CWE-306',
      vuln_title: 'Missing Authentication',
      remediation_guidance:
        'Aktifkan konfigurasi requirepass pada Redis dan batasi akses hanya via private subnet VPC / internal loopback.',
    },
  ],
})

const promptRegenerate = () => {
  showWarningModal.value = true
}

const executeRegenerate = () => {
  showWarningModal.value = false
  generating.value = true
  setTimeout(() => {
    generating.value = false
    alert('Narasi AI berhasil di-generate ulang dengan model Zero-PoC Gemini 2.0!')
  }, 1200)
}

const handleSaveNarrative = () => {
  alert('Narasi audit berhasil disimpan ke database!')
}
</script>
