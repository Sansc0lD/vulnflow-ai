<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 text-[10px] font-mono font-medium px-2 py-0.5 rounded-none border shrink-0 uppercase tracking-wider',
      badgeStyle.cls,
    ]"
  >
    <span v-if="badgeStyle.dot" :class="['h-1.5 w-1.5 rounded-full', badgeStyle.dot]" aria-hidden="true" />
    <span>{{ badgeStyle.label }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const badgeStyle = computed(() => {
  const key = props.status.toUpperCase()
  switch (key) {
    case 'OPEN':
      return {
        label: 'Open',
        cls: 'bg-red-500/10 text-red-300 border-red-400/25',
        dot: 'bg-red-500',
      }
    case 'IN_REVIEW':
      return {
        label: 'In Review',
        cls: 'bg-white/[0.04] text-[#F5F5F3] border-white/[0.16]',
        dot: 'bg-[#F5F5F3]',
      }
    case 'REMEDIATED':
      return {
        label: 'Remediated',
        cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-400/25',
        dot: 'bg-emerald-400',
      }
    case 'APPROVED':
      return {
        label: 'Approved',
        cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-400/25',
        dot: 'bg-emerald-400',
      }
    case 'ACTIVE':
      return {
        label: 'Active',
        cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-400/25',
        dot: 'bg-emerald-400',
      }
    case 'SETTLEMENT':
    case 'COMPLETED':
      return {
        label: 'Completed',
        cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-400/25',
        dot: 'bg-emerald-400',
      }
    case 'NORMAL':
      return {
        label: 'Healthy',
        cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-400/25',
        dot: 'bg-emerald-400',
      }
    case 'PRO':
      return {
        label: 'Pro',
        cls: 'bg-[#F5F5F3] text-[#050507] border-[#F5F5F3] font-semibold',
        dot: '',
      }
    case 'ENTERPRISE':
      return {
        label: 'Enterprise',
        cls: 'bg-white/[0.08] text-[#F5F5F3] border-white/[0.22]',
        dot: 'bg-[#F5F5F3]',
      }
    case 'FREE':
      return {
        label: 'Free',
        cls: 'bg-transparent text-[#8A8D96] border-white/[0.14]',
        dot: 'bg-zinc-500',
      }
    case 'REOPENED':
      return {
        label: 'Reopened',
        cls: 'bg-amber-500/10 text-amber-300 border-amber-400/25',
        dot: 'bg-amber-400',
      }
    case 'UPCOMING':
      return {
        label: 'Scheduled',
        cls: 'bg-amber-500/10 text-amber-300 border-amber-400/25',
        dot: 'bg-amber-400',
      }
    case 'PENDING':
      return {
        label: 'Pending',
        cls: 'bg-amber-500/10 text-amber-300 border-amber-400/25',
        dot: 'bg-amber-400',
      }
    case 'DRAFT':
      return {
        label: 'Draft',
        cls: 'bg-amber-500/10 text-amber-300 border-amber-400/25',
        dot: 'bg-amber-400',
      }
    case 'PROCESSING':
      return {
        label: 'Processing',
        cls: 'bg-amber-500/10 text-amber-300 border-amber-400/25',
        dot: 'bg-amber-400',
      }
    case 'FALSE_POSITIVE':
      return {
        label: 'False Positive',
        cls: 'bg-transparent text-[#8A8D96] border-white/[0.12]',
        dot: 'bg-zinc-500',
      }
    case 'ARCHIVED':
      return {
        label: 'Archived',
        cls: 'bg-transparent text-[#8A8D96] border-white/[0.12]',
        dot: 'bg-zinc-500',
      }
    case 'ACCEPTED_RISK':
      return {
        label: 'Accepted Risk',
        cls: 'bg-white/[0.04] text-zinc-200 border-white/[0.14]',
        dot: 'bg-zinc-300',
      }
    case 'IN-SCOPE':
    case 'IN_SCOPE':
      return {
        label: 'In Scope',
        cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-400/25',
        dot: 'bg-emerald-400',
      }
    case 'QUARANTINED':
      return {
        label: 'Out of Scope',
        cls: 'bg-red-500/10 text-red-300 border-red-400/25',
        dot: 'bg-red-500',
      }
    case 'EXPIRED':
      return {
        label: 'Expired',
        cls: 'bg-transparent text-[#8A8D96] border-white/[0.12]',
        dot: 'bg-zinc-500',
      }
    case 'SUSPENDED':
      return {
        label: 'Suspended',
        cls: 'bg-red-500/10 text-red-300 border-red-400/25',
        dot: 'bg-red-500',
      }
    case 'FAILED':
      return {
        label: 'Failed',
        cls: 'bg-red-500/10 text-red-300 border-red-400/25',
        dot: 'bg-red-500',
      }
    case 'TRIPPED':
      return {
        label: 'Limit Reached',
        cls: 'bg-red-500/10 text-red-300 border-red-400/25',
        dot: 'bg-red-500',
      }
    default:
      return {
        label: key
          .replace(/_/g, ' ')
          .toLowerCase()
          .replace(/\b\w/g, (c) => c.toUpperCase()),
        cls: 'bg-white/[0.03] text-zinc-300 border-white/[0.12]',
        dot: 'bg-zinc-400',
      }
  }
})
</script>
