<template>
  <PublicLayout>
    <!-- Header -->
    <section class="border-b border-white/[0.1]">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-14 pb-12">
        <div class="max-w-3xl space-y-3">
          <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
            Pricing &amp; Estimator
          </span>
          <h1 class="font-display text-4xl sm:text-5xl font-bold tracking-[-0.04em] text-[#F5F5F3] leading-[1.04]">
            Plans, Time Savings &amp;
            <span class="font-serif italic font-normal text-white">Team Licensing</span>
          </h1>
          <p class="text-sm sm:text-base text-[#8A8D96] leading-relaxed">
            Run an illustrative estimate of reporting hours saved per month, compare plan quotas, or preview our online checkout flow.
          </p>
        </div>
      </div>
    </section>

    <!-- Main Interactive Estimator & Form (UC-05 & UC-05a) -->
    <section class="py-12 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
      <div class="border border-white/[0.12] bg-[#08080B] grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.1]">
        <!-- Left: Illustrative Savings Estimator (5 cols) -->
        <div class="lg:col-span-5 p-6 sm:p-8 space-y-6">
          <div class="border-b border-white/[0.08] pb-3.5 space-y-1">
            <h2 class="text-base font-display font-semibold text-[#F5F5F3]">
              01. Illustrative Monthly Estimator
            </h2>
            <p class="font-mono text-[11px] text-[#8A8D96]">Based on typical manual vs structured turnaround</p>
          </div>

          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label for="scope-slider" class="text-xs sm:text-sm font-medium text-[#D4D4D8]">
                Assets reviewed per month
              </label>
              <span class="text-lg font-bold text-[#F5F5F3] font-mono tabular-nums">{{ assetCount }} Assets</span>
            </div>

            <input
              id="scope-slider"
              v-model.number="assetCount"
              type="range"
              min="5"
              max="100"
              step="5"
              class="w-full h-1.5 bg-white/[0.12] appearance-none cursor-pointer accent-[#F5F5F3]"
            />

            <div class="flex justify-between font-mono text-xs text-[#8A8D96]">
              <span>5</span>
              <span>50</span>
              <span>100</span>
            </div>
          </div>

          <dl class="grid grid-cols-2 border-y border-white/[0.1] divide-x divide-white/[0.1] text-xs">
            <div class="py-4 pr-4 space-y-1">
              <dt class="text-[#8A8D96]">Est. hours saved</dt>
              <dd class="text-lg font-bold font-mono text-emerald-400 tabular-nums">{{ hoursSaved }} hrs/mo</dd>
            </div>
            <div class="py-4 pl-4 space-y-1">
              <dt class="text-[#8A8D96]">Est. manual effort</dt>
              <dd class="text-lg font-bold font-mono text-[#F5F5F3] tabular-nums">{{ estimatedDays }} workdays</dd>
            </div>
          </dl>

          <dl class="divide-y divide-white/[0.08] text-xs">
            <div class="py-2.5 flex justify-between text-[#D4D4D8]">
              <dt>Recommended plan</dt>
              <dd class="font-semibold text-[#F5F5F3]">{{ recommendedPlan.name }}</dd>
            </div>
            <div class="py-2.5 flex justify-between text-[#D4D4D8]">
              <dt>Monthly report quota</dt>
              <dd class="font-mono">{{ recommendedPlan.quota }}</dd>
            </div>
            <div class="py-2.5 flex justify-between text-[#D4D4D8]">
              <dt>Illustrative team savings</dt>
              <dd class="text-emerald-400 font-mono font-semibold tabular-nums">Rp {{ formatRupiah(costSavedIdr) }}</dd>
            </div>
            <div class="pt-3 flex justify-between font-semibold text-sm text-[#F5F5F3]">
              <dt>Subscription cost</dt>
              <dd class="font-mono tabular-nums">{{ recommendedPlan.priceLabel }}</dd>
            </div>
          </dl>

          <p class="text-xs text-[#8A8D96] leading-relaxed pt-2 border-t border-white/[0.08]">
            Every plan includes local CLI uploads, automatic scope validation, CVSS v3.1 scoring, and private AI report drafting.
          </p>
        </div>

        <!-- Right: Real Enterprise & Team Licensing Inquiry Form (7 cols) -->
        <div class="lg:col-span-7 p-6 sm:p-8">
          <div v-if="submittedInquiry" class="space-y-5 py-4">
            <div class="h-12 w-12 bg-emerald-500/15 border border-emerald-400/40 text-emerald-300 flex items-center justify-center">
              <CheckCircle2 class="h-6 w-6" aria-hidden="true" />
            </div>
            <div class="space-y-1.5">
              <h2 class="text-lg font-display font-semibold text-[#F5F5F3]">
                Enterprise Inquiry Received
              </h2>
              <p class="text-xs text-[#D4D4D8] leading-relaxed">
                Our platform team has logged your licensing and deployment inquiry. Reference ticket ID:
                <code class="font-mono text-emerald-300">{{ submittedInquiry.id }}</code>.
              </p>
            </div>
            <dl class="p-4 bg-[#050507] border border-white/[0.1] text-xs space-y-2">
              <div class="flex justify-between text-[#8A8D96]">
                <dt>Company</dt>
                <dd class="text-[#F5F5F3] font-medium">{{ submittedInquiry.company_name }}</dd>
              </div>
              <div class="flex justify-between text-[#8A8D96]">
                <dt>Contact</dt>
                <dd class="text-[#F5F5F3]">{{ submittedInquiry.contact_name }} ({{ submittedInquiry.contact_email }})</dd>
              </div>
              <div class="flex justify-between text-[#8A8D96]">
                <dt>Status</dt>
                <dd class="font-mono text-emerald-300">{{ submittedInquiry.status }}</dd>
              </div>
              <div v-if="submittedInquiry.workspace_id" class="flex justify-between text-[#8A8D96]">
                <dt>Linked workspace</dt>
                <dd class="font-mono text-[#F5F5F3]">{{ submittedInquiry.workspace_id }}</dd>
              </div>
            </dl>
            <div class="flex flex-wrap gap-3 pt-1">
              <router-link
                v-if="submittedInquiry.workspace_id"
                to="/app/billing"
                class="btn-platinum px-4 py-2 text-xs"
              >
                <span>Back to Workspace Billing</span>
                <ArrowRight class="h-3.5 w-3.5" />
              </router-link>
              <router-link v-else to="/app/register" class="btn-platinum px-4 py-2 text-xs">
                <span>Start Free Workspace Meanwhile</span>
                <ArrowRight class="h-3.5 w-3.5" />
              </router-link>
              <button type="button" @click="resetInquiryForm" class="btn-glass px-4 py-2 text-xs">
                Submit Another Inquiry
              </button>
            </div>
          </div>

          <form v-else @submit.prevent="handleInquirySubmit" class="space-y-5">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.08] pb-3.5">
              <h2 class="text-base font-display font-semibold text-[#F5F5F3]">
                02. Request Enterprise &amp; Custom Licensing
              </h2>
              <span class="font-mono text-xs text-[#F5F5F3]">
                Suggested: {{ selectedTierLabel }}
              </span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label for="contact-pic" class="text-xs font-medium text-[#D4D4D8] block">
                  Full name
                </label>
                <input
                  id="contact-pic"
                  v-model.trim="form.fullName"
                  type="text"
                  required
                  placeholder="Alex Morgan"
                  class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
                />
              </div>

              <div class="space-y-1.5">
                <label for="contact-company" class="text-xs font-medium text-[#D4D4D8] block">
                  Company or team
                </label>
                <input
                  id="contact-company"
                  v-model.trim="form.company"
                  type="text"
                  required
                  placeholder="Northstar Security"
                  class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
                />
              </div>

              <div class="space-y-1.5">
                <label for="contact-email" class="text-xs font-medium text-[#D4D4D8] block">
                  Work email
                </label>
                <input
                  id="contact-email"
                  v-model.trim="form.email"
                  type="email"
                  required
                  placeholder="alex@northstar.io"
                  class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
                />
              </div>

              <div class="space-y-1.5">
                <label for="contact-team-size" class="text-xs font-medium text-[#D4D4D8] block">
                  Team size
                </label>
                <select
                  id="contact-team-size"
                  v-model="form.teamSize"
                  class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
                >
                  <option value="1-4">1-4 pentesters</option>
                  <option value="5-20">5-20 pentesters</option>
                  <option value="21-50">21-50 pentesters</option>
                  <option value="50+">50+ pentesters</option>
                </select>
              </div>
            </div>

            <div class="space-y-1.5">
              <label for="contact-scope" class="text-xs font-medium text-[#D4D4D8] block">
                Volume, private LLM / on-premise &amp; target notes
              </label>
              <textarea
                id="contact-scope"
                v-model.trim="form.scope"
                rows="3"
                required
                minlength="5"
                placeholder="Est. 80+ reports/mo, custom CLI batch limit 2,000+, private Ollama/VPC option..."
                class="w-full input-glass p-3 text-xs sm:text-sm font-mono"
              ></textarea>
            </div>

            <div v-if="canLinkWorkspace" class="p-4 bg-[#050507] border border-emerald-400/25">
              <label for="contact-link-ws" class="flex items-start gap-2.5 cursor-pointer">
                <input
                  id="contact-link-ws"
                  v-model="linkActiveWorkspace"
                  type="checkbox"
                  class="mt-1 bg-[#050507] border-white/25 text-[#F5F5F3]"
                />
                <span class="text-xs text-[#D4D4D8] leading-relaxed">
                  Link request to active workspace
                  <strong class="text-[#F5F5F3]">{{ activeWorkspaceName }}</strong>
                  so Admin Console enables 1-click <code class="font-mono text-emerald-300">Provision Enterprise</code>.
                </span>
              </label>
            </div>

            <div v-if="requiresCaptcha" class="p-4 bg-[#050507] border border-white/[0.1] space-y-2.5">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 text-xs font-medium text-[#F5F5F3]">
                  <ShieldCheck class="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
                  <span>Human verification</span>
                </div>
                <button
                  type="button"
                  @click="loadCaptchaChallenge"
                  :disabled="loadingCaptcha"
                  class="inline-flex items-center gap-1 text-[11px] font-mono text-[#8A8D96] hover:text-[#F5F5F3] disabled:opacity-50"
                >
                  <RefreshCw :class="['h-3 w-3', loadingCaptcha ? 'animate-spin' : '']" aria-hidden="true" />
                  <span>Refresh</span>
                </button>
              </div>

              <div v-if="loadingCaptcha && !captchaChallenge" class="text-xs text-[#8A8D96] font-mono">
                Loading security challenge...
              </div>
              <div v-else-if="captchaChallenge?.mode === 'turnstile'" class="pt-1">
                <div ref="turnstileContainer"></div>
              </div>
              <div v-else-if="captchaChallenge" class="flex flex-col sm:flex-row sm:items-center gap-2.5">
                <label
                  for="contact-captcha-answer"
                  class="px-3 py-2 bg-[#08080B] border border-white/[0.12] font-mono text-xs text-emerald-300 shrink-0"
                >
                  {{ captchaChallenge.prompt }}
                </label>
                <input
                  id="contact-captcha-answer"
                  v-model.trim="captchaAnswer"
                  type="text"
                  inputmode="numeric"
                  autocomplete="off"
                  required
                  placeholder="Enter answer"
                  class="w-full input-glass px-3 py-2 text-xs sm:text-sm font-mono"
                />
              </div>
              <div v-else class="text-xs text-amber-300">
                Verification challenge unavailable. Click Refresh to retry.
              </div>
            </div>

            <div class="p-4 bg-[#050507] border border-white/[0.1]">
              <label for="contact-nda" class="flex items-start gap-2.5 cursor-pointer">
                <input
                  id="contact-nda"
                  v-model="form.agreedNDA"
                  type="checkbox"
                  required
                  class="mt-1 bg-[#050507] border-white/25 text-[#F5F5F3]"
                />
                <span class="text-xs text-[#D4D4D8] leading-relaxed">
                  I confirm this inquiry represents an authorized organization and consent to follow-up under mutual <strong>NDA</strong>.
                </span>
              </label>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
              <router-link to="/app/register" class="text-xs font-medium text-[#F5F5F3] underline underline-offset-4 hover:text-white">
                Or start free workspace now
              </router-link>

              <button
                type="submit"
                :disabled="submitting"
                class="btn-platinum px-5 py-2.5 text-xs disabled:opacity-50"
              >
                <Send class="h-3.5 w-3.5" />
                <span>{{ submitting ? 'Submitting...' : 'Submit Enterprise inquiry' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ArrowRight, CheckCircle2, RefreshCw, Send, ShieldCheck } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'
import {
  api,
  type EnterpriseInquiryChallenge,
  type EnterpriseInquiryCreatePayload,
  type EnterpriseInquiryResponse,
} from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

interface TurnstileApi {
  render: (
    container: HTMLElement,
    options: {
      sitekey: string
      theme?: 'dark' | 'light'
      callback?: (token: string) => void
      'expired-callback'?: () => void
      'error-callback'?: () => void
    }
  ) => string
  reset: (widgetId?: string) => void
}

const assetCount = ref(25)
const submitting = ref(false)
const submittedInquiry = ref<EnterpriseInquiryResponse | null>(null)
const linkActiveWorkspace = ref(true)
const captchaChallenge = ref<EnterpriseInquiryChallenge | null>(null)
const loadingCaptcha = ref(false)
const captchaAnswer = ref('')
const turnstileToken = ref('')
const turnstileContainer = ref<HTMLElement | null>(null)
let turnstileWidgetId: string | null = null

const form = ref({
  fullName: '',
  company: '',
  email: '',
  teamSize: '5-20',
  scope: '',
  agreedNDA: false,
})

const hoursSaved = computed(() => Math.round(assetCount.value * 1.4))
const estimatedDays = computed(() => Math.max(2, Math.ceil(assetCount.value / 8)))
const costSavedIdr = computed(() => hoursSaved.value * 250000)

const recommendedPlan = computed(() => {
  if (assetCount.value <= 10) {
    return {
      name: 'Free',
      quota: '3 PDF exports / month',
      priceLabel: 'Rp 0 / month',
      numericPrice: 0,
    }
  }
  if (assetCount.value <= 65) {
    return {
      name: 'Pro',
      quota: '30 White-Label PDFs / month',
      priceLabel: 'Rp 750,000 / month',
      numericPrice: 750000,
    }
  }
  return {
    name: 'Enterprise',
    quota: 'Unlimited reports & custom batches',
    priceLabel: 'Custom Enterprise SLA',
    numericPrice: 2500000,
  }
})

const selectedTierLabel = computed(() => recommendedPlan.value.name)

const canLinkWorkspace = computed(
  () =>
    session.isAuthenticated.value &&
    !session.isSuperadmin.value &&
    Boolean(session.state.activeWorkspaceId) &&
    session.activeRole.value === 'MANAGER'
)
const activeWorkspaceName = computed(
  () => session.state.activeWorkspace?.name || 'Active Workspace'
)
const requiresCaptcha = computed(() => !(canLinkWorkspace.value && linkActiveWorkspace.value))

const loadTurnstileScript = (): Promise<TurnstileApi | null> =>
  new Promise((resolve) => {
    const win = window as unknown as { turnstile?: TurnstileApi }
    if (win.turnstile) {
      resolve(win.turnstile)
      return
    }
    const existing = document.querySelector<HTMLScriptElement>('script[data-vf-turnstile="true"]')
    if (existing) {
      existing.addEventListener('load', () => resolve(win.turnstile ?? null), { once: true })
      existing.addEventListener('error', () => resolve(null), { once: true })
      return
    }
    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.dataset.vfTurnstile = 'true'
    script.onload = () => resolve(win.turnstile ?? null)
    script.onerror = () => resolve(null)
    document.head.appendChild(script)
  })

const renderTurnstileIfNeeded = async () => {
  if (!requiresCaptcha.value || submittedInquiry.value) return
  if (captchaChallenge.value?.mode !== 'turnstile' || !captchaChallenge.value.site_key) return
  await nextTick()
  if (!turnstileContainer.value) return
  const apiTurnstile = await loadTurnstileScript()
  if (!apiTurnstile) return
  if (turnstileWidgetId) {
    apiTurnstile.reset(turnstileWidgetId)
    turnstileToken.value = ''
    return
  }
  turnstileWidgetId = apiTurnstile.render(turnstileContainer.value, {
    sitekey: captchaChallenge.value.site_key,
    theme: 'dark',
    callback: (token: string) => {
      turnstileToken.value = token
    },
    'expired-callback': () => {
      turnstileToken.value = ''
    },
    'error-callback': () => {
      turnstileToken.value = ''
    },
  })
}

const loadCaptchaChallenge = async () => {
  loadingCaptcha.value = true
  captchaAnswer.value = ''
  turnstileToken.value = ''
  try {
    captchaChallenge.value = await api.public.getEnterpriseInquiryChallenge()
    await renderTurnstileIfNeeded()
  } catch {
    captchaChallenge.value = null
  } finally {
    loadingCaptcha.value = false
  }
}

watch(requiresCaptcha, (needed) => {
  if (needed) {
    turnstileWidgetId = null
    if (!captchaChallenge.value) {
      void loadCaptchaChallenge()
    } else {
      void renderTurnstileIfNeeded()
    }
  }
})

const prefillFromSession = () => {
  if (!canLinkWorkspace.value) return
  if (!form.value.fullName && session.state.user?.full_name) {
    form.value.fullName = session.state.user.full_name
  }
  if (!form.value.email && session.state.user?.email) {
    form.value.email = session.state.user.email
  }
  if (!form.value.company && session.state.activeWorkspace?.name) {
    form.value.company = session.state.activeWorkspace.name
  }
}

onMounted(async () => {
  if (session.state.hasToken && !session.state.initialized) {
    try {
      await session.hydrate()
    } catch {
      // Public inquiry flow still works for guests or expired local tokens
    }
  }
  prefillFromSession()
  if (!captchaChallenge.value) {
    await loadCaptchaChallenge()
  }
})

const formatRupiah = (val: number) => val.toLocaleString('en-US')

const handleInquirySubmit = async () => {
  submitting.value = true
  const useWorkspaceLink = canLinkWorkspace.value && linkActiveWorkspace.value
  try {
    const payload: EnterpriseInquiryCreatePayload = {
      company_name: form.value.company,
      contact_name: form.value.fullName,
      contact_email: form.value.email,
      team_size: form.value.teamSize,
      estimated_monthly_reports: assetCount.value,
      requirements: form.value.scope,
    }
    const activeWsId = session.state.activeWorkspaceId
    if (useWorkspaceLink && activeWsId) {
      submittedInquiry.value = await api.billing.submitEnterpriseInquiry(activeWsId, payload)
    } else {
      if (!captchaChallenge.value) {
        toast.warning('Verification challenge unavailable. Refreshing challenge now.')
        await loadCaptchaChallenge()
        return
      }
      if (captchaChallenge.value.mode === 'turnstile') {
        if (!turnstileToken.value) {
          toast.error('Please complete the human verification challenge.')
          return
        }
        payload.captcha_token = turnstileToken.value
      } else {
        payload.captcha_token = captchaChallenge.value.challenge_token ?? null
        payload.captcha_answer = captchaAnswer.value
      }
      submittedInquiry.value = await api.public.submitEnterpriseInquiry(payload)
    }
    toast.success('Enterprise inquiry submitted successfully.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to submit Enterprise inquiry.')
    if (!useWorkspaceLink) {
      void loadCaptchaChallenge()
    }
  } finally {
    submitting.value = false
  }
}

const resetInquiryForm = () => {
  submittedInquiry.value = null
  linkActiveWorkspace.value = true
  turnstileWidgetId = null
  form.value = {
    fullName: '',
    company: '',
    email: '',
    teamSize: '5-20',
    scope: '',
    agreedNDA: false,
  }
  prefillFromSession()
  void loadCaptchaChallenge()
}
</script>
