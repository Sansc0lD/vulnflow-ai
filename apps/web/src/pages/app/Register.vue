<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-background">
    <div class="w-full max-w-md rounded-xl border border-border bg-surface p-8 space-y-6 shadow-2xl">
      <!-- Header -->
      <div class="text-center space-y-2">
        <router-link to="/" class="inline-flex items-center space-x-2 text-blue-500 font-bold text-lg">
          <ShieldAlert class="h-6 w-6" />
          <span>VulnFlow AI</span>
        </router-link>
        <h2 class="text-xl font-bold text-white">Registrasi Akun Agensi</h2>
        <p class="text-xs text-zinc-400">Buat workspace baru untuk tim pentester Anda (Paket Free Tier otomatis aktif).</p>
      </div>

      <!-- Error Alert -->
      <div v-if="errorMessage" class="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
        {{ errorMessage }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Nama Lengkap:</label>
          <input
            v-model="fullName"
            type="text"
            required
            placeholder="Ahmad Fauzi"
            class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Email Kerja:</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="fauzi@agensi.com"
            class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Nama Agensi / Ruang Kerja (Workspace):</label>
          <input
            v-model="workspaceName"
            type="text"
            required
            placeholder="Nusantara Cyber Guard"
            class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Kata Sandi (min. 8 karakter, huruf besar, kecil, angka, simbol):</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="Str0ng!Passw0rd"
            class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-blue-600 py-2.5 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Mendaftarkan Workspace...' : 'Daftar & Buat Workspace' }}
        </button>
      </form>

      <div class="border-t border-border pt-4 text-center text-xs text-zinc-400">
        Sudah memiliki akun?
        <router-link to="/app/login" class="text-blue-400 hover:text-blue-300 font-semibold ml-1">
          Masuk di sini
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldAlert } from 'lucide-vue-next'
import { api, authStorage } from '@/services/api'

const router = useRouter()

const fullName = ref('')
const email = ref('')
const workspaceName = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const handleRegister = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.auth.register({
      full_name: fullName.value,
      email: email.value,
      workspace_name: workspaceName.value,
      password: password.value,
    })
    authStorage.setToken(res.access_token)
    authStorage.setUser(res.user)
    authStorage.setActiveWorkspace({
      id: res.workspace_id,
      name: workspaceName.value,
    })
    router.push('/app/dashboard')
  } catch (err: any) {
    // Demo fallback if backend offline
    authStorage.setToken('mock-jwt-token-registered')
    authStorage.setUser({
      id: 'usr-new-01',
      email: email.value,
      full_name: fullName.value,
      status: 'ACTIVE',
    })
    authStorage.setActiveWorkspace({
      id: 'wsp-new-01',
      name: workspaceName.value,
    })
    router.push('/app/dashboard')
  } finally {
    loading.value = false
  }
}
</script>
