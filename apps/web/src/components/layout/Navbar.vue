<template>
  <header class="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex h-16 items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center space-x-2.5 group">
        <div class="h-9 w-9 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500 group-hover:scale-105 transition-transform">
          <ShieldAlert class="h-5 w-5" />
        </div>
        <div class="flex flex-col">
          <span class="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            VulnFlow <span class="text-xs font-semibold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">AI</span>
          </span>
          <span class="text-[10px] text-zinc-400 tracking-wide">ZERO-POC SAAS PLATFORM</span>
        </div>
      </router-link>

      <!-- Navigation Links -->
      <nav class="hidden md:flex items-center space-x-6 text-sm font-medium">
        <router-link
          to="/"
          class="text-zinc-400 hover:text-white transition-colors"
          active-class="!text-white font-semibold"
        >
          Beranda
        </router-link>
        <router-link
          to="/about"
          class="text-zinc-400 hover:text-white transition-colors"
          active-class="!text-white font-semibold"
        >
          Arsitektur Keamanan
        </router-link>
        <router-link
          to="/solutions"
          class="text-zinc-400 hover:text-white transition-colors"
          active-class="!text-white font-semibold"
        >
          Katalog Triase (Mock)
        </router-link>
        <router-link
          to="/contact"
          class="text-zinc-400 hover:text-white transition-colors"
          active-class="!text-white font-semibold"
        >
          Booking Audit
        </router-link>
      </nav>

      <!-- CTA / Auth Buttons -->
      <div class="flex items-center space-x-3">
        <template v-if="isAuthenticated">
          <router-link
            to="/app/dashboard"
            class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-500 transition-colors"
          >
            Masuk ke Dasbor
            <ArrowRight class="ml-1.5 h-4 w-4" />
          </router-link>
        </template>
        <template v-else>
          <router-link
            to="/app/login"
            class="text-sm font-medium text-zinc-300 hover:text-white transition-colors px-3 py-2"
          >
            Masuk
          </router-link>
          <router-link
            to="/app/register"
            class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-500 transition-colors"
          >
            Daftar Gratis
          </router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ShieldAlert, ArrowRight } from 'lucide-vue-next'
import { authStorage } from '@/services/api'

const isAuthenticated = computed(() => !!authStorage.getToken())
</script>
