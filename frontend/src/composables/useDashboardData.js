/**
 * useDashboardData - 首页 Dashboard 数据聚合 composable
 *
 * 将 Dashboard.vue 中的多接口并行请求逻辑抽取出来，
 * 每个区块独立失败降级，不会因某个接口报错导致整页清空。
 *
 * 并提供统一的 loadAll / refresh 方法供页面调用。
 */
import { computed } from 'vue'
import { useMultiBlockRequest } from './useSafeRequest'
import {
  getStatsOverview,
  getComfortTrend,
  getEyeTips,
} from '@/api/stats'
import { getExpiringLenses } from '@/api/lens'
import {
  getTodayWarning,
  getRecordList,
} from '@/api/record'
import {
  getUpcomingPlans,
  getOverduePlans,
  getOutfitPlanStats,
} from '@/api/outfitPlan'
import {
  getActiveRestockSuggestions,
  markRestockActionTaken,
  dismissRestockSuggestion,
} from '@/api/budget'
import { getUpcomingTravelPlans } from '@/api/travel'
import { safePromiseAll } from '@/utils/dataLoader'

export function useDashboardData() {
  const { blocks, loading, error, loadAll, reload } = useMultiBlockRequest({
    overview: {
      fn: () => getStatsOverview(),
      fallback: {},
      normalize: 'object',
      name: '首页概览统计',
    },
    todayWarning: {
      fn: () => getTodayWarning(),
      fallback: null,
      normalize: 'object',
      name: '今日佩戴提醒',
    },
    tips: {
      fn: () => getEyeTips(),
      fallback: [],
      normalize: 'array',
      name: '护眼小贴士',
    },
    expiringLenses: {
      fn: () => getExpiringLenses(30),
      fallback: [],
      normalize: 'array',
      name: '过期预警镜片',
    },
    recentRecords: {
      fn: () => getRecordList({ page_size: 10 }),
      fallback: [],
      normalize: 'array',
      name: '最近佩戴记录',
    },
    comfortTrend: {
      fn: () => getComfortTrend(30),
      fallback: [],
      normalize: 'array',
      name: '舒适度趋势数据',
    },
    upcomingPlans: {
      fn: () => getUpcomingPlans(7),
      fallback: [],
      normalize: 'array',
      name: '近期搭配计划',
    },
    overduePlans: {
      fn: () => getOverduePlans(),
      fallback: [],
      normalize: 'array',
      name: '逾期搭配计划',
    },
    outfitStats: {
      fn: () => getOutfitPlanStats(),
      fallback: {},
      normalize: 'object',
      name: '搭配计划统计',
    },
    restockSuggestions: {
      fn: () => getActiveRestockSuggestions(),
      fallback: [],
      normalize: 'array',
      name: '补货建议',
    },
    upcomingTravelPlans: {
      fn: () => getUpcomingTravelPlans(),
      fallback: [],
      normalize: 'array',
      name: '近期出行计划',
    },
  }, { immediate: false })

  const refresh = loadAll

  async function handleMarkActionTaken(id) {
    try {
      await markRestockActionTaken(id)
      await reload('restockSuggestions')
    } catch (err) {
      console.warn('[Dashboard] 标记补货已处理失败:', err?.message || err)
    }
  }

  async function handleDismissSuggestion(id) {
    try {
      await dismissRestockSuggestion(id)
      await reload('restockSuggestions')
    } catch (err) {
      console.warn('[Dashboard] 忽略补货建议失败:', err?.message || err)
    }
  }

  const alertClass = computed(() => {
    const w = blocks.todayWarning.data.value
    if (!w) return ''
    return ({
      normal: 'alert-success',
      warning: 'alert-warning',
      danger: 'alert-danger',
    }[w.status] || 'alert-info')
  })

  const alertIcon = computed(() => {
    const w = blocks.todayWarning.data.value
    if (!w) return '✅'
    return ({
      normal: '✅',
      warning: '⚠️',
      danger: '🚨',
    }[w.status] || 'ℹ️')
  })

  const progressWidth = computed(() => {
    const w = blocks.todayWarning.data.value
    if (!w) return 0
    return Math.min(100, (w.total_hours / (w.warning_threshold || 8)) * 100)
  })

  const progressClass = computed(() => {
    const w = blocks.todayWarning.data.value
    if (!w) return 'success'
    return ({
      normal: 'success',
      warning: 'warning',
      danger: 'danger',
    }[w.status] || 'success')
  })

  return {
    blocks,
    loading,
    error,
    loadAll,
    refresh,
    reload,
    handleMarkActionTaken,
    handleDismissSuggestion,
    alertClass,
    alertIcon,
    progressWidth,
    progressClass,
  }
}

/**
 * Dashboard 舒适度图表 option 工厂
 */
export function dashboardComfortChartOption(data, ec) {
  if (!data || !data.length) return null
  const dates = data.map((d) => (d.date ? d.date.slice(5) : '')).filter(Boolean)
  const comforts = data.map((d) => Number(d.avg_comfort || 0))
  const hours = data.map((d) => Number(d.total_hours || 0))
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['舒适度', '佩戴时长'], top: 0 },
    grid: { left: 40, right: 50, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: [
      { type: 'value', min: 0, max: 5, name: '舒适度' },
      { type: 'value', min: 0, name: '小时' },
    ],
    series: [
      {
        name: '舒适度',
        type: 'line',
        data: comforts,
        smooth: true,
        itemStyle: { color: '#8B5CF6' },
        areaStyle: {
          color: new ec.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
            { offset: 1, color: 'rgba(139, 92, 246, 0.02)' },
          ]),
        },
      },
      {
        name: '佩戴时长',
        type: 'bar',
        yAxisIndex: 1,
        data: hours,
        itemStyle: {
          color: new ec.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#F472B6' },
            { offset: 1, color: '#FBCFE8' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  }
}
