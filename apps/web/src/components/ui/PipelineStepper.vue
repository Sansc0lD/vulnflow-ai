<template>
  <nav
    v-if="activeProject"
    aria-label="Active project workflow progress"
    class="border border-white/[0.11] bg-[#08080B]"
  >
    <div
      class="px-3.5 py-2 border-b border-white/[0.08] bg-[#050507] flex flex-wrap items-center justify-between gap-2"
    >
      <div class="flex items-center gap-2 min-w-0">
        <span class="font-mono text-[10px] uppercase tracking-[0.12em] text-[#8A8D96] shrink-0">
          Workflow Progress
        </span>
        <span class="text-white/25" aria-hidden="true">/</span>
        <span class="text-xs font-medium text-[#F5F5F3] truncate">{{ activeProject.name }}</span>
      </div>
      <span class="font-mono text-[10px] text-[#8A8D96] tabular-nums shrink-0">
        {{ completedCount }} / {{ steps.length }} complete
      </span>
    </div>

    <ol class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-px bg-white/[0.09]">
      <li v-for="step in steps" :key="step.num" class="min-w-0 bg-[#08080B]">
        <component
          :is="step.action === 'cli' ? 'button' : RouterLink"
          v-bind="step.action === 'cli' ? { type: 'button' } : { to: step.to }"
          :aria-current="activeStep === step.num ? 'step' : undefined"
          @click="step.action === 'cli' ? emit('open-cli') : undefined"
          :class="[
            'w-full min-h-[50px] flex items-center gap-2.5 px-3.5 py-2.5 text-left transition-colors',
            activeStep === step.num
              ? 'bg-[#F5F5F3] text-[#050507]'
              : step.done
                ? 'text-[#F5F5F3] bg-emerald-500/[0.04] hover:bg-emerald-500/[0.08]'
                : step.inProgress
                  ? 'text-[#F5F5F3] bg-amber-500/[0.03] hover:bg-white/[0.04]'
                  : 'text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.03]',
          ]"
        >
          <span
            :class="[
              'h-5 w-5 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 tabular-nums border',
              activeStep === step.num && step.done
                ? 'border-[#050507]/30 bg-[#050507] text-emerald-400'
                : activeStep === step.num
                  ? 'border-[#050507]/30 bg-[#050507] text-[#F5F5F3]'
                  : step.done
                    ? 'border-emerald-400/40 text-emerald-400'
                    : step.inProgress
                      ? 'border-amber-400/40 text-amber-300'
                      : 'border-white/[0.14] text-[#8A8D96]',
            ]"
          >
            <Check v-if="step.done" class="h-3 w-3" aria-hidden="true" />
            <span v-else>{{ String(step.num).padStart(2, '0') }}</span>
          </span>
          <div class="min-w-0">
            <div class="text-xs font-semibold truncate">{{ step.label }}</div>
            <div
              :class="[
                'text-[10px] font-mono truncate',
                activeStep === step.num
                  ? 'text-[#3F3F46]'
                  : step.done
                    ? 'text-emerald-300'
                    : step.inProgress
                      ? 'text-amber-300'
                      : 'text-[#8A8D96]',
              ]"
            >
              {{ step.hint }}
            </div>
          </div>
        </component>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { Check } from 'lucide-vue-next'
import { session } from '@/stores/session'

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

interface WorkflowStepItem {
  num: number
  label: string
  hint: string
  to?: string
  action?: 'cli'
  done: boolean
  inProgress?: boolean
}

const activeProject = session.activeProject

const steps = computed<WorkflowStepItem[]>(() => {
  const proj = activeProject.value
  if (!proj) return []
  const progress = session.state.projectProgress
  const scopeCount = proj.target_scope.length

  return [
    {
      num: 1,
      label: 'Project & Scope',
      hint: `${scopeCount} target${scopeCount === 1 ? '' : 's'}`,
      to: '/app/projects',
      done: true,
    },
    {
      num: 2,
      label: 'Import Scans',
      hint:
        progress.totalFindings > 0
          ? `${progress.totalFindings} finding${progress.totalFindings === 1 ? '' : 's'}`
          : 'CLI or manual',
      action: 'cli',
      done: progress.totalFindings > 0,
    },
    {
      num: 3,
      label: 'Review Findings',
      hint: progress.curatedFindings > 0 ? `${progress.curatedFindings} in report` : 'Score & select',
      to: '/app/triage',
      done: progress.curatedFindings > 0,
      inProgress: progress.totalFindings > 0 && progress.curatedFindings === 0,
    },
    {
      num: 4,
      label: 'Report Draft',
      hint: progress.narrativeApproved
        ? 'Approved'
        : progress.hasNarrative
          ? 'Draft saved'
          : 'Write summary',
      to: '/app/ai-review',
      done: progress.narrativeApproved,
      inProgress: progress.hasNarrative && !progress.narrativeApproved,
    },
    {
      num: 5,
      label: 'Export PDF',
      hint:
        progress.reportCount > 0
          ? `${progress.reportCount} PDF${progress.reportCount === 1 ? '' : 's'}`
          : 'Brand & export',
      to: '/app/theme',
      done: progress.reportCount > 0,
    },
  ]
})

const completedCount = computed(() => steps.value.filter((s) => s.done).length)
</script>
