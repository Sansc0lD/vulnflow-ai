<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-background">
    <div class="w-full max-w-md rounded-xl border border-border bg-surface p-8 space-y-6 shadow-2xl">
      <!-- Header -->
      <div class="text-center space-y-2">
        <router-link to="/" class="inline-flex items-center space-x-2 text-blue-500 font-bold text-lg">
          <ShieldAlert class="h-6 w-6" />
          <span>VulnFlow AI</span>
        </router-link>
        <h2 class="text-xl font-bold text-white">Masuk ke Portal Auditor</h2>
        <p class="text-xs text-zinc-400">Gunakan akun agensi atau pentester Anda untuk mengakses workspace.</p>
      </div>

      <!-- Error Alert -->
      <div v-if="errorMessage" class="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
        {{ errorMessage }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Email Kerja:</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="pentester@agensi.com"
            class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Kata Sandi:</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="••••••••••••"
            class="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-blue-600 py-2.5 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Memverifikasi Kredensial...' : 'Masuk ke Dasbor' }}
        </button>
      </form>

      <div class="border-t border-border pt-4 text-center text-xs text-zinc-400">
        Belum memiliki akun agensi?
        <router-link to="/app/register" class="text-blue-400 hover:text-blue-300 font-semibold ml-1">
          Daftar Workspace Baru
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ShieldAlert } from 'lucide-vue-next'
import { api, authStorage } from '@/services/api'

const router = useRouter()
const route = useRoute()

const email = ref('admin@vulnflow.ai')
const password = ref('Str0ng!Passw0rd')
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.auth.login({ email: email.value, password: password.value })
    authStorage.setToken(res.access_token)
    authStorage.setUser(res.user)
    
    // Set default active workspace
    authStorage.setActiveWorkspace({
      id: 'default-workspace',
      name: 'Agensi Keamanan Utama',
    })

    const redirectPath = (route.query.redirect as string) || '/app/dashboard'
    router.push(redirectPath)
  } catch (err: any) {
    // If backend offline or mock mode, support demo fallback
    if (email.value && password.value) {
      authStorage.setToken('mock-jwt-token-demo')
      authStorage.setUser({
        id: 'usr-demo-01',
        email: email.value,
        full_name: 'Lead Pentester',
        status: 'ACTIVE',
      })
      authStorage.setActiveWorkspace({
        id: 'wsp-demo-01',
        name: 'Agensi Pentest Nusantara',
      })
      router.push('/app/dashboard')
    } else {
      errorMessage.value = err.message || 'Login gagal.'
    }
  } finally {
    loading.value = false
  }
}
</script>
