<template>
  <AuthShell>
    <div class="space-y-1.5">
      <h2 class="text-xl sm:text-2xl font-display font-semibold text-[#F5F5F3]">Reset your password</h2>
      <p class="text-xs sm:text-sm text-[#8A8D96]">
        Enter your account email and we’ll send a reset link valid for 15 minutes.
      </p>
    </div>

    <div
      v-if="sentMessage"
      role="status"
      class="p-4 bg-emerald-500/10 border border-emerald-400/35 text-emerald-200 text-xs space-y-2 leading-relaxed"
    >
      <div class="font-semibold flex items-center gap-1.5">
        <CheckCircle2 class="h-4 w-4 text-emerald-400" aria-hidden="true" />
        <span>Reset request sent</span>
      </div>
      <p>{{ sentMessage }}</p>
      <p class="text-[#D4D4D8]">
        Check your inbox or spam folder for instructions to set a new password.
      </p>
    </div>

    <div
      v-if="errorMessage"
      role="alert"
      class="p-3.5 bg-red-500/10 border border-red-400/35 text-red-200 text-xs"
    >
      {{ errorMessage }}
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="space-y-1.5">
        <label for="forgot-email" class="text-xs font-medium text-[#D4D4D8] block">
          Account email
        </label>
        <input
          id="forgot-email"
          v-model.trim="email"
          type="email"
          required
          autocomplete="email"
          placeholder="you@company.com"
          class="w-full input-glass px-3 py-2.5 text-xs sm:text-sm"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="btn-platinum w-full py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
        <span>{{ loading ? 'Sending reset link...' : 'Send reset link' }}</span>
      </button>
    </form>

    <div class="border-t border-white/[0.1] pt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-[#8A8D96]">
      <router-link to="/app/login" class="text-[#F5F5F3] underline underline-offset-4 hover:text-white font-medium">
        ← Back to sign in
      </router-link>
      <router-link to="/app/reset-password" class="text-[#D4D4D8] hover:text-white underline underline-offset-4">
        Already have a reset token?
      </router-link>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2, Loader2 } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import { api } from '@/services/api'

const email = ref('')
const loading = ref(false)
const sentMessage = ref('')
const errorMessage = ref('')

const handleSubmit = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.auth.forgotPassword(email.value)
    sentMessage.value = res.message
  } catch (err: unknown) {
    errorMessage.value =
      err instanceof Error ? err.message : 'Unable to send password reset request.'
  } finally {
    loading.value = false
  }
}
</script>
