<template>
  <nav
    aria-label="Reporting workflow"
    class="border border-white/[0.11] bg-[#08080B]"
  >
    <ol class="grid grid-cols-2 sm:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-white/[0.09]">
      <li v-for="step in steps" :key="step.num" class="min-w-0">
        <button
          v-if="step.action === 'cli'"
          type="button"
          @click="emit('open-cli')"
          :class="[
            'w-full flex items-center gap-2.5 px-3.5 py-2.5 text-left transition-colors',
            activeStep === step.num
              ? 'bg-[#F5F5F3] text-[#050507]'
              : 'text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
          ]"
        >
          <span
            :class="[
              'h-5 w-5 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 tabular-nums border',
              activeStep === step.num
                ? 'border-[#050507]/30 bg-[#050507] text-[#F5F5F3]'
                : 'border-white/[0.14] text-[#8A8D96]',
            ]"
          >
            {{ String(step.num).padStart(2, '0') }}
          </span>
          <div class="min-w-0">
            <div class="text-xs font-semibold truncate">{{ step.label }}</div>
            <div :class="['text-[10px] font-mono truncate', activeStep === step.num ? 'text-[#050507]/70' : 'text-[#8A8D96]']">
              {{ step.hint }}
            </div>
          </div>
        </button>

        <router-link
          v-else
          :to="step.to"
          :class="[
            'w-full flex items-center gap-2.5 px-3.5 py-2.5 text-left transition-colors',
            activeStep === step.num
              ? 'bg-[#F5F5F3] text-[#050507]'
              : activeStep > step.num
                ? 'text-[#F5F5F3] bg-emerald-500/[0.04] hover:bg-emerald-500/[0.08]'
                : 'text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
          ]"
        >
          <span
            :class="[
              'h-5 w-5 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 tabular-nums border',
              activeStep === step.num
                ? 'border-[#050507]/30 bg-[#050507] text-[#F5F5F3]'
                : activeStep > step.num
                  ? 'border-emerald-400/40 text-emerald-400'
                  : 'border-white/[0.14] text-[#8A8D96]',
            ]"
          >
            <Check v-if="activeStep > step.num" class="h-3 w-3" aria-hidden="true" />
            <span v-else>{{ String(step.num).padStart(2, '0') }}</span>
          </span>
          <div class="min-w-0">
            <div class="text-xs font-semibold truncate">{{ step.label }}</div>
            <div :class="['text-[10px] font-mono truncate', activeStep === step.num ? 'text-[#050507]/70' : 'text-[#8A8D96]']">
              {{ step.hint }}
            </div>
          </div>
        </router-link>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { Check } from 'lucide-vue-next'

withDefaults(
  defineProps<{
    activeStep?: number
  }>(),
  {
    activeStep: 0,
  }
)

const emit = defineEmits<{
  (e: 'open-cli'): void
}>()

const steps: Array<{ num: number; label: string; hint: string; to: string; action?: 'cli' }> = [
  { num: 1, label: 'Project & Scope', hint: 'Targets & dates', to: '/app/projects' },
  { num: 2, label: 'Import Scans', hint: 'CLI or manual', to: '/app/projects', action: 'cli' },
  { num: 3, label: 'Review Findings', hint: 'Score & select', to: '/app/triage' },
  { num: 4, label: 'Report Draft', hint: 'Executive summary', to: '/app/ai-review' },
  { num: 5, label: 'Export PDF', hint: 'Brand & download', to: '/app/theme' },
]
</script>
