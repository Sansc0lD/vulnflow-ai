<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-bold text-white">Manajemen Proyek Audit & Target Scope ROE</h1>
        <p class="text-xs text-zinc-400 font-mono">WORKSPACE: Agensi Pentest Nusantara</p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white">Daftar Proyek Audit Aktif</h2>
          <p class="text-xs text-zinc-400">Tentukan batas cakupan (target scope) dan rentang waktu Rules of Engagement (ROE).</p>
        </div>

        <button
          @click="showCreateModal = true"
          class="inline-flex items-center space-x-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
        >
          <Plus class="h-3.5 w-3.5" />
          <span>Buat Proyek Audit Baru</span>
        </button>
      </div>

      <!-- Project Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="p in projects"
          :key="p.id"
          class="rounded-xl border border-border bg-surface p-5 space-y-4 hover:border-zinc-700 transition-colors"
        >
          <div class="flex items-start justify-between border-b border-border pb-3">
            <div class="space-y-0.5">
              <span class="text-[10px] font-mono text-zinc-500 block">ID: {{ p.id }}</span>
              <h3 class="text-sm font-bold text-white">{{ p.name }}</h3>
              <p class="text-xs text-zinc-400">{{ p.client }}</p>
            </div>
            <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              ROE AKTIF
            </span>
          </div>

          <div class="space-y-2 text-xs font-mono">
            <div>
              <span class="text-zinc-500 text-[10px] block">RENTANG ROE (TIMESTAMPTZ, EC-05):</span>
              <span class="text-zinc-300">{{ p.roeStart }} s.d. {{ p.roeEnd }}</span>
            </div>

            <div>
              <span class="text-zinc-500 text-[10px] block">TARGET SCOPE WHITELIST:</span>
              <div class="flex flex-wrap gap-1 mt-1">
                <span
                  v-for="(target, i) in p.scope"
                  :key="i"
                  class="px-2 py-0.5 rounded bg-surface-elevated border border-border text-[11px] text-zinc-300"
                >
                  {{ target }}
                </span>
              </div>
            </div>
          </div>

          <div class="border-t border-border pt-3 flex items-center justify-between">
            <router-link
              to="/app/triage"
              class="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <span>Buka Triase Temuan</span>
              <ArrowRight class="h-3 w-3" />
            </router-link>

            <button
              @click="handleCopyApiKey(p.apiKey)"
              class="text-[11px] font-mono text-zinc-400 hover:text-white px-2 py-1 rounded bg-surface-elevated border border-border"
            >
              Salin API Key CLI
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Project Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
    >
      <div class="w-full max-w-lg rounded-xl border border-border bg-surface p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-border pb-3">
          <h3 class="text-sm font-bold text-white">Inisialisasi Proyek Audit & Definisi ROE</h3>
          <button @click="showCreateModal = false" class="text-zinc-400 hover:text-white">
            <X class="h-4 w-4" />
          </button>
        </div>

        <form @submit.prevent="handleCreateProject" class="space-y-4 text-xs">
          <div class="space-y-1">
            <label class="font-medium text-zinc-300">Nama Proyek:</label>
            <input
              v-model="newProject.name"
              type="text"
              required
              placeholder="Audit Core Banking Web 2026"
              class="w-full bg-background border border-border rounded-lg px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="space-y-1">
            <label class="font-medium text-zinc-300">Nama Klien / Organisasi:</label>
            <input
              v-model="newProject.client"
              type="text"
              required
              placeholder="PT Bank Bukopin Tbk"
              class="w-full bg-background border border-border rounded-lg px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="font-medium text-zinc-300">Tanggal Mulai ROE:</label>
              <input
                v-model="newProject.roeStart"
                type="date"
                required
                class="w-full bg-background border border-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div class="space-y-1">
              <label class="font-medium text-zinc-300">Tanggal Selesai ROE:</label>
              <input
                v-model="newProject.roeEnd"
                type="date"
                required
                class="w-full bg-background border border-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div class="space-y-1">
            <label class="font-medium text-zinc-300">Target Scope Whitelist (pisahkan baris):</label>
            <textarea
              v-model="newProject.scopeRaw"
              rows="3"
              required
              placeholder="*.bukopin.co.id&#10;103.20.15.0/24"
              class="w-full bg-background border border-border rounded-lg p-3 font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-2 pt-2 border-t border-border">
            <button
              type="button"
              @click="showCreateModal = false"
              class="px-4 py-2 rounded-lg border border-border text-zinc-400 hover:text-white"
            >
              Batal
            </button>
            <button
              type="submit"
              class="px-4 py-2 rounded-lg bg-blue-600 font-semibold text-white hover:bg-blue-500"
            >
              Simpan & Dapatkan API Key
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { Plus, ArrowRight, X } from 'lucide-vue-next'

const showCreateModal = ref(false)

const projects = ref([
  {
    id: 'PRJ-01',
    name: 'Audit Core Banking Web 2026',
    client: 'PT Bank Bukopin Tbk',
    roeStart: '2026-10-01',
    roeEnd: '2026-11-30',
    scope: ['*.bukopin.co.id', '103.20.15.0/24', 'api.bukopin.co.id'],
    apiKey: 'vf_live_8f3a129d8b7462a8c19e482b7194fbc2',
  },
  {
    id: 'PRJ-02',
    name: 'Mobile Gateway API Assessment',
    client: 'Fintech Nusantara Ltd',
    roeStart: '2026-10-15',
    roeEnd: '2026-11-15',
    scope: ['api.fintech-nusantara.com', '192.168.10.0/24'],
    apiKey: 'vf_live_2e718b9c440a12f93e8174cb81204d19',
  },
])

const newProject = ref({
  name: '',
  client: '',
  roeStart: '2026-11-01',
  roeEnd: '2026-12-01',
  scopeRaw: '*.client.com\n10.0.0.0/16',
})

const handleCreateProject = () => {
  const scopeList = newProject.value.scopeRaw
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)

  projects.value.push({
    id: `PRJ-0${projects.value.length + 1}`,
    name: newProject.value.name,
    client: newProject.value.client,
    roeStart: newProject.value.roeStart,
    roeEnd: newProject.value.roeEnd,
    scope: scopeList,
    apiKey: `vf_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
  })

  showCreateModal.value = false
}

const handleCopyApiKey = (key: string) => {
  navigator.clipboard.writeText(key)
  alert('API Key berhasil disalin ke clipboard! Gunakan: vulnflow configure --token ' + key)
}
</script>
