<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ dimensions: Record<string, number> }>()

const DIM_KEYS = ['category', 'title', 'color', 'brand', 'time', 'distance', 'feature']
const DIM_LABELS = ['类别', '名称', '颜色', '品牌', '时间', '距离', '特征']

const CX = 150
const CY = 124
const R = 84

function angle(i: number) {
  return -Math.PI / 2 + (i * 2 * Math.PI) / DIM_LABELS.length
}

const values = computed(() =>
  DIM_KEYS.map((k) => Math.max(0, Math.min(100, Math.round(props.dimensions?.[k] ?? 0)))),
)

const points = computed(() =>
  values.value.map((v, i) => {
    const r = (R * v) / 100
    return { x: CX + Math.cos(angle(i)) * r, y: CY + Math.sin(angle(i)) * r, v }
  }),
)

const areaPoints = computed(() =>
  points.value.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '),
)

const rings = computed(() =>
  [0.25, 0.5, 0.75, 1].map((f) =>
    DIM_LABELS.map((_, i) => {
      const r = R * f
      return `${(CX + Math.cos(angle(i)) * r).toFixed(1)},${(CY + Math.sin(angle(i)) * r).toFixed(1)}`
    }).join(' '),
  ),
)

const axes = computed(() =>
  DIM_LABELS.map((_, i) => ({
    x: CX + Math.cos(angle(i)) * R,
    y: CY + Math.sin(angle(i)) * R,
  })),
)

const labels = computed(() =>
  DIM_LABELS.map((label, i) => {
    const x = CX + Math.cos(angle(i)) * (R + 26)
    const y = CY + Math.sin(angle(i)) * (R + 26)
    const anchor = x < CX - 8 ? 'end' : x > CX + 8 ? 'start' : 'middle'
    return { x, y, label, value: values.value[i], anchor }
  }),
)
</script>

<template>
  <svg class="match-radar" viewBox="0 0 300 250" role="img" aria-label="匹配度七维雷达图">
    <defs>
      <linearGradient id="radarFill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.35" />
        <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.08" />
      </linearGradient>
    </defs>

    <!-- 网格环 -->
    <polygon
      v-for="(ring, i) in rings"
      :key="`ring-${i}`"
      :points="ring"
      fill="none"
      stroke="rgba(0, 229, 255, 0.14)"
      stroke-width="1"
    />
    <!-- 轴线 -->
    <line
      v-for="(p, i) in axes"
      :key="`axis-${i}`"
      :x1="CX"
      :y1="CY"
      :x2="p.x"
      :y2="p.y"
      stroke="rgba(0, 229, 255, 0.16)"
      stroke-width="1"
    />

    <!-- 数据区域 -->
    <polygon :points="areaPoints" fill="url(#radarFill)" stroke="#00e5ff" stroke-width="2" class="match-radar__area" />

    <!-- 顶点 -->
    <circle v-for="(p, i) in points" :key="`pt-${i}`" :cx="p.x" :cy="p.y" r="3.5" fill="#00e5ff">
      <title>{{ DIM_LABELS[i] }}：{{ p.v }}</title>
    </circle>

    <!-- 标签 + 分数 -->
    <g class="match-radar__labels">
      <text
        v-for="(l, i) in labels"
        :key="`lb-${i}`"
        :x="l.x"
        :y="l.y"
        :text-anchor="l.anchor"
        dominant-baseline="middle"
      >
        <tspan class="match-radar__name">{{ l.label }}</tspan>
        <tspan class="match-radar__val" :x="l.x" dy="13">{{ l.value }}</tspan>
      </text>
    </g>
  </svg>
</template>

<style scoped>
.match-radar {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
  animation: radar-in 0.45s ease-out;
}
.match-radar__area {
  transform-origin: 150px 124px;
  animation: radar-grow 0.5s ease-out;
}
.match-radar__name {
  fill: #8fb3d9;
  font-size: 10px;
}
.match-radar__val {
  fill: #00e5ff;
  font-size: 10px;
  font-weight: 700;
}
@keyframes radar-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes radar-grow {
  from {
    transform: scale(0.92);
    opacity: 0.3;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .match-radar,
  .match-radar__area {
    animation: none;
  }
}
</style>
