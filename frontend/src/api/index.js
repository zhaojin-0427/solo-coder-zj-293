/**
 * API 统一导出入口
 * 方便 composables 中使用聚合 import { ... } from '@/api'
 */

export * from './stats'
export * from './lens'
export * from './record'
export * from './outfitPlan'
export * from './budget'
export * from './travel'

/**
 * 获取采购渠道可选项（根据现有记录动态生成，若无则使用默认列表）
 */
export async function getPurchaseChannelOptions() {
  const defaults = [
    { value: 'official', label: '官方渠道' },
    { value: 'pharmacy', label: '药店/眼镜店' },
    { value: 'ecommerce', label: '电商平台' },
    { value: 'duty_free', label: '免税店' },
    { value: 'other', label: '其他' },
  ]
  try {
    const records = await import('./budget').then((m) => m.getPurchaseRecordList({ page_size: 200 }))
    const list = Array.isArray(records) ? records : records?.results || records?.data || []
    const set = new Set()
    list.forEach((r) => {
      if (r.channel) set.add(r.channel)
    })
    if (set.size === 0) return defaults
    return Array.from(set).map((ch) => ({ value: ch, label: ch }))
  } catch {
    return defaults
  }
}

/**
 * 获取可查询月份列表
 */
export async function getPurchaseMonthList() {
  try {
    const { getPurchaseRecordMonths } = await import('./budget')
    const raw = await getPurchaseRecordMonths()
    if (Array.isArray(raw)) return raw
    if (raw && Array.isArray(raw.months)) return raw.months
    if (raw && Array.isArray(raw.data)) return raw.data
  } catch {
    /* ignore */
  }
  const months = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return months
}

/**
 * 调用补货建议生成（别名，兼容 composable 中的调用）
 */
export { generateRestockSuggestions as generateRestockSuggestionsApi } from './budget'
