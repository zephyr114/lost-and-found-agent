<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{ dimensions: Record<string, number> }>()

const el = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const DIM_KEYS = ['category', 'title', 'color', 'brand', 'time', 'distance', 'feature']
const DIM_LABELS = ['类别', '名称', '颜色', '品牌', '时间', '距离', '特征']

function render() {
  if (!el.value) return
  chart ??= echarts.init(el.value)
  const values = DIM_KEYS.map((k) => props.dimensions[k] ?? 0)
  chart.setOption({
    radar: {
      indicator: DIM_LABELS.map((name) => ({ name, max: 100 })),
      radius: '60%',
      center: ['50%', '54%'],
      axisName: { color: '#8fb3d9', fontSize: 10 },
      splitArea: { areaStyle: { color: ['rgba(0, 229, 255, 0.04)', 'rgba(255, 255, 255, 0.02)'] } },
      axisLine: { lineStyle: { color: 'rgba(0, 229, 255, 0.16)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 229, 255, 0.14)' } },
    },
    series: [
      {
        type: 'radar',
        symbol: 'circle',
        symbolSize: 4,
        data: [
          {
            value: values,
            name: '匹配度',
            areaStyle: { color: 'rgba(0, 229, 255, 0.22)' },
            lineStyle: { color: '#00e5ff', width: 2 },
            itemStyle: { color: '#00e5ff' },
          },
        ],
      },
    ],
  })
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', resize)
})

watch(() => props.dimensions, render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})
</script>

<template>
  <div ref="el" class="match-radar" />
</template>

<style scoped>
.match-radar {
  width: 100%;
  height: 190px;
}
</style>
