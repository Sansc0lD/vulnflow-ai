import { reactive } from 'vue'

export type ToastKind = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: number
  kind: ToastKind
  title?: string
  message: string
}

interface TimerMeta {
  timerId: number | null
  remainingMs: number
  startedAt: number
}

let nextId = 1
const timers = new Map<number, TimerMeta>()

export const toastState = reactive<{ items: ToastItem[] }>({
  items: [],
})

function startTimer(id: number, durationMs: number): void {
  if (durationMs <= 0) return
  const timerId = window.setTimeout(() => {
    toast.dismiss(id)
  }, durationMs)
  timers.set(id, {
    timerId,
    remainingMs: durationMs,
    startedAt: Date.now(),
  })
}

export const toast = {
  show(kind: ToastKind, message: string, title?: string, durationMs = 4500): number {
    const id = nextId++
    toastState.items.push({ id, kind, title, message })
    startTimer(id, durationMs)
    return id
  },
  success: (message: string, title = 'Success') => toast.show('success', message, title),
  error: (message: string, title = 'Error') => toast.show('error', message, title, 6000),
  warning: (message: string, title = 'Notice') => toast.show('warning', message, title, 5500),
  info: (message: string, title = 'Info') => toast.show('info', message, title),
  pause(id: number): void {
    const meta = timers.get(id)
    if (!meta || meta.timerId === null) return
    window.clearTimeout(meta.timerId)
    const elapsed = Date.now() - meta.startedAt
    meta.timerId = null
    meta.remainingMs = Math.max(800, meta.remainingMs - elapsed)
  },
  resume(id: number): void {
    const meta = timers.get(id)
    if (!meta || meta.timerId !== null) return
    startTimer(id, meta.remainingMs)
  },
  dismiss(id: number): void {
    const meta = timers.get(id)
    if (meta && meta.timerId !== null) {
      window.clearTimeout(meta.timerId)
    }
    timers.delete(id)
    const idx = toastState.items.findIndex((item) => item.id === id)
    if (idx !== -1) {
      toastState.items.splice(idx, 1)
    }
  },
}
