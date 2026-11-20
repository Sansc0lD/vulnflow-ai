<template>
  <div
    class="fixed bottom-4 inset-x-4 sm:inset-x-auto sm:right-4 z-[100] flex flex-col gap-2 sm:w-full sm:max-w-sm pointer-events-none"
    aria-live="polite"
    aria-atomic="false"
  >
    <TransitionGroup name="vf-toast">
      <div
        v-for="item in toastState.items"
        :key="item.id"
        :role="item.kind === 'error' ? 'alert' : 'status'"
        @mouseenter="toast.pause(item.id)"
        @mouseleave="toast.resume(item.id)"
        :class="[
          'pointer-events-auto rounded-none bg-[#08080B] border border-white/[0.16] p-3.5 flex items-start gap-3 text-xs border-l-2 transition-all shadow-2xl',
          accentClass(item.kind),
        ]"
      >
        <CheckCircle2 v-if="item.kind === 'success'" class="h-4 w-4 shrink-0 mt-0.5 text-emerald-400" aria-hidden="true" />
        <AlertCircle v-else-if="item.kind === 'error'" class="h-4 w-4 shrink-0 mt-0.5 text-red-400" aria-hidden="true" />
        <AlertTriangle v-else-if="item.kind === 'warning'" class="h-4 w-4 shrink-0 mt-0.5 text-amber-300" aria-hidden="true" />
        <Info v-else class="h-4 w-4 shrink-0 mt-0.5 text-[#F5F5F3]" aria-hidden="true" />

        <div class="flex-1 min-w-0">
          <div v-if="item.title" class="font-semibold text-[#F5F5F3]">{{ item.title }}</div>
          <div class="text-[#D4D4D8] leading-relaxed break-words">{{ item.message }}</div>
        </div>

        <button
          type="button"
          @click="toast.dismiss(item.id)"
          class="text-[#8A8D96] hover:text-[#F5F5F3] shrink-0 p-1 rounded-none hover:bg-white/[0.06]"
          aria-label="Dismiss notification"
        >
          <X class="h-3.5 w-3.5" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import { toastState, toast, type ToastKind } from '@/stores/toast'

const accentClass = (kind: ToastKind): string => {
  switch (kind) {
    case 'success':
      return 'border-l-emerald-400'
    case 'error':
      return 'border-l-red-500'
    case 'warning':
      return 'border-l-amber-400'
    default:
      return 'border-l-[#F5F5F3]'
  }
}
</script>
