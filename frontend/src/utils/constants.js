export const STATUS_MAP = {
  unopened: { label: '未开封', class: 'tag-blue' },
  opened: { label: '已开封', class: 'tag-green' },
  used_up: { label: '已用完', class: 'tag-gray' },
  expired: { label: '已过期', class: 'tag-red' }
}

export const PURPOSE_MAP = {
  daily: { label: '日常', class: 'tag-primary', icon: '🌞' },
  date: { label: '约会', class: 'tag-pink', icon: '💕' },
  photo: { label: '拍照', class: 'tag-blue', icon: '📸' }
}

export const REACTION_MAP = {
  none: { label: '无不适', class: 'tag-green' },
  dryness: { label: '干涩', class: 'tag-yellow' },
  redness: { label: '红血丝', class: 'tag-red' },
  fatigue: { label: '视疲劳', class: 'tag-yellow' },
  dryness_redness: { label: '干涩+红血丝', class: 'tag-red' },
  dryness_fatigue: { label: '干涩+视疲劳', class: 'tag-yellow' },
  redness_fatigue: { label: '红血丝+视疲劳', class: 'tag-red' },
  all: { label: '全部不适', class: 'tag-red' }
}

export const PURPOSE_OPTIONS = [
  { value: 'daily', label: '日常' },
  { value: 'date', label: '约会' },
  { value: 'photo', label: '拍照' }
]

export const STATUS_OPTIONS = [
  { value: 'unopened', label: '未开封' },
  { value: 'opened', label: '已开封' },
  { value: 'used_up', label: '已用完' },
  { value: 'expired', label: '已过期' }
]

export const REACTION_OPTIONS = [
  { value: 'none', label: '无不适' },
  { value: 'dryness', label: '干涩' },
  { value: 'redness', label: '红血丝' },
  { value: 'fatigue', label: '视疲劳' },
  { value: 'dryness_redness', label: '干涩+红血丝' },
  { value: 'dryness_fatigue', label: '干涩+视疲劳' },
  { value: 'redness_fatigue', label: '红血丝+视疲劳' },
  { value: 'all', label: '全部不适' }
]

export const COMFORT_LABELS = {
  1: '非常不适',
  2: '较不适',
  3: '一般',
  4: '舒适',
  5: '非常舒适'
}

export function formatDate(date) {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('zh-CN')
}

export function daysBetween(date1, date2) {
  const d1 = typeof date1 === 'string' ? new Date(date1) : date1
  const d2 = typeof date2 === 'string' ? new Date(date2) : date2
  return Math.ceil((d2 - d1) / (1000 * 60 * 60 * 24))
}

export function todayString() {
  return new Date().toISOString().split('T')[0]
}

export function getComfortClass(level) {
  if (level >= 4) return 'text-success'
  if (level >= 3) return 'text-warning'
  return 'text-danger'
}

export function renderStars(level) {
  return '⭐'.repeat(level) + '☆'.repeat(5 - level)
}
