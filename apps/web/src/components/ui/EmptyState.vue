<template>
  <div
    class="rounded-none border border-dashed border-white/[0.16] bg-[#08080B] p-8 sm:p-10 text-center flex flex-col items-center justify-center gap-3"
  >
    <div
      class="h-11 w-11 rounded-none bg-white/[0.03] border border-white/[0.16] flex items-center justify-center text-[#F5F5F3]"
    >
      <component v-if="icon" :is="icon" class="h-5 w-5" aria-hidden="true" />
      <Inbox v-else class="h-5 w-5" aria-hidden="true" />
    </div>

    <div class="space-y-1 max-w-md">
      <h3 class="text-sm sm:text-base font-display font-bold text-[#F5F5F3]">{{ title }}</h3>
      <p class="text-xs sm:text-sm text-[#8A8D96] leading-relaxed">{{ description }}</p>
    </div>

    <div v-if="$slots.actions || actionLabel" class="pt-1 flex flex-wrap items-center justify-center gap-2.5">
      <slot name="actions">
        <router-link v-if="actionTo && actionLabel" :to="actionTo" class="btn-platinum px-4 py-2 text-xs">
          <span>{{ actionLabel }}</span>
        </router-link>
        <button
          v-else-if="actionLabel"
          type="button"
          @click="emit('action')"
          class="btn-platinum px-4 py-2 text-xs"
        >
          <span>{{ actionLabel }}</span>
        </button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { Inbox } from 'lucide-vue-next'

withDefaults(
  defineProps<{
    icon?: Component
    title: string
    description: string
    actionLabel?: string
    actionTo?: string
  }>(),
  {
    icon: undefined,
    actionLabel: '',
    actionTo: '',
  }
)

const emit = defineEmits<{
  (e: 'action'): void
}>()
</script>
