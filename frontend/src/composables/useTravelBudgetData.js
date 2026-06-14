/**
 * useTravelData - 旅行计划页数据 composable
 * useBudgetData - 预算补货页数据 composable
 */
import { ref, computed } from 'vue'
import { useMultiBlockRequest, useSafeRequest } from './useSafeRequest'
import {
  getTravelPlanList,
  getUpcomingTravelPlans,
  createTravelPlan,
  updateTravelPlan,
  deleteTravelPlan,
  getTravelPlanDetail,
  generateRestockSuggestionsApi,
  getActiveRestockSuggestions,
  markRestockActionTaken,
  markAllRestockActionTaken,
  dismissRestockSuggestion,
  dismissAllRestockSuggestions,
  getPurchaseRecordList,
  createPurchaseRecord,
  updatePurchaseRecord,
  deletePurchaseRecord,
  getBudgetStats,
  getPurchaseChannelOptions,
  getPurchaseMonthList,
} from '@/api'

export function useTravelData() {
  const filterStatus = ref('')
  const filterRiskLevel = ref('')
  const filterMonth = ref('')
  const filterDestination = ref('')
  const searchKeyword = ref('')

  const { blocks, loading, loadAll, reload } = useMultiBlockRequest({
    plans: {
      fn: () => getTravelPlanList({
        status: filterStatus.value || undefined,
        risk_level: filterRiskLevel.value || undefined,
        month: filterMonth.value || undefined,
        destination: filterDestination.value || undefined,
      }),
      fallback: [],
      normalize: 'array',
      name: '旅行计划列表',
    },
    upcomingPlans: {
      fn: () => getUpcomingTravelPlans(),
      fallback: [],
      normalize: 'array',
      name: '即将出行列表',
    },
  }, { immediate: false })

  const upcomingHighRiskPlans = computed(() => {
    const plans = blocks.upcomingPlans.data.value || []
    return plans.filter((p) => p.risk_level === 'high')
  })

  const filteredPlans = computed(() => {
    let plans = blocks.plans.data.value || []
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      plans = plans.filter((p) =>
        p.name?.toLowerCase().includes(kw)
        || p.destination?.toLowerCase().includes(kw)
        || p.notes?.toLowerCase().includes(kw),
      )
    }
    return plans
  })

  let debounceTimer = null
  function debouncedLoad() {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => reload('plans'), 300)
  }

  async function refresh() {
    await loadAll()
  }

  async function handleCreate(payload) {
    try {
      await createTravelPlan(payload)
      await refresh()
      return { ok: true }
    } catch (err) {
      console.warn('[Travel] 创建失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function handleUpdate(id, payload) {
    try {
      await updateTravelPlan(id, payload)
      await refresh()
      return { ok: true }
    } catch (err) {
      console.warn('[Travel] 更新失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function handleDelete(id) {
    try {
      await deleteTravelPlan(id)
      await refresh()
      return { ok: true }
    } catch (err) {
      console.warn('[Travel] 删除失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  return {
    blocks,
    loading,
    filterStatus,
    filterRiskLevel,
    filterMonth,
    filterDestination,
    searchKeyword,
    upcomingHighRiskPlans,
    filteredPlans,
    debouncedLoad,
    loadAll,
    reload,
    refresh,
    handleCreate,
    handleUpdate,
    handleDelete,
  }
}

export function useBudgetData() {
  const filterBrand = ref('')
  const filterChannel = ref('')
  const filterPriority = ref('')
  const filterMonth = ref('')
  const budgetLimit = ref(500)
  const activeTab = ref('purchases')

  const { blocks, loading, loadAll, reload } = useMultiBlockRequest({
    budgetStats: {
      fn: () => getBudgetStats({ month: filterMonth.value || undefined, limit: budgetLimit.value }).catch(() => ({})),
      fallback: {},
      normalize: 'object',
      name: '预算统计',
    },
    restockSuggestions: {
      fn: () => getActiveRestockSuggestions(),
      fallback: [],
      normalize: 'array',
      name: '补货建议',
    },
    purchaseRecords: {
      fn: () => getPurchaseRecordList({
        brand: filterBrand.value || undefined,
        channel: filterChannel.value || undefined,
        restock_priority: filterPriority.value || undefined,
        budget_month: filterMonth.value || undefined,
      }),
      fallback: [],
      normalize: 'array',
      name: '采购记录',
    },
    monthList: {
      fn: () => getPurchaseMonthList().catch(() => []),
      fallback: [],
      normalize: 'array',
      name: '可查月份列表',
    },
  }, { immediate: false })

  const totalWarnings = computed(() => {
    const bs = blocks.budgetStats.data.value || {}
    const low = bs.low_comfort_high_cost?.length || 0
    const expiring = bs.expiring_with_stock?.length || 0
    const running = bs.running_out_soon?.length || 0
    const restock = blocks.restockSuggestions.data.value?.length || 0
    return low + expiring + running + restock
  })

  const brandList = computed(() => {
    const records = blocks.purchaseRecords.data.value || []
    const set = new Set()
    records.forEach((r) => {
      if (r.lens_brand) set.add(r.lens_brand)
    })
    return Array.from(set).sort()
  })

  async function refresh() {
    await loadAll()
  }

  async function loadBudgetStats() {
    await reload('budgetStats')
  }

  async function loadPurchaseRecords() {
    await reload('purchaseRecords')
  }

  async function loadAllData() {
    await loadAll()
  }

  async function generateSuggestions() {
    try {
      await generateRestockSuggestionsApi()
      await reload('restockSuggestions')
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 生成补货建议失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function markActionTaken(id) {
    try {
      await markRestockActionTaken(id)
      await reload('restockSuggestions')
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 标记已处理失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function dismissSuggestion(id) {
    try {
      await dismissRestockSuggestion(id)
      await reload('restockSuggestions')
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 忽略建议失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function markAllActionTaken() {
    try {
      await markAllRestockActionTaken()
      await reload('restockSuggestions')
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 批量标记失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function dismissAll() {
    try {
      await dismissAllRestockSuggestions()
      await reload('restockSuggestions')
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 批量忽略失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function createPurchase(payload) {
    try {
      await createPurchaseRecord(payload)
      await Promise.all([reload('purchaseRecords'), reload('budgetStats')])
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 创建采购记录失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function updatePurchase(id, payload) {
    try {
      await updatePurchaseRecord(id, payload)
      await Promise.all([reload('purchaseRecords'), reload('budgetStats')])
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 更新采购记录失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  async function deletePurchase(id) {
    try {
      await deletePurchaseRecord(id)
      await Promise.all([reload('purchaseRecords'), reload('budgetStats')])
      return { ok: true }
    } catch (err) {
      console.warn('[Budget] 删除采购记录失败:', err?.message || err)
      return { ok: false, error: err }
    }
  }

  return {
    blocks,
    loading,
    filterBrand,
    filterChannel,
    filterPriority,
    filterMonth,
    budgetLimit,
    activeTab,
    totalWarnings,
    brandList,
    loadAll,
    reload,
    refresh,
    loadBudgetStats,
    loadPurchaseRecords,
    loadAllData,
    generateSuggestions,
    markActionTaken,
    dismissSuggestion,
    markAllActionTaken,
    dismissAll,
    createPurchase,
    updatePurchase,
    deletePurchase,
  }
}
