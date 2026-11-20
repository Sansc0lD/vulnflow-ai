<template>
  <div
    class="fixed inset-0 z-0 pointer-events-none select-none overflow-hidden bg-[#050507]"
    aria-hidden="true"
  >
    <div class="absolute inset-0 vf-noise-overlay" />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    intensity?: 'hero' | 'subtle'
  }>(),
  {
    intensity: 'hero',
  }
)
</script>
