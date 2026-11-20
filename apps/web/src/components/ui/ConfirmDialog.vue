<template>
  <BaseModal
    :open="open"
    max-width="sm"
    :closable="!loading"
    :close-on-backdrop="!loading"
    @close="emit('cancel')"
  >
    <template #header>
      <div class="flex items-center gap-2.5">
        <div :class="['h-8 w-8 rounded-none flex items-center justify-center shrink-0 border', iconBoxClass]">
          <AlertTriangle v-if="variant === 'danger' || variant === 'warning'" class="h-4 w-4" />
          <Info v-else class="h-4 w-4" />
        </div>
        <h3 class="text-sm font-display font-bold text-[#F5F5F3]">{{ title }}</h3>
      </div>
    </template>

    <p class="text-sm text-[#D4D4D8] leading-relaxed">{{ message }}</p>

    <template #footer>
      <button
        type="button"
        :disabled="loading"
        @click="emit('cancel')"
        class="btn-glass px-4 py-2 text-xs disabled:opacity-50"
      >
        {{ cancelText }}
      </button>
      <button
        type="button"
        :disabled="loading"
        @click="emit('confirm')"
        :class="[
          'inline-flex items-center gap-1.5 px-4 py-2 rounded-none text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
          confirmBtnClass,
        ]"
      >
        <Loader2 v-if="loading" class="h-3.5 w-3.5 animate-spin" />
        <span>{{ confirmText }}</span>
      </button>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, Info, Loader2 } from 'lucide-vue-next'
import BaseModal from '@/components/ui/BaseModal.vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    variant?: 'danger' | 'warning' | 'primary'
    loading?: boolean
  }>(),
  {
    confirmText: 'Continue',
    cancelText: 'Cancel',
    variant: 'primary',
    loading: false,
  }
)

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const iconBoxClass = computed(() => {
  switch (props.variant) {
    case 'danger':
      return 'bg-red-500/10 border-red-400/35 text-red-300'
    case 'warning':
      return 'bg-amber-500/10 border-amber-400/35 text-amber-300'
    default:
      return 'bg-white/[0.04] border-white/[0.16] text-[#F5F5F3]'
  }
})

const confirmBtnClass = computed(() => {
  switch (props.variant) {
    case 'danger':
      return 'bg-red-600 text-white hover:bg-red-500'
    case 'warning':
      return 'bg-amber-600 text-white hover:bg-amber-500'
    default:
      return 'bg-[#F5F5F3] text-[#050507] hover:bg-white'
  }
})
</script>
