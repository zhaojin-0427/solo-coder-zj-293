import request from '@/utils/request'

export function getOutfitPlanList(params) {
  return request({
    url: '/outfit-plans/',
    method: 'get',
    params
  })
}

export function getOutfitPlanDetail(id) {
  return request({
    url: `/outfit-plans/${id}/`,
    method: 'get'
  })
}

export function createOutfitPlan(data) {
  return request({
    url: '/outfit-plans/',
    method: 'post',
    data
  })
}

export function updateOutfitPlan(id, data) {
  return request({
    url: `/outfit-plans/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteOutfitPlan(id) {
  return request({
    url: `/outfit-plans/${id}/`,
    method: 'delete'
  })
}

export function markPlanCompleted(id, wearRecordId = null) {
  return request({
    url: `/outfit-plans/${id}/mark_completed/`,
    method: 'post',
    data: { wear_record_id: wearRecordId }
  })
}

export function markPlanCancelled(id) {
  return request({
    url: `/outfit-plans/${id}/mark_cancelled/`,
    method: 'post'
  })
}

export function linkWearRecord(id, wearRecordId) {
  return request({
    url: `/outfit-plans/${id}/link_record/`,
    method: 'post',
    data: { wear_record_id: wearRecordId }
  })
}

export function unlinkWearRecord(id) {
  return request({
    url: `/outfit-plans/${id}/unlink_record/`,
    method: 'post'
  })
}

export function getUpcomingPlans(days = 7) {
  return request({
    url: '/outfit-plans/upcoming/',
    method: 'get',
    params: { days }
  })
}

export function getOverduePlans() {
  return request({
    url: '/outfit-plans/overdue/',
    method: 'get'
  })
}

export function getPlansByDate(date) {
  return request({
    url: '/outfit-plans/by_date/',
    method: 'get',
    params: { date }
  })
}

export function getCalendarData(params) {
  return request({
    url: '/outfit-plans/calendar/',
    method: 'get',
    params
  })
}

export function getOutfitPlanStats() {
  return request({
    url: '/outfit-plans/stats/',
    method: 'get'
  })
}
