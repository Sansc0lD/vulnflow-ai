<template>
  <AuthShell>
    <div class="space-y-1.5">
      <h2 class="text-xl sm:text-2xl font-display font-semibold text-[#F5F5F3]">Sign in</h2>
      <p class="text-xs sm:text-sm text-[#8A8D96]">
        Enter your credentials to access your workspaces and active reports.
      </p>
    </div>

    <div
      v-if="errorMessage"
      role="alert"
      class="p-3.5 bg-red-500/10 border border-red-400/35 text-red-200 text-xs leading-relaxed"
    >
      {{ errorMessage }}
    </div>

    <div
      v-if="mfaRequired"
      role="status"
      class="p-3.5 bg-amber-500/10 border border-amber-400/35 text-amber-200 text-xs space-y-1"
    >
      <div class="font-semibold flex items-center gap-1.5">
        <KeyRound class="h-4 w-4 text-amber-300" aria-hidden="true" />
        <span>Two-factor authentication required</span>
      </div>
      <p class="text-[#D4D4D8] leading-relaxed">
        Enter the 6-digit verification code from your authenticator app to continue.
      </p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div class="space-y-1.5">
        <label for="login-email" class="text-xs font-medium text-[#D4D4D8] block">Work email</label>
        <input
          id="login-email"
          v-model.trim="email"
          type="email"
          required
          autocomplete="email"
          placeholder="you@company.com"
          class="w-full input-glass px-3 py-2.5 text-xs sm:text-sm"
        />
      </div>

      <div class="space-y-1.5">
        <div class="flex items-center justify-between">
          <label for="login-password" class="text-xs font-medium text-[#D4D4D8]">Password</label>
          <router-link to="/app/forgot-password" class="text-xs text-[#F5F5F3] underline underline-offset-4 hover:text-white">
            Forgot password?
          </router-link>
        </div>
        <div class="relative">
          <input
            id="login-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            autocomplete="current-password"
            placeholder="••••••••••••"
            class="w-full input-glass pl-3 pr-10 py-2.5 text-xs sm:text-sm"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-[#8A8D96] hover:text-[#F5F5F3]"
          >
            <EyeOff v-if="showPassword" class="h-4 w-4" />
            <Eye v-else class="h-4 w-4" />
          </button>
        </div>
      </div>

      <div v-if="mfaRequired" class="space-y-1.5">
        <label for="login-totp" class="text-xs font-medium text-amber-200 block">
          6-digit verification code
        </label>
        <input
          id="login-totp"
          ref="totpInputRef"
          v-model.trim="totpCode"
          type="text"
          inputmode="numeric"
          autocomplete="one-time-code"
          pattern="\d{6}"
          maxlength="6"
          required
          placeholder="123456"
          class="w-full bg-[#050507] border border-amber-400/50 px-3 py-2.5 text-sm font-mono tracking-widest text-[#F5F5F3] placeholder-[#8A8D96]"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="btn-platinum w-full py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
        <span>
          {{ loading ? 'Signing in...' : mfaRequired ? 'Verify & Sign in' : 'Sign in' }}
        </span>
      </button>
    </form>

    <div class="border-t border-white/[0.1] pt-4 text-center text-xs text-[#8A8D96]">
      Don’t have a workspace yet?
      <router-link to="/app/register" class="text-[#F5F5F3] underline underline-offset-4 hover:text-white font-medium ml-1">
        Create one for free
      </router-link>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff, KeyRound, Loader2 } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import { api, ApiError } from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const totpCode = ref('')
const totpInputRef = ref<HTMLInputElement | null>(null)
const mfaRequired = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.auth.login({
      email: email.value,
      password: password.value,
      totp_code: mfaRequired.value ? totpCode.value : undefined,
    })
    await session.applyLogin(res)
    toast.success(`Welcome back, ${res.user.full_name}.`)
    const rawRedirect =
      typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/app')
        ? route.query.redirect
        : ''
    const redirectPath = res.user.is_superadmin
      ? rawRedirect.startsWith('/app/admin') || rawRedirect.startsWith('/app/settings')
        ? rawRedirect
        : '/app/admin'
      : rawRedirect && !rawRedirect.startsWith('/app/admin')
        ? rawRedirect
        : '/app/dashboard'
    await router.push(redirectPath)
  } catch (err: unknown) {
    if (err instanceof ApiError && err.code === 'MFA_REQUIRED') {
      mfaRequired.value = true
      errorMessage.value = ''
      await nextTick()
      totpInputRef.value?.focus()
      return
    }
    errorMessage.value =
      err instanceof Error ? err.message : 'Sign in failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>
