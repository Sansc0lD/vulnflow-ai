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

        <!-- Right: Plan Inquiry & Checkout Preview Form (7 cols) -->
        <div class="lg:col-span-7 p-6 sm:p-8">
          <form @submit.prevent="handleBookingSubmit" class="space-y-5">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.08] pb-3.5">
              <h2 class="text-base font-display font-semibold text-[#F5F5F3]">
                02. Plan Preview &amp; Workspace Inquiry
              </h2>
              <span class="font-mono text-xs text-[#F5F5F3]">
                Plan: {{ selectedTierLabel }}
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
                <label for="contact-audit-type" class="text-xs font-medium text-[#D4D4D8] block">
                  Primary engagement type
                </label>
                <select
                  id="contact-audit-type"
                  v-model="form.auditType"
                  class="w-full input-glass px-3 py-2 text-xs sm:text-sm"
                >
                  <option value="GREY_BOX">Web &amp; API Assessment</option>
                  <option value="BLACK_BOX">External Perimeter Testing</option>
                  <option value="WHITE_BOX">Enterprise Compliance Audit</option>
                </select>
              </div>
            </div>

            <div class="space-y-1.5">
              <label for="contact-scope" class="text-xs font-medium text-[#D4D4D8] block">
                Notes or target examples
              </label>
              <textarea
                id="contact-scope"
                v-model.trim="form.scope"
                rows="3"
                required
                placeholder="app.example.com&#10;api.example.com&#10;Custom branding and team access for 5 reviewers"
                class="w-full input-glass p-3 text-xs sm:text-sm font-mono"
              ></textarea>
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
                  I confirm that my organization authorizes all tested targets and agrees to the standard <strong>Non-Disclosure Agreement (NDA)</strong> terms.
                </span>
              </label>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
              <router-link to="/app/register" class="text-xs font-medium text-[#F5F5F3] underline underline-offset-4 hover:text-white">
                Or start free now →
              </router-link>

              <button type="submit" class="btn-platinum px-5 py-2.5 text-xs">
                <CreditCard class="h-4 w-4" />
                <span>Preview checkout</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>

    <!-- Checkout Preview Modal (UC-05a) -->
    <BaseModal
      :open="showSnapModal"
      title="Checkout Preview"
      subtitle="Preview the payment flow using QRIS or Virtual Account before activating your workspace."
      max-width="md"
      @close="showSnapModal = false"
    >
      <div v-if="paymentSettled" class="space-y-5 text-center py-2">
        <div class="h-14 w-14 bg-emerald-500/15 border border-emerald-400/40 text-emerald-300 flex items-center justify-center mx-auto">
          <CheckCircle2 class="h-8 w-8" aria-hidden="true" />
        </div>
        <div class="space-y-1">
          <h4 class="text-lg font-display font-semibold text-[#F5F5F3]">Payment Verified</h4>
          <p class="text-xs text-[#D4D4D8]">
            Status: <strong class="text-emerald-300">Completed</strong>
          </p>
        </div>

        <dl class="p-4 bg-[#050507] border border-white/[0.1] text-left text-xs space-y-2">
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Order Reference</dt>
            <dd class="text-[#F5F5F3] font-mono font-semibold">{{ orderId }}</dd>
          </div>
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Organization</dt>
            <dd class="text-[#F5F5F3]">{{ form.company }}</dd>
          </div>
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Plan</dt>
            <dd class="text-[#F5F5F3] font-semibold">{{ selectedTierLabel }}</dd>
          </div>
          <div class="flex justify-between text-emerald-300 font-semibold border-t border-white/[0.08] pt-2 tabular-nums">
            <dt>Monthly Total</dt>
            <dd class="font-mono">Rp {{ formatRupiah(recommendedPlan.numericPrice) }}</dd>
          </div>
        </dl>

        <div class="flex flex-col sm:flex-row gap-2.5 pt-2">
          <router-link
            to="/app/register"
            @click="showSnapModal = false"
            class="btn-platinum flex-1 px-4 py-2.5 text-xs"
          >
            <span>Create &amp; activate workspace</span>
            <ArrowRight class="h-3.5 w-3.5" />
          </router-link>
          <button type="button" @click="resetModalAndForm" class="btn-glass px-4 py-2.5 text-xs">
            Done
          </button>
        </div>
      </div>

      <div v-else class="space-y-5">
        <dl class="p-4 bg-[#050507] border border-white/[0.1] space-y-2 text-xs">
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Order ID</dt>
            <dd class="text-[#F5F5F3] font-mono font-semibold">{{ orderId }}</dd>
          </div>
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Organization</dt>
            <dd class="text-[#F5F5F3]">{{ form.company }}</dd>
          </div>
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Estimated Volume</dt>
            <dd class="text-[#F5F5F3] tabular-nums">{{ assetCount }} Assets / month</dd>
          </div>
          <div class="border-t border-white/[0.08] pt-2 flex justify-between font-semibold text-sm text-emerald-400 tabular-nums">
            <dt>Monthly Total</dt>
            <dd class="font-mono">Rp {{ formatRupiah(recommendedPlan.numericPrice) }}</dd>
          </div>
        </dl>

        <div class="space-y-3">
          <span class="text-xs font-medium text-[#D4D4D8] block">Choose payment method</span>
          <div class="grid grid-cols-2 border border-white/[0.12] divide-x divide-white/[0.12] text-xs">
            <button
              type="button"
              @click="paymentMethod = 'qris'"
              :class="[
                'p-3 text-center transition-colors',
                paymentMethod === 'qris'
                  ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
                  : 'bg-[#050507] text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              QRIS / E-Wallet
            </button>
            <button
              type="button"
              @click="paymentMethod = 'va'"
              :class="[
                'p-3 text-center transition-colors',
                paymentMethod === 'va'
                  ? 'bg-[#F5F5F3] text-[#050507] font-semibold'
                  : 'bg-[#050507] text-[#8A8D96] hover:text-[#F5F5F3]',
              ]"
            >
              Bank Virtual Account
            </button>
          </div>

          <div
            v-if="paymentMethod === 'qris'"
            class="p-4 bg-white flex flex-col items-center justify-center gap-2"
          >
            <svg viewBox="0 0 120 120" class="h-32 w-32 text-slate-900" role="img" aria-label="QRIS Demo Code">
              <rect width="120" height="120" fill="#ffffff" />
              <path
                fill="#0f172a"
                d="M10 10h32v32H10zm6 6v20h20V16zm6 6h8v8h-8zM78 10h32v32H78zm6 6v20h20V16zm6 6h8v8h-8zM10 78h32v32H10zm6 6v20h20V84zm6 6h8v8h-8zM50 12h8v8h-8zm14 0h8v14h-8zm-14 18h14v8H50zm0 16h8v14h-8zm16 0h10v8H66zm18 0h10v14H84zm-72 10h14v8H12zm20 0h10v14H32zm22 10h16v8H54zm22 4h14v8H76zm18 0h16v14H94zM50 78h8v14h-8zm14 8h10v8H64zm16-6h8v24h-8zm14 14h16v16H94zm-30 12h10v10H64z"
              />
            </svg>
            <span class="text-xs font-medium text-slate-700">
              Sample QRIS Checkout Code
            </span>
          </div>

          <div v-else class="p-4 bg-[#050507] border border-white/[0.1] space-y-2 text-xs">
            <div class="text-[#8A8D96]">Sample Virtual Account Number</div>
            <div class="text-base font-mono font-bold text-[#F5F5F3] flex items-center justify-between gap-2">
              <span>{{ virtualAccountNumber }}</span>
              <button type="button" @click="copyVaNumber" class="btn-glass px-2.5 py-1 text-xs font-sans">
                <Copy class="h-3 w-3" />
                <span>Copy VA</span>
              </button>
            </div>
            <div class="text-xs text-[#8A8D96]">Payment window: 24 hours</div>
          </div>
        </div>

        <div class="flex justify-end pt-2">
          <button
            type="button"
            @click="simulateSuccess"
            class="bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors"
          >
            Simulate successful payment
          </button>
        </div>
      </div>
    </BaseModal>
  </PublicLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowRight, CheckCircle2, Copy, CreditCard } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import { toast } from '@/stores/toast'

const assetCount = ref(25)
const showSnapModal = ref(false)
const paymentSettled = ref(false)
const paymentMethod = ref<'qris' | 'va'>('qris')
const orderId = ref('VF-2026-8421')
const virtualAccountNumber = '70012-9842103841'

const form = ref({
  fullName: '',
  company: '',
  email: '',
  auditType: 'GREY_BOX',
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
    quota: 'Unlimited reports & workspaces',
    priceLabel: 'Rp 2,500,000 / month (Est.)',
    numericPrice: 2500000,
  }
})

const selectedTierLabel = computed(() => recommendedPlan.value.name)

const formatRupiah = (val: number) => val.toLocaleString('en-US')

const handleBookingSubmit = () => {
  paymentSettled.value = false
  orderId.value = `VF-2026-${Math.floor(1000 + Math.random() * 9000)}`
  showSnapModal.value = true
}

const copyVaNumber = async () => {
  try {
    await navigator.clipboard.writeText(virtualAccountNumber)
    toast.success('Virtual Account number copied to clipboard.')
  } catch {
    toast.info(virtualAccountNumber, 'Virtual Account')
  }
}

const simulateSuccess = () => {
  paymentSettled.value = true
  toast.success(`Checkout preview ${orderId.value} completed.`)
}

const resetModalAndForm = () => {
  showSnapModal.value = false
  paymentSettled.value = false
  form.value = {
    fullName: '',
    company: '',
    email: '',
    auditType: 'GREY_BOX',
    scope: '',
    agreedNDA: false,
  }
}
</script>
