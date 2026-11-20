<template>
  <footer class="relative z-10 border-t border-white/[0.1] bg-[#050507] mt-auto">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div class="md:col-span-2 space-y-3">
          <BrandLogo size="md" />
          <p class="text-xs sm:text-sm text-[#8A8D96] leading-relaxed max-w-md">
            Turn security scan results into clear, client-ready reports — without exposing sensitive proof.
          </p>
        </div>

        <div>
          <h4 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#F5F5F3] mb-3">
            Product
          </h4>
          <ul class="space-y-2.5 text-xs sm:text-sm text-[#8A8D96]">
            <li>
              <router-link to="/" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                Home
              </router-link>
            </li>
            <li>
              <router-link to="/about" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                How it works
              </router-link>
            </li>
            <li>
              <router-link to="/solutions" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                Interactive demo
              </router-link>
            </li>
            <li>
              <router-link to="/contact" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                Pricing &amp; estimator
              </router-link>
            </li>
          </ul>
        </div>

        <div>
          <h4 class="font-mono text-[11px] uppercase tracking-[0.12em] text-[#F5F5F3] mb-3">
            Account
          </h4>
          <ul class="space-y-2.5 text-xs sm:text-sm text-[#8A8D96]">
            <li>
              <router-link to="/app/login" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                Sign in
              </router-link>
            </li>
            <li>
              <router-link to="/app/register" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                Create free workspace
              </router-link>
            </li>
            <li>
              <router-link to="/app/forgot-password" class="hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors">
                Reset password
              </router-link>
            </li>
          </ul>
        </div>
      </div>

      <div
        class="border-t border-white/[0.1] mt-10 pt-6 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-[#8A8D96]"
      >
        <p>© 2026 VulnFlow. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import BrandLogo from '@/components/ui/BrandLogo.vue'
</script>
