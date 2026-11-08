<template>
  <div class="flex flex-col min-h-screen">
    <Navbar />

    <section class="py-16 border-b border-border bg-gradient-to-b from-blue-950/10 to-background">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto space-y-4">
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400 text-xs font-mono">
            <Cpu class="h-3.5 w-3.5" />
            <span>ARSITEKTUR TERDISTRIBUSI C4 LEVEL 2/3</span>
          </div>
          <h1 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Pipeline Keamanan 4-Node VulnFlow AI
          </h1>
          <p class="text-sm sm:text-base text-zinc-400">
            Klik salah satu simpul pipa di bawah ini untuk melihat mitigasi ancaman STRIDE, isolasi multi-tenant, dan perlindungan Zero-PoC.
          </p>
        </div>
      </div>
    </section>

    <!-- Interactive 4-Node Pipeline (UC-02 Desweb) -->
    <section class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Node Selector Bar -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <button
          v-for="(node, index) in nodes"
          :key="node.id"
          @click="activeNodeIndex = index"
          :class="[
            'p-4 rounded-xl border text-left transition-all relative overflow-hidden',
            activeNodeIndex === index
              ? 'border-blue-500 bg-blue-950/20 shadow-lg shadow-blue-500/10'
              : 'border-border bg-surface hover:bg-surface-elevated'
          ]"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
              NODE 0{{ index + 1 }}
            </span>
            <component :is="node.icon" :class="['h-5 w-5', activeNodeIndex === index ? 'text-blue-400' : 'text-zinc-500']" />
          </div>
          <h3 class="text-xs sm:text-sm font-semibold text-white truncate">{{ node.name }}</h3>
          <p class="text-[11px] text-zinc-400 truncate mt-0.5">{{ node.subtitle }}</p>
        </button>
      </div>

      <!-- Active Node Detail Card -->
      <div class="rounded-xl border border-border bg-surface p-6 sm:p-8 space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div class="space-y-1">
            <div class="flex items-center space-x-3">
              <span class="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                NODE {{ activeNodeIndex + 1 }} OF 4
              </span>
              <h2 class="text-xl font-bold text-white">{{ activeNode.name }}</h2>
            </div>
            <p class="text-xs sm:text-sm text-zinc-400 font-mono">{{ activeNode.location }}</p>
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-xs text-zinc-500 font-mono">STRIDE MITIGATION:</span>
            <span class="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-zinc-800 text-emerald-400 border border-zinc-700">
              {{ activeNode.stride }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-zinc-300">Peran & Tanggung Jawab</h4>
            <p class="text-xs sm:text-sm text-zinc-300 leading-relaxed">{{ activeNode.description }}</p>

            <div class="space-y-2 pt-2">
              <h5 class="text-xs font-semibold text-zinc-300">Spesifikasi Kepatuhan & Jaminan:</h5>
              <ul class="space-y-1.5 text-xs text-zinc-400">
                <li v-for="(spec, i) in activeNode.specs" :key="i" class="flex items-start gap-2">
                  <span class="text-blue-400 font-bold">•</span>
                  <span>{{ spec }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="space-y-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-zinc-300">Cuplikan Implementasi Kode</h4>
            <div class="rounded-lg bg-black/80 border border-border p-4 font-mono text-[11px] sm:text-xs text-zinc-300 overflow-x-auto leading-relaxed">
              <pre>{{ activeNode.codeSnippet }}</pre>
            </div>
          </div>
        </div>
      </div>
    </section>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'
import { Terminal, Shield, Sparkles, FileText, Cpu } from 'lucide-vue-next'

const activeNodeIndex = ref(0)

const nodes = [
  {
    id: 'node1',
    name: 'Local CLI Agent',
    subtitle: 'Typer & Rich Engine (Python 3.12+)',
    icon: Terminal,
    location: 'apps/cli/vulnflow/ (Client-side Machine)',
    stride: 'Information Disclosure & Spoofing',
    description:
      'Agen pemindaian lokal dijalankan langsung di mesin pentester (Kali/Parrot/macOS/Windows). Cloud SaaS VulnFlow AI tidak pernah melancarkan pemindaian aktif secara langsung ke infrastruktur target klien.',
    specs: [
      'Wrapper aman eksekusi biner Nuclei v3 dan Nmap XML (EC-06).',
      'Chunked idempotent upload via header Idempotency-Key (EC-07).',
      'Penyimpanan konfigurasi aman di ~/.vulnflow/config.json (mode 0o600).',
    ],
    codeSnippet: `# apps/cli/vulnflow/ingest_client.py
headers = {
    "X-VulnFlow-API-Key": api_key,
    "Idempotency-Key": f"{file_hash}:{chunk_idx}"
}
client.post("/api/v1/workspaces/{w_id}/projects/{p_id}/findings/batch", ...)`
  },
  {
    id: 'node2',
    name: 'Scope Gateway',
    subtitle: 'CIDR & Nested Subdomain Enforcer',
    icon: Shield,
    location: 'apps/api/app/domain/scope.py (SaaS API)',
    stride: 'Elevation of Privilege & Tampering',
    description:
      'Memeriksa setiap temuan hasil scan terhadap daftar target scope dan rentang waktu Rules of Engagement (ROE). Temuan di luar cakupan sah akan otomatis dikarantina (is_quarantined = true).',
    specs: [
      'Pencocokan FQDN hirarkis & wildcard (*.target.com) (EC-04).',
      'Pengecekan subnet IPv4/IPv6 via pustaka standar ipaddress.',
      'Validasi rentang waktu ROE berpresisi timezone TIMESTAMPTZ (EC-05).',
    ],
    codeSnippet: `# apps/api/app/domain/scope.py
def is_target_in_scope(target: str, scope_rules: list[str]) -> bool:
    # Memeriksa target terhadap domain & CIDR whitelist
    for rule in scope_rules:
        if matches_rule(target, rule):
            return True
    return False`
  },
  {
    id: 'node3',
    name: 'Zero-PoC AI Sanitizer',
    subtitle: 'Data Sanitizer & CWE Fallback',
    icon: Sparkles,
    location: 'apps/api/app/domain/sanitizer.py & fallback.py',
    stride: 'Information Disclosure & Denial of Service',
    description:
      'Menjaga kerahasiaan bukti eksploitasi klien dengan aturan ketat: teks payload, IP internal, dan kredensial dilarang keras diteruskan ke LLM. Jika kuota LLM habis, sistem beralih ke katalog CWE in-memory tanpa gagal.',
    specs: [
      'Whitelist kolom ketat: hanya title, cwe_id, cvss_score, severity yang lolos.',
      'Regex datar anti-ReDoS membersihkan IP & hostname banner (EC-13).',
      'Pemuatan in-memory O(1) CWE catalog fallback saat timeout/429 (EC-14).',
    ],
    codeSnippet: `# apps/api/app/domain/sanitizer.py
def whitelist_finding_metadata(raw: dict) -> dict:
    return {
        "title": sanitize_text(raw["title"]),
        "cwe_id": raw["cwe_id"],
        "cvss_score": float(raw["cvss_score"]),
        "severity": raw["severity"]
    }`
  },
  {
    id: 'node4',
    name: 'WeasyPrint Engine',
    subtitle: 'Anti-SSRF SafeURLFetcher & S3 Vault',
    icon: FileText,
    location: 'apps/api/app/services/safe_fetcher.py & Celery Worker',
    stride: 'Server-Side Request Forgery (SSRF)',
    description:
      'Merender laporan PDF eksekutif dan teknis menggunakan HTML/CSS. SafeURLFetcher mencegah serangan SSRF saat WeasyPrint memuat gambar/aset eksternal, memblokir akses ke IP privat dan cloud metadata.',
    specs: [
      'Resolusi IP tunggal & pinning transport mencegah DNS Rebinding.',
      'Blokir mutlak terhadap 127.0.0.0/8, 169.254.0.0/16, RFC 1918, file://.',
      'Pemberian watermark otomatis pada akun Free Tier; white-label pada Pro (UC-14).',
    ],
    codeSnippet: `# apps/api/app/services/safe_fetcher.py
def validate_target_ip(ip_str: str) -> None:
    ip = ipaddress.ip_address(ip_str)
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        raise SSRFBlockedError(f"Access to private IP {ip} is strictly forbidden.")`
  },
]

const activeNode = computed(() => nodes[activeNodeIndex.value])
</script>
