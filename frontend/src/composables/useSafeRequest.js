/**
 * useSafeRequest - 安全请求 composable
 *
 * 提供区块级请求隔离，某个 API 失败不会影响其他区块渲染。
 * 封装了 loading、error、retry 等常见状态管理。
 */
import { ref, shallowRef, computed } from 'vue'
import { normalizeArray, normalizeObject } from '@/utils/dataLoader'

/**
 * @param {Function} requestFn - 请求函数 (返回 Promise)
 * @param {Object} options
 * @param {*} options.initialData - 初始/回退数据
 * @param {'array'|'object'|'raw'} options.normalize - 数据规范化模式
 * @param {boolean} options.immediate - 是否立即执行
 * @param {string} options.name - 模块名称（用于日志）
 */
export function useSafeRequest(requestFn, options = {}) {
  const {
    initialData = null,
    normalize = 'raw',
    immediate = true,
    name = '未命名模块',
  } = options

  const data = shallowRef(initialData)
  const loading = ref(false)
  const error = ref(null)
  const loaded = ref(false)

  const hasData = computed(() => {
    const d = data.value
    if (d == null) return false
    if (Array.isArray(d)) return d.length > 0
    if (typeof d === 'object') return Object.keys(d).length > 0
    return !!d
  })

  const isEmpty = computed(() => !hasData.value)

  function applyNormalize(raw) {
    if (normalize === 'array') return normalizeArray(raw, initialData || [])
    if (normalize === 'object') return normalizeObject(raw, initialData || {})
    return raw ?? initialData
  }

  async function execute(...args) {
    loading.value = true
    error.value = null
    try {
      const result = await requestFn(...args)
      data.value = applyNormalize(result)
      loaded.value = true
      return data.value
    } catch (err) {
      console.warn(`[useSafeRequest] ${name} 请求失败:`, err?.message || err)
      error.value = err
      data.value = initialData
      return initialData
    } finally {
      loading.value = false
    }
  }

  function setData(newData) {
    data.value = newData
  }

  function reset() {
    data.value = initialData
    error.value = null
    loaded.value = false
  }

  function retry(...args) {
    return execute(...args)
  }

  if (immediate) {
    execute()
  }

  return {
    data,
    loading,
    error,
    loaded,
    hasData,
    isEmpty,
    execute,
    retry,
    reset,
    setData,
  }
}

/**
 * useMultiBlockRequest - 多区块并行请求 composable
 *
 * 同时发起多个区块的请求，每个区块独立失败降级。
 * 适用于 Dashboard/Statistics 这类聚合页面。
 *
 * @param {Object} blockConfig - 区块配置 { key: { fn, fallback, normalize, name } }
 * @param {Object} options
 * @param {boolean} options.immediate
 *
 * 示例:
 * const { blocks, loading, loadAll } = useMultiBlockRequest({
 *   overview: { fn: () => api.getOverview(), fallback: {}, normalize: 'object', name: '概览统计' },
 *   lenses:   { fn: () => api.getLenses(),   fallback: [], normalize: 'array',  name: '镜片列表' },
 * })
 */
export function useMultiBlockRequest(blockConfig, options = {}) {
  const { immediate = true } = options
  const keys = Object.keys(blockConfig)

  const blocks = {}
  const loaders = {}

  for (const key of keys) {
    const cfg = blockConfig[key]
    const {
      fn,
      fallback,
      normalize = 'raw',
      name = key,
    } = cfg

    const dataRef = shallowRef(fallback)
    const loadingRef = ref(false)
    const errorRef = ref(null)

    blocks[key] = {
      data: dataRef,
      loading: loadingRef,
      error: errorRef,
      isEmpty: computed(() => {
        const d = dataRef.value
        if (d == null) return true
        if (Array.isArray(d)) return d.length === 0
        if (typeof d === 'object') return Object.keys(d).length === 0
        return !d
      }),
    }

    loaders[key] = async () => {
      loadingRef.value = true
      errorRef.value = null
      try {
        const raw = await fn()
        if (normalize === 'array') {
          dataRef.value = normalizeArray(raw, fallback || [])
        } else if (normalize === 'object') {
          dataRef.value = normalizeObject(raw, fallback || {})
        } else {
          dataRef.value = raw ?? fallback
        }
      } catch (err) {
        console.warn(`[多区块降级] ${name} 加载失败:`, err?.message || err)
        errorRef.value = err
        dataRef.value = fallback
      } finally {
        loadingRef.value = false
      }
      return dataRef.value
    }
  }

  const anyLoading = computed(() => keys.some((k) => blocks[k].loading.value))
  const anyError = computed(() => keys.some((k) => blocks[k].error.value != null))

  async function loadAll() {
    await Promise.all(keys.map((k) => loaders[k]()))
  }

  async function reload(key) {
    if (key && loaders[key]) {
      return loaders[key]()
    }
    return loadAll()
  }

  if (immediate) {
    loadAll()
  }

  return {
    blocks,
    loading: anyLoading,
    error: anyError,
    loadAll,
    reload,
  }
}
