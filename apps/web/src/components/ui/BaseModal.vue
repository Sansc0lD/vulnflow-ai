<template>
  <Teleport to="body">
    <Transition name="vf-modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto"
        @click.self="handleBackdropClick"
      >
        <div
          ref="dialogRef"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : undefined"
          tabindex="-1"
          :class="[
            'w-full rounded-none bg-[#08080B] border border-white/[0.14] overflow-hidden flex flex-col max-h-[90vh] outline-none my-auto',
            maxWidthClass,
          ]"
        >
          <!-- Header -->
          <div
            v-if="title || $slots.header"
            class="flex items-start justify-between gap-4 px-6 py-4 border-b border-white/[0.1] bg-[#050507] shrink-0"
          >
            <slot name="header">
              <div class="min-w-0">
                <h3 :id="titleId" class="text-base font-display font-bold text-[#F5F5F3] truncate">
                  {{ title }}
                </h3>
                <p v-if="subtitle" class="text-xs text-[#8A8D96] mt-0.5 leading-relaxed">
                  {{ subtitle }}
                </p>
              </div>
            </slot>

            <button
              v-if="closable"
              type="button"
              @click="emit('close')"
              class="p-1.5 rounded-none text-[#8A8D96] hover:text-[#F5F5F3] hover:bg-white/[0.06] transition-colors shrink-0 min-h-[36px] min-w-[36px] flex items-center justify-center"
              aria-label="Close dialog"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 overflow-y-auto flex-1">
            <slot />
          </div>

          <!-- Footer -->
          <div
            v-if="$slots.footer"
            class="px-6 py-4 border-t border-white/[0.1] bg-[#050507] flex flex-wrap items-center justify-end gap-2.5 shrink-0"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    subtitle?: string
    maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
    closable?: boolean
    closeOnBackdrop?: boolean
  }>(),
  {
    title: '',
    subtitle: '',
    maxWidth: 'lg',
    closable: true,
    closeOnBackdrop: true,
  }
)

const emit = defineEmits<{
  (e: 'close'): void
}>()

const titleId = `vf-modal-${Math.random().toString(36).slice(2, 9)}`
const dialogRef = ref<HTMLElement | null>(null)

const maxWidthClass = computed(() => {
  switch (props.maxWidth) {
    case 'sm':
      return 'max-w-sm'
    case 'md':
      return 'max-w-md'
    case 'xl':
      return 'max-w-2xl'
    case '2xl':
      return 'max-w-4xl'
    default:
      return 'max-w-lg'
  }
})

const handleBackdropClick = () => {
  if (props.closable && props.closeOnBackdrop) {
    emit('close')
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.open && props.closable) {
    emit('close')
  }
}

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeydown)
      await nextTick()
      dialogRef.value?.focus()
    } else {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeydown)
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleKeydown)
})
</script>
