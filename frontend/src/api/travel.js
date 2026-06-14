import request from '@/utils/request'

export function getTravelPlanList(params) {
  return request({
    url: '/travel-plans/',
    method: 'get',
    params
  })
}

export function getTravelPlanDetail(id) {
  return request({
    url: `/travel-plans/${id}/`,
    method: 'get'
  })
}

export function createTravelPlan(data) {
  return request({
    url: '/travel-plans/',
    method: 'post',
    data
  })
}

export function updateTravelPlan(id, data) {
  return request({
    url: `/travel-plans/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteTravelPlan(id) {
  return request({
    url: `/travel-plans/${id}/`,
    method: 'delete'
  })
}

export function getUpcomingTravelPlans(days = 30) {
  return request({
    url: '/travel-plans/upcoming/',
    method: 'get',
    params: { days }
  })
}

export function getInProgressTravelPlans() {
  return request({
    url: '/travel-plans/in_progress/',
    method: 'get'
  })
}

export function getTravelPlanSuggestions(id) {
  return request({
    url: `/travel-plans/${id}/suggestions/`,
    method: 'get'
  })
}

export function recalculateTravelRisk(id) {
  return request({
    url: `/travel-plans/${id}/recalculate_risk/`,
    method: 'post'
  })
}

export function markTravelPlanCompleted(id) {
  return request({
    url: `/travel-plans/${id}/mark_completed/`,
    method: 'post'
  })
}

export function markTravelPlanCancelled(id) {
  return request({
    url: `/travel-plans/${id}/mark_cancelled/`,
    method: 'post'
  })
}

export function generateTravelAlerts(id) {
  return request({
    url: `/travel-plans/${id}/generate_alerts/`,
    method: 'post'
  })
}

export function getTravelPlanStats() {
  return request({
    url: '/travel-plans/stats/',
    method: 'get'
  })
}

export function getTravelLensItems(params) {
  return request({
    url: '/travel-lens-items/',
    method: 'get',
    params
  })
}

export function createTravelLensItem(data) {
  return request({
    url: '/travel-lens-items/',
    method: 'post',
    data
  })
}

export function updateTravelLensItem(id, data) {
  return request({
    url: `/travel-lens-items/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteTravelLensItem(id) {
  return request({
    url: `/travel-lens-items/${id}/`,
    method: 'delete'
  })
}

export function getTravelSupplyItems(params) {
  return request({
    url: '/travel-supply-items/',
    method: 'get',
    params
  })
}

export function createTravelSupplyItem(data) {
  return request({
    url: '/travel-supply-items/',
    method: 'post',
    data
  })
}

export function updateTravelSupplyItem(id, data) {
  return request({
    url: `/travel-supply-items/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteTravelSupplyItem(id) {
  return request({
    url: `/travel-supply-items/${id}/`,
    method: 'delete'
  })
}

export function toggleTravelSupplyItem(id) {
  return request({
    url: `/travel-supply-items/${id}/toggle/`,
    method: 'post'
  })
}

export function getTravelDailyPlans(params) {
  return request({
    url: '/travel-daily-plans/',
    method: 'get',
    params
  })
}

export function createTravelDailyPlan(data) {
  return request({
    url: '/travel-daily-plans/',
    method: 'post',
    data
  })
}

export function updateTravelDailyPlan(id, data) {
  return request({
    url: `/travel-daily-plans/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteTravelDailyPlan(id) {
  return request({
    url: `/travel-daily-plans/${id}/`,
    method: 'delete'
  })
}

export function getTravelRiskAlerts(params) {
  return request({
    url: '/travel-risk-alerts/',
    method: 'get',
    params
  })
}

export function getActiveTravelRiskAlerts() {
  return request({
    url: '/travel-risk-alerts/active/',
    method: 'get'
  })
}

export function dismissTravelRiskAlert(id) {
  return request({
    url: `/travel-risk-alerts/${id}/dismiss/`,
    method: 'post'
  })
}
