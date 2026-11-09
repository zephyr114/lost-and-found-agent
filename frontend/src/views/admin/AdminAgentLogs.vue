<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { listAgentLogs } from '@/api/admin'
import type { AgentLogRow } from '@/api/admin'

const logs = ref<AgentLogRow[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 50

const TOOL_META: Record<string, { label: string; icon: string }> = {
  extract_item_attributes: { label: '属性提取', icon: '🏷️' },
  search_similar_items: { label: '相似检索', icon: '🔍' },
  calculate_match_score: { label: '匹配打分', icon: '🎯' },
  send_match_notification: { label: '匹配通知', icon: '🔔' },
  submit_audit_task: { label: '风险审查', icon: '🛡️' },
  analyze_image: { label: '图片识别', icon: '🖼️' },
  slot_filling_dialog: { label: '对话追问', icon: '💬' },
  precheck_item: { label: '发布预审', icon: '✅' },
}

interface Chain {
  task: string
  steps: AgentLogRow[]
  totalMs: number
}

const chains = computed<Chain[]>(() => {
  const sorted = [...logs.value].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  )
  const groups: Chain[] = []
  for (const log of sorted) {
    const last = groups[groups.length - 1]
    const prevTime = last ? new Date(last.steps[last.steps.length - 1].created_at).getTime() : 0
    const currTime = new Date(log.created_at).getTime()
    if (last && last.task === log.task_type && currTime - prevTime < 30_000) {
      last.steps.push(log)
      last.totalMs += log.execution_time_ms || 0
    } else {
      groups.push({ task: log.task_type, steps: [log], totalMs: log.execution_time_ms || 0 })
    }
  }
  return groups.slice(-4).reverse()
})

const TASK_LABELS: Record<string, string> = {
  item_matching: '物品匹配流水线',
  attribute_extract: 'AI 一键填充',
  image_recognition: '图片识别',
  dialog_publish: '对话式发布',
  risk_precheck: '发布前预审',
}

function toolMeta(name: string) {
  return TOOL_META[name] || { label: name, icon: '⚙️' }
}

async function load() {
  loading.value = true
  try {
    const res = await listAgentLogs(page.value, size)
    logs.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function pretty(obj: unknown): string {
  if (obj === null || obj === undefined) return '—'
  const text = JSON.stringify(obj)
  return text.length > 160 ? text.slice(0, 160) + '…' : text
}

onMounted(load)
</script>

<template>
  <div v-loading="loading" class="agent-page">
    <el-card shadow="never" class="chain-card">
      <template #header>
        <span>🤖 Agent 决策链（最近 {{ chains.length }} 次运行）</span>
        <span class="hint">每一步都记录在 Agent 日志中，可追溯、可解释</span>
      </template>

      <el-empty v-if="!chains.length" description="暂无 Agent 运行记录" />
      <div v-for="(chain, ci) in chains" :key="ci" class="chain">
        <div class="chain__head">
          <el-tag size="small" type="info" effect="plain">{{ TASK_LABELS[chain.task] || chain.task }}</el-tag>
          <span class="chain__meta">
            {{ chain.steps.length }} 步 · 共 {{ chain.totalMs }} ms ·
            {{ new Date(chain.steps[0].created_at).toLocaleString('zh-CN') }}
          </span>
        </div>
        <div class="chain__steps">
          <div v-for="(step, si) in chain.steps" :key="si" class="chain__step-wrap">
            <div class="chain__step" :class="{ 'chain__step--fail': step.status !== 'success' }">
              <div class="chain__icon">{{ toolMeta(step.tool_name).icon }}</div>
              <div class="chain__body">
                <div class="chain__name">{{ toolMeta(step.tool_name).label }}</div>
                <div class="chain__ms">{{ step.execution_time_ms }} ms</div>
                <el-tooltip :content="pretty(step.tool_result)" placement="top">
                  <div class="chain__result">{{ pretty(step.tool_result) }}</div>
                </el-tooltip>
              </div>
            </div>
            <div v-if="si < chain.steps.length - 1" class="chain__arrow">→</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="log-card">
      <template #header><span>📜 原始日志（共 {{ total }} 条）</span></template>
      <el-table :data="logs" border stripe size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="task_type" label="任务" width="140" />
        <el-table-column prop="tool_name" label="工具" width="190" />
        <el-table-column label="输入" min-width="150">
          <template #default="{ row }">{{ pretty(row.input_data) }}</template>
        </el-table-column>
        <el-table-column label="结果" min-width="180">
          <template #default="{ row }">{{ pretty(row.tool_result) }}</template>
        </el-table-column>
        <el-table-column prop="execution_time_ms" label="耗时(ms)" width="95" />
        <el-table-column label="状态" width="85">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="165">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.agent-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.chain {
  padding: 12px 4px;
  border-bottom: 1px dashed rgba(0, 229, 255, 0.15);
}
.chain:last-child {
  border-bottom: none;
}
.chain__head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.chain__meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.chain__steps {
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 6px;
}
.chain__step-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chain__step {
  min-width: 150px;
  max-width: 190px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(0, 229, 255, 0.22);
  background: rgba(0, 229, 255, 0.05);
}
.chain__step--fail {
  border-color: rgba(255, 77, 79, 0.5);
  background: rgba(255, 77, 79, 0.08);
}
.chain__icon {
  font-size: 18px;
}
.chain__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.chain__ms {
  font-size: 11px;
  color: #00e5ff;
  margin: 2px 0 4px;
}
.chain__result {
  font-size: 11px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.chain__arrow {
  color: rgba(0, 229, 255, 0.5);
  font-size: 16px;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
</style>
