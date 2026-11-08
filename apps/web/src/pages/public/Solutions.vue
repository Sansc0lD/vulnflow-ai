<template>
  <div class="flex flex-col min-h-screen">
    <Navbar />

    <section class="py-12 border-b border-border bg-gradient-to-b from-blue-950/10 to-background">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="max-w-2xl space-y-2">
          <div class="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400 text-xs font-mono">
            <span>KATALOG TRIASE MOCK DATA</span>
          </div>
          <h1 class="text-3xl font-extrabold text-white tracking-tight">Katalog Contoh Temuan Kerentanan</h1>
          <p class="text-sm text-zinc-400">
            Jelajahi simulasi papan triase interaktif master-detail (40/60) untuk melihat standarisasi format temuan Nuclei & Nmap.
          </p>
        </div>
      </div>
    </section>

    <!-- Master-Detail 40/60 Layout (UC-03 Desweb) -->
    <section class="py-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[720px]">
        <!-- Master Column (40% width -> 5 cols on lg) -->
        <div class="lg:col-span-5 flex flex-col rounded-xl border border-border bg-surface overflow-hidden">
          <!-- Filters & Search Bar -->
          <div class="p-3 border-b border-border bg-surface-elevated space-y-2.5">
            <div class="relative">
              <Search class="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Cari kerentanan atau CWE..."
                class="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <!-- Severity Filter Badges -->
            <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono">
              <button
                v-for="sev in ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']"
                :key="sev"
                @click="selectedSeverity = sev"
                :class="[
                  'px-2.5 py-1 rounded text-[11px] font-semibold transition-colors',
                  selectedSeverity === sev
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-800 text-zinc-400 hover:text-white'
                ]"
              >
                {{ sev }}
              </button>
            </div>
          </div>

          <!-- Finding List -->
          <div class="flex-1 overflow-y-auto divide-y divide-border">
            <div
              v-for="item in filteredFindings"
              :key="item.id"
              @click="selectedId = item.id"
              :class="[
                'p-3.5 cursor-pointer transition-colors text-left space-y-1.5',
                selectedId === item.id ? 'bg-blue-950/20 border-l-4 border-l-blue-500' : 'hover:bg-surface-elevated'
              ]"
            >
              <div class="flex items-center justify-between">
                <span
                  :class="[
                    'text-[10px] font-mono font-bold px-2 py-0.5 rounded border',
                    getSeverityClass(item.severity)
                  ]"
                >
                  {{ item.severity }}
                </span>
                <span class="text-xs font-mono font-bold text-zinc-300">CVSS {{ item.cvss }}</span>
              </div>

              <h4 class="text-xs font-semibold text-white line-clamp-1">{{ item.title }}</h4>

              <div class="flex items-center justify-between text-[11px] text-zinc-400 font-mono">
                <span>{{ item.cwe }}</span>
                <span>{{ item.scanner }}</span>
              </div>
            </div>

            <div v-if="filteredFindings.length === 0" class="p-8 text-center text-xs text-zinc-500">
              Tidak ada temuan yang cocok dengan filter.
            </div>
          </div>
        </div>

        <!-- Detail Column (60% width -> 7 cols on lg) -->
        <div class="lg:col-span-7 flex flex-col rounded-xl border border-border bg-surface overflow-hidden p-6 space-y-6">
          <div class="flex items-start justify-between border-b border-border pb-4">
            <div class="space-y-1.5">
              <div class="flex items-center space-x-2">
                <span
                  :class="[
                    'text-xs font-mono font-bold px-2 py-0.5 rounded border',
                    getSeverityClass(selectedFinding.severity)
                  ]"
                >
                  {{ selectedFinding.severity }}
                </span>
                <span class="text-xs text-zinc-400 font-mono">{{ selectedFinding.cwe }}</span>
                <span class="text-xs text-zinc-500">•</span>
                <span class="text-xs text-zinc-400 font-mono">{{ selectedFinding.scanner }}</span>
              </div>
              <h2 class="text-lg font-bold text-white">{{ selectedFinding.title }}</h2>
            </div>

            <router-link
              :to="`/solutions/${selectedFinding.id}`"
              class="inline-flex items-center space-x-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-blue-500 transition-colors shrink-0"
            >
              <span>Lihat Detail & PoC</span>
              <ArrowRight class="h-3.5 w-3.5" />
            </router-link>
          </div>

          <!-- Finding Metrics Grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div class="p-3 rounded-lg bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">CVSS SCORE</span>
              <span class="text-base font-bold text-white">{{ selectedFinding.cvss }} / 10.0</span>
            </div>
            <div class="p-3 rounded-lg bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">TARGET HOST</span>
              <span class="text-xs text-white truncate block">{{ selectedFinding.host }}</span>
            </div>
            <div class="p-3 rounded-lg bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">PORT / PROTOKOL</span>
              <span class="text-xs text-white block">{{ selectedFinding.port }} / {{ selectedFinding.protocol }}</span>
            </div>
            <div class="p-3 rounded-lg bg-surface-elevated border border-border">
              <span class="text-zinc-500 text-[10px] block">STATUS TRIASE</span>
              <span class="text-xs text-emerald-400 block font-semibold">{{ selectedFinding.status }}</span>
            </div>
          </div>

          <!-- Description & Impact -->
          <div class="space-y-3 text-xs leading-relaxed text-zinc-300">
            <div>
              <h4 class="font-semibold text-white mb-1">Deskripsi Teknis:</h4>
              <p>{{ selectedFinding.description }}</p>
            </div>

            <div>
              <h4 class="font-semibold text-white mb-1">Dampak Bisnis (Business Impact):</h4>
              <p>{{ selectedFinding.businessImpact }}</p>
            </div>

            <div>
              <h4 class="font-semibold text-white mb-1">Rekomendasi Remediasi Standar:</h4>
              <p>{{ selectedFinding.remediation }}</p>
            </div>
          </div>

          <!-- CVSS Vector String -->
          <div class="mt-auto pt-4 border-t border-border flex items-center justify-between text-xs font-mono text-zinc-400">
            <span>VEKTOR CVSS: {{ selectedFinding.vector }}</span>
            <span class="text-[11px] text-zinc-500">ID: {{ selectedFinding.id }}</span>
          </div>
        </div>
      </div>
    </section>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'
import { Search, ArrowRight } from 'lucide-vue-next'
import { mockFindings, MockFinding } from '@/services/mockData'

const searchQuery = ref('')
const selectedSeverity = ref('ALL')
const selectedId = ref('VF-001')

const filteredFindings = computed(() => {
  return mockFindings.filter((item) => {
    const matchQuery =
      item.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      item.cwe.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchSev =
      selectedSeverity.value === 'ALL' || item.severity === selectedSeverity.value
    return matchQuery && matchSev
  })
})

const selectedFinding = computed(() => {
  return mockFindings.find((f) => f.id === selectedId.value) || mockFindings[0]
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
