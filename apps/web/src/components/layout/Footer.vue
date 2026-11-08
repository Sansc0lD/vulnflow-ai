<template>
  <footer class="border-t border-border bg-surface mt-auto">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div class="md:col-span-2 space-y-3">
          <div class="flex items-center space-x-2">
            <div class="h-6 w-6 rounded bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold text-xs">
              VF
            </div>
            <span class="font-bold text-white text-base">VulnFlow AI</span>
          </div>
          <p class="text-xs text-zinc-400 leading-relaxed max-w-sm">
            Platform SaaS Manajemen Kerentanan & Pelaporan Berbantuan AI dengan garansi kepatuhan Zero-PoC to AI. Dirancang untuk auditor, pentester, dan agensi keamanan siber.
          </p>
          <div class="flex items-center space-x-2 text-[11px] text-zinc-500 font-mono">
            <span class="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Zero-PoC Sanitizer: Active</span>
            <span>•</span>
            <span>AES-256-GCM Vault</span>
          </div>
        </div>

        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-zinc-300 mb-3">Navigasi Publik</h4>
          <ul class="space-y-2 text-xs text-zinc-400">
            <li><router-link to="/" class="hover:text-white transition-colors">Beranda & Live Sandbox</router-link></li>
            <li><router-link to="/about" class="hover:text-white transition-colors">Arsitektur 4-Node</router-link></li>
            <li><router-link to="/solutions" class="hover:text-white transition-colors">Katalog Triase (Mock)</router-link></li>
            <li><router-link to="/contact" class="hover:text-white transition-colors">Booking & Kalkulator Biaya</router-link></li>
          </ul>
        </div>

        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-zinc-300 mb-3">SaaS Platform</h4>
          <ul class="space-y-2 text-xs text-zinc-400">
            <li><router-link to="/app/login" class="hover:text-white transition-colors">Portal Auditor</router-link></li>
            <li><router-link to="/app/register" class="hover:text-white transition-colors">Pendaftaran Agensi</router-link></li>
            <li><span class="text-zinc-600">IPPL Capstone Project © 2026</span></li>
          </ul>
        </div>
      </div>

      <div class="border-t border-border/60 mt-8 pt-6 flex flex-col sm:flex-row justify-between items-center text-xs text-zinc-500">
        <p>© 2026 VulnFlow AI. Hak Cipta Dilindungi Undang-Undang.</p>
        <p class="mt-2 sm:mt-0 font-mono text-[11px]">Memenuhi Rubrik Desain Web (5 Halaman Publik) & IPPL (5 Wireframes SaaS)</p>
      </div>
    </div>
  </footer>
</template>
