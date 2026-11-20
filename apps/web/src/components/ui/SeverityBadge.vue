<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 font-mono font-medium rounded-none border shrink-0 tabular-nums uppercase tracking-wider',
      size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-[11px] px-2.5 py-1',
      styleInfo.badgeClass,
    ]"
  >
    <span :class="['h-1.5 w-1.5 rounded-full shrink-0', styleInfo.dotClass]" aria-hidden="true" />
    <span>{{ titleLabel }}</span>
    <span v-if="typeof score === 'number'" class="opacity-85">
      {{ score.toFixed(1) }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getSeverityStyle } from '@/utils/cvss'

const props = withDefaults(
  defineProps<{
    severity: string
    score?: number
    size?: 'sm' | 'md'
  }>(),
  {
    score: undefined,
    size: 'sm',
  }
)

const styleInfo = computed(() => getSeverityStyle(props.severity))
const titleLabel = computed(() => {
  const lbl = styleInfo.value.label
  return lbl.charAt(0) + lbl.slice(1).toLowerCase()
})
</script>
