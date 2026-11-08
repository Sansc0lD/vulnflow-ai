<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-bold text-white">Papan Triase & Dekripsi Bukti Teknis PoC (WF2)</h1>
        <p class="text-xs text-zinc-400 font-mono">PROJECT PRJ-01 > VULNERABILITY TRIAGE BOARD</p>
      </div>
    </template>

    <div class="space-y-5 max-w-7xl mx-auto">
      <!-- Toolbar / Filters -->
      <div class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-border bg-surface">
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center space-x-2 text-xs font-mono">
            <span class="text-zinc-400">FILTER SEVERITY:</span>
            <select
              v-model="severityFilter"
              class="bg-background border border-border rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Severities (19)</option>
              <option value="CRITICAL">Critical Only (2)</option>
              <option value="HIGH">High Only (5)</option>
              <option value="MEDIUM">Medium Only (8)</option>
              <option value="LOW">Low Only (4)</option>
            </select>
          </div>

          <div class="flex items-center space-x-2 text-xs font-mono">
            <span class="text-zinc-400">STATUS:</span>
            <select
              v-model="statusFilter"
              class="bg-background border border-border rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">Semua Status</option>
              <option value="OPEN">OPEN</option>
              <option value="IN_REVIEW">IN_REVIEW</option>
              <option value="REMEDIATED">REMEDIATED</option>
              <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
              <option value="ACCEPTED_RISK">ACCEPTED_RISK</option>
            </select>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="showCvssCalcModal = true"
            class="inline-flex items-center space-x-1.5 rounded-lg border border-border bg-surface-elevated px-3 py-1.5 text-xs font-semibold text-zinc-200 hover:text-white"
          >
            <Calculator class="h-3.5 w-3.5 text-blue-400" />
            <span>Kalkulator CVSS v3.1</span>
          </button>
        </div>
      </div>

      <!-- Triage Grid Table (SDD §4.2.2) -->
      <div class="rounded-xl border border-border bg-surface overflow-hidden shadow-xl">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-surface-elevated border-b border-border text-[11px] font-mono text-zinc-400 uppercase">
              <tr>
                <th class="py-3 px-4 w-12 text-center">RPT</th>
                <th class="py-3 px-4 w-24">ID</th>
                <th class="py-3 px-4">Judul Kerentanan</th>
                <th class="py-3 px-4 w-28">Keparahan</th>
                <th class="py-3 px-4 w-20 text-center">CVSS</th>
                <th class="py-3 px-4 w-36">Status Triase</th>
                <th class="py-3 px-4 w-28 text-center">Scope</th>
                <th class="py-3 px-4 w-28 text-center">Bukti PoC</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr
                v-for="f in filteredFindings"
                :key="f.id"
                class="hover:bg-surface-elevated/60 transition-colors"
              >
                <!-- Curated Checkbox (EC-12 auto-uncheck on FALSE_POSITIVE) -->
                <td class="py-3 px-4 text-center">
                  <input
                    type="checkbox"
                    v-model="f.isCurated"
                    :disabled="f.status === 'FALSE_POSITIVE'"
                    class="rounded bg-background border-border text-blue-600 focus:ring-0 cursor-pointer disabled:opacity-30"
                    title="Sertakan dalam PDF Laporan"
                  />
                </td>

                <td class="py-3 px-4 font-mono text-zinc-400">{{ f.id }}</td>

                <td class="py-3 px-4">
                  <div class="font-semibold text-white">{{ f.title }}</div>
                  <div class="text-[11px] text-zinc-400 font-mono flex items-center gap-2 mt-0.5">
                    <span>{{ f.cwe }}</span>
                    <span>•</span>
                    <span>{{ f.endpoint }}</span>
                  </div>
                </td>

                <td class="py-3 px-4">
                  <span
                    :class="[
                      'text-[10px] font-mono font-bold px-2 py-0.5 rounded border',
                      getSeverityClass(f.severity)
                    ]"
                  >
                    {{ f.severity }}
                  </span>
                </td>

                <td class="py-3 px-4 text-center font-mono font-bold text-white">
                  {{ f.cvss }}
                </td>

                <!-- Inline Status Dropdown with Optimistic Lock Version Support -->
                <td class="py-3 px-4">
                  <select
                    v-model="f.status"
                    @change="handleStatusChange(f)"
                    class="bg-background border border-border rounded px-2 py-1 text-xs font-mono text-zinc-200 focus:outline-none focus:border-blue-500 w-full"
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="IN_REVIEW">IN_REVIEW</option>
                    <option value="REMEDIATED">REMEDIATED</option>
                    <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
                    <option value="ACCEPTED_RISK">ACCEPTED_RISK</option>
                  </select>
                </td>

                <td class="py-3 px-4 text-center">
                  <span
                    :class="[
                      'text-[10px] font-mono px-2 py-0.5 rounded border',
                      f.isQuarantined
                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    ]"
                  >
                    {{ f.isQuarantined ? 'QUARANTINE' : 'IN-SCOPE' }}
                  </span>
                </td>

                <td class="py-3 px-4 text-center">
                  <button
                    @click="openPoCModal(f)"
                    class="p-1.5 rounded bg-surface-elevated border border-border text-zinc-300 hover:text-emerald-400 hover:border-emerald-500/30 transition-colors"
                    title="Buka Bukti PoC Terenkripsi"
                  >
                    <Lock class="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- PoC Vault Decryption Modal -->
    <div
      v-if="activePoCFinding"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
    >
      <div class="w-full max-w-lg rounded-xl border border-border bg-surface p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-border pb-3">
          <div class="flex items-center space-x-2 text-emerald-400">
            <Key class="h-4 w-4" />
            <h3 class="text-sm font-bold text-white">PoC Vault: {{ activePoCFinding.id }}</h3>
          </div>
          <button @click="activePoCFinding = null" class="text-zinc-400 hover:text-white">
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="space-y-1 text-xs">
          <span class="text-zinc-400 font-mono text-[10px]">TARGET: {{ activePoCFinding.endpoint }}</span>
          <h4 class="font-bold text-white">{{ activePoCFinding.title }}</h4>
        </div>

        <div class="p-3 rounded-lg bg-black/80 border border-zinc-800 space-y-2 font-mono text-xs">
          <div class="flex justify-between text-[10px] text-zinc-500">
            <span>CIPHER: AES-256-GCM AEAD</span>
            <span>TAG: 128-bit OK</span>
          </div>
          <div class="text-zinc-200 overflow-x-auto whitespace-pre-wrap">{{ activePoCFinding.poc }}</div>
        </div>

        <div class="flex justify-end pt-2">
          <button
            @click="activePoCFinding = null"
            class="px-4 py-2 rounded-lg bg-blue-600 text-xs font-semibold text-white hover:bg-blue-500"
          >
            Tutup Dialog
          </button>
        </div>
      </div>
    </div>

    <!-- CVSS Calculator Modal -->
    <div
      v-if="showCvssCalcModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
    >
      <div class="w-full max-w-xl rounded-xl border border-border bg-surface p-6 space-y-5 shadow-2xl">
        <div class="flex items-center justify-between border-b border-border pb-3">
          <div class="flex items-center space-x-2 text-blue-400">
            <Calculator class="h-4 w-4" />
            <h3 class="text-sm font-bold text-white">Kalkulator Metrik CVSS v3.1 FIRST</h3>
          </div>
          <button @click="showCvssCalcModal = false" class="text-zinc-400 hover:text-white">
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="grid grid-cols-2 gap-4 text-xs font-mono">
          <div class="space-y-1">
            <label class="text-zinc-400 block">Attack Vector (AV):</label>
            <select v-model="calcAV" class="w-full bg-background border border-border rounded px-2 py-1.5 text-white">
              <option value="N">Network (0.85)</option>
              <option value="A">Adjacent (0.62)</option>
              <option value="L">Local (0.55)</option>
              <option value="P">Physical (0.2)</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="text-zinc-400 block">Attack Complexity (AC):</label>
            <select v-model="calcAC" class="w-full bg-background border border-border rounded px-2 py-1.5 text-white">
              <option value="L">Low (0.77)</option>
              <option value="H">High (0.44)</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="text-zinc-400 block">Confidentiality (C):</label>
            <select v-model="calcC" class="w-full bg-background border border-border rounded px-2 py-1.5 text-white">
              <option value="H">High (0.56)</option>
              <option value="L">Low (0.22)</option>
              <option value="N">None (0.0)</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="text-zinc-400 block">Integrity (I):</label>
            <select v-model="calcI" class="w-full bg-background border border-border rounded px-2 py-1.5 text-white">
              <option value="H">High (0.56)</option>
              <option value="L">Low (0.22)</option>
              <option value="N">None (0.0)</option>
            </select>
          </div>
        </div>

        <!-- Calculated Output -->
        <div class="p-4 rounded-lg bg-surface-elevated border border-border flex items-center justify-between">
          <div>
            <span class="text-[10px] font-mono text-zinc-500 block">CALCULATED BASE SCORE:</span>
            <span class="text-2xl font-bold font-mono text-white">{{ calculatedScore }} / 10.0</span>
          </div>
          <span
            :class="[
              'text-xs font-mono font-bold px-3 py-1 rounded border',
              getSeverityClass(calculatedSeverity)
            ]"
          >
            {{ calculatedSeverity }}
          </span>
        </div>

        <div class="flex justify-end pt-2">
          <button
            @click="showCvssCalcModal = false"
            class="px-4 py-2 rounded-lg bg-blue-600 text-xs font-semibold text-white hover:bg-blue-500"
          >
            Terapkan Skor
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { Calculator, Lock, Key, X } from 'lucide-vue-next'

const severityFilter = ref('ALL')
const statusFilter = ref('ALL')
const activePoCFinding = ref<any>(null)
const showCvssCalcModal = ref(false)

const calcAV = ref('N')
const calcAC = ref('L')
const calcC = ref('H')
const calcI = ref('H')

const calculatedScore = computed(() => {
  if (calcC.value === 'H' && calcI.value === 'H') return 9.8
  if (calcC.value === 'H') return 7.5
  return 5.3
})

const calculatedSeverity = computed(() => {
  if (calculatedScore.value >= 9.0) return 'CRITICAL'
  if (calculatedScore.value >= 7.0) return 'HIGH'
  if (calculatedScore.value >= 4.0) return 'MEDIUM'
  return 'LOW'
})

const findings = ref([
  {
    id: 'FND-001',
    title: 'SQL Injection in User Authentication Route',
    cwe: 'CWE-89',
    endpoint: '/api/v1/auth/login',
    severity: 'CRITICAL',
    cvss: 9.8,
    status: 'OPEN',
    isQuarantined: false,
    isCurated: true,
    version: 1,
    poc: "admin' UNION SELECT id, password_hash FROM users--",
  },
  {
    id: 'FND-002',
    title: 'Server-Side Request Forgery via Avatar Importer',
    cwe: 'CWE-918',
    endpoint: '/profile/avatar?url=http://169.254.169.254',
    severity: 'HIGH',
    cvss: 8.6,
    status: 'IN_REVIEW',
    isQuarantined: false,
    isCurated: true,
    version: 2,
    poc: "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
  },
  {
    id: 'FND-003',
    title: 'Stored Cross-Site Scripting in Ticket Notes',
    cwe: 'CWE-79',
    endpoint: '/tickets/notes/create',
    severity: 'MEDIUM',
    cvss: 6.1,
    status: 'FALSE_POSITIVE',
    isQuarantined: false,
    isCurated: false,
    version: 1,
    poc: "<script>alert(document.domain)<\\/script>",
  },
  {
    id: 'FND-004',
    title: 'Exposed Redis Port 6379 Without Password',
    cwe: 'CWE-306',
    endpoint: 'redis://cache.bukopin.co.id:6379',
    severity: 'CRITICAL',
    cvss: 9.8,
    status: 'OPEN',
    isQuarantined: false,
    isCurated: true,
    version: 1,
    poc: "redis-cli -h cache.bukopin.co.id ping -> PONG (No AUTH needed)",
  },
  {
    id: 'FND-005',
    title: 'Out-of-Scope Dev Subdomain Discovered',
    cwe: 'CWE-200',
    endpoint: 'http://internal-staging.dev.othercorp.com',
    severity: 'LOW',
    cvss: 3.1,
    status: 'ACCEPTED_RISK',
    isQuarantined: true,
    isCurated: false,
    version: 1,
    poc: "Subdomain out-of-scope; quarantined automatically (EC-04).",
  },
])

const filteredFindings = computed(() => {
  return findings.value.filter((f) => {
    const matchSev = severityFilter.value === 'ALL' || f.severity === severityFilter.value
    const matchStat = statusFilter.value === 'ALL' || f.status === statusFilter.value
    return matchSev && matchStat
  })
})

const handleStatusChange = (f: any) => {
  // EC-12: If status set to FALSE_POSITIVE, auto-uncheck curated
  if (f.status === 'FALSE_POSITIVE') {
    f.isCurated = false
  }
  // Optimistic lock increment
  f.version += 1
}

const openPoCModal = (f: any) => {
  activePoCFinding.value = f
}

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
