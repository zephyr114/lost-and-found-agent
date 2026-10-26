<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    duration?: number
    suffix?: string
  }>(),
  { duration: 900, suffix: '' },
)

const display = ref(0)
let raf = 0

function animate(from: number, to: number) {
  cancelAnimationFrame(raf)
  const start = performance.now()
  const step = (now: number) => {
    const progress = Math.min((now - start) / props.duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    display.value = Math.round(from + (to - from) * eased)
    if (progress < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}

watch(
  () => props.value,
  (to, from) => animate(from ?? 0, to),
  { immediate: true },
)

onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<template>
  <span class="number-roll">{{ display.toLocaleString('zh-CN') }}{{ suffix }}</span>
</template>

<style scoped>
.number-roll {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}
</style>
