<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">😊</span>舒适度追踪</h1>
    </div>

    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-label">平均舒适度</div>
        <div class="stat-value small">
          <span v-if="overview.avg_comfort">{{ '⭐'.repeat(Math.round(overview.avg_comfort)) }}</span>
          <span v-else>-</span>
        </div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">舒适率(≥4分)</div>
        <div class="stat-value small">{{ comfortRate }}%</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-label">有不适反应</div>
        <div class="stat-value small">{{ reactionCount }} 次</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">最长单次佩戴</div>
        <div class="stat-value small">{{ maxDuration }}h</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">📈 舒适度趋势（近{{ trendDays }}天）</div>
        <div class="mb-12">
          <select v-model="trendDays" class="form-control" style="width: auto; display: inline;" @change="loadTrend">
            <option :value="7">近7天</option>
            <option :value="14">近14天</option>
            <option :value="30">近30天</option>
            <option :value="90">近90天</option>
          </select>
        </div>
        <div class="chart-container small" ref="trendChartRef"></div>
      </div>

      <div class="card">
        <div class="card-title">😊 舒适度分布</div>
        <div class="chart-container small" ref="comfortPieRef"></div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">👁️ 眼部反应统计</div>
        <div class="chart-container small" ref="reactionChartRef"></div>
      </div>

      <div class="card">
        <div class="card-title">⏱️ 佩戴时长 vs 舒适度</div>
        <div class="chart-container small" ref="durationChartRef"></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">🔍 各镜片舒适度详情</div>
      <table class="table" v-if="lensComfortList.length">
        <thead>
          <tr>
            <th>镜片</th>
            <th>佩戴次数</th>
            <th>累计时长</th>
            <th>平均舒适度</th>
            <th>最近佩戴</th>
            <th>不适率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in lensComfortList" :key="item.id">
            <td>
              <div class="text-bold">{{ item.brand }}</div>
              <div class="text-xs text-light">{{ item.model_name }} · {{ item.power_sph }}D</div>
            </td>
            <td>{{ item.wear_count }} 次</td>
            <td>{{ item.total_hours }}h</td>
            <td>
              <div class="rating">
                <span v-for="i in 5" :key="i" class="star" :class="{ active: i <= Math.round(item.avg_comfort || 0) }">★</span>
              </div>
              <span class="text-sm ml-8">{{ item.avg_comfort?.toFixed(1) || '-' }}</span>
            </td>
            <td class="text-sm">{{ formatDate(item.last_wear_date) || '未佩戴' }}</td>
            <td>
              <span class="tag" :class="item.bad_rate > 30 ? 'tag-red' : item.bad_rate > 10 ? 'tag-yellow' : 'tag-green'">
                {{ item.bad_rate }}%
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state" style="padding: 40px;">
        <div class="empty-icon">📊</div>
        <p>暂无数据，请先添加佩戴记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getStatsOverview, getComfortTrend } from '@/api/stats'
import { getLensList } from '@/api/lens'
import { getRecordList } from '@/api/record'
import { formatDate } from '@/utils/constants'

const overview = ref({})
const trendData = ref([])
const allRecords = ref([])
const allLenses = ref([])
const trendDays = ref(30)

const trendChartRef = ref(null)
const comfortPieRef = ref(null)
const reactionChartRef = ref(null)
const durationChartRef = ref(null)
let trendChart = null, pieChart = null, reactionChart = null, durationChart = null

const comfortRate = computed(() => {
  if (!allRecords.value.length) return 0
  const good = allRecords.value.filter(r => r.comfort_level >= 4).length
  return Math.round(good / allRecords.value.length * 100)
})

const reactionCount = computed(() => {
  return allRecords.value.filter(r => r.eye_reaction !== 'none').length
})

const maxDuration = computed(() => {
  if (!allRecords.value.length) return 0
  return Math.max(...allRecords.value.map(r => r.duration_hours))
})

const lensComfortList = computed(() => {
  const map = {}
  allRecords.value.forEach(r => {
    if (!map[r.lens]) {
      const lens = allLenses.value.find(l => l.id === r.lens)
      map[r.lens] = {
        id: r.lens,
        brand: lens?.brand || '未知',
        model_name: lens?.model_name || '',
        power_sph: lens?.power_sph || 0,
        wear_count: 0,
        total_hours: 0,
        comfort_sum: 0,
        last_wear_date: null,
        bad_count: 0,
        avg_comfort: 0,
        bad_rate: 0
      }
    }
    const m = map[r.lens]
    m.wear_count++
    m.total_hours += r.duration_hours
    m.comfort_sum += r.comfort_level
    if (!m.last_wear_date || r.wear_date > m.last_wear_date) {
      m.last_wear_date = r.wear_date
    }
    if (r.eye_reaction !== 'none' || r.comfort_level <= 2) {
      m.bad_count++
    }
  })
  return Object.values(map).map(m => ({
    ...m,
    total_hours: m.total_hours.toFixed(1),
    avg_comfort: m.comfort_sum / m.wear_count,
    bad_rate: Math.round(m.bad_count / m.wear_count * 100)
  })).sort((a, b) => b.wear_count - a.wear_count)
})

const loadTrend = async () => {
  try {
    trendData.value = await getComfortTrend(trendDays.value)
    await nextTick()
    renderTrendChart()
  } catch (e) {
    console.error(e)
  }
}

const loadAll = async () => {
  try {
    const [ov, records, lenses] = await Promise.all([
      getStatsOverview(),
      getRecordList({ page_size: 1000 }),
      getLensList()
    ])
    overview.value = ov
    allRecords.value = Array.isArray(records) ? records : (records.results || [])
    allLenses.value = Array.isArray(lenses) ? lenses : (lenses.results || [])
    await nextTick()
    renderPieChart()
    renderReactionChart()
    renderDurationChart()
  } catch (e) {
    console.error(e)
  }
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
  const dates = trendData.value.map(d => d.date ? d.date.slice(5) : '')
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 50, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: [
      { type: 'value', min: 0, max: 5, name: '舒适度' },
      { type: 'value', name: '小时' }
    ],
    series: [
      {
        name: '舒适度',
        type: 'line',
        data: trendData.value.map(d => Number(d.avg_comfort || 0)),
        smooth: true,
        itemStyle: { color: '#10B981' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.02)' }
          ])
        }
      },
      {
        name: '时长',
        type: 'bar',
        yAxisIndex: 1,
        data: trendData.value.map(d => Number(d.total_hours || 0)),
        itemStyle: { color: 'rgba(139, 92, 246, 0.6)', borderRadius: [4, 4, 0, 0] }
      }
    ]
  })
}

const renderPieChart = () => {
  if (!comfortPieRef.value) return
  if (!pieChart) pieChart = echarts.init(comfortPieRef.value)
  const counts = [0, 0, 0, 0, 0]
  allRecords.value.forEach(r => { if (r.comfort_level >= 1) counts[r.comfort_level - 1]++ })
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, itemWidth: 12, itemHeight: 12 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%' },
      data: [
        { value: counts[4], name: '⭐⭐⭐⭐⭐ 非常舒适', itemStyle: { color: '#10B981' } },
        { value: counts[3], name: '⭐⭐⭐⭐ 舒适', itemStyle: { color: '#84CC16' } },
        { value: counts[2], name: '⭐⭐⭐ 一般', itemStyle: { color: '#F59E0B' } },
        { value: counts[1], name: '⭐⭐ 较不适', itemStyle: { color: '#F97316' } },
        { value: counts[0], name: '⭐ 非常不适', itemStyle: { color: '#EF4444' } }
      ].filter(d => d.value > 0)
    }]
  })
}

const renderReactionChart = () => {
  if (!reactionChartRef.value) return
  if (!reactionChart) reactionChart = echarts.init(reactionChartRef.value)
  const rmap = { none: '无不适', dryness: '干涩', redness: '红血丝', fatigue: '视疲劳',
    dryness_redness: '干涩+红血丝', dryness_fatigue: '干涩+视疲劳',
    redness_fatigue: '红血丝+视疲劳', all: '全部不适' }
  const counts = {}
  allRecords.value.forEach(r => { counts[r.eye_reaction] = (counts[r.eye_reaction] || 0) + 1 })
  const data = Object.entries(counts).map(([k, v]) => ({
    name: rmap[k] || k,
    value: v,
    itemStyle: { color: k === 'none' ? '#10B981' : '#F59E0B' }
  })).sort((a, b) => b.value - a.value)
  reactionChart.setOption({
    tooltip: { trigger: 'item' },
    grid: { left: 100, right: 30, top: 20, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: data.map(d => d.name) },
    series: [{
      type: 'bar',
      data: data,
      itemStyle: { borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right' }
    }]
  })
}

const renderDurationChart = () => {
  if (!durationChartRef.value) return
  if (!durationChart) durationChart = echarts.init(durationChartRef.value)
  const buckets = [
    { range: '0-4h', sum: 0, count: 0, min: 0, max: 4 },
    { range: '4-6h', sum: 0, count: 0, min: 4, max: 6 },
    { range: '6-8h', sum: 0, count: 0, min: 6, max: 8 },
    { range: '8-10h', sum: 0, count: 0, min: 8, max: 10 },
    { range: '>10h', sum: 0, count: 0, min: 10, max: 999 }
  ]
  allRecords.value.forEach(r => {
    const b = buckets.find(b => r.duration_hours >= b.min && r.duration_hours < b.max)
    if (b) { b.sum += r.comfort_level; b.count++ }
  })
  durationChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: buckets.map(b => b.range) },
    yAxis: { type: 'value', min: 0, max: 5, name: '平均舒适度' },
    series: [{
      type: 'bar',
      data: buckets.map(b => ({
        value: b.count ? Number((b.sum / b.count).toFixed(2)) : 0,
        itemStyle: {
          color: b.max <= 8 ? '#10B981' : b.max <= 10 ? '#F59E0B' : '#EF4444',
          borderRadius: [8, 8, 0, 0]
        }
      })),
      label: { show: true, position: 'top', formatter: p => p.value || '无数据' }
    }]
  })
}

onMounted(async () => {
  await Promise.all([loadTrend(), loadAll()])
  window.addEventListener('resize', () => {
    trendChart?.resize(); pieChart?.resize(); reactionChart?.resize(); durationChart?.resize()
  })
})
</script>
