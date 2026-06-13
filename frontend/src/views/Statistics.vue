<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">📊</span>统计分析</h1>
    </div>

    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-label">镜片总数</div>
        <div class="stat-value">{{ overview.total_lenses || 0 }}</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">累计佩戴时长</div>
        <div class="stat-value small">{{ overview.total_hours || 0 }}h</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">佩戴次数</div>
        <div class="stat-value">{{ overview.total_records || 0 }}</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-label">平均舒适度</div>
        <div class="stat-value small">{{ overview.avg_comfort || 0 }} ⭐</div>
      </div>
    </div>

    <div class="stats-grid" style="margin-top: 0;">
      <div class="stat-card cyan">
        <div class="stat-label">护理执行率</div>
        <div class="stat-value small">{{ careStats.care_execution_rate || 0 }}%</div>
        <div class="stat-sub">近30天 {{ careStats.total_care_records_30d || 0 }} 次护理</div>
      </div>
      <div class="stat-card orange">
        <div class="stat-label">复查逾期</div>
        <div class="stat-value">{{ overview.checkup_overdue_count || 0 }}</div>
        <div class="stat-sub">需尽快安排眼科检查</div>
      </div>
      <div class="stat-card red">
        <div class="stat-label">护理逾期</div>
        <div class="stat-value">{{ overview.care_overdue_count || 0 }}</div>
        <div class="stat-sub">镜片需立即护理</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-label">停戴观察中</div>
        <div class="stat-value">{{ overview.rest_count || 0 }}</div>
        <div class="stat-sub">即将到期: {{ overview.care_soon_count || 0 }} 副</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">🏆 品牌舒适度排行榜</div>
        <div v-if="brandStats.length" class="chart-container small" ref="brandChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🏆</div>
          <p>暂无品牌数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🧴 护理方式舒适度对比</div>
        <div v-if="careMethodComfort.length" class="chart-container small" ref="careMethodChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🧴</div>
          <p>暂无护理方式数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">💧 含水量适配度分析</div>
        <div v-if="waterStats.length" class="chart-container small" ref="waterChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">💧</div>
          <p>暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🎯 用途分布统计</div>
        <div v-if="purposeStats.length" class="chart-container small" ref="purposeChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🎯</div>
          <p>暂无数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">⏱️ 累计佩戴时长分布（按镜片）</div>
        <div v-if="lensHoursList.length" class="chart-container small" ref="hoursPieRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">⏱️</div>
          <p>暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🔔 护理与风险提醒统计</div>
        <div v-if="Object.keys(careStats.reminder_type_stats || {}).length" class="chart-container small" ref="reminderChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🔔</div>
          <p>暂无提醒数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">🏆 品牌舒适度详情表</div>
        <table class="table" v-if="brandStats.length">
          <thead>
            <tr>
              <th>排名</th>
              <th>品牌</th>
              <th>平均舒适</th>
              <th>佩戴次数</th>
              <th>累计时长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(b, idx) in brandStats" :key="b.brand">
              <td>
                <span v-if="idx === 0">🥇</span>
                <span v-else-if="idx === 1">🥈</span>
                <span v-else-if="idx === 2">🥉</span>
                <span v-else class="text-light">{{ idx + 1 }}</span>
              </td>
              <td class="text-bold">{{ b.brand }}</td>
              <td>
                <span :class="getComfortClass(Math.round(b.avg_comfort))">
                  {{ '⭐'.repeat(Math.round(b.avg_comfort)) }}
                </span>
                <span class="text-sm ml-8">{{ b.avg_comfort }}</span>
              </td>
              <td>{{ b.total_records }} 次</td>
              <td>{{ b.total_hours }}h</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无品牌数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🧴 护理方式详细对比</div>
        <table class="table" v-if="careMethodComfort.length">
          <thead>
            <tr>
              <th>护理方式</th>
              <th>镜片数</th>
              <th>平均舒适</th>
              <th>不适率</th>
              <th>总时长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in careMethodComfort" :key="c.care_method">
              <td class="text-bold">{{ c.care_method_display || '-' }}</td>
              <td>{{ c.lens_count }} 副</td>
              <td>
                <span :class="getComfortClass(Math.round(c.avg_comfort))">
                  {{ c.avg_comfort ? '⭐'.repeat(Math.round(c.avg_comfort)) : '-' }}
                </span>
                <span class="text-sm ml-8">{{ c.avg_comfort || '-' }}</span>
              </td>
              <td>
                <span class="tag" :class="getCareBadRateClass(c)">
                  {{ calcCareBadRate(c) }}%
                </span>
              </td>
              <td>{{ c.total_hours }}h</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无护理方式数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">💧 含水量详细分析</div>
        <table class="table" v-if="waterStats.length">
          <thead>
            <tr>
              <th>含水量区间</th>
              <th>镜片数</th>
              <th>平均舒适</th>
              <th>不适率</th>
              <th>总时长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="w in waterStats" :key="w.range">
              <td class="text-bold">{{ w.range }}</td>
              <td>{{ w.lens_count }} 副</td>
              <td>
                <span :class="getComfortClass(Math.round(w.avg_comfort))">
                  {{ w.avg_comfort ? '⭐'.repeat(Math.round(w.avg_comfort)) : '-' }}
                </span>
                <span class="text-sm ml-8">{{ w.avg_comfort || '-' }}</span>
              </td>
              <td>
                <span class="tag" :class="getBadRateClass(w)">
                  {{ calcBadRate(w) }}%
                </span>
              </td>
              <td>{{ w.total_hours }}h</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">📋 护理记录统计概览</div>
        <table class="table" v-if="Object.keys(careStats.care_type_stats || {}).length">
          <thead>
            <tr>
              <th>护理类型</th>
              <th>次数</th>
              <th>占比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(count, type) in careStats.care_type_stats" :key="type">
              <td class="text-bold">{{ getCareTypeLabel(type) }}</td>
              <td>{{ count }} 次</td>
              <td>
                <span class="tag tag-blue">
                  {{ careStats.total_care_records ? Math.round(count / careStats.total_care_records * 100) : 0 }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无护理记录</p>
        </div>
      </div>
    </div>

    <div class="card mb-20">
      <div class="card-title">🔔 长期未使用镜片提醒</div>
      <table class="table" v-if="unusedLenses.length">
        <thead>
          <tr>
            <th>镜片</th>
            <th>度数</th>
            <th>参数</th>
            <th>护理状态</th>
            <th>上次佩戴</th>
            <th>未使用</th>
            <th>有效期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lens in unusedLenses" :key="lens.id">
            <td>
              <div class="text-bold">{{ lens.brand }}</div>
              <div class="text-xs text-light">{{ lens.model_name || '-' }}</div>
            </td>
            <td>{{ lens.power_sph }}D</td>
            <td class="text-sm">{{ lens.water_content }}% · BC{{ lens.base_curve }}</td>
            <td>
              <span v-if="lens.care_status" class="tag" :class="getCareStatusTagClass(lens.care_status)">
                {{ getCareStatusLabel(lens.care_status) }}
              </span>
              <span v-else class="tag tag-gray">未设置</span>
            </td>
            <td>{{ formatDate(lens.last_wear_date) || '从未佩戴' }}</td>
            <td>
              <span class="tag tag-blue">超过 {{ getUnusedDays(lens) }} 天</span>
            </td>
            <td :class="lens.is_expired ? 'text-danger' : ''">
              {{ formatDate(lens.expiry_date) }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state" style="padding: 30px;">
        <div class="empty-icon">✨</div>
        <p>没有长期未使用的镜片，保持得很好！</p>
      </div>
    </div>

    <div class="card">
      <div class="card-title">💡 护眼小贴士</div>
      <div v-if="tips.length" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px;">
        <div v-for="(tip, idx) in tips" :key="idx" :class="['tip-card', tip.level]">
          <div class="tip-title">{{ tip.title }}</div>
          <div class="tip-content">{{ tip.content }}</div>
        </div>
      </div>
      <div v-else class="empty-state" style="padding: 30px;">
        <div class="empty-icon">💭</div>
        <p>暂无提示</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  getStatsOverview, getBrandComfort, getWaterContentFit,
  getPurposeStats, getEyeTips, getCareStats, getCareMethodComfort
} from '@/api/stats'
import { getUnusedLenses, getLensList } from '@/api/lens'
import { getRecordList } from '@/api/record'
import {
  formatDate, getComfortClass, CARE_STATUS_MAP, CARE_TYPE_OPTIONS
} from '@/utils/constants'

const overview = ref({})
const brandStats = ref([])
const waterStats = ref([])
const purposeStats = ref([])
const unusedLenses = ref([])
const tips = ref([])
const allRecords = ref([])
const allLenses = ref([])
const careStats = ref({})
const careMethodComfort = ref([])

const brandChartRef = ref(null)
const waterChartRef = ref(null)
const purposeChartRef = ref(null)
const hoursPieRef = ref(null)
const careMethodChartRef = ref(null)
const reminderChartRef = ref(null)
let brandChart = null, waterChart = null, purposeChart = null, hoursPieChart = null
let careMethodChart = null, reminderChart = null

const lensHoursList = ref([])

const REMINDER_TYPE_LABELS = {
  care: '护理提醒',
  replacement: '更换提醒',
  checkup: '复查提醒',
  rest: '停戴提醒',
  risk: '风险提醒'
}

const calcBadRate = (w) => {
  if (!w.total_records) return 0
  const badReactions = ['dryness', 'redness', 'fatigue', 'dryness_redness', 'dryness_fatigue', 'redness_fatigue', 'all']
  let badCount = 0
  w.reactions.forEach(r => {
    if (badReactions.includes(r.eye_reaction)) badCount += r.count
  })
  return Math.round(badCount / w.total_records * 100)
}

const getBadRateClass = (w) => {
  const rate = calcBadRate(w)
  if (rate > 50) return 'tag-red'
  if (rate > 30) return 'tag-yellow'
  return 'tag-green'
}

const calcCareBadRate = (c) => {
  if (!c.total_records) return 0
  const badReactions = ['dryness', 'redness', 'fatigue', 'dryness_redness', 'dryness_fatigue', 'redness_fatigue', 'all']
  let badCount = 0
  c.reactions?.forEach(r => {
    if (badReactions.includes(r.eye_reaction)) badCount += r.count
  })
  return Math.round(badCount / c.total_records * 100)
}

const getCareBadRateClass = (c) => {
  const rate = calcCareBadRate(c)
  if (rate > 50) return 'tag-red'
  if (rate > 30) return 'tag-yellow'
  return 'tag-green'
}

const getUnusedDays = (lens) => {
  const refDate = lens.last_wear_date ? new Date(lens.last_wear_date) : new Date(lens.created_at)
  return Math.floor((Date.now() - refDate.getTime()) / 86400000)
}

const getCareStatusLabel = (status) => CARE_STATUS_MAP[status] || status
const getCareStatusTagClass = (status) => {
  const map = { normal: 'tag-green', rest: 'tag-purple', overdue: 'tag-red', soon: 'tag-yellow' }
  return map[status] || 'tag-gray'
}
const getCareTypeLabel = (type) => {
  const opt = CARE_TYPE_OPTIONS.find(o => o.value === type)
  return opt ? opt.label : type
}

const loadData = async () => {
  try {
    const [ov, brands, waters, purposes, unused, tps, records, lenses, care, careMethod] = await Promise.all([
      getStatsOverview(),
      getBrandComfort(),
      getWaterContentFit(),
      getPurposeStats(),
      getUnusedLenses(90),
      getEyeTips(),
      getRecordList({ page_size: 1000 }),
      getLensList(),
      getCareStats(),
      getCareMethodComfort()
    ])
    overview.value = ov
    brandStats.value = Array.isArray(brands) ? brands : []
    waterStats.value = Array.isArray(waters) ? waters : []
    purposeStats.value = Array.isArray(purposes) ? purposes : []
    unusedLenses.value = Array.isArray(unused) ? unused : (unused.results || [])
    tips.value = Array.isArray(tps) ? tps : []
    allRecords.value = Array.isArray(records) ? records : (records.results || [])
    allLenses.value = Array.isArray(lenses) ? lenses : (lenses.results || [])
    careStats.value = care || {}
    careMethodComfort.value = Array.isArray(careMethod) ? careMethod : []

    const hoursMap = {}
    allRecords.value.forEach(r => {
      const lens = allLenses.value.find(l => l.id === r.lens)
      const name = lens ? `${lens.brand} ${lens.model_name || ''}` : `镜片#${r.lens}`
      hoursMap[name] = (hoursMap[name] || 0) + r.duration_hours
    })
    lensHoursList.value = Object.entries(hoursMap)
      .map(([name, hours]) => ({ name, value: Number(hours.toFixed(1)) }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)

    await nextTick()
    renderBrandChart()
    renderWaterChart()
    renderPurposeChart()
    renderHoursPie()
    renderCareMethodChart()
    renderReminderChart()
  } catch (e) {
    console.error(e)
  }
}

const renderBrandChart = () => {
  if (!brandChartRef.value || !brandStats.value.length) return
  if (!brandChart) brandChart = echarts.init(brandChartRef.value)
  brandChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 50, top: 20, bottom: 30 },
    xAxis: { type: 'value', min: 0, max: 5, name: '舒适度' },
    yAxis: {
      type: 'category',
      data: [...brandStats.value].reverse().map(b => b.brand)
    },
    series: [{
      type: 'bar',
      data: [...brandStats.value].reverse().map(b => ({
        value: b.avg_comfort,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#A78BFA' },
            { offset: 1, color: '#8B5CF6' }
          ]),
          borderRadius: [0, 8, 8, 0]
        }
      })),
      label: { show: true, position: 'right', formatter: p => p.value + ' ⭐' },
      barWidth: 20
    }]
  })
}

const renderWaterChart = () => {
  if (!waterChartRef.value || !waterStats.value.length) return
  if (!waterChart) waterChart = echarts.init(waterChartRef.value)
  const data = waterStats.value.filter(w => w.total_records > 0)
  waterChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均舒适度', '佩戴次数'], top: 0 },
    grid: { left: 50, right: 60, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: data.map(w => w.range) },
    yAxis: [
      { type: 'value', min: 0, max: 5, name: '舒适度' },
      { type: 'value', name: '次数' }
    ],
    series: [
      {
        name: '平均舒适度',
        type: 'bar',
        data: data.map(w => w.avg_comfort),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#60A5FA' },
            { offset: 1, color: '#3B82F6' }
          ]),
          borderRadius: [6, 6, 0, 0]
        },
        label: { show: true, position: 'top' }
      },
      {
        name: '佩戴次数',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(w => w.total_records),
        smooth: true,
        itemStyle: { color: '#F472B6' },
        lineStyle: { width: 3 }
      }
    ]
  })
}

const renderPurposeChart = () => {
  if (!purposeChartRef.value || !purposeStats.value.length) return
  if (!purposeChart) purposeChart = echarts.init(purposeChartRef.value)
  const labels = { daily: '日常', date: '约会', photo: '拍照' }
  const colors = { daily: '#8B5CF6', date: '#F472B6', photo: '#3B82F6' }
  purposeChart.setOption({
    tooltip: { trigger: 'item', formatter: p => `${p.name}<br/>时长: ${p.value}h (${p.percent}%)` },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['40%', '45%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
        label: { formatter: '{b}\n{d}%' },
        data: purposeStats.value.filter(p => p.total_hours > 0).map(p => ({
          name: labels[p.purpose] || p.purpose,
          value: p.total_hours,
          itemStyle: { color: colors[p.purpose] }
        }))
      }
    ]
  })
}

const renderHoursPie = () => {
  if (!hoursPieRef.value || !lensHoursList.value.length) return
  if (!hoursPieChart) hoursPieChart = echarts.init(hoursPieRef.value)
  hoursPieChart.setOption({
    tooltip: { trigger: 'item', formatter: p => `${p.name}<br/>${p.value}h (${p.percent}%)` },
    legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['30%', '60%'],
      center: ['50%', '45%'],
      roseType: 'radius',
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: lensHoursList.value
    }]
  })
}

const renderCareMethodChart = () => {
  if (!careMethodChartRef.value || !careMethodComfort.value.length) return
  if (!careMethodChart) careMethodChart = echarts.init(careMethodChartRef.value)
  const data = careMethodComfort.value.filter(c => c.total_records > 0)
  careMethodChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均舒适度', '不适率(%)'], top: 0 },
    grid: { left: 90, right: 60, top: 40, bottom: 30 },
    xAxis: { type: 'value', min: 0, max: 5, name: '舒适度' },
    yAxis: {
      type: 'category',
      data: [...data].reverse().map(c => c.care_method_display || c.care_method)
    },
    series: [
      {
        name: '平均舒适度',
        type: 'bar',
        data: [...data].reverse().map(c => c.avg_comfort),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#34D399' },
            { offset: 1, color: '#10B981' }
          ]),
          borderRadius: [0, 8, 8, 0]
        },
        label: { show: true, position: 'right', formatter: p => p.value + ' ⭐' },
        barWidth: 18
      }
    ]
  })
}

const renderReminderChart = () => {
  if (!reminderChartRef.value || !Object.keys(careStats.value.reminder_type_stats || {}).length) return
  if (!reminderChart) reminderChart = echarts.init(reminderChartRef.value)
  const data = Object.entries(careStats.value.reminder_type_stats || {}).map(([type, count]) => ({
    name: REMINDER_TYPE_LABELS[type] || type,
    value: count
  }))
  const colors = ['#60A5FA', '#F59E0B', '#EF4444', '#8B5CF6', '#F472B6']
  reminderChart.setOption({
    tooltip: { trigger: 'item', formatter: p => `${p.name}<br/>${p.value}条 (${p.percent}%)` },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
      label: { formatter: '{b}\n{d}%' },
      data: data.map((d, i) => ({
        ...d,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  })
}

onMounted(async () => {
  await loadData()
  window.addEventListener('resize', () => {
    brandChart?.resize(); waterChart?.resize(); purposeChart?.resize(); hoursPieChart?.resize()
    careMethodChart?.resize(); reminderChart?.resize()
  })
})
</script>
