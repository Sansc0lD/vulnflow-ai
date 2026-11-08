<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-bold text-white">White-labeling & Live Preview Sampul Laporan (WF4)</h1>
        <p class="text-xs text-zinc-400 font-mono">WORKSPACE SETTINGS > BRANDING & THEME STUDIO</p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- Settings Form (5 cols) -->
        <div class="lg:col-span-5 space-y-6">
          <div class="rounded-xl border border-border bg-surface p-6 space-y-5">
            <div class="border-b border-border pb-3">
              <h2 class="text-sm font-bold text-white flex items-center gap-2">
                <Palette class="h-4 w-4 text-blue-400" />
                <span>Kustomisasi Brand Agensi (Pro Tier)</span>
              </h2>
              <p class="text-xs text-zinc-400 mt-1">
                Atur palet warna dan logo agensi Anda untuk disematkan pada header, footer, dan sampul PDF WeasyPrint.
              </p>
            </div>

            <!-- Logo Upload -->
            <div class="space-y-2">
              <label class="text-xs font-medium text-zinc-300">Logo Agensi (PNG / SVG Transparan):</label>
              <div class="flex items-center space-x-3">
                <div class="h-12 w-12 rounded-lg bg-surface-elevated border border-border flex items-center justify-center font-bold text-xs font-mono text-blue-400">
                  VF
                </div>
                <button
                  type="button"
                  class="px-3 py-1.5 rounded-lg border border-border bg-surface-elevated text-xs font-medium text-zinc-300 hover:text-white"
                >
                  Ganti Logo Agensi
                </button>
              </div>
            </div>

            <!-- Hex Color Pickers -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-xs font-medium text-zinc-300">Warna Utama (Primary):</label>
                <div class="flex items-center space-x-2">
                  <input
                    v-model="primaryColor"
                    type="color"
                    class="h-8 w-8 rounded border border-border bg-transparent cursor-pointer p-0.5"
                  />
                  <input
                    v-model="primaryColor"
                    type="text"
                    class="w-full bg-background border border-border rounded px-2.5 py-1 text-xs font-mono text-white"
                  />
                </div>
              </div>

              <div class="space-y-1.5">
                <label class="text-xs font-medium text-zinc-300">Warna Aksen (Accent):</label>
                <div class="flex items-center space-x-2">
                  <input
                    v-model="accentColor"
                    type="color"
                    class="h-8 w-8 rounded border border-border bg-transparent cursor-pointer p-0.5"
                  />
                  <input
                    v-model="accentColor"
                    type="text"
                    class="w-full bg-background border border-border rounded px-2.5 py-1 text-xs font-mono text-white"
                  />
                </div>
              </div>
            </div>

            <!-- Confidentiality Notice Text -->
            <div class="space-y-1.5">
              <label class="text-xs font-medium text-zinc-300">Pernyataan Kerahasiaan (Confidentiality Notice):</label>
              <textarea
                v-model="confidentialityText"
                rows="3"
                class="w-full bg-background border border-border rounded-lg p-2.5 text-xs text-zinc-200 focus:outline-none focus:border-blue-500"
              ></textarea>
            </div>

            <div class="pt-2">
              <button
                @click="compilePDF"
                :disabled="isCompiling"
                class="w-full inline-flex items-center justify-center space-x-2 rounded-lg bg-blue-600 py-2.5 text-xs font-semibold text-white shadow hover:bg-blue-500 disabled:opacity-50 transition-colors"
              >
                <FileDown class="h-4 w-4" />
                <span>{{ isCompiling ? 'Memproses Render WeasyPrint (Celery)...' : 'Kompilasi Laporan PDF (Async Celery)' }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Live Cover WYSIWYG Preview (7 cols) -->
        <div class="lg:col-span-7 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-300 font-mono">
              Live Preview Sampul PDF (A4 Ratio)
            </span>
            <span class="text-[10px] font-mono text-zinc-500">WEASYPRINT SAFE-RENDERER</span>
          </div>

          <!-- A4 Mock Paper Canvas -->
          <div class="rounded-xl border border-zinc-700 bg-white text-zinc-900 p-8 sm:p-12 shadow-2xl aspect-[1/1.414] max-w-md mx-auto flex flex-col justify-between">
            <!-- Header on Paper -->
            <div class="flex justify-between items-start border-b pb-4" :style="{ borderColor: primaryColor }">
              <div class="flex items-center space-x-2">
                <div
                  class="h-9 w-9 rounded flex items-center justify-center text-white font-bold text-xs"
                  :style="{ backgroundColor: primaryColor }"
                >
                  VF
                </div>
                <div>
                  <div class="font-bold text-xs text-zinc-900">Agensi Pentest Nusantara</div>
                  <div class="text-[9px] text-zinc-500 font-mono">CONFIDENTIAL AUDIT REPORT</div>
                </div>
              </div>

              <span
                class="text-[9px] font-mono font-bold px-2 py-0.5 rounded text-white"
                :style="{ backgroundColor: accentColor }"
              >
                PRO VERIFIED
              </span>
            </div>

            <!-- Title Section on Paper -->
            <div class="space-y-4 my-auto">
              <div class="text-[10px] font-mono tracking-widest text-zinc-400 uppercase">
                LAPORAN AKHIR ASESMEN KEAMANAN SIBER
              </div>
              <h1 class="text-2xl font-black text-zinc-900 leading-tight" :style="{ color: primaryColor }">
                Vulnerability Assessment & Pentest Report
              </h1>
              <div class="space-y-1 text-xs text-zinc-600">
                <div><strong>Klien:</strong> PT Bank Bukopin Tbk</div>
                <div><strong>Target:</strong> Core Banking Web & API Gateway</div>
                <div><strong>Periode:</strong> 1 Oktober 2026 – 30 November 2026</div>
              </div>
            </div>

            <!-- Footer on Paper -->
            <div class="border-t pt-4 space-y-2 border-zinc-200">
              <p class="text-[9px] text-zinc-500 italic leading-snug">
                {{ confidentialityText }}
              </p>
              <div class="flex justify-between items-center text-[8px] font-mono text-zinc-400">
                <span>Diterbitkan via VulnFlow AI</span>
                <span>Halaman 1 dari 18</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { Palette, FileDown } from 'lucide-vue-next'

const primaryColor = ref('#1e40af')
const accentColor = ref('#0d9488')
const confidentialityText = ref(
  'DOKUMEN SANGAT RAHASIA: Laporan ini hanya ditujukan untuk entitas berwenang PT Bank Bukopin Tbk dan dilarang disebarluaskan tanpa izin tertulis.'
)
const isCompiling = ref(false)

const compilePDF = () => {
  isCompiling.value = true
  setTimeout(() => {
    isCompiling.value = false
    alert('Kompilasi PDF selesai! Presigned URL S3 telah digenerate (HTTP 202 -> 307 Redirect).')
  }, 1800)
}
</script>
