<template>
  <div class="min-h-screen bg-[#050507] text-[#F5F5F3] flex flex-col font-sans">
    <!-- Branded Hydration Loader on initial /app/* bootstrap -->
    <div
      v-if="session.state.hydrating && !session.state.initialized"
      class="fixed inset-0 z-50 flex flex-col items-center justify-center gap-5 p-6"
      role="status"
      aria-live="polite"
    >
      <AmbientCanvas intensity="subtle" />
      <div class="relative z-10 glass-panel-solid rounded-none px-8 py-6 flex flex-col items-center gap-4">
        <BrandLogo size="lg" />
        <div class="flex items-center gap-2 text-xs text-[#8A8D96]">
          <Loader2 class="h-4 w-4 animate-spin text-[#F5F5F3]" aria-hidden="true" />
          <span>Loading your workspace...</span>
        </div>
      </div>
    </div>

    <router-view />
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next'
import AmbientCanvas from '@/components/ui/AmbientCanvas.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'
import { session } from '@/stores/session'
</script>
