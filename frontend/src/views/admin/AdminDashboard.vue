<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'

import { getStatistics } from '@/api/admin'
import type { Statistics } from '@/api/admin'

const stats = ref<Statistics | null>(null)
const pieRef = ref<HTMLElement>()
const barRef = ref<HTMLElement>()
let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

async function load() {
  stats.value = await getStatistics()
  renderCharts()
}

function renderCharts() {
  if (!stats.value) return
  if (pieRef.value) {
    pieChart = echarts.init(pieRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          name: '物品类型',
          type: 'pie',
          radius: ['40%', '65%'],
          data: [
            { value: stats.value.items_lost, name: '失物', itemStyle: { color: '#f56c6c' } },
            { value: stats.value.items_found, name: '招领', itemStyle: { color: '#67c23a' } },
          ],
        },
      ],
    })
  }
  if (barRef.value) {
    barChart = echarts.init(barRef.value)
    barChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['用户', '物品', '认领申请', '匹配记录', '待处理举报'] },
      yAxis: { type: 'value' },
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
