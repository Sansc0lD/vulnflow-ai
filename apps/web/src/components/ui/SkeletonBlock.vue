<template>
  <div v-if="variant === 'kpi'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border border-white/[0.11] divide-y sm:divide-y-0 sm:divide-x divide-white/[0.11] bg-[#08080B]">
    <div
      v-for="i in count"
      :key="i"
      class="p-5 space-y-3 animate-pulse"
    >
      <div class="flex items-center justify-between">
        <div class="h-3 w-24 bg-white/[0.07]"></div>
        <div class="h-4 w-4 bg-white/[0.07]"></div>
      </div>
      <div class="h-7 w-28 bg-white/[0.09]"></div>
      <div class="h-3 w-36 bg-white/[0.05]"></div>
    </div>
  </div>

  <div v-else-if="variant === 'card'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div
      v-for="i in count"
      :key="i"
      class="border border-white/[0.11] bg-[#08080B] p-5 space-y-4 animate-pulse"
    >
      <div class="h-4 w-2/3 bg-white/[0.08]"></div>
      <div class="h-3 w-1/2 bg-white/[0.05]"></div>
      <div class="space-y-2 pt-2">
        <div class="h-3 w-full bg-white/[0.06]"></div>
        <div class="h-3 w-5/6 bg-white/[0.05]"></div>
      </div>
      <div class="h-8 w-full bg-white/[0.07] border border-white/[0.08]"></div>
    </div>
  </div>

  <div v-else-if="variant === 'table-row'" class="space-y-2.5 animate-pulse p-4">
    <div
      v-for="i in count"
      :key="i"
      class="h-11 w-full bg-white/[0.04] border border-white/[0.08]"
    ></div>
  </div>

  <div v-else class="space-y-2.5 animate-pulse">
    <div
      v-for="i in count"
      :key="i"
      :class="['h-3.5 bg-white/[0.06]', i % 2 === 0 ? 'w-4/5' : 'w-full']"
    ></div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'kpi' | 'card' | 'table-row' | 'text'
    count?: number
  }>(),
  {
    variant: 'text',
    count: 3,
  }
)
</script>
