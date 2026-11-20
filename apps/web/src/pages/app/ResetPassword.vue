<template>
  <AuthShell>
    <div class="space-y-1.5">
      <h2 class="text-xl sm:text-2xl font-display font-semibold text-[#F5F5F3]">Set a new password</h2>
      <p class="text-xs sm:text-sm text-[#8A8D96]">
        Choose a strong password to restore access to your workspace.
      </p>
    </div>

    <div
      v-if="errorMessage"
      role="alert"
      class="p-3.5 bg-red-500/10 border border-red-400/35 text-red-200 text-xs"
    >
      {{ errorMessage }}
    </div>

    <form @submit.prevent="handleReset" class="space-y-4">
      <div
        v-if="hasUrlToken && !editTokenManual"
        class="p-3 bg-emerald-500/10 border border-emerald-400/30 flex items-center justify-between gap-2 text-xs"
      >
        <span class="text-emerald-200 font-medium flex items-center gap-1.5">
          <CheckCircle2 class="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>Reset token detected from link</span>
        </span>
        <button
          type="button"
          @click="editTokenManual = true"
          class="text-[#D4D4D8] hover:text-white underline text-[11px]"
        >
          Edit
        </button>
      </div>

      <div v-else class="space-y-1.5">
        <label for="reset-token" class="text-xs font-medium text-[#D4D4D8] block">Reset token</label>
        <input
          id="reset-token"
          v-model.trim="token"
          type="text"
          required
          placeholder="Paste reset token from your email..."
          class="w-full input-glass px-3 py-2 text-xs sm:text-sm font-mono"
        />
      </div>

      <div class="space-y-1.5">
        <label for="reset-new-password" class="text-xs font-medium text-[#D4D4D8] block">
          New password
        </label>
        <div class="relative">
          <input
            id="reset-new-password"
            v-model="newPassword"
            :type="showNewPassword ? 'text' : 'password'"
            required
            minlength="8"
            autocomplete="new-password"
            placeholder="Str0ng!Passw0rd"
            class="w-full input-glass pl-3 pr-10 py-2 text-xs sm:text-sm"
          />
          <button
            type="button"
            @click="showNewPassword = !showNewPassword"
            :aria-label="showNewPassword ? 'Hide new password' : 'Show new password'"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-[#8A8D96] hover:text-[#F5F5F3]"
          >
            <EyeOff v-if="showNewPassword" class="h-4 w-4" />
            <Eye v-else class="h-4 w-4" />
          </button>
        </div>

        <ul class="grid grid-cols-1 sm:grid-cols-2 gap-1 pt-1 text-[11px]">
          <li
            v-for="rule in passwordRules"
            :key="rule.label"
            :class="['flex items-center gap-1.5', rule.passed ? 'text-emerald-300' : 'text-[#8A8D96]']"
          >
            <Check v-if="rule.passed" class="h-3 w-3 shrink-0" aria-hidden="true" />
            <span v-else class="h-1.5 w-1.5 rounded-full bg-zinc-500 mx-0.5 shrink-0" aria-hidden="true" />
            <span>{{ rule.label }}</span>
          </li>
        </ul>
      </div>

      <div class="space-y-1.5">
        <label for="reset-confirm-password" class="text-xs font-medium text-[#D4D4D8] block">
          Confirm new password
        </label>
        <div class="relative">
          <input
            id="reset-confirm-password"
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            required
            minlength="8"
            autocomplete="new-password"
            placeholder="••••••••••••"
            class="w-full input-glass pl-3 pr-10 py-2 text-xs sm:text-sm"
          />
          <button
            type="button"
            @click="showConfirmPassword = !showConfirmPassword"
            :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-[#8A8D96] hover:text-[#F5F5F3]"
          >
            <EyeOff v-if="showConfirmPassword" class="h-4 w-4" />
            <Eye v-else class="h-4 w-4" />
          </button>
        </div>
        <p v-if="confirmPassword && !passwordsMatch" class="text-[11px] text-amber-300">
          Passwords do not match.
        </p>
      </div>

      <button
        type="submit"
        :disabled="loading || !isPasswordValid || !passwordsMatch"
        class="btn-platinum w-full py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
        <span>{{ loading ? 'Saving password...' : 'Save new password' }}</span>
      </button>
    </form>

    <div class="border-t border-white/[0.1] pt-4 text-center text-xs text-[#8A8D96]">
      <router-link to="/app/login" class="text-[#F5F5F3] underline underline-offset-4 hover:text-white font-medium">
        ← Back to sign in
      </router-link>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, CheckCircle2, Eye, EyeOff, Loader2 } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import { api } from '@/services/api'
import { toast } from '@/stores/toast'

const route = useRoute()
const router = useRouter()

const token = ref(typeof route.query.token === 'string' ? route.query.token.trim() : '')
const hasUrlToken = computed(() =>
  Boolean(typeof route.query.token === 'string' && route.query.token.trim())
)
const editTokenManual = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const passwordRules = computed(() => {
  const pw = newPassword.value
  return [
    { label: 'At least 8 characters', passed: pw.length >= 8 },
    { label: 'Uppercase letter (A-Z)', passed: /[A-Z]/.test(pw) },
    { label: 'Lowercase letter (a-z)', passed: /[a-z]/.test(pw) },
    { label: 'Number (0-9)', passed: /[0-9]/.test(pw) },
    { label: 'Special character (!@#...)', passed: /[^A-Za-z0-9]/.test(pw) },
  ]
})

const isPasswordValid = computed(() => passwordRules.value.every((r) => r.passed))
const passwordsMatch = computed(() => newPassword.value === confirmPassword.value)

const handleReset = async () => {
  errorMessage.value = ''
  if (!isPasswordValid.value) {
    errorMessage.value = 'Please satisfy all password requirements.'
    return
  }
  if (!passwordsMatch.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  try {
    await api.auth.resetPassword(token.value, newPassword.value)
    toast.success('Password updated. You can now sign in with your new password.')
    await router.push('/app/login')
  } catch (err: unknown) {
    errorMessage.value =
      err instanceof Error ? err.message : 'Invalid or expired reset token.'
  } finally {
    loading.value = false
  }
}
</script>
