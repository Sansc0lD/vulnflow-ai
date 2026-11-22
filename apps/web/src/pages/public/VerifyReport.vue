<template>
  <PublicLayout>
    <section class="py-14 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex-1 space-y-8">
      <div class="space-y-2 border-b border-white/[0.1] pb-6">
        <span class="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8A8D96] block">
          Document Authenticity Verification
        </span>
        <h1 class="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F5F3]">
          Verify Pentest Report Provenance
        </h1>
        <p class="text-xs sm:text-sm text-[#8A8D96] leading-relaxed">
          Check a report’s verification ID against the platform ledger and optionally confirm its local SHA-256 checksum inside your browser without uploading the PDF.
        </p>
      </div>

      <form @submit.prevent="lookupCode" class="border border-white/[0.12] bg-[#08080B] p-6 space-y-4">
        <label for="verify-code-input" class="text-xs font-medium text-[#D4D4D8] block">
          Verification ID
        </label>
        <div class="flex flex-wrap gap-2.5">
          <input
            id="verify-code-input"
            v-model.trim="codeInput"
            type="text"
            required
            placeholder="VF-XXXX-XXXX-XXXX"
            class="input-glass flex-1 min-w-[220px] px-3 py-2 text-xs font-mono uppercase"
          />
          <button
            type="submit"
            :disabled="loading"
            class="btn-platinum px-5 py-2 text-xs disabled:opacity-50"
          >
            {{ loading ? 'Checking...' : 'Verify ID' }}
          </button>
        </div>
      </form>

      <div v-if="errorMsg" role="alert" class="p-4 border border-red-400/35 bg-red-500/10 text-xs text-red-200">
        {{ errorMsg }}
      </div>

      <div v-if="result" class="border border-white/[0.12] bg-[#08080B] p-6 space-y-5 text-xs">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
          <div class="flex items-center gap-2.5">
            <ShieldCheck v-if="result.valid" class="h-5 w-5 text-emerald-400" />
            <ShieldAlert v-else class="h-5 w-5 text-red-400" />
            <div>
              <div class="text-sm font-display font-semibold text-[#F5F5F3]">
                {{ result.valid ? 'Authentic VulnFlow Report Record' : 'Verification Code Not Found' }}
              </div>
              <div class="font-mono text-[11px] text-[#8A8D96]">{{ result.verification_code }}</div>
            </div>
          </div>
          <span
            :class="[
              'font-mono text-[10px] uppercase tracking-wider px-2.5 py-1 border font-semibold',
              result.valid
                ? 'border-emerald-400/35 bg-emerald-500/15 text-emerald-300'
                : 'border-red-400/35 bg-red-500/15 text-red-200',
            ]"
          >
            {{ result.valid ? 'VALID RECORD' : 'NOT FOUND' }}
          </span>
        </div>

        <template v-if="result.valid">
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="p-3 bg-[#050507] border border-white/[0.08]">
              <dt class="font-mono uppercase text-[10px] text-[#8A8D96]">Issuer / Agency</dt>
              <dd class="text-[#F5F5F3] font-medium mt-1">{{ result.agency_name || 'VulnFlow AI' }}</dd>
            </div>
            <div class="p-3 bg-[#050507] border border-white/[0.08]">
              <dt class="font-mono uppercase text-[10px] text-[#8A8D96]">Version &amp; Issued</dt>
              <dd class="text-[#F5F5F3] font-mono mt-1">
                {{ result.report_version || '-' }} · {{ formatDate(result.generated_at) }}
              </dd>
            </div>
            <div class="p-3 bg-[#050507] border border-white/[0.08]">
              <dt class="font-mono uppercase text-[10px] text-[#8A8D96]">Protection Mode</dt>
              <dd class="text-[#D4D4D8] mt-1">
                {{ result.watermark_applied ? 'Free-Tier Preview Watermark' : 'White-Label Edition' }}
                · {{ result.is_rasterized ? 'Rasterized Pixel Lock' : 'Vector PDF' }}
                · {{ result.is_signed ? 'PAdES Certified' : 'SHA-256 Fingerprinted' }}
              </dd>
            </div>
            <div class="p-3 bg-[#050507] border border-white/[0.08]">
              <dt class="font-mono uppercase text-[10px] text-[#8A8D96]">Expected SHA-256</dt>
              <dd class="text-[#F5F5F3] font-mono break-all mt-1 text-[11px]">
                {{ result.sha256_hash || 'Unavailable' }}
              </dd>
            </div>
          </dl>

          <!-- Local Client-Side PDF Checksum Comparison -->
          <div
            v-if="result.sha256_hash"
            class="p-4 border border-white/[0.1] bg-[#050507] space-y-3"
          >
            <div>
              <div class="font-semibold text-[#F5F5F3]">Verify Local PDF File (Zero Upload)</div>
              <p class="text-[#8A8D96] mt-0.5">
                Select your downloaded PDF file to compute its SHA-256 checksum locally in the browser and detect any post-export tampering.
              </p>
            </div>
            <input
              type="file"
              accept="application/pdf"
              @change="handleLocalFileHash"
              class="block text-xs text-[#D4D4D8] file:mr-3 file:px-3 file:py-1.5 file:border file:border-white/[0.16] file:bg-[#08080B] file:text-[#F5F5F3]"
            />
            <div v-if="localHash" class="space-y-1.5 font-mono text-[11px]">
              <div class="text-[#8A8D96] break-all">Computed SHA-256: {{ localHash }}</div>
              <div
                :class="
                  localHash === result.sha256_hash
                    ? 'text-emerald-300 font-semibold'
                    : 'text-red-300 font-semibold'
                "
              >
                {{
                  localHash === result.sha256_hash
                    ? 'MATCH: This PDF matches the original exported binary byte-for-byte.'
                    : 'MISMATCH: This PDF differs from the issued checksum (modified or wrong file).'
                }}
              </div>
            </div>
          </div>
        </template>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ShieldAlert, ShieldCheck } from 'lucide-vue-next'
import PublicLayout from '@/components/layout/PublicLayout.vue'
import { api, type PublicReportVerifyResponse } from '@/services/api'

const route = useRoute()
const router = useRouter()

const codeInput = ref(typeof route.params.code === 'string' ? route.params.code : '')
const loading = ref(false)
const errorMsg = ref('')
const result = ref<PublicReportVerifyResponse | null>(null)
const localHash = ref('')

const formatDate = (iso?: string | null) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })
}

const lookupCode = async () => {
  const cleaned = codeInput.value.trim().toUpperCase()
  if (!cleaned) return
  codeInput.value = cleaned
  loading.value = true
  errorMsg.value = ''
  localHash.value = ''
  try {
    result.value = await api.public.verifyReport(cleaned)
    void router.replace({ path: `/verify/${encodeURIComponent(cleaned)}` })
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : 'Unable to verify code.'
    result.value = null
  } finally {
    loading.value = false
  }
}

const handleLocalFileHash = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const buf = await file.arrayBuffer()
  const digest = await crypto.subtle.digest('SHA-256', buf)
  localHash.value = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

onMounted(() => {
  if (codeInput.value) {
    void lookupCode()
  }
})
</script>
