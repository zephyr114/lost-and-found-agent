<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([PieChart, BarChart, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

import { getStatistics } from '@/api/admin'
import type { Statistics } from '@/api/admin'

const stats = ref<Statistics | null>(null)
const pieRef = ref<HTMLElement>()
const barRef = ref<HTMLElement>()
let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

async function load() {
  stats.value = await getStatistics()
  // 等 v-if 渲染出容器后再初始化图表，否则 ref 为空、图表不显示
  await nextTick()
  renderCharts()
}

function renderCharts() {
  if (!stats.value) return
  const palette = ['#00e5ff', '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#9b59b6', '#16a085', '#7f8c8d']
  const categoryEntries = Object.entries(stats.value.category_distribution || {})
  const pieData = categoryEntries.length
    ? categoryEntries.map(([name, value], i) => ({ name, value, itemStyle: { color: palette[i % palette.length] } }))
    : [
        { value: stats.value.items_lost, name: '失物', itemStyle: { color: '#f56c6c' } },
        { value: stats.value.items_found, name: '招领', itemStyle: { color: '#67c23a' } },
      ]

  if (pieRef.value) {
    pieChart?.dispose()
    pieChart = echarts.init(pieRef.value)
    pieChart.setOption({
      textStyle: { color: '#8fb3d9' },
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#8fb3d9' } },
      series: [
        {
          name: '物品类型',
          type: 'pie',
          radius: ['42%', '66%'],
          center: ['50%', '46%'],
          label: { color: '#cfe6ff', formatter: '{b}\n{c}' },
          data: pieData,
        },
      ],
    })
  }
  if (barRef.value) {
    barChart?.dispose()
    barChart = echarts.init(barRef.value)
    barChart.setOption({
      textStyle: { color: '#8fb3d9' },
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: {
        type: 'category',
        data: ['用户', '物品', '认领申请', '匹配记录', '待处理举报'],
        axisLabel: { color: '#8fb3d9' },
        axisLine: { lineStyle: { color: 'rgba(0,229,255,0.2)' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#8fb3d9' },
        splitLine: { lineStyle: { color: 'rgba(0,229,255,0.08)' } },
      },
      series: [
        {
          type: 'bar',
          barWidth: 36,
          data: [
            stats.value.users_total,
            stats.value.items_total,
            stats.value.claims_total,
            stats.value.matches_total,
            stats.value.reports_pending,
          ],
          itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
        },
      ],
    })
  }
}

function onResize() {
  pieChart?.resize()
  barChart?.resize()
}

onMounted(async () => {
  await load()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  pieChart?.dispose()
  barChart?.dispose()
})
</script>

<template>
  <div class="dashboard" v-if="stats">
    <el-row :gutter="14">
      <el-col v-for="card in [
        { label: '注册用户', value: stats.users_total, color: '#409eff' },
        { label: '物品总数', value: stats.items_total, color: '#67c23a' },
        { label: '待审核物品', value: stats.items_pending_audit, color: '#e6a23c' },
        { label: '已认领物品', value: stats.items_claimed, color: '#f56c6c' },
        { label: '认领申请', value: stats.claims_total, color: '#909399' },
        { label: '待处理举报', value: stats.reports_pending, color: '#f56c6c' },
      ]" :key="card.label" :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="dashboard__stat">
          <div class="dashboard__stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="dashboard__stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="dashboard__charts">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span>物品类型分布</span></template>
          <div ref="pieRef" class="dashboard__chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span>核心数据概览</span></template>
          <div ref="barRef" class="dashboard__chart" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard__stat {
  text-align: center;
  margin-bottom: 14px;
}
.dashboard__stat-value {
  font-size: 30px;
  font-weight: 700;
}
.dashboard__stat-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.dashboard__chart {
  height: 300px;
}
</style>
