<template>
  <div class="flex flex-col items-center gap-2 select-none">
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 260 260"
      class="overflow-visible max-w-full"
      role="img"
      :aria-label="`CVSS v3.1 risk radar score ${computedResult.score} (${computedResult.severity})`"
    >
      <!-- Concentric grid rings -->
      <g stroke="rgba(255,255,255,0.11)" stroke-width="1" fill="none">
        <polygon
          v-for="ring in [0.25, 0.5, 0.75, 1]"
          :key="ring"
          :points="polygonPointsForRing(ring)"
          :stroke-dasharray="ring < 1 ? '3 3' : undefined"
        />
      </g>

      <!-- Axis spokes -->
      <g stroke="rgba(255,255,255,0.12)" stroke-width="1">
        <line
          v-for="(pt, idx) in outerAxes"
          :key="idx"
          :x1="cx"
          :y1="cy"
          :x2="pt.x"
          :y2="pt.y"
        />
      </g>

      <!-- Active metric polygon -->
      <polygon
        :points="dataPolygonPoints"
        :fill="severityColors.fill"
        :stroke="severityColors.stroke"
        stroke-width="1.75"
        stroke-linejoin="round"
        class="transition-all duration-300"
      />

      <!-- Data nodes -->
      <g>
        <circle
          v-for="pt in dataPoints"
          :key="pt.key"
          :cx="pt.x"
          :cy="pt.y"
          r="3.5"
          :fill="severityColors.stroke"
          stroke="#050507"
          stroke-width="1.5"
          class="transition-all duration-300"
        >
          <title>{{ pt.title }}</title>
        </circle>
      </g>

      <!-- Axis labels -->
      <g class="font-mono text-[10px] font-semibold">
        <text
          v-for="lbl in labelCoords"
          :key="lbl.key"
          :x="lbl.x"
          :y="lbl.y"
          text-anchor="middle"
          dominant-baseline="central"
          class="fill-zinc-300"
        >
          <title>{{ lbl.fullTitle }}</title>
          {{ lbl.text }}
        </text>
      </g>

      <!-- Matte center score disc -->
      <g>
        <circle
          :cx="cx"
          :cy="cy"
          r="25"
          fill="#050507"
          :stroke="severityColors.stroke"
          stroke-width="1.5"
        />
        <text
          :x="cx"
          :y="cy - 3"
          text-anchor="middle"
          dominant-baseline="central"
          class="font-mono text-sm font-bold fill-[#F5F5F3] tabular-nums"
        >
          {{ displayScore }}
        </text>
        <text
          :x="cx"
          :y="cy + 11"
          text-anchor="middle"
          dominant-baseline="central"
          class="font-mono text-[8px] font-semibold fill-[#8A8D96]"
        >
          CVSS
        </text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  computeCvss31,
  CVSS_METRIC_DEFS,
  getSeverityStyle,
  type CvssMetrics,
} from '@/utils/cvss'
import type { Severity } from '@/services/api'

const props = withDefaults(
  defineProps<{
    metrics: CvssMetrics
    score?: number
    severity?: Severity
    size?: number
  }>(),
  {
    score: undefined,
    severity: undefined,
    size: 240,
  }
)

const cx = 130
const cy = 130
const radius = 84

const axisOrder: Array<keyof CvssMetrics> = ['AV', 'AC', 'PR', 'UI', 'S', 'C', 'I', 'A']

const computedResult = computed(() => computeCvss31(props.metrics))

const displayScore = computed(() =>
  typeof props.score === 'number' ? props.score.toFixed(1) : computedResult.value.score.toFixed(1)
)

const effectiveSeverity = computed(() => props.severity ?? computedResult.value.severity)

const severityColors = computed(() => {
  const style = getSeverityStyle(effectiveSeverity.value)
  return {
    stroke: style.hex,
    fill: `${style.hex}24`,
  }
})

function polarToCartesian(angleDeg: number, r: number): { x: number; y: number } {
  const rad = ((angleDeg - 90) * Math.PI) / 180
  return {
    x: Number((cx + r * Math.cos(rad)).toFixed(2)),
    y: Number((cy + r * Math.sin(rad)).toFixed(2)),
  }
}

const outerAxes = computed(() =>
  axisOrder.map((_, idx) => polarToCartesian((360 / axisOrder.length) * idx, radius))
)

function polygonPointsForRing(scale: number): string {
  return axisOrder
    .map((_, idx) => {
      const pt = polarToCartesian((360 / axisOrder.length) * idx, radius * scale)
      return `${pt.x},${pt.y}`
    })
    .join(' ')
}

function weightForMetric(key: keyof CvssMetrics): { weight: number; optLabel: string } {
  const def = CVSS_METRIC_DEFS[key]
  const val = props.metrics[key]
  const opt = def.options.find((o) => o.value === val) ?? def.options[0]
  return {
    weight: opt?.radarWeight ?? 0.5,
    optLabel: opt?.shortLabel ?? String(val),
  }
}

const dataPoints = computed(() =>
  axisOrder.map((key, idx) => {
    const { weight, optLabel } = weightForMetric(key)
    const pt = polarToCartesian((360 / axisOrder.length) * idx, radius * weight)
    return {
      key,
      x: pt.x,
      y: pt.y,
      title: `${CVSS_METRIC_DEFS[key].name}: ${optLabel}`,
    }
  })
)

const dataPolygonPoints = computed(() =>
  dataPoints.value.map((pt) => `${pt.x},${pt.y}`).join(' ')
)

const labelCoords = computed(() =>
  axisOrder.map((key, idx) => {
    const pt = polarToCartesian((360 / axisOrder.length) * idx, radius + 22)
    const { optLabel } = weightForMetric(key)
    return {
      key,
      x: pt.x,
      y: pt.y,
      text: `${CVSS_METRIC_DEFS[key].shortName}:${props.metrics[key]}`,
      fullTitle: `${CVSS_METRIC_DEFS[key].name} — ${optLabel}`,
    }
  })
)
</script>
