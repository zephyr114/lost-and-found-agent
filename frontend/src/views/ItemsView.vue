<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getCategories, getItems } from '@/api/items'
import type { Item, ItemType } from '@/api/items'
import ItemCard from '@/components/ItemCard.vue'

const route = useRoute()

const activeType = ref<ItemType>((route.query.type as ItemType) === 'found' ? 'found' : 'lost')
const items = ref<Item[]>([])
const total = ref(0)
const loading = ref(false)
const categories = ref<string[]>([])
const page = ref(1)
const size = 20

const filters = reactive({
  q: '',
  category: '',
  location: '',
  sort: 'newest' as 'newest' | 'oldest' | 'distance',
})

async function load() {
  loading.value = true
  try {
    const res = await getItems({
      item_type: activeType.value,
      q: filters.q || undefined,
      category: filters.category || undefined,
      location: filters.location || undefined,
      sort: filters.sort,
      page: page.value,
      size,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

watch(activeType, () => {
  page.value = 1
  load()
})

onMounted(async () => {
  categories.value = await getCategories()
  await load()
})
</script>

<template>
  <div class="items-page">
    <div class="items-page__tabs">
      <el-radio-group v-model="activeType" size="large">
        <el-radio-button value="lost">🔍 失物信息</el-radio-button>
        <el-radio-button value="found">📦 招领信息</el-radio-button>
      </el-radio-group>
    </div>

    <el-card shadow="never" class="items-page__filters">
      <div class="filter-row">
        <el-input v-model="filters.q" placeholder="搜索标题 / 描述 / 品牌" clearable class="filter-item filter-item--wide" @keyup.enter="search" @clear="search" />
        <el-select v-model="filters.category" placeholder="物品类别" clearable class="filter-item" @change="search">
          <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
        </el-select>
        <el-input v-model="filters.location" placeholder="地点关键词" clearable class="filter-item" @keyup.enter="search" @clear="search" />
        <el-select v-model="filters.sort" class="filter-item filter-item--sort" @change="search">
          <el-option label="最新发布" value="newest" />
          <el-option label="最早发布" value="oldest" />
        </el-select>
        <el-button type="primary" @click="search">搜索</el-button>
      </div>
    </el-card>

    <div v-loading="loading" class="items-page__grid">
      <el-empty v-if="!loading && items.length === 0" description="暂无数据（新发布的信息需审核通过后展示）" />
      <el-row v-else :gutter="16">
        <el-col v-for="item in items" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6">
          <ItemCard :item="item" />
        </el-col>
      </el-row>
    </div>

    <div class="items-page__pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="size"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="load"
      />
    </div>
  </div>
</template>

<style scoped>
.items-page {
  max-width: 1080px;
  margin: 0 auto;
}
.items-page__tabs {
  text-align: center;
  margin-bottom: 16px;
}
.items-page__filters {
  margin-bottom: 16px;
}
.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.filter-item {
  width: 160px;
}
.filter-item--wide {
  flex: 1;
  min-width: 200px;
}
.items-page__grid {
  min-height: 200px;
}
.items-page__pager {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}
</style>
