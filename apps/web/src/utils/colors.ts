function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.trim().replace('#', '')
  if (!/^[0-9a-fA-F]{6}$/.test(clean)) {
    return [15, 23, 42]
  }
  return [
    parseInt(clean.slice(0, 2), 16),
    parseInt(clean.slice(2, 4), 16),
    parseInt(clean.slice(4, 6), 16),
  ]
}

function channelLuminance(c: number): number {
  const srgb = c / 255
  return srgb <= 0.03928 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4)
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex)
  return (
    0.2126 * channelLuminance(r) +
    0.7152 * channelLuminance(g) +
    0.0722 * channelLuminance(b)
  )
}

export function computeContrastRatio(fgHex: string, bgHex: string): number {
  const l1 = relativeLuminance(fgHex)
  const l2 = relativeLuminance(bgHex)
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  return (lighter + 0.05) / (darker + 0.05)
}

export function pickAccessibleTextColor(bgHex: string): '#0F172A' | '#FFFFFF' {
  const darkRatio = computeContrastRatio('#0F172A', bgHex)
  const whiteRatio = computeContrastRatio('#FFFFFF', bgHex)
  return whiteRatio >= darkRatio ? '#FFFFFF' : '#0F172A'
}
