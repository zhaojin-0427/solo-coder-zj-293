/**
 * useCharts - ECharts 图表初始化 composable
 *
 * 抽象通用的图表初始化、设置配置、resize、销毁逻辑，
 * 避免每个页面重复书写 echarts.init / setOption / resize 样板代码。
 */
import { ref, onMounted, onBeforeUnmount, nextTick, shallowRef } from 'vue'
import * as echarts from 'echarts'

/**
 * 创建单个图表实例的辅助函数
 *
 * 使用示例:
 * const { chartRef, setOption, resize, dispose } = createChart(options => {
 *   // 自定义 option，接收传入的 data 参数
 *   return {
 *     tooltip: { trigger: 'axis' },
 *     xAxis: { type: 'category', data: data.xData },
 *     series: [{ type: 'bar', data: data.yData }]
 *   }
 * })
 *
 * // 在获取数据后调用:
 * setOption({ xData: [...], yData: [...] })
 */
export function createChart(optionFactory, theme = null, opts = {}) {
  const chartRef = ref(null)
  const instance = shallowRef(null)
  const lastData = shallowRef(null)

  function ensureInit() {
    if (!instance.value && chartRef.value) {
      instance.value = echarts.init(chartRef.value, theme, opts)
    }
    return instance.value
  }

  function setOption(data = {}, notMerge = false) {
    lastData.value = data
    nextTick(() => {
      const chart = ensureInit()
      if (!chart) return
      const option = typeof optionFactory === 'function'
        ? optionFactory(data, echarts)
        : optionFactory
      if (option) {
        chart.setOption(option, notMerge)
      }
    })
  }

  function resize() {
    instance.value?.resize()
  }

  function dispose() {
    if (instance.value) {
      instance.value.dispose()
      instance.value = null
    }
  }

  function rerender() {
    if (lastData.value) {
      setOption(lastData.value, true)
    }
  }

  return {
    chartRef,
    instance,
    setOption,
    resize,
    dispose,
    rerender,
  }
}

/**
 * 批量管理多个图表的 composable —— 适合 Statistics 这类多图表页面
 *
 * 使用示例:
 * const charts = useCharts({
 *   comfort: (data, ec) => ({ ... 舒适度图表 option ... }),
 *   brand:   (data, ec) => ({ ... 品牌排行图表 option ... }),
 * })
 *
 * // 页面中绑定: <div ref="charts.comfort.chartRef"></div>
 * // 数据就绪后: charts.comfort.setOption({ ... })
 * // 全部 resize: charts.resizeAll()
 */
export function useCharts(configs) {
  const chartMap = {}
  const keys = Object.keys(configs)

  for (const key of keys) {
    chartMap[key] = createChart(configs[key])
  }

  let resizeHandler = null

  function setAll(dataMap = {}) {
    for (const key of keys) {
      if (dataMap[key] !== undefined) {
        chartMap[key].setOption(dataMap[key])
      }
    }
  }

  function resizeAll() {
    for (const key of keys) {
      chartMap[key].resize()
    }
  }

  function disposeAll() {
    for (const key of keys) {
      chartMap[key].dispose()
    }
  }

  onMounted(() => {
    resizeHandler = () => resizeAll()
    window.addEventListener('resize', resizeHandler)
  })

  onBeforeUnmount(() => {
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    disposeAll()
  })

  return {
    ...chartMap,
    _keys: keys,
    resizeAll,
    disposeAll,
    setAll,
  }
}

/**
 * 通用图表预设（常用颜色渐变等）
 * 减少页面中重复书写相同颜色配置
 */
export const CHART_PRESETS = {
  gradients: {
    purple: (ec) => new ec.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#A78BFA' },
      { offset: 1, color: '#8B5CF6' },
    ]),
    blue: (ec) => new ec.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#60A5FA' },
      { offset: 1, color: '#3B82F6' },
    ]),
    pink: (ec) => new ec.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#F472B6' },
      { offset: 1, color: '#EC4899' },
    ]),
    green: (ec) => new ec.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#34D399' },
      { offset: 1, color: '#10B981' },
    ]),
    yellow: (ec) => new ec.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#FBBF24' },
      { offset: 1, color: '#F59E0B' },
    ]),
    indigo: (ec) => new ec.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#818CF8' },
      { offset: 1, color: '#6366F1' },
    ]),
  },
  pieColors: ['#60A5FA', '#F59E0B', '#EF4444', '#8B5CF6', '#F472B6', '#10B981', '#F97316', '#3B82F6'],
}
