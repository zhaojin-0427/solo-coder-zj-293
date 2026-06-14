/**
 * 安全数据加载工具
 * 提供区块级降级能力，单个请求失败不影响其他区块
 */

/**
 * 将 API 返回值规范化为数组
 * @param {*} data - API 返回的原始数据
 * @param {Array} fallback - 回退默认值
 * @returns {Array}
 */
export function normalizeArray(data, fallback = []) {
  if (Array.isArray(data)) return data
  if (data && Array.isArray(data.results)) return data.results
  if (data && Array.isArray(data.data)) return data.data
  return fallback
}

/**
 * 将 API 返回值规范化为对象
 * @param {*} data - API 返回的原始数据
 * @param {Object} fallback - 回退默认值
 * @returns {Object}
 */
export function normalizeObject(data, fallback = {}) {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    return data.data && typeof data.data === 'object' && !Array.isArray(data.data)
      ? data.data
      : data
  }
  return fallback
}

/**
 * 并行发起多个请求，每个请求独立失败降级
 * 与 Promise.all 不同：单个请求失败不会导致整体 reject
 *
 * @param {Array<{fn: Function, fallback: *, name: string}>} tasks - 任务列表
 * @param {Object} options - 配置项
 * @param {boolean} options.logErrors - 是否打印错误日志
 * @returns {Promise<Array>} - 按顺序返回结果，失败位置为 fallback 值
 *
 * 示例:
 * const [a, b, c] = await safePromiseAll([
 *   { fn: () => fetchA(), fallback: [], name: 'A模块' },
 *   { fn: () => fetchB(), fallback: {}, name: 'B模块' },
 *   { fn: () => fetchC(), fallback: null, name: 'C模块' },
 * ])
 */
export async function safePromiseAll(tasks, options = {}) {
  const { logErrors = true } = options
  const results = await Promise.all(
    tasks.map(async (task) => {
      try {
        const result = await task.fn()
        return { ok: true, data: result, name: task.name }
      } catch (err) {
        if (logErrors) {
          console.warn(`[数据降级] ${task.name || '未命名模块'} 加载失败:`, err?.message || err)
        }
        return { ok: false, data: task.fallback, name: task.name, error: err }
      }
    })
  )
  return results.map((r) => r.data)
}

/**
 * 创建带加载状态的区块数据加载器
 * @param {Function} apiFn - API 调用函数
 * @param {*} fallback - 失败时的回退值
 * @param {string} blockName - 区块名称（用于日志）
 */
export function createBlockLoader(apiFn, fallback, blockName = '') {
  return async (...args) => {
    try {
      const data = await apiFn(...args)
      return { data, error: null, loading: false }
    } catch (err) {
      console.warn(`[区块降级] ${blockName} 加载失败:`, err?.message || err)
      return { data: fallback, error: err, loading: false }
    }
  }
}

/**
 * 判断数据是否为空（用于渲染空态）
 * @param {*} data
 * @returns {boolean}
 */
export function isEmpty(data) {
  if (data == null) return true
  if (Array.isArray(data)) return data.length === 0
  if (typeof data === 'object') return Object.keys(data).length === 0
  return !data
}
