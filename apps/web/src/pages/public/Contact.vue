<template>
  <div class="flex flex-col min-h-screen">
    <Navbar />

    <section class="py-12 border-b border-border bg-gradient-to-b from-blue-950/10 to-background">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="max-w-3xl space-y-2">
          <div class="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400 text-xs font-mono">
            <span>KALKULATOR & SIMULATOR LEAD-GEN AUDIT</span>
          </div>
          <h1 class="text-3xl font-extrabold text-white tracking-tight">Booking Audit Keamanan Siber</h1>
          <p class="text-sm text-zinc-400">
            Hitung estimasi investasi audit penetration testing secara transparan berdasarkan jumlah aset target, lengkapi formulir NDA, dan simulasikan checkout via Midtrans Snap.
          </p>
        </div>
      </div>
    </section>

    <!-- Main Booking Section (UC-05 Desweb) -->
    <section class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- Left: Asset Slider & Calculator (5 cols) -->
        <div class="lg:col-span-5 space-y-6">
          <div class="rounded-xl border border-border bg-surface p-6 space-y-6">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <Sliders class="h-4 w-4 text-blue-400" />
              <span>1. Estimasi Lingkup Aset (Scope)</span>
            </h3>

            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-xs font-medium text-zinc-300">Jumlah Target (IP / FQDN / Endpoint):</label>
                <span class="text-lg font-bold text-blue-400 font-mono">{{ assetCount }} Aset</span>
              </div>

              <!-- Interactive Slider -->
              <input
                v-model.number="assetCount"
                type="range"
                min="1"
                max="50"
                step="1"
                class="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />

              <div class="flex justify-between text-[10px] text-zinc-500 font-mono">
                <span>1 Target</span>
                <span>25 Target</span>
                <span>50 Target</span>
              </div>
            </div>

            <!-- Cost Calculation Breakdown -->
            <div class="p-4 rounded-lg bg-surface-elevated border border-border space-y-2.5 font-mono text-xs">
              <div class="flex justify-between text-zinc-400">
                <span>Biaya Dasar Audit:</span>
                <span>Rp {{ formatRupiah(baseFee) }}</span>
              </div>
              <div class="flex justify-between text-zinc-400">
                <span>Investasi Tambahan ({{ assetCount }} target):</span>
                <span>Rp {{ formatRupiah(assetFee) }}</span>
              </div>
              <div class="border-t border-border/80 pt-2 flex justify-between font-bold text-sm text-white">
                <span>Estimasi Total:</span>
                <span class="text-emerald-400">Rp {{ formatRupiah(totalFee) }}</span>
              </div>
            </div>

            <div class="text-[11px] text-zinc-500 leading-relaxed">
              * Termasuk laporan eksekutif PDF bersertifikat, ringkasan AI Zero-PoC, dan 1x sesi re-test remediasi gratis dalam rentang waktu 30 hari.
            </div>
          </div>
        </div>

        <!-- Right: NDA Form & Booking Submission (7 cols) -->
        <div class="lg:col-span-7">
          <form @submit.prevent="handleBookingSubmit" class="rounded-xl border border-border bg-surface p-6 sm:p-8 space-y-5">
            <h3 class="text-base font-bold text-white flex items-center gap-2 border-b border-border pb-3">
              <FileCheck class="h-4 w-4 text-emerald-400" />
              <span>2. Informasi Entitas & Perjanjian NDA</span>
            </h3>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-xs font-medium text-zinc-300">Nama Perusahaan / Organisasi:</label>
                <input
                  v-model="bookingForm.company"
                  type="text"
                  required
                  placeholder="PT Solusi Digital Nusantara"
                  class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div class="space-y-1.5">
                <label class="text-xs font-medium text-zinc-300">Email Narahubung (PIC Security):</label>
                <input
                  v-model="bookingForm.email"
                  type="email"
                  required
                  placeholder="security@perusahaan.com"
                  class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-medium text-zinc-300">Daftar Target Host / FQDN Scope (pisahkan dengan baris):</label>
              <textarea
                v-model="bookingForm.scope"
                rows="3"
                required
                placeholder="app.perusahaan.com&#10;api.perusahaan.com&#10;103.20.15.4"
                class="w-full bg-background border border-border rounded-lg p-3 text-xs font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
              ></textarea>
            </div>

            <!-- NDA Agreement Checkbox -->
            <div class="p-3.5 rounded-lg bg-surface-elevated border border-border space-y-2">
              <label class="flex items-start space-x-2.5 cursor-pointer">
                <input
                  v-model="bookingForm.agreedNDA"
                  type="checkbox"
                  required
                  class="mt-0.5 rounded bg-background border-border text-blue-600 focus:ring-0 focus:ring-offset-0"
                />
                <span class="text-xs text-zinc-300 leading-relaxed">
                  Saya menyatakan memiliki otorisasi penuh atas aset di atas dan menyetujui klausul <strong>Non-Disclosure Agreement (NDA)</strong> serta kepatuhan pemindaian dalam batas Rules of Engagement (ROE).
                </span>
              </label>
            </div>

            <div class="pt-2 flex justify-end">
              <button
                type="submit"
                class="inline-flex items-center space-x-2 rounded-lg bg-blue-600 px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-blue-500/20 hover:bg-blue-500 transition-colors"
              >
                <span>Buka Simulator Pembayaran Midtrans</span>
                <CreditCard class="h-3.5 w-3.5" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>

    <!-- Midtrans Snap Simulation Modal (UC-05a Desweb) -->
    <div
      v-if="showSnapModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
    >
      <div class="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-900 p-6 space-y-5 shadow-2xl">
        <!-- Modal Header -->
        <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div class="flex items-center space-x-2">
            <div class="h-6 w-6 rounded bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs font-mono">
              M
            </div>
            <h3 class="text-sm font-bold text-white">MIDTRANS SECURE PAYMENT (SIMULATOR)</h3>
          </div>
          <button @click="showSnapModal = false" class="text-zinc-400 hover:text-white">
            <X class="h-4 w-4" />
          </button>
        </div>

        <!-- Order Details -->
        <div class="p-3.5 rounded-lg bg-black/50 border border-zinc-800 space-y-1.5 font-mono text-xs">
          <div class="flex justify-between text-zinc-400">
            <span>Order ID:</span>
            <span class="text-white">{{ orderId }}</span>
          </div>
          <div class="flex justify-between text-zinc-400">
            <span>Client:</span>
            <span class="text-white">{{ bookingForm.company }}</span>
          </div>
          <div class="flex justify-between text-zinc-400">
            <span>Scope:</span>
            <span class="text-white">{{ assetCount }} Target Aset</span>
          </div>
          <div class="border-t border-zinc-800 pt-1.5 flex justify-between font-bold text-sm text-emerald-400">
            <span>Total Tagihan:</span>
            <span>Rp {{ formatRupiah(totalFee) }}</span>
          </div>
        </div>

        <!-- Payment Method Selection -->
        <div class="space-y-3">
          <span class="text-xs font-semibold text-zinc-300 block">PILIH METODE PEMBAYARAN:</span>

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
              QRIS / GoPay / ShopeePay
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
              Virtual Account BCA
            </button>
          </div>

          <!-- Method Display -->
          <div v-if="paymentMethod === 'qris'" class="p-4 rounded-lg bg-white flex flex-col items-center justify-center space-y-2">
            <QrCode class="h-32 w-32 text-black" />
            <span class="text-[11px] font-mono text-zinc-600 font-semibold">SCAN DENGAN APLIKASI E-WALLET</span>
          </div>

          <div v-else class="p-4 rounded-lg bg-black/60 border border-zinc-800 space-y-2 font-mono text-xs">
            <div class="text-zinc-400">Nomor Rekening Virtual Account:</div>
            <div class="text-base font-bold text-blue-400 flex items-center justify-between">
              <span>70012-9842103841</span>
              <span class="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">Salin VA</span>
            </div>
            <div class="text-[10px] text-zinc-500">Batas Waktu Pembayaran: 24 Jam</div>
          </div>
        </div>

        <div class="flex justify-between items-center pt-2">
          <span class="text-[10px] font-mono text-zinc-500">SHA-512 Signed Signature</span>
          <button
            @click="simulateSuccess"
            class="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            Simulasikan Sukses (200 OK)
          </button>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'
import { Sliders, FileCheck, CreditCard, X, QrCode } from 'lucide-vue-next'

const assetCount = ref(5)
const baseFee = 2500000
const perAssetFee = 250000

const assetFee = computed(() => assetCount.value * perAssetFee)
const totalFee = computed(() => baseFee + assetFee.value)

const bookingForm = ref({
  company: '',
  email: '',
  scope: '',
  agreedNDA: false,
})

const showSnapModal = ref(false)
const paymentMethod = ref<'qris' | 'va'>('qris')
const orderId = ref('')

const formatRupiah = (val: number) => {
  return new Intl.NumberFormat('id-ID').format(val)
}

const handleBookingSubmit = () => {
  orderId.value = `ORD-DEMO-${Date.now().toString().slice(-6)}`
  showSnapModal.value = true
}

const simulateSuccess = () => {
  alert('Simulasi Webhook Midtrans Sukses! Notifikasi SETTLEMENT terkirim ke sistem.')
  showSnapModal.value = false
}
</script>
