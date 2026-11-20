<template>
  <div class="relative flex flex-col min-h-screen bg-[#050507] text-[#F5F5F3]">
    <AmbientCanvas intensity="hero" />

    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[120] focus:px-4 focus:py-2 focus:rounded-none focus:bg-[#F5F5F3] focus:text-[#050507] focus:text-xs focus:font-semibold"
    >
      Skip to main content
    </a>

    <Navbar />

    <main id="main-content" class="relative z-10 flex-1 flex flex-col">
      <slot />
    </main>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import AmbientCanvas from '@/components/ui/AmbientCanvas.vue'
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'
</script>
