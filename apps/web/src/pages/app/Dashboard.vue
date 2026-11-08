<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-bold text-white">Dasbor Utama & Sebaran Metrik CVSS (WF1)</h1>
        <p class="text-xs text-zinc-400 font-mono">PROJECT: PRJ-01 > BANK BUKOPIN AUDIT</p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Quick Action Buttons (SDD §4.2.1) -->
      <div class="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-border bg-surface">
        <div class="flex items-center space-x-2">
          <span class="text-xs font-mono font-semibold text-zinc-400">TINDAKAN CEPAT:</span>
        </div>
        <div class="flex flex-wrap items-center gap-2.5">
          <router-link
            to="/app/ai-review"
            class="inline-flex items-center space-x-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
          >
            <Sparkles class="h-3.5 w-3.5" />
            <span>Jalankan AI Ghostwriter</span>
          </router-link>

          <router-link
            to="/app/triage"
            class="inline-flex items-center space-x-1.5 rounded-lg border border-border bg-surface-elevated px-3.5 py-1.5 text-xs font-semibold text-zinc-200 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <CheckSquare class="h-3.5 w-3.5" />
            <span>Papan Triase Temuan</span>
          </router-link>

          <router-link
            to="/app/theme"
            class="inline-flex items-center space-x-1.5 rounded-lg border border-border bg-surface-elevated px-3.5 py-1.5 text-xs font-semibold text-zinc-200 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <FileText class="h-3.5 w-3.5" />
            <span>Export PDF (Pro White-label)</span>
          </router-link>
        </div>
      </div>

      <!-- Overview Stats Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="p-5 rounded-xl border border-border bg-surface space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-zinc-400">Total Kerentanan</span>
            <AlertTriangle class="h-4 w-4 text-zinc-500" />
          </div>
          <div class="text-2xl font-bold text-white font-mono">19 Temuan</div>
          <p class="text-[11px] text-zinc-500">Terkonsolidasi dari Nmap & Nuclei</p>
        </div>

        <div class="p-5 rounded-xl border border-border bg-surface space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-zinc-400">Kepatuhan Scope ROE</span>
            <ShieldCheck class="h-4 w-4 text-emerald-400" />
          </div>
          <div class="text-2xl font-bold text-emerald-400 font-mono">100% Valid</div>
          <p class="text-[11px] text-zinc-500">0 temuan out-of-scope terkarantina</p>
        </div>

        <div class="p-5 rounded-xl border border-border bg-surface space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-zinc-400">Kurasi untuk Laporan</span>
            <BookmarkCheck class="h-4 w-4 text-blue-400" />
          </div>
          <div class="text-2xl font-bold text-blue-400 font-mono">15 Temuan</div>
          <p class="text-[11px] text-zinc-500">4 ditandai FALSE_POSITIVE (uncheck)</p>
        </div>

        <div class="p-5 rounded-xl border border-border bg-surface space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-zinc-400">Katalog Narasi AI</span>
            <Sparkles class="h-4 w-4 text-purple-400" />
          </div>
          <div class="text-2xl font-bold text-purple-400 font-mono">Siap Review</div>
          <p class="text-[11px] text-zinc-500">Zero-PoC Sanitized • Gemini 2.0</p>
        </div>
      </div>

      <!-- CVSS Distribution Breakdown & Recent Activity (SDD §4.2.1) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- CVSS Breakdown Card (7 cols) -->
        <div class="lg:col-span-7 rounded-xl border border-border bg-surface p-6 space-y-5">
          <div class="flex items-center justify-between border-b border-border pb-3">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 class="h-4 w-4 text-blue-400" />
              <span>Distribusi Tingkat Keparahan CVSS v3.1</span>
            </h3>
            <span class="text-xs font-mono text-zinc-400">Total: 19 Temuan</span>
          </div>

          <div class="space-y-4">
            <!-- Critical -->
            <div class="space-y-1.5">
              <div class="flex justify-between text-xs font-mono">
                <span class="text-red-400 font-semibold flex items-center gap-1.5">
                  <span class="h-2 w-2 rounded-full bg-red-500"></span>
                  CRITICAL (CVSS 9.0 - 10.0)
                </span>
                <span class="text-white font-bold">2 Temuan (10.5%)</span>
              </div>
              <div class="h-2.5 rounded-full bg-zinc-800 overflow-hidden">
                <div class="h-full bg-red-500 rounded-full" style="width: 10.5%"></div>
              </div>
            </div>

            <!-- High -->
            <div class="space-y-1.5">
              <div class="flex justify-between text-xs font-mono">
                <span class="text-orange-400 font-semibold flex items-center gap-1.5">
                  <span class="h-2 w-2 rounded-full bg-orange-500"></span>
                  HIGH (CVSS 7.0 - 8.9)
                </span>
                <span class="text-white font-bold">5 Temuan (26.3%)</span>
              </div>
              <div class="h-2.5 rounded-full bg-zinc-800 overflow-hidden">
                <div class="h-full bg-orange-500 rounded-full" style="width: 26.3%"></div>
              </div>
            </div>

            <!-- Medium -->
            <div class="space-y-1.5">
              <div class="flex justify-between text-xs font-mono">
                <span class="text-yellow-400 font-semibold flex items-center gap-1.5">
                  <span class="h-2 w-2 rounded-full bg-yellow-500"></span>
                  MEDIUM (CVSS 4.0 - 6.9)
                </span>
                <span class="text-white font-bold">8 Temuan (42.1%)</span>
              </div>
              <div class="h-2.5 rounded-full bg-zinc-800 overflow-hidden">
                <div class="h-full bg-yellow-500 rounded-full" style="width: 42.1%"></div>
              </div>
            </div>

            <!-- Low -->
            <div class="space-y-1.5">
              <div class="flex justify-between text-xs font-mono">
                <span class="text-emerald-400 font-semibold flex items-center gap-1.5">
                  <span class="h-2 w-2 rounded-full bg-emerald-500"></span>
                  LOW (CVSS 0.1 - 3.9)
                </span>
                <span class="text-white font-bold">4 Temuan (21.1%)</span>
              </div>
              <div class="h-2.5 rounded-full bg-zinc-800 overflow-hidden">
                <div class="h-full bg-emerald-500 rounded-full" style="width: 21.1%"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Scanner Activity (5 cols) -->
        <div class="lg:col-span-5 rounded-xl border border-border bg-surface p-6 space-y-4">
          <div class="flex items-center justify-between border-b border-border pb-3">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <Activity class="h-4 w-4 text-emerald-400" />
              <span>Aktivitas Ingesti Pemindaian</span>
            </h3>
            <span class="text-[10px] font-mono text-zinc-500">LIVE FEED</span>
          </div>

          <div class="space-y-3 font-mono text-xs">
            <div class="p-3 rounded-lg bg-surface-elevated border border-border space-y-1">
              <div class="flex justify-between text-[11px]">
                <span class="text-blue-400 font-bold">NUCLEI SCAN v3.11</span>
                <span class="text-zinc-500">14:20 WIB</span>
              </div>
              <div class="text-zinc-300">14 temuan terunggah • 2 duplikat tersaring</div>
              <div class="text-[10px] text-zinc-500">Idempotency-Key: chunk-001 (Processed)</div>
            </div>

            <div class="p-3 rounded-lg bg-surface-elevated border border-border space-y-1">
              <div class="flex justify-between text-[11px]">
                <span class="text-emerald-400 font-bold">NMAP XML v1.04</span>
                <span class="text-zinc-500">11:05 WIB</span>
              </div>
              <div class="text-zinc-300">8 service terekam • 5 port terbuka</div>
              <div class="text-[10px] text-zinc-500">Idempotency-Key: chunk-000 (Processed)</div>
            </div>

            <div class="p-3 rounded-lg bg-surface-elevated border border-border space-y-1">
              <div class="flex justify-between text-[11px]">
                <span class="text-purple-400 font-bold">MANUAL TRIAGE ENTRY</span>
                <span class="text-zinc-500">09:12 WIB</span>
              </div>
              <div class="text-zinc-300">1 temuan bisnis manual ditambahkan</div>
              <div class="text-[10px] text-zinc-500">Auditor: lead-pentester@vulnflow.ai</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/layout/AppLayout.vue'
import {
  Sparkles,
  CheckSquare,
  FileText,
  AlertTriangle,
  ShieldCheck,
  BookmarkCheck,
  BarChart3,
  Activity,
} from 'lucide-vue-next'
</script>
