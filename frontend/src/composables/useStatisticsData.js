/**
 * useStatisticsData - 统计分析页数据与图表 composable
 *
 * 将 Statistics.vue 中的数据请求、图表 option 工厂、标签映射等
 * 重复逻辑抽离出来，页面组件只负责渲染。
 */
import { computed, ref, watch, nextTick } from 'vue'
import { useMultiBlockRequest } from './useSafeRequest'
import { useCharts, CHART_PRESETS } from './useCharts'
import {
  getStatsOverview,
  getBrandComfort,
  getWaterContentFit,
  getPurposeStats,
  getEyeTips,
  getCareStats,
  getCareMethodComfort,
} from '@/api/stats'
import { getOutfitPlanStats } from '@/api/outfitPlan'
import { getUnusedLenses, getLensList } from '@/api/lens'
import { getRecordList } from '@/api/record'
import { getBudgetStats, getBudgetMonthlySummary } from '@/api/budget'
import { getTravelPlanStats } from '@/api/travel'

const REMINDER_TYPE_LABELS = {
  care: '护理提醒',
  replacement: '更换提醒',
  checkup: '复查提醒',
  rest: '停戴提醒',
  risk: '风险提醒',
}

export function useStatisticsData() {
  const budgetLimit = ref(500)
  const lensHoursList = ref([])

  const { blocks, loading, loadAll, reload } = useMultiBlockRequest({
    overview: { fn: () => getStatsOverview(), fallback: {}, normalize: 'object', name: '概览统计' },
    brandStats: { fn: () => getBrandComfort(), fallback: [], normalize: 'array', name: '品牌舒适度' },
    waterStats: { fn: () => getWaterContentFit(), fallback: [], normalize: 'array', name: '含水量适配' },
    purposeStats: { fn: () => getPurposeStats(), fallback: [], normalize: 'array', name: '用途分布' },
    unusedLenses: { fn: () => getUnusedLenses(90), fallback: [], normalize: 'array', name: '长期未用镜片' },
    tips: { fn: () => getEyeTips(), fallback: [], normalize: 'array', name: '护眼小贴士' },
    allRecords: { fn: () => getRecordList({ page_size: 1000 }), fallback: [], normalize: 'array', name: '全部佩戴记录' },
    allLenses: { fn: () => getLensList(), fallback: [], normalize: 'array', name: '镜片列表' },
    careStats: { fn: () => getCareStats(), fallback: {}, normalize: 'object', name: '护理统计' },
    careMethodComfort: { fn: () => getCareMethodComfort(), fallback: [], normalize: 'array', name: '护理方式舒适度' },
    outfitStats: { fn: () => getOutfitPlanStats(), fallback: {}, normalize: 'object', name: '搭配计划统计' },
    budgetStats: {
      fn: () => getBudgetStats({ limit: budgetLimit.value }).catch(() => ({})),
      fallback: {},
      normalize: 'object',
      name: '预算统计',
    },
    travelStats: {
      fn: () => getTravelPlanStats().catch(() => ({})),
      fallback: {},
      normalize: 'object',
      name: '旅行统计',
    },
  }, { immediate: false })

  watch(budgetLimit, () => reload('budgetStats'))

  watch(
    [() => blocks.allRecords.data.value, () => blocks.allLenses.data.value],
    ([records, lenses]) => {
      if (!records || !lenses) return
      const hoursMap = {}
      records.forEach((r) => {
        const lens = lenses.find((l) => l.id === r.lens)
        const name = lens
          ? `${lens.brand} ${lens.model_name || ''}`
          : `镜片#${r.lens}`
        hoursMap[name] = (hoursMap[name] || 0) + r.duration_hours
      })
      lensHoursList.value = Object.entries(hoursMap)
        .map(([name, hours]) => ({ name, value: Number(Number(hours).toFixed(1)) }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
    },
    { immediate: true }
  )

  const charts = useCharts({
    brand: (data, ec) => {
      if (!data?.length) return null
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 100, right: 50, top: 20, bottom: 30 },
        xAxis: { type: 'value', min: 0, max: 5, name: '舒适度' },
        yAxis: { type: 'category', data: [...data].reverse().map((b) => b.brand) },
        series: [{
          type: 'bar',
          data: [...data].reverse().map((b) => ({
            value: b.avg_comfort,
            itemStyle: { color: CHART_PRESETS.gradients.purple(ec), borderRadius: [0, 8, 8, 0] },
          })),
          label: { show: true, position: 'right', formatter: (p) => p.value + ' ⭐' },
          barWidth: 20,
        }],
      }
    },
    water: (data, ec) => {
      if (!data?.length) return null
      const filtered = data.filter((w) => w.total_records > 0)
      return {
        tooltip: { trigger: 'axis' },
        legend: { data: ['平均舒适度', '佩戴次数'], top: 0 },
        grid: { left: 50, right: 60, top: 40, bottom: 30 },
        xAxis: { type: 'category', data: filtered.map((w) => w.range) },
        yAxis: [
          { type: 'value', min: 0, max: 5, name: '舒适度' },
          { type: 'value', name: '次数' },
        ],
        series: [
          {
            name: '平均舒适度', type: 'bar',
            data: filtered.map((w) => w.avg_comfort),
            itemStyle: { color: CHART_PRESETS.gradients.blue(ec), borderRadius: [6, 6, 0, 0] },
            label: { show: true, position: 'top' },
          },
          {
            name: '佩戴次数', type: 'line', yAxisIndex: 1,
            data: filtered.map((w) => w.total_records),
            smooth: true, itemStyle: { color: '#F472B6' }, lineStyle: { width: 3 },
          },
        ],
      }
    },
    purpose: (data, ec) => {
      if (!data?.length) return null
      const labels = { daily: '日常', date: '约会', photo: '拍照' }
      const colors = { daily: '#8B5CF6', date: '#F472B6', photo: '#3B82F6' }
      return {
        tooltip: { trigger: 'item', formatter: (p) => `${p.name}<br/>时长: ${p.value}h (${p.percent}%)` },
        legend: { bottom: 0 },
        series: [{
          type: 'pie', radius: ['35%', '65%'], center: ['40%', '45%'],
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
          label: { formatter: '{b}\n{d}%' },
          data: data.filter((p) => p.total_hours > 0).map((p) => ({
            name: labels[p.purpose] || p.purpose,
            value: p.total_hours,
            itemStyle: { color: colors[p.purpose] },
          })),
        }],
      }
    },
    hoursPie: (data) => {
      if (!data?.length) return null
      return {
        tooltip: { trigger: 'item', formatter: (p) => `${p.name}<br/>${p.value}h (${p.percent}%)` },
        legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11 } },
        series: [{
          type: 'pie', radius: ['30%', '60%'], center: ['50%', '45%'], roseType: 'radius',
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          data,
        }],
      }
    },
    careMethod: (data, ec) => {
      if (!data?.length) return null
      const filtered = data.filter((c) => c.total_records > 0)
      return {
        tooltip: { trigger: 'axis' },
        legend: { data: ['平均舒适度', '不适率(%)'], top: 0 },
        grid: { left: 90, right: 60, top: 40, bottom: 30 },
        xAxis: { type: 'value', min: 0, max: 5, name: '舒适度' },
        yAxis: { type: 'category', data: [...filtered].reverse().map((c) => c.care_method_display || c.care_method) },
        series: [{
          name: '平均舒适度', type: 'bar',
          data: [...filtered].reverse().map((c) => c.avg_comfort),
          itemStyle: { color: CHART_PRESETS.gradients.green(ec), borderRadius: [0, 8, 8, 0] },
          label: { show: true, position: 'right', formatter: (p) => p.value + ' ⭐' },
          barWidth: 18,
        }],
      }
    },
    reminder: (data, ec) => {
      if (!data || !Object.keys(data).length) return null
      const seriesData = Object.entries(data).map(([type, count]) => ({
        name: REMINDER_TYPE_LABELS[type] || type,
        value: count,
      }))
      return {
        tooltip: { trigger: 'item', formatter: (p) => `${p.name}<br/>${p.value}条 (${p.percent}%)` },
        legend: { bottom: 0 },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
          label: { formatter: '{b}\n{d}%' },
          data: seriesData.map((d, i) => ({ ...d, itemStyle: { color: CHART_PRESETS.pieColors[i % CHART_PRESETS.pieColors.length] } })),
        }],
      }
    },
    makeup: (data, ec) => {
      if (!data?.length) return null
      const reversed = [...data].reverse().slice(0, 10)
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 40, top: 20, bottom: 30 },
        xAxis: { type: 'value', name: '次数' },
        yAxis: { type: 'category', data: reversed.map((d) => d.style) },
        series: [{
          type: 'bar',
          data: reversed.map((d) => ({
            value: d.count,
            itemStyle: { color: CHART_PRESETS.gradients.pink(ec), borderRadius: [0, 8, 8, 0] },
          })),
          label: { show: true, position: 'right' },
          barWidth: 20,
        }],
      }
    },
    sceneLens: (data) => {
      if (!data?.length) return null
      const top = data.slice(0, 10)
      const scenes = [...new Set(top.map((d) => d.scene))]
      const lenses = [...new Set(top.map((d) => d.lens))]
      const series = lenses.map((lens) => ({
        name: lens, type: 'bar', stack: 'total',
        data: scenes.map((scene) => {
          const item = top.find((d) => d.scene === scene && d.lens === lens)
          return item ? item.count : 0
        }),
      }))
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: 80, right: 30, top: 40, bottom: 60 },
        xAxis: { type: 'category', data: scenes, axisLabel: { fontSize: 11, rotate: 30 } },
        yAxis: { type: 'value', name: '使用次数' },
        series,
      }
    },
    matchScore: (data, ec) => {
      if (!data?.length) return null
      const reversed = [...data].reverse().slice(0, 10)
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 40, top: 20, bottom: 30 },
        xAxis: { type: 'value', min: 0, max: 5, name: '搭配评分' },
        yAxis: { type: 'category', data: reversed.map((d) => `${d.scene} - ${d.lens}`) },
        series: [{
          type: 'bar',
          data: reversed.map((d) => ({
            value: d.match_score,
            itemStyle: { color: CHART_PRESETS.gradients.yellow(ec), borderRadius: [0, 8, 8, 0] },
          })),
          label: { show: true, position: 'right', formatter: (p) => p.value + ' ⭐' },
          barWidth: 20,
        }],
      }
    },
    tagStats: (data, ec) => {
      if (!data) return null
      const entries = Object.entries(data).filter(([_, v]) => v.count > 0)
      if (!entries.length) return null
      return {
        tooltip: { trigger: 'item', formatter: (p) => `${p.name}<br/>${p.value}条 (${p.percent}%)` },
        legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11 } },
        series: [{
          type: 'pie', radius: ['35%', '65%'], center: ['50%', '45%'],
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
          label: { formatter: '{b}\n{d}%', fontSize: 11 },
          data: entries.map(([key, val], i) => ({
            name: val.label,
            value: val.count,
            itemStyle: { color: CHART_PRESETS.pieColors[i % CHART_PRESETS.pieColors.length] },
          })),
        }],
      }
    },
    budgetTrend: (data, ec) => {
      if (!data?.length) return null
      return {
        tooltip: { trigger: 'axis' },
        legend: { data: ['消费金额', '采购次数'], top: 0 },
        grid: { left: 50, right: 60, top: 40, bottom: 40 },
        xAxis: { type: 'category', data: data.map((d) => d.month.slice(5) + '月'), axisLabel: { fontSize: 11 } },
        yAxis: [{ type: 'value', name: '元' }, { type: 'value', name: '次' }],
        series: [
          {
            name: '消费金额', type: 'bar',
            data: data.map((d) => d.total_spent),
            itemStyle: { color: CHART_PRESETS.gradients.purple(ec), borderRadius: [6, 6, 0, 0] },
          },
          {
            name: '采购次数', type: 'line', yAxisIndex: 1,
            data: data.map((d) => d.purchase_count),
            smooth: true, itemStyle: { color: '#F472B6' }, lineStyle: { width: 3 },
          },
        ],
      }
    },
    brandValue: (data, ec) => {
      if (!data?.length) return null
      const reversed = data.slice(0, 8).reverse()
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: ['性价比评分', '平均舒适度'], top: 0 },
        grid: { left: 120, right: 50, top: 40, bottom: 30 },
        xAxis: [
          { type: 'value', min: 0, max: 10, name: '评分' },
          { type: 'value', min: 0, max: 5, name: '舒适度' },
        ],
        yAxis: { type: 'category', data: reversed.map((d) => `${d.brand} ${d.model}`), axisLabel: { fontSize: 11 } },
        series: [
          {
            name: '性价比评分', type: 'bar',
            data: reversed.map((d) => ({
              value: d.value_score,
              itemStyle: { color: CHART_PRESETS.gradients.yellow(ec), borderRadius: [0, 8, 8, 0] },
            })),
            label: { show: true, position: 'right' },
            barWidth: 14,
          },
          {
            name: '平均舒适度', type: 'bar', xAxisIndex: 1,
            data: reversed.map((d) => ({
              value: d.avg_comfort,
              itemStyle: { color: CHART_PRESETS.gradients.green(ec), borderRadius: [0, 8, 8, 0] },
            })),
            barWidth: 14,
          },
        ],
      }
    },
    travelLens: (data, ec) => {
      if (!data?.length) return null
      const reversed = data.slice(0, 8).reverse()
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 50, top: 20, bottom: 30 },
        xAxis: { type: 'value', name: '使用次数' },
        yAxis: {
          type: 'category',
          data: reversed.map((d) => (d.brand ? `${d.brand} ${d.model || ''}` : `镜片#${d.lens_id}`)),
          axisLabel: { fontSize: 11 },
        },
        series: [{
          type: 'bar',
          data: reversed.map((d) => ({
            value: d.count || d.travel_count || 0,
            itemStyle: { color: CHART_PRESETS.gradients.indigo(ec), borderRadius: [0, 8, 8, 0] },
          })),
          label: { show: true, position: 'right', formatter: (p) => p.value + ' 次' },
          barWidth: 16,
        }],
      }
    },
    travelComfort: (data, ec) => {
      if (!data?.length) return null
      const reversed = data.slice(0, 8).reverse()
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 50, top: 20, bottom: 30 },
        xAxis: { type: 'value', min: 0, max: 5, name: '舒适度' },
        yAxis: {
          type: 'category',
          data: reversed.map((d) => (d.brand ? `${d.brand} ${d.model || ''}` : `镜片#${d.lens_id}`)),
          axisLabel: { fontSize: 11 },
        },
        series: [{
          type: 'bar',
          data: reversed.map((d) => ({
            value: d.avg_comfort || 0,
            itemStyle: { color: CHART_PRESETS.gradients.pink(ec), borderRadius: [0, 8, 8, 0] },
          })),
          label: { show: true, position: 'right', formatter: (p) => p.value + ' ⭐' },
          barWidth: 16,
        }],
      }
    },
    travelAlert: (data, ec, alertTypeMap) => {
      if (!data || !Object.keys(data).length) return null
      return {
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, type: 'scroll' },
        series: [{
          type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
          avoidLabelOverlap: true,
          label: { show: true, formatter: '{b}\n{c}个' },
          data: Object.entries(data).map(([type, count]) => ({
            name: alertTypeMap?.[type]?.label || type,
            value: count,
            itemStyle: { color: alertTypeMap?.[type]?.color || '#6366F1' },
          })),
        }],
      }
    },
    travelSupply: (data, ec, supplyTypeMap) => {
      if (!data?.length) return null
      const reversed = data.slice(0, 10).reverse()
      return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 100, right: 50, top: 20, bottom: 30 },
        xAxis: { type: 'value', name: '携带次数' },
        yAxis: {
          type: 'category',
          data: reversed.map((d) => (
            supplyTypeMap?.[d.supply_type]?.label
            || d.supply_type
            || d.custom_name
            || '其他'
          )),
        },
        series: [{
          type: 'bar',
          data: reversed.map((d) => ({
            value: d.count || 0,
            itemStyle: { color: CHART_PRESETS.gradients.green(ec), borderRadius: [0, 8, 8, 0] },
          })),
          label: { show: true, position: 'right', formatter: (p) => p.value + ' 次' },
          barWidth: 14,
        }],
      }
    },
  })

  async function renderAllCharts(extra = {}) {
    await nextTick()
    charts.brand.setOption(blocks.brandStats.data.value)
    charts.water.setOption(blocks.waterStats.data.value)
    charts.purpose.setOption(blocks.purposeStats.data.value)
    charts.hoursPie.setOption(lensHoursList.value)
    charts.careMethod.setOption(blocks.careMethodComfort.data.value)
    charts.reminder.setOption(blocks.careStats.data.value?.reminder_type_stats || {})
    charts.makeup.setOption(blocks.outfitStats.data.value?.top_makeup_styles || [])
    charts.sceneLens.setOption(blocks.outfitStats.data.value?.lens_usage_by_scene || [])
    charts.matchScore.setOption(blocks.outfitStats.data.value?.match_score_ranking || [])
    charts.tagStats.setOption(blocks.outfitStats.data.value?.tag_stats || {})
    charts.budgetTrend.setOption(blocks.budgetStats.data.value?.monthly_trend || [])
    charts.brandValue.setOption(blocks.budgetStats.data.value?.brand_value_ranking || [])
    charts.travelLens.setOption(blocks.travelStats.data.value?.lens_usage_ranking || [])
    charts.travelComfort.setOption(blocks.travelStats.data.value?.comfort_ranking || [])
    charts.travelAlert.setOption(blocks.travelStats.data.value?.alert_type_stats || {}, extra.alertTypeMap)
    charts.travelSupply.setOption(blocks.travelStats.data.value?.common_supplies || [], extra.supplyTypeMap)
  }

  async function refresh() {
    await loadAll()
    await renderAllCharts()
  }

  return {
    blocks,
    loading,
    budgetLimit,
    lensHoursList,
    charts,
    loadAll,
    reload,
    refresh,
    renderAllCharts,
  }
}

export function calcBadRate(item) {
  if (!item?.total_records) return 0
  const badReactions = [
    'dryness', 'redness', 'fatigue',
    'dryness_redness', 'dryness_fatigue', 'redness_fatigue', 'all',
  ]
  let badCount = 0
  ;(item.reactions || []).forEach((r) => {
    if (badReactions.includes(r.eye_reaction)) badCount += r.count
  })
  return Math.round((badCount / item.total_records) * 100)
}

export function getBadRateClass(rate) {
  if (rate > 50) return 'tag-red'
  if (rate > 30) return 'tag-yellow'
  return 'tag-green'
}
