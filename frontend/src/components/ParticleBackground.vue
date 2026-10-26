<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let raf = 0
let width = 0
let height = 0
let running = true

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  r: number
}

let particles: Particle[] = []

function initParticles() {
  const count = Math.min(80, Math.floor((width * height) / 22000))
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.32,
    vy: (Math.random() - 0.5) * 0.32,
    r: Math.random() * 1.5 + 0.6,
  }))
}

function drawGrid(c: CanvasRenderingContext2D) {
  const gap = 96
  c.strokeStyle = 'rgba(0, 229, 255, 0.045)'
  c.lineWidth = 1
  c.beginPath()
  for (let x = 0; x < width; x += gap) {
    c.moveTo(x, 0)
    c.lineTo(x, height)
  }
  for (let y = 0; y < height; y += gap) {
    c.moveTo(0, y)
    c.lineTo(width, y)
  }
  c.stroke()
}

function draw() {
  if (!ctx) return
  ctx.clearRect(0, 0, width, height)
  drawGrid(ctx)

  for (const p of particles) {
    p.x += p.vx
    p.y += p.vy
    if (p.x < 0 || p.x > width) p.vx *= -1
    if (p.y < 0 || p.y > height) p.vy *= -1

    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0, 229, 255, 0.55)'
    ctx.fill()
  }

  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i]
      const b = particles[j]
      const dx = a.x - b.x
      const dy = a.y - b.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 120) {
        ctx.strokeStyle = `rgba(0, 229, 255, ${0.12 * (1 - dist / 120)})`
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)
        ctx.stroke()
      }
    }
  }

  if (running) raf = requestAnimationFrame(draw)
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  width = window.innerWidth
  height = window.innerHeight
  canvas.width = Math.floor(width * dpr)
  canvas.height = Math.floor(height * dpr)
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  const c = canvas.getContext('2d')
  if (c) {
    c.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx = c
  }
  initParticles()
}

function onVisibility() {
  if (document.hidden) {
    running = false
    cancelAnimationFrame(raf)
  } else if (!running) {
    running = true
    raf = requestAnimationFrame(draw)
  }
}

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  document.addEventListener('visibilitychange', onVisibility)
  raf = requestAnimationFrame(draw)
})

onBeforeUnmount(() => {
  running = false
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
  document.removeEventListener('visibilitychange', onVisibility)
})
</script>

<template>
  <canvas ref="canvasRef" class="particle-bg" aria-hidden="true" />
</template>

<style scoped>
.particle-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
</style>
