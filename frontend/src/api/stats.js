import request from '@/utils/request'

export function getStatsOverview() {
  return request({
    url: '/stats/overview/',
    method: 'get'
  })
}

export function getBrandComfort() {
  return request({
    url: '/stats/brand_comfort/',
    method: 'get'
  })
}

export function getWaterContentFit() {
  return request({
    url: '/stats/water_content_fit/',
    method: 'get'
  })
}

export function getPurposeStats() {
  return request({
    url: '/stats/purpose_stats/',
    method: 'get'
  })
}

export function getComfortTrend(days = 30) {
  return request({
    url: '/stats/comfort_trend/',
    method: 'get',
    params: { days }
  })
}

export function getEyeTips() {
  return request({
    url: '/stats/eye_tips/',
    method: 'get'
  })
}
