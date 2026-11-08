<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-bold text-white">Meteran Kuota Real-time & Billing (WF5)</h1>
        <p class="text-xs text-zinc-400 font-mono">WORKSPACE BILLING & USAGE MONITORING</p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Real-time Quota Meter (SDD §4.2.5) -->
      <div class="rounded-xl border border-border bg-surface p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <CreditCard class="h-4 w-4 text-blue-400" />
              <span>Status Langganan Agensi & Penggunaan Kuota</span>
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">Pantau alokasi kuota kompilasi PDF bulanan Anda secara langsung.</p>
          </div>
          <span class="text-xs font-mono font-bold px-3 py-1 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
            PAKET SAAT INI: {{ currentTier }}
          </span>
        </div>

        <div class="space-y-2 font-mono">
          <div class="flex justify-between text-xs">
            <span class="text-zinc-400">Kuota Laporan Terpakai Bulan Ini (UC-15):</span>
            <span class="text-white font-bold">{{ usedReports }} / {{ maxReports }} Laporan</span>
          </div>

          <!-- Progress Bar -->
          <div class="h-3 rounded-full bg-surface-elevated border border-border overflow-hidden">
            <div
              :class="[
                'h-full rounded-full transition-all duration-500',
                usedReports >= maxReports ? 'bg-red-500' : 'bg-blue-500'
              ]"
              :style="{ width: `${(usedReports / maxReports) * 100}%` }"
            ></div>
          </div>
        </div>

        <div v-if="usedReports >= maxReports" class="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span>Kuota laporan bulan ini telah habis (HTTP 402 Payment Required). Upgrade ke paket Agency Pro untuk menambah 30 laporan baru dan mengaktifkan fitur White-label.</span>
        </div>
      </div>

      <!-- Pricing Plans Comparison Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Free Tier -->
        <div class="rounded-xl border border-border bg-surface p-6 flex flex-col justify-between space-y-6">
          <div class="space-y-4">
            <div class="space-y-1">
              <span class="text-[10px] font-mono text-zinc-400 uppercase">TIER 1</span>
              <h3 class="text-lg font-bold text-white">Agency Free</h3>
              <p class="text-xs text-zinc-400">Untuk pentester independen dan uji coba asesmen awal.</p>
            </div>

            <div class="text-2xl font-black text-white font-mono">Rp 0 <span class="text-xs font-normal text-zinc-500">/ bulan</span></div>

            <ul class="space-y-2 text-xs text-zinc-300">
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Maksimal 3 kompilasi laporan PDF / bulan</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Batas 50 temuan per batch upload (EC-10)</span>
              </li>
              <li class="flex items-center gap-2 text-zinc-500">
                <X class="h-4 w-4 text-zinc-600 shrink-0" />
                <span>Watermark VulnFlow AI wajib (tidak bisa dihapus)</span>
              </li>
            </ul>
          </div>

          <button
            disabled
            class="w-full py-2 rounded-lg border border-border bg-surface-elevated text-xs font-semibold text-zinc-400 cursor-not-allowed"
          >
            Paket Aktif Saat Ini
          </button>
        </div>

        <!-- Pro Tier (Recommended / Highlighted) -->
        <div class="rounded-xl border-2 border-blue-500 bg-surface-elevated p-6 flex flex-col justify-between space-y-6 relative shadow-xl shadow-blue-500/10">
          <div class="absolute -top-3 right-5 px-2.5 py-0.5 rounded-full bg-blue-600 text-white font-mono text-[10px] font-bold">
            RECOMMENDED
          </div>

          <div class="space-y-4">
            <div class="space-y-1">
              <span class="text-[10px] font-mono text-blue-400 uppercase">TIER 2</span>
              <h3 class="text-lg font-bold text-white">Agency Pro</h3>
              <p class="text-xs text-zinc-400">Dirancang khusus untuk agensi konsultansi keamanan siber profesional.</p>
            </div>

            <div class="text-2xl font-black text-white font-mono">Rp 750.000 <span class="text-xs font-normal text-zinc-500">/ bulan</span></div>

            <ul class="space-y-2 text-xs text-zinc-300">
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>30 kompilasi laporan PDF eksekutif / bulan</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>White-labeling penuh: Tanpa watermark, logo kustom</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Batas upload batch hingga 500 temuan</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Dukungan AI Ghostwriter Gemini 2.0 berkecepatan tinggi</span>
              </li>
            </ul>
          </div>

          <button
            @click="openUpgradeModal"
            class="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-lg transition-colors"
          >
            Upgrade ke Agency Pro (Midtrans Snap)
          </button>
        </div>

        <!-- Enterprise Tier -->
        <div class="rounded-xl border border-border bg-surface p-6 flex flex-col justify-between space-y-6">
          <div class="space-y-4">
            <div class="space-y-1">
              <span class="text-[10px] font-mono text-zinc-400 uppercase">TIER 3</span>
              <h3 class="text-lg font-bold text-white">Enterprise</h3>
              <p class="text-xs text-zinc-400">Untuk institusi keuangan, BUMN, dan agensi skala korporat.</p>
            </div>

            <div class="text-2xl font-black text-white font-mono">Hubungi Sales</div>

            <ul class="space-y-2 text-xs text-zinc-300">
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Kompilasi laporan tanpa batas (Unlimited)</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Instalasi On-Premise / Private Cloud VPC</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" />
                <span>Dukungan SLA 24/7 dan Dedicated Security Engineer</span>
              </li>
            </ul>
          </div>

          <router-link
            to="/contact"
            class="w-full py-2 rounded-lg border border-border bg-surface-elevated text-xs font-semibold text-zinc-300 hover:text-white text-center block transition-colors"
          >
            Hubungi Konsultan
          </router-link>
        </div>
      </div>
    </div>

    <!-- Midtrans Snap Modal for Agency Pro (UC-16 / Wireframe 5) -->
    <div
      v-if="showSnapModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
    >
      <div class="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-900 p-6 space-y-5 shadow-2xl">
        <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div class="flex items-center space-x-2">
            <div class="h-6 w-6 rounded bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold text-xs font-mono">
              M
            </div>
            <h3 class="text-sm font-bold text-white">MIDTRANS SECURE CHECKOUT (SNAP)</h3>
          </div>
          <button @click="showSnapModal = false" class="text-zinc-400 hover:text-white">
            <X class="h-4 w-4" />
          </button>
        </div>

        <!-- Order Summary -->
        <div class="p-3.5 rounded-lg bg-black/50 border border-zinc-800 space-y-1.5 font-mono text-xs">
          <div class="flex justify-between text-zinc-400">
            <span>Order ID:</span>
            <span class="text-white">{{ orderId }}</span>
          </div>
          <div class="flex justify-between text-zinc-400">
            <span>Item:</span>
            <span class="text-white">Agency Pro Subscription (1 Bulan)</span>
          </div>
          <div class="border-t border-zinc-800 pt-1.5 flex justify-between font-bold text-sm text-emerald-400">
            <span>Total Tagihan:</span>
            <span>Rp 750.000</span>
          </div>
        </div>

        <!-- Payment Channel -->
        <div class="space-y-3">
          <span class="text-xs font-semibold text-zinc-300 block">METODE PEMBAYARAN:</span>

          <div class="grid grid-cols-2 gap-2 text-xs font-mono">
            <button
              type="button"
              @click="paymentMethod = 'qris'"
              :class="[
                'p-3 rounded-lg border text-center transition-colors',
                paymentMethod === 'qris'
                  ? 'border-blue-500 bg-blue-950/20 text-blue-400 font-bold'
                  : 'border-zinc-800 bg-zinc-800/50 text-zinc-400 hover:text-white'
              ]"
            >
              QRIS Instant
            </button>
            <button
              type="button"
              @click="paymentMethod = 'va'"
              :class="[
                'p-3 rounded-lg border text-center transition-colors',
                paymentMethod === 'va'
                  ? 'border-blue-500 bg-blue-950/20 text-blue-400 font-bold'
                  : 'border-zinc-800 bg-zinc-800/50 text-zinc-400 hover:text-white'
              ]"
            >
              BCA Virtual Account
            </button>
          </div>

          <div v-if="paymentMethod === 'qris'" class="p-4 rounded-lg bg-white flex flex-col items-center justify-center space-y-2">
            <QrCode class="h-32 w-32 text-black" />
            <span class="text-[11px] font-mono text-zinc-600 font-semibold">SCAN DENGAN APLIKASI E-WALLET / MOBILE BANKING</span>
          </div>

          <div v-else class="p-4 rounded-lg bg-black/60 border border-zinc-800 space-y-2 font-mono text-xs">
            <div class="text-zinc-400">Nomor Rekening Virtual Account:</div>
            <div class="text-base font-bold text-blue-400 flex items-center justify-between">
              <span>70012-9842103841</span>
              <span class="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">Salin VA</span>
            </div>
            <div class="text-[10px] text-zinc-500">Otomatis terverifikasi dalam 1 menit</div>
          </div>
        </div>

        <div class="flex justify-between items-center pt-2">
          <span class="text-[10px] font-mono text-zinc-500">SHA-512 Idempotent Webhook</span>
          <button
            @click="simulateSettlement"
            class="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            Simulasikan Pembayaran Sukses
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { CreditCard, AlertTriangle, Check, X, QrCode } from 'lucide-vue-next'

const currentTier = ref('FREE')
const usedReports = ref(2)
const maxReports = ref(3)

const showSnapModal = ref(false)
const paymentMethod = ref<'qris' | 'va'>('qris')
const orderId = ref('')

const openUpgradeModal = () => {
  orderId.value = `ORD-WSP01-${Date.now().toString().slice(-6)}`
  showSnapModal.value = true
}

const simulateSettlement = () => {
  currentTier.value = 'PRO'
  maxReports.value = 30
  usedReports.value = 0
  showSnapModal.value = false
  alert('Pembayaran terkonfirmasi via Midtrans Webhook (SETTLEMENT)! Workspace Anda kini aktif sebagai Agency Pro.')
}
</script>
