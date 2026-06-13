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
    method: 'put',
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
