<template>
  <component
    :is="as"
    :class="[
      strong ? 'glass-panel-solid' : 'glass-panel',
      rounded,
      padding,
    ]"
  >
    <div class="relative z-10 h-full">
      <slot />
    </div>
  </component>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    as?: string
    interactive?: boolean
    tilt?: boolean
    strong?: boolean
    rounded?: string
    padding?: string
  }>(),
  {
    as: 'div',
    interactive: false,
    tilt: false,
    strong: false,
    rounded: 'rounded-none',
    padding: '',
  }
)
</script>
