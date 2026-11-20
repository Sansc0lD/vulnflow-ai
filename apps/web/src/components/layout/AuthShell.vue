<template>
  <div class="relative min-h-screen bg-[#050507] text-[#F5F5F3] grid grid-cols-1 lg:grid-cols-12">
    <AmbientCanvas intensity="hero" />

    <!-- Left Editorial Monograph Showcase (Desktop) -->
    <div
      class="relative z-10 hidden lg:flex lg:col-span-5 border-r border-white/[0.1] bg-[#050507] p-10 xl:p-12 flex-col justify-between"
    >
      <div class="space-y-10 max-w-md">
        <router-link to="/" class="inline-block">
          <BrandLogo size="lg" />
        </router-link>

        <div class="space-y-4">
          <h1 class="font-display text-4xl font-bold tracking-[-0.035em] text-[#F5F5F3] leading-[1.06]">
            Security reporting,
            stripped of <span class="font-serif italic font-normal text-white">noise.</span>
          </h1>
          <p class="text-sm text-[#8A8D96] leading-relaxed">
            Organize scan results locally, draft executive summaries without exposing proof, and export white-label A4 reports from one calm workspace.
          </p>
        </div>

        <ul class="border-y border-white/[0.1] divide-y divide-white/[0.08] text-xs">
          <li class="py-4 flex items-start gap-3">
            <Lock class="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <div class="font-semibold text-[#F5F5F3]">Private by default</div>
              <div class="text-[#8A8D96] mt-0.5 leading-relaxed">Sensitive technical proof stays encrypted inside your vault and never leaves your boundary.</div>
            </div>
          </li>
          <li class="py-4 flex items-start gap-3">
            <Terminal class="h-4 w-4 text-[#F5F5F3] shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <div class="font-semibold text-[#F5F5F3]">Local-first imports</div>
              <div class="text-[#8A8D96] mt-0.5 leading-relaxed">Run scans on your own workstation and sync structured outputs whenever ready.</div>
            </div>
          </li>
          <li class="py-4 flex items-start gap-3">
            <FileText class="h-4 w-4 text-[#F5F5F3] shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <div class="font-semibold text-[#F5F5F3]">Client-ready PDF exports</div>
              <div class="text-[#8A8D96] mt-0.5 leading-relaxed">Customize colors, logos, and executive summaries before delivery.</div>
            </div>
          </li>
        </ul>
      </div>

      <div class="text-xs font-mono text-[#8A8D96]">
        © 2026 VulnFlow
      </div>
    </div>

    <!-- Right Auth Form Area -->
    <div class="relative z-10 lg:col-span-7 flex flex-col items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-md space-y-6">
        <div class="flex items-center justify-between lg:justify-end">
          <router-link to="/" class="lg:hidden">
            <BrandLogo size="sm" />
          </router-link>
          <router-link
            to="/"
            class="text-xs text-[#8A8D96] hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors inline-flex items-center gap-1"
          >
            <ArrowLeft class="h-3.5 w-3.5" />
            <span>Back to home</span>
          </router-link>
        </div>

        <GlassSurface strong padding="p-6 sm:p-8 space-y-6">
          <slot />
        </GlassSurface>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, FileText, Lock, Terminal } from 'lucide-vue-next'
import AmbientCanvas from '@/components/ui/AmbientCanvas.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import GlassSurface from '@/components/ui/GlassSurface.vue'
</script>
