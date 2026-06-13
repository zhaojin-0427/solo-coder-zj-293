import request from '@/utils/request'

export function getRecordList(params) {
  return request({
    url: '/records/',
    method: 'get',
    params
  })
}

export function getRecordDetail(id) {
  return request({
    url: `/records/${id}/`,
    method: 'get'
  })
}

export function createRecord(data) {
  return request({
    url: '/records/',
    method: 'post',
    data
  })
}

export function updateRecord(id, data) {
  return request({
    url: `/records/${id}/`,
    method: 'patch',
    data
  })
}

export function deleteRecord(id) {
  return request({
    url: `/records/${id}/`,
    method: 'delete'
  })
}

export function getDailyTotals(params) {
  return request({
    url: '/records/daily_totals/',
    method: 'get',
    params
  })
}

export function getTodayWarning() {
  return request({
    url: '/records/today_warning/',
    method: 'get'
  })
}
