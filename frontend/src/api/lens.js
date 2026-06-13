import request from '@/utils/request'

export function getLensList(params) {
  return request({
    url: '/lenses/',
    method: 'get',
    params
  })
}

export function getLensDetail(id) {
  return request({
    url: `/lenses/${id}/`,
    method: 'get'
  })
}

export function createLens(data) {
  return request({
    url: '/lenses/',
    method: 'post',
    data
  })
}

export function updateLens(id, data) {
  return request({
    url: `/lenses/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteLens(id) {
  return request({
    url: `/lenses/${id}/`,
    method: 'delete'
  })
}

export function openLens(id) {
  return request({
    url: `/lenses/${id}/open/`,
    method: 'post'
  })
}

export function markLensUsedUp(id) {
  return request({
    url: `/lenses/${id}/mark_used_up/`,
    method: 'post'
  })
}

export function getExpiringLenses(days = 30) {
  return request({
    url: '/lenses/expiring/',
    method: 'get',
    params: { days }
  })
}

export function getUnusedLenses(days = 90) {
  return request({
    url: '/lenses/unused/',
    method: 'get',
    params: { days }
  })
}

export function getCareWarningLenses() {
  return request({
    url: '/lenses/care_warnings/',
    method: 'get'
  })
}

export function markLensCareDone(id, data = {}) {
  return request({
    url: `/lenses/${id}/mark_care_done/`,
    method: 'post',
    data
  })
}

export function markLensCheckupDone(id, data = {}) {
  return request({
    url: `/lenses/${id}/mark_checkup_done/`,
    method: 'post',
    data
  })
}

export function startLensRest(id, data = {}) {
  return request({
    url: `/lenses/${id}/start_rest/`,
    method: 'post',
    data
  })
}

export function endLensRest(id, data = {}) {
  return request({
    url: `/lenses/${id}/end_rest/`,
    method: 'post',
    data
  })
}

export function getLensCareRecords(id) {
  return request({
    url: `/lenses/${id}/care_records/`,
    method: 'get'
  })
}

export function getLensReminders(id, includeDismissed = false) {
  return request({
    url: `/lenses/${id}/reminders/`,
    method: 'get',
    params: { include_dismissed: includeDismissed }
  })
}

export function getCareRecordList(params) {
  return request({
    url: '/care-records/',
    method: 'get',
    params
  })
}

export function createCareRecord(data) {
  return request({
    url: '/care-records/',
    method: 'post',
    data
  })
}

export function updateCareRecord(id, data) {
  return request({
    url: `/care-records/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteCareRecord(id) {
  return request({
    url: `/care-records/${id}/`,
    method: 'delete'
  })
}

export function getCareReminderList(params) {
  return request({
    url: '/care-reminders/',
    method: 'get',
    params
  })
}

export function getActiveCareReminders() {
  return request({
    url: '/care-reminders/active/',
    method: 'get'
  })
}

export function markReminderRead(id) {
  return request({
    url: `/care-reminders/${id}/mark_read/`,
    method: 'post'
  })
}

export function dismissReminder(id) {
  return request({
    url: `/care-reminders/${id}/dismiss/`,
    method: 'post'
  })
}

export function markAllRemindersRead() {
  return request({
    url: '/care-reminders/mark_all_read/',
    method: 'post'
  })
}

export function generateAllReminders() {
  return request({
    url: '/care-reminders/generate_all/',
    method: 'post'
  })
}
