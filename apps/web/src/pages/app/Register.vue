<template>
  <AuthShell>
    <div class="space-y-1.5">
      <h2 class="text-xl sm:text-2xl font-display font-semibold text-[#F5F5F3]">
        {{ hasInvite ? 'Accept workspace invitation' : 'Create your workspace' }}
      </h2>
      <p class="text-xs sm:text-sm text-[#8A8D96]">
        {{
          hasInvite
            ? 'Finish setting up your account to join your team’s workspace.'
            : 'Start free with 3 PDF exports per month and invite your team anytime.'
        }}
      </p>
    </div>

    <div
      v-if="hasInvite"
      class="p-3.5 bg-white/[0.03] border border-white/[0.16] text-[#F5F5F3] text-xs flex items-center gap-2.5"
    >
      <MailCheck class="h-4 w-4 shrink-0" aria-hidden="true" />
      <span>Invitation token detected. You will join the team workspace automatically.</span>
    </div>

    <div
      v-if="errorMessage"
      role="alert"
      class="p-3.5 bg-red-500/10 border border-red-400/35 text-red-200 text-xs leading-relaxed"
    >
      {{ errorMessage }}
    </div>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <div class="space-y-1.5">
        <label for="reg-fullname" class="text-xs font-medium text-[#D4D4D8] block">Full name</label>
        <input
          id="reg-fullname"
          v-model.trim="fullName"
          type="text"
          required
          maxlength="100"
          placeholder="Alex Morgan"
          class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
        />
      </div>

      <div class="space-y-1.5">
        <label for="reg-email" class="text-xs font-medium text-[#D4D4D8] block">Work email</label>
        <input
          id="reg-email"
          v-model.trim="email"
          type="email"
          required
          autocomplete="email"
          placeholder="alex@northstar.io"
          class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
        />
      </div>

      <div v-if="!hasInvite" class="space-y-1.5">
        <label for="reg-workspace" class="text-xs font-medium text-[#D4D4D8] block">
          Workspace name
        </label>
        <input
          id="reg-workspace"
          v-model.trim="workspaceName"
          type="text"
          required
          maxlength="150"
          placeholder="Northstar Security"
          class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
        />
      </div>

      <div class="space-y-1.5">
        <label for="reg-password" class="text-xs font-medium text-[#D4D4D8] block">Password</label>
        <div class="relative">
          <input
            id="reg-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            minlength="8"
            maxlength="128"
            autocomplete="new-password"
            placeholder="Str0ng!Passw0rd"
            class="w-full input-glass pl-3 pr-10 py-2 text-xs sm:text-sm"
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
        <label for="reg-confirm-password" class="text-xs font-medium text-[#D4D4D8] block">
          Confirm password
        </label>
        <div class="relative">
          <input
            id="reg-confirm-password"
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            required
            autocomplete="new-password"
            placeholder="Re-enter password..."
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
        <span>
          {{ loading ? 'Creating account...' : hasInvite ? 'Join workspace' : 'Create workspace' }}
        </span>
      </button>
    </form>

    <div class="border-t border-white/[0.1] pt-4 text-center text-xs text-[#8A8D96]">
      Already have an account?
      <router-link to="/app/login" class="text-[#F5F5F3] underline underline-offset-4 hover:text-white font-medium ml-1">
        Sign in
      </router-link>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, Eye, EyeOff, Loader2, MailCheck } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import { api, ApiError } from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const router = useRouter()
const route = useRoute()

const invitationToken = ref(
  typeof route.query.invite === 'string' ? route.query.invite.trim() : ''
)
const hasInvite = computed(() => invitationToken.value.length > 0)

const fullName = ref('')
const email = ref(typeof route.query.email === 'string' ? route.query.email.trim() : '')
const workspaceName = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const passwordRules = computed(() => {
  const pw = password.value
  return [
    { label: 'At least 8 characters', passed: pw.length >= 8 },
    { label: 'Uppercase letter (A-Z)', passed: /[A-Z]/.test(pw) },
    { label: 'Lowercase letter (a-z)', passed: /[a-z]/.test(pw) },
    { label: 'Number (0-9)', passed: /[0-9]/.test(pw) },
    { label: 'Special character (!@#...)', passed: /[^A-Za-z0-9]/.test(pw) },
  ]
})

const isPasswordValid = computed(() => passwordRules.value.every((r) => r.passed))
const passwordsMatch = computed(() => password.value === confirmPassword.value)

const handleRegister = async () => {
  if (!isPasswordValid.value) {
    errorMessage.value = 'Please satisfy all password requirements.'
    return
  }
  if (!passwordsMatch.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await api.auth.register({
      full_name: fullName.value,
      email: email.value,
      workspace_name: hasInvite.value ? 'Invited Workspace' : workspaceName.value,
      password: password.value,
      invitation_token: hasInvite.value ? invitationToken.value : undefined,
    })
    await session.applyRegister(res)
    toast.success(
      hasInvite.value
        ? 'Account created and workspace joined successfully.'
        : 'Account and workspace created successfully.'
    )
    await router.push('/app/dashboard')
  } catch (err: unknown) {
    if (err instanceof ApiError && err.details.length > 0) {
      errorMessage.value =
        err.details.map((d) => d.message).filter(Boolean).join(' • ') || err.message
    } else {
      errorMessage.value = err instanceof Error ? err.message : 'Unable to create your account.'
    }
  } finally {
    loading.value = false
  }
}
</script>
