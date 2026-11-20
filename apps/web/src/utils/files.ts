import type { ImageContentType } from '@/services/api'

export interface EncodedImagePayload {
  filename: string
  content_type: ImageContentType
  data_base64: string
}

export async function readFileAsBase64<T extends ImageContentType>(
  file: File,
  opts: { maxBytes: number; allowedTypes: readonly T[] }
): Promise<{ filename: string; content_type: T; data_base64: string }> {
  const mime = (file.type || '').toLowerCase() as T
  if (!opts.allowedTypes.includes(mime)) {
    throw new Error(
      `Unsupported file format (${file.type || 'unknown'}). Allowed: ${opts.allowedTypes.join(', ')}`
    )
  }
  if (file.size <= 0 || file.size > opts.maxBytes) {
    const maxMb = (opts.maxBytes / (1024 * 1024)).toFixed(1)
    throw new Error(`File size exceeds the ${maxMb} MB limit.`)
  }

  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('Failed to read file from disk.'))
    reader.readAsDataURL(file)
  })

  const commaIndex = dataUrl.indexOf(',')
  const base64 = commaIndex >= 0 ? dataUrl.slice(commaIndex + 1) : dataUrl
  return {
    filename: file.name,
    content_type: mime,
    data_base64: base64,
  }
}
