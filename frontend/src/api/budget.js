import request from '@/utils/request'

export function getPurchaseRecordList(params) {
  return request({
    url: '/purchase-records/',
    method: 'get',
    params
  })
}

export function getPurchaseRecordDetail(id) {
  return request({
    url: `/purchase-records/${id}/`,
    method: 'get'
  })
}

export function createPurchaseRecord(data) {
  return request({
    url: '/purchase-records/',
    method: 'post',
    data
  })
}

export function updatePurchaseRecord(id, data) {
  return request({
    url: `/purchase-records/${id}/`,
    method: 'patch',
    data
  })
}

export function deletePurchaseRecord(id) {
  return request({
    url: `/purchase-records/${id}/`,
    method: 'delete'
  })
}

export function getPurchaseRecordsByMonth(month) {
  return request({
    url: '/purchase-records/by_month/',
    method: 'get',
    params: { month }
  })
}

export function getPurchaseRecordMonths() {
  return request({
    url: '/purchase-records/months/',
    method: 'get'
  })
}

export function getRestockSuggestionList(params) {
  return request({
    url: '/restock-suggestions/',
    method: 'get',
    params
  })
}

export function getActiveRestockSuggestions() {
  return request({
    url: '/restock-suggestions/active/',
    method: 'get'
  })
}

export function generateRestockSuggestions() {
  return request({
    url: '/restock-suggestions/generate/',
    method: 'post'
  })
}

export function markRestockActionTaken(id, data = {}) {
  return request({
    url: `/restock-suggestions/${id}/mark_action_taken/`,
    method: 'post',
    data
  })
}

export function dismissRestockSuggestion(id) {
  return request({
    url: `/restock-suggestions/${id}/dismiss/`,
    method: 'post'
  })
}

export function markAllRestockActionTaken() {
  return request({
    url: '/restock-suggestions/mark_all_action_taken/',
    method: 'post'
  })
}

export function dismissAllRestockSuggestions() {
  return request({
    url: '/restock-suggestions/dismiss_all/',
    method: 'post'
  })
}

export function getBudgetStats(params) {
  return request({
    url: '/budget/stats/',
    method: 'get',
    params
  })
}

export function getBudgetMonthlySummary() {
  return request({
    url: '/budget/monthly_summary/',
    method: 'get'
  })
}
