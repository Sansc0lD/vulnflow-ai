import type { Severity } from '@/services/api'

export interface CvssMetrics {
  AV: 'N' | 'A' | 'L' | 'P'
  AC: 'L' | 'H'
  PR: 'N' | 'L' | 'H'
  UI: 'N' | 'R'
  S: 'U' | 'C'
  C: 'H' | 'L' | 'N'
  I: 'H' | 'L' | 'N'
  A: 'H' | 'L' | 'N'
}

export const DEFAULT_CVSS_METRICS: CvssMetrics = {
  AV: 'N',
  AC: 'L',
  PR: 'N',
  UI: 'N',
  S: 'U',
  C: 'H',
  I: 'H',
  A: 'N',
}

const AV_WEIGHTS: Record<CvssMetrics['AV'], number> = { N: 0.85, A: 0.62, L: 0.55, P: 0.2 }
const AC_WEIGHTS: Record<CvssMetrics['AC'], number> = { L: 0.77, H: 0.44 }
const PR_UNCHANGED: Record<CvssMetrics['PR'], number> = { N: 0.85, L: 0.62, H: 0.27 }
const PR_CHANGED: Record<CvssMetrics['PR'], number> = { N: 0.85, L: 0.68, H: 0.5 }
const UI_WEIGHTS: Record<CvssMetrics['UI'], number> = { N: 0.85, R: 0.62 }
const IMPACT_WEIGHTS: Record<CvssMetrics['C'], number> = { H: 0.56, L: 0.22, N: 0.0 }

function roundup(value: number): number {
  const intInput = Math.round(value * 100000)
  if (intInput % 10000 === 0) {
    return intInput / 100000
  }
  return (Math.floor(intInput / 10000) + 1) / 10
}

export function severityFromScore(score: number): Severity {
  if (score >= 9.0) return 'CRITICAL'
  if (score >= 7.0) return 'HIGH'
  if (score >= 4.0) return 'MEDIUM'
  if (score >= 0.1) return 'LOW'
  return 'INFO'
}

export function computeCvss31(metrics: CvssMetrics): {
  score: number
  severity: Severity
  vector: string
} {
  const scopeChanged = metrics.S === 'C'
  const prWeight = (scopeChanged ? PR_CHANGED : PR_UNCHANGED)[metrics.PR]
  const exploitability =
    8.22 *
    AV_WEIGHTS[metrics.AV] *
    AC_WEIGHTS[metrics.AC] *
    prWeight *
    UI_WEIGHTS[metrics.UI]

  const impactBase =
    1 -
    (1 - IMPACT_WEIGHTS[metrics.C]) *
      (1 - IMPACT_WEIGHTS[metrics.I]) *
      (1 - IMPACT_WEIGHTS[metrics.A])

  let score = 0.0
  if (impactBase > 0) {
    if (scopeChanged) {
      const impact = 7.52 * (impactBase - 0.029) - 3.25 * Math.pow(impactBase - 0.02, 15)
      score = roundup(Math.min(1.08 * (impact + exploitability), 10.0))
    } else {
      const impact = 6.42 * impactBase
      score = roundup(Math.min(impact + exploitability, 10.0))
    }
  }

  const vector = `CVSS:3.1/AV:${metrics.AV}/AC:${metrics.AC}/PR:${metrics.PR}/UI:${metrics.UI}/S:${metrics.S}/C:${metrics.C}/I:${metrics.I}/A:${metrics.A}`
  return {
    score: Number(score.toFixed(1)),
    severity: severityFromScore(score),
    vector,
  }
}

export function parseCvssVector(vector: string | null | undefined): CvssMetrics {
  const parsed: CvssMetrics = { ...DEFAULT_CVSS_METRICS }
  if (!vector) return parsed

  const parts = vector.trim().split('/')
  for (const part of parts) {
    const [key, val] = part.split(':')
    if (!key || !val) continue
    switch (key) {
      case 'AV':
        if (val === 'N' || val === 'A' || val === 'L' || val === 'P') parsed.AV = val
        break
      case 'AC':
        if (val === 'L' || val === 'H') parsed.AC = val
        break
      case 'PR':
        if (val === 'N' || val === 'L' || val === 'H') parsed.PR = val
        break
      case 'UI':
        if (val === 'N' || val === 'R') parsed.UI = val
        break
      case 'S':
        if (val === 'U' || val === 'C') parsed.S = val
        break
      case 'C':
        if (val === 'H' || val === 'L' || val === 'N') parsed.C = val
        break
      case 'I':
        if (val === 'H' || val === 'L' || val === 'N') parsed.I = val
        break
      case 'A':
        if (val === 'H' || val === 'L' || val === 'N') parsed.A = val
        break
    }
  }
  return parsed
}

export interface CvssMetricOption<K extends keyof CvssMetrics = keyof CvssMetrics> {
  value: CvssMetrics[K]
  label: string
  shortLabel: string
  radarWeight: number
}

export interface CvssMetricDef<K extends keyof CvssMetrics = keyof CvssMetrics> {
  key: K
  name: string
  shortName: string
  description: string
  options: Array<CvssMetricOption<K>>
}

export const CVSS_METRIC_DEFS: { [K in keyof CvssMetrics]: CvssMetricDef<K> } = {
  AV: {
    key: 'AV',
    name: 'Attack Vector',
    shortName: 'AV',
    description: 'How an attacker can reach the vulnerable component.',
    options: [
      { value: 'N', label: 'Network (Remote / Internet)', shortLabel: 'Network', radarWeight: 1.0 },
      { value: 'A', label: 'Adjacent (Local Network)', shortLabel: 'Adjacent', radarWeight: 0.72 },
      { value: 'L', label: 'Local (Local Access / CLI)', shortLabel: 'Local', radarWeight: 0.5 },
      { value: 'P', label: 'Physical (Physical Access)', shortLabel: 'Physical', radarWeight: 0.25 },
    ],
  },
  AC: {
    key: 'AC',
    name: 'Attack Complexity',
    shortName: 'AC',
    description: 'Conditions beyond the attacker’s control required to trigger the issue.',
    options: [
      { value: 'L', label: 'Low (Repeatable / Direct)', shortLabel: 'Low', radarWeight: 1.0 },
      { value: 'H', label: 'High (Complex Conditions)', shortLabel: 'High', radarWeight: 0.45 },
    ],
  },
  PR: {
    key: 'PR',
    name: 'Privileges Required',
    shortName: 'PR',
    description: 'Level of access needed before triggering the issue.',
    options: [
      { value: 'N', label: 'None (Unauthenticated)', shortLabel: 'None', radarWeight: 1.0 },
      { value: 'L', label: 'Low (Standard User)', shortLabel: 'Low', radarWeight: 0.65 },
      { value: 'H', label: 'High (Admin / Privileged)', shortLabel: 'High', radarWeight: 0.35 },
    ],
  },
  UI: {
    key: 'UI',
    name: 'User Interaction',
    shortName: 'UI',
    description: 'Whether a user must click or take an action for exploitation to occur.',
    options: [
      { value: 'N', label: 'None (No User Needed)', shortLabel: 'None', radarWeight: 1.0 },
      { value: 'R', label: 'Required (User Action Needed)', shortLabel: 'Required', radarWeight: 0.45 },
    ],
  },
  S: {
    key: 'S',
    name: 'Scope',
    shortName: 'Scope',
    description: 'Whether an issue in one component impacts other systems or privileges.',
    options: [
      { value: 'U', label: 'Unchanged (Single Component)', shortLabel: 'Unchanged', radarWeight: 0.55 },
      { value: 'C', label: 'Changed (Impacts Other Systems)', shortLabel: 'Changed', radarWeight: 1.0 },
    ],
  },
  C: {
    key: 'C',
    name: 'Confidentiality',
    shortName: 'Conf',
    description: 'Potential disclosure of sensitive or restricted data.',
    options: [
      { value: 'H', label: 'High (Full Data Exposure)', shortLabel: 'High', radarWeight: 1.0 },
      { value: 'L', label: 'Low (Limited Exposure)', shortLabel: 'Low', radarWeight: 0.55 },
      { value: 'N', label: 'None (No Impact)', shortLabel: 'None', radarWeight: 0.15 },
    ],
  },
  I: {
    key: 'I',
    name: 'Integrity',
    shortName: 'Integ',
    description: 'Potential unauthorized modification of stored data or settings.',
    options: [
      { value: 'H', label: 'High (Full Modification)', shortLabel: 'High', radarWeight: 1.0 },
      { value: 'L', label: 'Low (Limited Modification)', shortLabel: 'Low', radarWeight: 0.55 },
      { value: 'N', label: 'None (No Impact)', shortLabel: 'None', radarWeight: 0.15 },
    ],
  },
  A: {
    key: 'A',
    name: 'Availability',
    shortName: 'Avail',
    description: 'Potential disruption or downtime of the affected service.',
    options: [
      { value: 'H', label: 'High (Full Outage)', shortLabel: 'High', radarWeight: 1.0 },
      { value: 'L', label: 'Low (Degraded Service)', shortLabel: 'Low', radarWeight: 0.55 },
      { value: 'N', label: 'None (No Impact)', shortLabel: 'None', radarWeight: 0.15 },
    ],
  },
}

export interface SeverityStyle {
  label: Severity
  badgeClass: string
  barClass: string
  textClass: string
  dotClass: string
  hex: string
}

const SEVERITY_MAP: Record<Severity, SeverityStyle> = {
  CRITICAL: {
    label: 'CRITICAL',
    badgeClass: 'bg-red-500/10 text-red-300 border-red-400/20',
    barClass: 'bg-red-500',
    textClass: 'text-red-400',
    dotClass: 'bg-red-500',
    hex: '#ef4444',
  },
  HIGH: {
    label: 'HIGH',
    badgeClass: 'bg-orange-500/10 text-orange-300 border-orange-400/20',
    barClass: 'bg-orange-500',
    textClass: 'text-orange-400',
    dotClass: 'bg-orange-500',
    hex: '#f97316',
  },
  MEDIUM: {
    label: 'MEDIUM',
    badgeClass: 'bg-amber-500/10 text-amber-300 border-amber-400/20',
    barClass: 'bg-amber-400',
    textClass: 'text-amber-300',
    dotClass: 'bg-amber-400',
    hex: '#eab308',
  },
  LOW: {
    label: 'LOW',
    badgeClass: 'bg-white/[0.04] text-zinc-200 border-white/[0.14]',
    barClass: 'bg-zinc-300',
    textClass: 'text-zinc-200',
    dotClass: 'bg-zinc-300',
    hex: '#d4d4d8',
  },
  INFO: {
    label: 'INFO',
    badgeClass: 'bg-white/[0.02] text-zinc-400 border-white/[0.11]',
    barClass: 'bg-zinc-500',
    textClass: 'text-zinc-400',
    dotClass: 'bg-zinc-500',
    hex: '#71717a',
  },
}

export function getSeverityStyle(severity: string): SeverityStyle {
  const key = severity.toUpperCase() as Severity
  return SEVERITY_MAP[key] ?? SEVERITY_MAP.INFO
}

export const CWE_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'CWE-89', label: 'CWE-89 — SQL Injection' },
  { id: 'CWE-79', label: 'CWE-79 — Cross-Site Scripting (XSS)' },
  { id: 'CWE-78', label: 'CWE-78 — OS Command Injection' },
  { id: 'CWE-22', label: 'CWE-22 — Path Traversal' },
  { id: 'CWE-287', label: 'CWE-287 — Improper Authentication' },
  { id: 'CWE-200', label: 'CWE-200 — Exposure of Sensitive Information' },
  { id: 'CWE-538', label: 'CWE-538 — Sensitive File/Directory Exposure' },
  { id: 'CWE-502', label: 'CWE-502 — Deserialization of Untrusted Data' },
  { id: 'CWE-306', label: 'CWE-306 — Missing Authentication for Critical Function' },
  { id: 'CWE-319', label: 'CWE-319 — Cleartext Transmission of Sensitive Info' },
  { id: 'CWE-326', label: 'CWE-326 — Inadequate Encryption Strength' },
  { id: 'CWE-352', label: 'CWE-352 — Cross-Site Request Forgery (CSRF)' },
  { id: 'CWE-639', label: 'CWE-639 — Authorization Bypass (IDOR/BOLA)' },
  { id: 'CWE-693', label: 'CWE-693 — Protection Mechanism Failure (Headers)' },
  { id: 'CWE-798', label: 'CWE-798 — Use of Hard-coded Credentials' },
  { id: 'CWE-918', label: 'CWE-918 — Server-Side Request Forgery (SSRF)' },
  { id: 'UNKNOWN', label: 'UNKNOWN — Unclassified Weakness' },
]
