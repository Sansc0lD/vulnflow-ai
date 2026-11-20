<template>
  <header class="sticky top-0 z-40 border-b border-white/[0.1] bg-[#050507]">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
      <!-- Brand -->
      <router-link to="/" class="shrink-0">
        <BrandLogo size="sm" />
      </router-link>

      <!-- Desktop Navigation -->
      <nav aria-label="Main navigation" class="hidden md:flex items-center gap-7 text-xs font-medium">
        <router-link
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="text-[#8A8D96] hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors"
          active-class="!text-[#F5F5F3] font-semibold underline underline-offset-4"
        >
          {{ link.label }}
        </router-link>
      </nav>

      <!-- Desktop Auth CTA + Mobile Toggle -->
      <div class="flex items-center gap-4">
        <div class="hidden sm:flex items-center gap-4">
          <template v-if="isAuthenticated">
            <router-link :to="isSuperadmin ? '/app/admin' : '/app/dashboard'" class="btn-platinum px-4 py-1.5 text-xs">
              <span>{{ isSuperadmin ? 'Admin Console' : 'Dashboard' }}</span>
              <ArrowRight class="h-3.5 w-3.5" />
            </router-link>
          </template>
          <template v-else>
            <router-link
              to="/app/login"
              class="text-xs font-medium text-[#8A8D96] hover:text-[#F5F5F3] hover:underline underline-offset-4 transition-colors"
            >
              Sign in
            </router-link>
            <router-link to="/app/register" class="btn-platinum px-4 py-1.5 text-xs">
              Start free
            </router-link>
          </template>
        </div>

        <button
          type="button"
          @click="mobileMenuOpen = !mobileMenuOpen"
          :aria-expanded="mobileMenuOpen"
          aria-controls="public-mobile-nav"
          :aria-label="mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'"
          class="md:hidden min-h-[40px] min-w-[40px] flex items-center justify-center rounded-none border border-white/[0.14] bg-[#08080B] text-[#F5F5F3] hover:bg-white/[0.06] transition-colors"
        >
          <X v-if="mobileMenuOpen" class="h-4 w-4" />
          <Menu v-else class="h-4 w-4" />
        </button>
      </div>
    </div>

    <!-- Mobile Navigation Drawer -->
    <Transition name="vf-fade">
      <div
        v-if="mobileMenuOpen"
        id="public-mobile-nav"
        class="md:hidden border-t border-white/[0.1] bg-[#08080B] px-4 py-4 space-y-3"
      >
        <nav aria-label="Mobile navigation" class="flex flex-col divide-y divide-white/[0.08]">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            @click="mobileMenuOpen = false"
            class="py-2.5 text-sm font-medium text-[#8A8D96] hover:text-[#F5F5F3] transition-colors"
            active-class="!text-[#F5F5F3] font-semibold"
          >
            {{ link.label }}
          </router-link>
        </nav>

        <div class="pt-3 border-t border-white/[0.1] flex flex-col gap-2">
          <template v-if="isAuthenticated">
            <router-link
              :to="isSuperadmin ? '/app/admin' : '/app/dashboard'"
              @click="mobileMenuOpen = false"
              class="btn-platinum w-full py-2.5 text-xs"
            >
              <span>{{ isSuperadmin ? 'Go to Admin Console' : 'Go to Dashboard' }}</span>
              <ArrowRight class="h-3.5 w-3.5" />
            </router-link>
          </template>
          <template v-else>
            <router-link
              to="/app/login"
              @click="mobileMenuOpen = false"
              class="btn-glass w-full py-2.5 text-xs"
            >
              Sign in
            </router-link>
            <router-link
              to="/app/register"
              @click="mobileMenuOpen = false"
              class="btn-platinum w-full py-2.5 text-xs"
            >
              Create free workspace
            </router-link>
          </template>
        </div>
      </div>
    </Transition>
  </header>
</template>

<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowRight, Menu, X } from 'lucide-vue-next'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import { session } from '@/stores/session'

const route = useRoute()
const mobileMenuOpen = ref(false)
const isAuthenticated = session.isAuthenticated
const isSuperadmin = session.isSuperadmin

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/about', label: 'How it works' },
  { to: '/solutions', label: 'Demo' },
  { to: '/contact', label: 'Pricing' },
]

watch(
  () => route.fullPath,
  () => {
    mobileMenuOpen.value = false
  }
)

const onKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && mobileMenuOpen.value) {
    mobileMenuOpen.value = false
  }
}

window.addEventListener('keydown', onKeydown)
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
