<template>
  <div class="inline-flex items-center gap-2.5 select-none">
    <div
      :class="[
        'rounded-none bg-white/[0.03] border border-white/[0.18] flex items-center justify-center shrink-0',
        sizeClasses.box,
      ]"
    >
      <svg
        :class="sizeClasses.icon"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <path
          d="M12 2.5L19.5 5.75V11.75C19.5 16.85 16.25 21 12 22.5C7.75 21 4.5 16.85 4.5 11.75V5.75L12 2.5Z"
          class="fill-white/[0.04] stroke-[#F5F5F3]"
          stroke-width="1.6"
          stroke-linejoin="round"
        />
        <path
          d="M8.75 11.75L11 14L15.5 9.5"
          class="stroke-[#F5F5F3]"
          stroke-width="1.9"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>

    <div class="flex flex-col leading-none">
      <span
        :class="[
          'font-display font-semibold tracking-tight text-[#F5F5F3]',
          sizeClasses.title,
        ]"
      >
        VulnFlow
      </span>
      <span v-if="subtitle" class="text-[11px] text-[#8A8D96] mt-0.5">
        {{ subtitle }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    size?: 'sm' | 'md' | 'lg'
    subtitle?: string
    showBadge?: boolean
  }>(),
  {
    size: 'md',
    subtitle: '',
    showBadge: false,
  }
)

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return { box: 'h-7 w-7', icon: 'h-4 w-4', title: 'text-sm' }
    case 'lg':
      return { box: 'h-10 w-10', icon: 'h-5 w-5', title: 'text-lg' }
    default:
      return { box: 'h-9 w-9', icon: 'h-5 w-5', title: 'text-base' }
  }
})
</script>
