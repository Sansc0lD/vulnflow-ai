<template>
  <div class="flex flex-col min-h-screen">
    <Navbar />

    <section class="py-10 border-b border-border bg-gradient-to-b from-blue-950/10 to-background">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
        <router-link
          to="/solutions"
          class="inline-flex items-center text-xs text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft class="mr-1.5 h-3.5 w-3.5" />
          <span>Kembali ke Katalog Triase</span>
        </router-link>

        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="space-y-1.5">
            <div class="flex items-center space-x-2">
              <span
                :class="[
                  'text-xs font-mono font-bold px-2 py-0.5 rounded border',
                  getSeverityClass(finding.severity)
                ]"
              >
                {{ finding.severity }}
              </span>
              <span class="text-xs text-zinc-400 font-mono">{{ finding.cwe }}</span>
              <span class="text-xs text-zinc-500">•</span>
              <span class="text-xs text-zinc-400 font-mono">ID: {{ finding.id }}</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-bold text-white">{{ finding.title }}</h1>
          </div>

          <button
            @click="showDecryptModal = true"
            class="inline-flex items-center space-x-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-500 transition-colors shrink-0"
          >
            <Key class="h-3.5 w-3.5" />
            <span>Dekripsi Bukti PoC (AES-256)</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Main Detail Content -->
    <section class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8 flex-1 w-full">
      <!-- CVSS v3.1 Visualizer & Target Scope Card -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- CVSS Breakdown -->
        <div class="lg:col-span-2 rounded-xl border border-border bg-surface p-6 space-y-4">
          <div class="flex items-center justify-between border-b border-border pb-3">
            <h3 class="text-sm font-semibold text-white flex items-center gap-2">
              <ShieldAlert class="h-4 w-4 text-blue-400" />
              <span>Metrik Kerentanan CVSS v3.1</span>
            </h3>
            <span class="text-xs font-mono text-zinc-400">Score: <strong class="text-white text-sm">{{ finding.cvss }}</strong> / 10.0</span>
          </div>

          <!-- CVSS Sub-metrics Grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">ATTACK VECTOR (AV)</span>
              <span class="text-white font-semibold">NETWORK (AV:N)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">COMPLEXITY (AC)</span>
              <span class="text-white font-semibold">LOW (AC:L)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">PRIVILEGES (PR)</span>
              <span class="text-white font-semibold">NONE (PR:N)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">USER INTERACTION</span>
              <span class="text-white font-semibold">NONE (UI:N)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">SCOPE (S)</span>
              <span class="text-white font-semibold">UNCHANGED (S:U)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">CONFIDENTIALITY (C)</span>
              <span class="text-red-400 font-semibold">HIGH (C:H)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">INTEGRITY (I)</span>
              <span class="text-red-400 font-semibold">HIGH (I:H)</span>
            </div>
            <div class="p-2.5 rounded bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">AVAILABILITY (A)</span>
              <span class="text-red-400 font-semibold">HIGH (A:H)</span>
            </div>
          </div>

          <div class="p-2.5 rounded bg-black/60 font-mono text-[11px] text-zinc-400 border border-zinc-800">
            Vector: {{ finding.vector }}
          </div>
        </div>

        <!-- Infrastructure Target Card -->
        <div class="rounded-xl border border-border bg-surface p-6 space-y-4">
          <h3 class="text-sm font-semibold text-white border-b border-border pb-3 flex items-center gap-2">
            <Server class="h-4 w-4 text-emerald-400" />
            <span>Infrastruktur Target</span>
          </h3>

          <div class="space-y-3 text-xs font-mono">
            <div>
              <span class="text-zinc-500 text-[10px] block">HOST TARGET:</span>
              <span class="text-white font-semibold">{{ finding.host }}</span>
            </div>
            <div>
              <span class="text-zinc-500 text-[10px] block">PORT & PROTOKOL:</span>
              <span class="text-white">{{ finding.port }} / {{ finding.protocol }}</span>
            </div>
            <div>
              <span class="text-zinc-500 text-[10px] block">ENDPOINT PATH:</span>
              <span class="text-zinc-300 break-all">{{ finding.endpoint }}</span>
            </div>
            <div>
              <span class="text-zinc-500 text-[10px] block">SCANNER SOURCE:</span>
              <span class="text-blue-400">{{ finding.scanner }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Description, Remediation, and PoC Tabs -->
      <div class="rounded-xl border border-border bg-surface overflow-hidden">
        <div class="border-b border-border bg-surface-elevated flex text-xs font-medium">
          <button
            @click="activeTab = 'description'"
            :class="[
              'px-5 py-3 border-b-2 transition-colors',
              activeTab === 'description'
                ? 'border-blue-500 text-white bg-surface font-semibold'
                : 'border-transparent text-zinc-400 hover:text-white'
            ]"
          >
            Analisis Teknis & Dampak
          </button>
          <button
            @click="activeTab = 'remediation'"
            :class="[
              'px-5 py-3 border-b-2 transition-colors',
              activeTab === 'remediation'
                ? 'border-blue-500 text-white bg-surface font-semibold'
                : 'border-transparent text-zinc-400 hover:text-white'
            ]"
          >
            Langkah Mitigasi & Panduan Remediasi
          </button>
          <button
            @click="activeTab = 'poc'"
            :class="[
              'px-5 py-3 border-b-2 transition-colors',
              activeTab === 'poc'
                ? 'border-blue-500 text-white bg-surface font-semibold'
                : 'border-transparent text-zinc-400 hover:text-white'
            ]"
          >
            Bukti Eksekusi (PoC Evidence)
          </button>
        </div>

        <div class="p-6 text-xs sm:text-sm text-zinc-300 leading-relaxed">
          <div v-if="activeTab === 'description'" class="space-y-4">
            <div>
              <h4 class="font-semibold text-white text-sm mb-1.5">Penjelasan Kerentanan:</h4>
              <p>{{ finding.description }}</p>
            </div>
            <div>
              <h4 class="font-semibold text-white text-sm mb-1.5">Dampak Bisnis (Impact):</h4>
              <p>{{ finding.businessImpact }}</p>
            </div>
          </div>

          <div v-else-if="activeTab === 'remediation'" class="space-y-4">
            <div>
              <h4 class="font-semibold text-white text-sm mb-1.5">Saran Perbaikan Developer:</h4>
              <p>{{ finding.remediation }}</p>
            </div>
            <div class="p-3 rounded-lg bg-blue-950/20 border border-blue-900/40 text-blue-200 text-xs">
              <strong>Catatan Kepatuhan:</strong> Setelah perbaikan di-deploy ke production, jadwalkan pemindaian ulang via CLI <code>vulnflow scan --target {{ finding.host }}</code> untuk memverifikasi remediate.
            </div>
          </div>

          <div v-else-if="activeTab === 'poc'" class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-white text-sm">Muatan Bukti Serangan (PoC):</span>
              <span class="text-xs font-mono text-zinc-500">DECRYPTED PREVIEW</span>
            </div>
            <div class="rounded-lg bg-black/80 border border-border p-4 font-mono text-xs text-zinc-300 overflow-x-auto">
              <pre>{{ finding.poc }}</pre>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- PoC Decryption Modal (UC-04a Desweb) -->
    <div
      v-if="showDecryptModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
    >
      <div class="w-full max-w-lg rounded-xl border border-border bg-surface p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-border pb-3">
          <div class="flex items-center space-x-2 text-emerald-400">
            <Key class="h-4 w-4" />
            <h3 class="text-sm font-bold text-white">Dekripsi PoC At-Rest (AES-256-GCM)</h3>
          </div>
          <button @click="showDecryptModal = false" class="text-zinc-400 hover:text-white">
            <X class="h-4 w-4" />
          </button>
        </div>

        <p class="text-xs text-zinc-400 leading-relaxed">
          Di backend PostgreSQL, kolom <code>encrypted_raw_evidence</code> disimpan terenkripsi dengan AES-256-GCM menggunakan IV/Nonce acak 96-bit dan 128-bit authentication tag.
        </p>

        <div class="space-y-2">
          <label class="text-[11px] font-mono text-zinc-400 block">SIMULASI ENCRYPTION MASTER KEY:</label>
          <input
            type="text"
            readonly
            value="9EL3Yj4ANNfiuFYY7zBoYc6XLnoD3GZpcBc6lWGLL9U="
            class="w-full bg-background border border-border rounded px-3 py-1.5 text-xs font-mono text-zinc-400 select-all"
          />
        </div>

        <div class="p-3 rounded-lg bg-black/80 border border-zinc-800 space-y-1 font-mono text-[11px]">
          <div class="text-emerald-400">// DECRYPTED EVIDENCE RESULT:</div>
          <div class="text-zinc-300 break-all">{{ finding.poc }}</div>
        </div>

        <div class="flex justify-end pt-2">
          <button
            @click="showDecryptModal = false"
            class="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-500"
          >
            Tutup Dialog
          </button>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'
import { ArrowLeft, Key, ShieldAlert, Server, X } from 'lucide-vue-next'
import { mockFindings } from '@/services/mockData'

const route = useRoute()
const activeTab = ref<'description' | 'remediation' | 'poc'>('description')
const showDecryptModal = ref(false)

const finding = computed(() => {
  const id = route.params.id as string
  return mockFindings.find((f) => f.id === id) || mockFindings[0]
})

const getSeverityClass = (sev: string) => {
  switch (sev) {
    case 'CRITICAL':
      return 'bg-red-500/10 text-red-400 border-red-500/20'
    case 'HIGH':
      return 'bg-orange-500/10 text-orange-400 border-orange-500/20'
    case 'MEDIUM':
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
    case 'LOW':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    default:
      return 'bg-zinc-800 text-zinc-300 border-zinc-700'
  }
}
</script>
