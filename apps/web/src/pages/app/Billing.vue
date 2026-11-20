<template>
  <AppLayout>
    <template #header-title>
      <div>
        <h1 class="text-base font-display font-semibold text-[#F5F5F3] tracking-tight">
          Billing &amp; Usage
        </h1>
        <p class="text-xs text-[#8A8D96] truncate">
          {{ session.state.activeWorkspace?.name || 'Subscription & quota monitoring' }}
        </p>
      </div>
    </template>

    <div class="space-y-6 max-w-7xl mx-auto">
      <!-- Pending Checkout Reminder Banner -->
      <div
        v-if="checkoutResult && !snapModalOpen && currentTier === 'FREE'"
        class="border border-white/[0.16] bg-[#08080B] p-4 flex flex-wrap items-center justify-between gap-3"
      >
        <div class="text-xs sm:text-sm text-[#F5F5F3]">
          <strong>Pending checkout ({{ checkoutResult.order_id }}):</strong>
          Complete your Pro payment or sync the transaction status.
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            @click="snapModalOpen = true"
            class="btn-platinum px-3.5 py-1.5 text-xs"
          >
            Open checkout
          </button>
          <a
            :href="checkoutResult.redirect_url"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-glass px-3 py-1.5 text-xs"
          >
            <span>Open Midtrans</span>
            <ExternalLink class="h-3 w-3" />
          </a>
        </div>
      </div>

      <!-- Real-time Quota Meter -->
      <div class="border border-white/[0.11] bg-[#08080B] p-6 space-y-4">
        <div
          class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-3.5"
        >
          <div>
            <h2 class="text-sm sm:text-base font-display font-semibold text-[#F5F5F3] flex items-center gap-2">
              <CreditCard class="h-4 w-4 text-[#8A8D96]" aria-hidden="true" />
              <span>Subscription &amp; Monthly Usage</span>
            </h2>
            <p class="text-xs text-[#8A8D96] mt-0.5">
              Monitor your monthly PDF export allowance and payment status.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button
              v-if="isManager && sub?.midtrans_order_id"
              type="button"
              @click="handleSyncStatus"
              :disabled="syncing"
              class="btn-glass px-3 py-1.5 text-xs disabled:opacity-50"
            >
              <RefreshCw
                :class="['h-3.5 w-3.5', syncing ? 'animate-spin' : '']"
                aria-hidden="true"
              />
              <span>Sync payment status</span>
            </button>
            <StatusBadge :status="currentTier" />
          </div>
        </div>

        <div class="space-y-2.5">
          <div class="flex flex-wrap justify-between gap-2 text-xs">
            <span class="text-[#D4D4D8]">Monthly PDF exports</span>
            <span class="text-[#F5F5F3] font-mono font-semibold tabular-nums">
              {{ usedReports }} / {{ maxReports }} reports ({{ remainingReports }} remaining)
            </span>
          </div>

          <div class="h-2 bg-[#050507] border border-white/[0.1] overflow-hidden">
            <div
              :class="['h-full transition-all duration-500', quotaBarClass]"
              :style="{ width: `${quotaPct}%` }"
            ></div>
          </div>

          <div class="flex flex-wrap justify-between gap-2 text-xs text-[#8A8D96] pt-1">
            <span>Resets on {{ formattedResetDate }}</span>
            <span v-if="sub?.midtrans_order_id" class="font-mono text-[11px]">
              Latest order: {{ sub.midtrans_order_id }} ({{ sub.payment_status }}{{ sub.payment_type ? ` · ${sub.payment_type}` : '' }})
            </span>
          </div>
        </div>

        <div
          v-if="usedReports >= maxReports"
          role="alert"
          class="p-3.5 bg-red-500/10 border border-red-400/25 text-red-200 text-xs flex items-center gap-2.5"
        >
          <AlertTriangle class="h-4 w-4 text-red-400 shrink-0" aria-hidden="true" />
          <span>
            You have reached your monthly PDF quota. Upgrade to Pro for 30 exports per month and white-label reports.
          </span>
        </div>

        <div
          v-else-if="quotaPct >= 80"
          role="status"
          class="p-3.5 bg-amber-500/10 border border-amber-400/25 text-amber-200 text-xs flex items-center gap-2.5 tabular-nums"
        >
          <AlertTriangle class="h-4 w-4 text-amber-400 shrink-0" aria-hidden="true" />
          <span>
            You have used {{ Math.round(quotaPct) }}% of your monthly export quota.
          </span>
        </div>
      </div>

      <!-- Unified Ruled 3-Column Plans Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 border border-white/[0.12] divide-y md:divide-y-0 md:divide-x divide-white/[0.12] bg-[#08080B]">
        <!-- Free -->
        <div
          :class="[
            'p-6 flex flex-col justify-between space-y-6',
            currentTier === 'FREE' ? 'bg-white/[0.02]' : '',
          ]"
        >
          <div class="space-y-4">
            <div class="space-y-1">
              <div class="flex items-center justify-between gap-2">
                <h3 class="text-lg font-display font-semibold text-[#F5F5F3]">Free</h3>
                <span
                  v-if="currentTier === 'FREE'"
                  class="px-2 py-0.5 bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 font-mono text-[10px] uppercase tracking-wider"
                >
                  Active
                </span>
              </div>
              <p class="text-xs text-[#8A8D96]">For independent testers and initial evaluations.</p>
            </div>

            <div class="pt-3 border-t border-white/[0.08] text-2xl font-display font-bold text-[#F5F5F3] font-mono tabular-nums">
              Rp 0 <span class="text-xs font-sans font-normal text-[#8A8D96]">/ month</span>
            </div>

            <ul class="space-y-2 text-xs sm:text-sm text-[#D4D4D8]">
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>3 PDF exports per month</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>Up to 50 findings per CLI upload</span>
              </li>
              <li class="flex items-center gap-2 text-[#8A8D96]">
                <X class="h-4 w-4 text-amber-400 shrink-0" aria-hidden="true" />
                <span>Preview watermark included</span>
              </li>
            </ul>
          </div>

          <button
            type="button"
            disabled
            class="btn-glass w-full py-2.5 text-xs opacity-50 cursor-not-allowed"
          >
            {{ currentTier === 'FREE' ? 'Current plan' : 'Free tier' }}
          </button>
        </div>

        <!-- Pro -->
        <div
          :class="[
            'p-6 flex flex-col justify-between space-y-6',
            currentTier === 'PRO' ? 'bg-emerald-500/[0.03]' : 'bg-white/[0.025]',
          ]"
        >
          <div class="space-y-4">
            <div class="space-y-1">
              <div class="flex items-center justify-between gap-2">
                <h3 class="text-lg font-display font-semibold text-[#F5F5F3]">Pro</h3>
                <span
                  :class="[
                    'px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider border',
                    currentTier === 'PRO'
                      ? 'bg-emerald-500/10 border-emerald-400/30 text-emerald-300'
                      : 'bg-[#F5F5F3] border-[#F5F5F3] text-[#050507] font-semibold',
                  ]"
                >
                  {{ currentTier === 'PRO' ? 'Active' : 'Popular' }}
                </span>
              </div>
              <p class="text-xs text-[#D4D4D8]">
                Clean, white-label reporting designed for consulting teams.
              </p>
            </div>

            <div class="pt-3 border-t border-white/[0.08] text-2xl font-display font-bold text-[#F5F5F3] font-mono tabular-nums">
              Rp 750,000 <span class="text-xs font-sans font-normal text-[#8A8D96]">/ month</span>
            </div>

            <ul class="space-y-2 text-xs sm:text-sm text-[#F5F5F3]">
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>30 branded PDF exports per month</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>Custom logo, colors, and NDA notice</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>Up to 500 findings per CLI upload</span>
              </li>
            </ul>
          </div>

          <button
            v-if="currentTier === 'PRO'"
            type="button"
            disabled
            class="btn-glass w-full py-2.5 text-xs border-emerald-400/35 text-emerald-300 cursor-not-allowed"
          >
            Pro plan active
          </button>
          <button
            v-else-if="currentTier === 'ENTERPRISE'"
            type="button"
            disabled
            class="btn-glass w-full py-2.5 text-xs opacity-50 cursor-not-allowed"
          >
            Included in Enterprise
          </button>
          <button
            v-else
            type="button"
            :disabled="!isManager || checkingOut"
            @click="handleCheckoutPro"
            class="btn-platinum w-full py-2.5 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="checkingOut" class="h-3.5 w-3.5 animate-spin" />
            <span>
              {{
                checkingOut
                  ? 'Starting checkout...'
                  : isManager
                    ? 'Upgrade to Pro'
                    : 'Only Managers can upgrade'
              }}
            </span>
          </button>
        </div>

        <!-- Enterprise -->
        <div
          :class="[
            'p-6 flex flex-col justify-between space-y-6',
            currentTier === 'ENTERPRISE' ? 'bg-white/[0.03]' : '',
          ]"
        >
          <div class="space-y-4">
            <div class="space-y-1">
              <div class="flex items-center justify-between gap-2">
                <h3 class="text-lg font-display font-semibold text-[#F5F5F3]">Enterprise</h3>
                <span
                  v-if="currentTier === 'ENTERPRISE'"
                  class="px-2 py-0.5 bg-white/[0.08] border border-white/[0.24] text-[#F5F5F3] font-mono text-[10px] uppercase tracking-wider"
                >
                  Active
                </span>
              </div>
              <p class="text-xs text-[#8A8D96]">For larger security teams and dedicated environments.</p>
            </div>

            <div class="pt-3 border-t border-white/[0.08] text-2xl font-display font-bold text-[#F5F5F3]">Contact sales</div>

            <ul class="space-y-2 text-xs sm:text-sm text-[#D4D4D8]">
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>Custom quota and dedicated support</span>
              </li>
              <li class="flex items-center gap-2">
                <Check class="h-4 w-4 text-emerald-400 shrink-0" aria-hidden="true" />
                <span>On-premise or private cloud deployment</span>
              </li>
            </ul>
          </div>

          <button
            v-if="currentTier === 'ENTERPRISE'"
            type="button"
            disabled
            class="btn-glass w-full py-2.5 text-xs border-white/[0.25] text-[#F5F5F3] cursor-not-allowed"
          >
            Enterprise plan active
          </button>
          <router-link
            v-else
            to="/contact"
            class="btn-glass w-full py-2.5 text-xs justify-center"
          >
            Contact sales
          </router-link>
        </div>
      </div>

      <!-- Compact Feature Comparison Matrix -->
      <div class="border border-white/[0.11] bg-[#08080B] overflow-hidden">
        <div class="px-6 py-4 border-b border-white/[0.1] bg-[#050507]">
          <h3 class="text-sm font-display font-semibold text-[#F5F5F3]">Plan Comparison</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b border-white/[0.1] text-[#8A8D96] bg-[#050507] font-mono uppercase text-[10px] tracking-wider">
              <tr>
                <th class="py-3 px-6 font-medium">Feature</th>
                <th class="py-3 px-4 font-medium">Free</th>
                <th class="py-3 px-4 font-medium text-[#F5F5F3]">Pro</th>
                <th class="py-3 px-4 font-medium text-[#D4D4D8]">Enterprise</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.08] text-[#D4D4D8]">
              <tr>
                <td class="py-3 px-6 font-medium text-[#F5F5F3]">Monthly PDF quota</td>
                <td class="py-3 px-4 font-mono tabular-nums">3 / mo</td>
                <td class="py-3 px-4 font-mono text-[#F5F5F3] font-semibold tabular-nums">30 / mo</td>
                <td class="py-3 px-4">Unlimited</td>
              </tr>
              <tr>
                <td class="py-3 px-6 font-medium text-[#F5F5F3]">CLI upload limit</td>
                <td class="py-3 px-4 font-mono tabular-nums">50 findings</td>
                <td class="py-3 px-4 font-mono text-[#F5F5F3] font-semibold tabular-nums">500 findings</td>
                <td class="py-3 px-4">Custom</td>
              </tr>
              <tr>
                <td class="py-3 px-6 font-medium text-[#F5F5F3]">White-label branding</td>
                <td class="py-3 px-4">Preview watermark</td>
                <td class="py-3 px-4 text-emerald-400 font-medium">Clean + Custom Logo</td>
                <td class="py-3 px-4 text-emerald-400 font-medium">Custom Templates</td>
              </tr>
              <tr>
                <td class="py-3 px-6 font-medium text-[#F5F5F3]">Deployment &amp; support</td>
                <td class="py-3 px-4">Cloud SaaS</td>
                <td class="py-3 px-4">Priority Cloud SaaS</td>
                <td class="py-3 px-4">On-Premise / SLA</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Midtrans Checkout Modal -->
    <BaseModal
      :open="Boolean(checkoutResult) && snapModalOpen"
      title="Midtrans Checkout"
      subtitle="Complete payment on Midtrans, then click Sync payment status."
      max-width="md"
      @close="snapModalOpen = false"
    >
      <div v-if="checkoutResult" class="space-y-4">
        <dl class="p-4 bg-[#050507] border border-white/[0.1] space-y-2 text-xs">
          <div class="flex justify-between text-[#8A8D96]">
            <dt>Order ID</dt>
            <dd class="text-[#F5F5F3] font-mono font-semibold">{{ checkoutResult.order_id }}</dd>
          </div>
          <div class="border-t border-white/[0.08] pt-2 flex justify-between font-semibold text-sm text-emerald-400 tabular-nums">
            <dt>Amount due</dt>
            <dd class="font-mono">Rp {{ checkoutResult.gross_amount.toLocaleString('en-US') }}</dd>
          </div>
        </dl>

        <details class="text-xs font-mono text-[#8A8D96] border border-white/[0.1] bg-[#050507] p-3">
          <summary class="cursor-pointer font-sans text-[#D4D4D8] font-medium">Payment token details</summary>
          <div class="mt-2 break-all text-[#F5F5F3]">{{ checkoutResult.snap_token }}</div>
        </details>

        <div class="flex flex-col gap-2.5 pt-1">
          <a
            :href="checkoutResult.redirect_url"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-platinum w-full px-4 py-2.5 text-xs"
          >
            <span>Open payment page</span>
            <ExternalLink class="h-3.5 w-3.5" aria-hidden="true" />
          </a>

          <button
            type="button"
            @click="handleSyncStatus"
            :disabled="syncing"
            class="btn-glass w-full px-4 py-2.5 text-xs border-emerald-400/35 text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50"
          >
            <RefreshCw :class="['h-3.5 w-3.5', syncing ? 'animate-spin' : '']" aria-hidden="true" />
            <span>{{ syncing ? 'Checking payment status...' : 'Sync payment status' }}</span>
          </button>
        </div>
      </div>
    </BaseModal>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  AlertTriangle,
  Check,
  CreditCard,
  ExternalLink,
  Loader2,
  RefreshCw,
  X,
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { api, type MidtransCheckoutResponse } from '@/services/api'
import { session } from '@/stores/session'
import { toast } from '@/stores/toast'

const sub = computed(() => session.state.subscription)
const isManager = computed(() => session.activeRole.value === 'MANAGER')

const currentTier = computed(() => sub.value?.tier || 'FREE')
const usedReports = computed(() => sub.value?.reports_used_this_month ?? 0)
const maxReports = computed(() => sub.value?.monthly_report_quota ?? 3)
const remainingReports = computed(
  () => sub.value?.remaining_reports ?? Math.max(0, maxReports.value - usedReports.value)
)
const quotaPct = computed(() =>
  maxReports.value > 0 ? Math.min(100, (usedReports.value / maxReports.value) * 100) : 0
)
const quotaBarClass = computed(() => {
  if (usedReports.value >= maxReports.value) return 'bg-red-500'
  if (quotaPct.value >= 80) return 'bg-amber-400'
  return 'bg-[#F5F5F3]'
})
const formattedResetDate = computed(() => {
  const raw = sub.value?.quota_reset_date
  if (!raw) return '—'
  const d = new Date(raw)
  return Number.isNaN(d.getTime())
    ? raw
    : d.toLocaleDateString('en-US', { day: '2-digit', month: 'long', year: 'numeric' })
})

const checkingOut = ref(false)
const syncing = ref(false)
const checkoutResult = ref<MidtransCheckoutResponse | null>(null)
const snapModalOpen = ref(false)

onMounted(() => {
  void session.refreshSubscription()
})

watch(
  () => session.state.activeWorkspaceId,
  () => {
    checkoutResult.value = null
    snapModalOpen.value = false
  }
)

const handleCheckoutPro = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  checkingOut.value = true
  try {
    checkoutResult.value = await api.billing.checkoutPro(wId)
    snapModalOpen.value = true
    await session.refreshSubscription()
    toast.success('Midtrans checkout session created.')
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to start checkout session.')
  } finally {
    checkingOut.value = false
  }
}

const handleSyncStatus = async () => {
  const wId = session.state.activeWorkspaceId
  if (!wId) return
  syncing.value = true
  try {
    const updated = await api.billing.syncStatus(wId)
    session.state.subscription = updated
    if (updated.tier === 'PRO') {
      checkoutResult.value = null
      snapModalOpen.value = false
      toast.success('Payment confirmed! Your workspace is now on the Pro plan.')
    } else {
      toast.info(`Latest payment status: ${updated.payment_status}`)
    }
  } catch (err: unknown) {
    toast.error(err instanceof Error ? err.message : 'Unable to sync payment status.')
  } finally {
    syncing.value = false
  }
}
</script>
