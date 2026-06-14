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

export const CARE_METHOD_MAP = {
  hydrogen_peroxide: { label: '双氧水护理', class: 'tag-blue' },
  multi_purpose: { label: '多功能护理液', class: 'tag-green' },
  daily_disposable: { label: '日抛无需护理', class: 'tag-gray' },
  other: { label: '其他方式', class: 'tag-yellow' }
}

export const CARE_METHOD_OPTIONS = [
  { value: '', label: '未设置' },
  { value: 'hydrogen_peroxide', label: '双氧水护理' },
  { value: 'multi_purpose', label: '多功能护理液' },
  { value: 'daily_disposable', label: '日抛无需护理' },
  { value: 'other', label: '其他方式' }
]

export const REPLACEMENT_CYCLE_OPTIONS = [
  { value: '', label: '未设置' },
  { value: 1, label: '每天更换（日抛）' },
  { value: 7, label: '每周更换（周抛）' },
  { value: 14, label: '每2周更换（双周抛）' },
  { value: 30, label: '每月更换（月抛）' },
  { value: 60, label: '每2月更换' },
  { value: 90, label: '每季度更换（季抛）' },
  { value: 180, label: '每半年更换（半年抛）' },
  { value: 365, label: '每年更换（年抛）' }
]

export const CARE_STATUS_MAP = {
  normal: { label: '护理正常', class: 'tag-green', icon: '✅' },
  rest: { label: '停戴观察中', class: 'tag-red', icon: '🛑' },
  replace_overdue: { label: '已过更换期', class: 'tag-red', icon: '🔴' },
  care_overdue: { label: '护理逾期', class: 'tag-red', icon: '🔴' },
  checkup_overdue: { label: '复查逾期', class: 'tag-red', icon: '🔴' },
  replace_soon: { label: '即将更换', class: 'tag-yellow', icon: '🟡' },
  care_soon: { label: '即将护理', class: 'tag-yellow', icon: '🟡' },
  checkup_soon: { label: '即将复查', class: 'tag-yellow', icon: '🟡' }
}

export const CARE_TYPE_OPTIONS = [
  { value: 'routine', label: '常规护理' },
  { value: 'deep_clean', label: '深度清洁' },
  { value: 'case_replace', label: '更换镜盒' },
  { value: 'solution_replace', label: '更换护理液' },
  { value: 'replacement', label: '镜片更换' },
  { value: 'checkup', label: '眼科复查' },
  { value: 'rest_start', label: '开始停戴观察' },
  { value: 'rest_end', label: '结束停戴观察' },
  { value: 'other', label: '其他' }
]

export const REMINDER_TYPE_MAP = {
  care: { label: '护理提醒', class: 'tag-blue', icon: '🧴' },
  replacement: { label: '更换提醒', class: 'tag-yellow', icon: '🔄' },
  checkup: { label: '复查提醒', class: 'tag-primary', icon: '👁️' },
  rest: { label: '停戴提醒', class: 'tag-red', icon: '🛑' },
  risk: { label: '高风险提醒', class: 'tag-red', icon: '⚠️' }
}

export const SEVERITY_MAP = {
  info: { label: '提示', class: 'tag-blue' },
  warning: { label: '警告', class: 'tag-yellow' },
  danger: { label: '危险', class: 'tag-red' }
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

export const CARE_STATUS_FILTER_OPTIONS = [
  { value: '', label: '全部护理状态' },
  { value: 'normal', label: '正常' },
  { value: 'rest', label: '停戴中' },
  { value: 'overdue', label: '护理/复查逾期' },
  { value: 'soon', label: '即将到期' }
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

export const SCENE_OPTIONS = [
  { value: 'daily', label: '日常通勤' },
  { value: 'date', label: '约会' },
  { value: 'party', label: '派对/聚会' },
  { value: 'wedding', label: '婚礼/宴会' },
  { value: 'photo', label: '拍照/写真' },
  { value: 'travel', label: '旅行/出游' },
  { value: 'interview', label: '面试/商务' },
  { value: 'sports', label: '运动' },
  { value: 'other', label: '其他' }
]

export const MAKEUP_STYLE_OPTIONS = [
  { value: 'natural', label: '自然裸妆' },
  { value: 'fresh', label: '清新淡妆' },
  { value: 'elegant', label: '优雅知性' },
  { value: 'sweet', label: '甜美可爱' },
  { value: 'sexy', label: '性感妩媚' },
  { value: 'cool', label: '酷飒欧美' },
  { value: 'gothic', label: '哥特暗黑' },
  { value: 'korean', label: '韩系妆容' },
  { value: 'japanese', label: '日系妆容' },
  { value: 'custom', label: '自定义风格' }
]

export const CLOTHING_COLOR_OPTIONS = [
  { value: 'warm', label: '暖色系' },
  { value: 'cool', label: '冷色系' },
  { value: 'neutral', label: '中性色系' },
  { value: 'earth', label: '大地色系' },
  { value: 'pastel', label: '马卡龙色系' },
  { value: 'monochrome', label: '黑白灰' },
  { value: 'bright', label: '鲜艳亮色' },
  { value: 'mixed', label: '撞色搭配' }
]

export const LIGHTING_OPTIONS = [
  { value: 'natural_day', label: '自然光(白天)' },
  { value: 'natural_sunset', label: '自然光(黄昏)' },
  { value: 'indoor_soft', label: '室内柔光' },
  { value: 'indoor_bright', label: '室内强光' },
  { value: 'neon', label: '霓虹灯光' },
  { value: 'candle', label: '烛光/暖光' },
  { value: 'flash', label: '闪光灯' },
  { value: 'mixed', label: '混合光线' }
]

export const OUTFIT_STATUS_MAP = {
  pending: { label: '待执行', class: 'tag-yellow', icon: '⏳' },
  completed: { label: '已执行', class: 'tag-green', icon: '✅' },
  cancelled: { label: '已取消', class: 'tag-gray', icon: '❌' }
}

export const OUTFIT_STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待执行' },
  { value: 'completed', label: '已执行' },
  { value: 'cancelled', label: '已取消' }
]

export const OUTFIT_TAG_MAP = {
  high_look_low_comfort: { label: '高颜值但低舒适', class: 'tag-red', icon: '👁️' },
  comfort_low_fit: { label: '舒适但不适配场景', class: 'tag-yellow', icon: '🤔' },
  reusable: { label: '适合重复使用', class: 'tag-green', icon: '🔄' },
  perfect_match: { label: '完美搭配', class: 'tag-pink', icon: '✨' },
  needs_adjustment: { label: '需要调整', class: 'tag-orange', icon: '⚙️' },
  overtime: { label: '佩戴超时', class: 'tag-red', icon: '⏰' },
  undertime: { label: '佩戴不足', class: 'tag-blue', icon: '⏱️' }
}

export const SCENE_ICON_MAP = {
  daily: '🏢',
  date: '💕',
  party: '🎉',
  wedding: '💒',
  photo: '📸',
  travel: '✈️',
  interview: '💼',
  sports: '🏃',
  other: '📌'
}

export const MAKEUP_ICON_MAP = {
  natural: '🌸',
  fresh: '🍃',
  elegant: '💎',
  sweet: '🍬',
  sexy: '🔥',
  cool: '😎',
  gothic: '🦇',
  korean: '🇰🇷',
  japanese: '🇯🇵',
  custom: '🎨'
}

export const COLOR_ICON_MAP = {
  warm: '🔴',
  cool: '🔵',
  neutral: '⚪',
  earth: '🟤',
  pastel: '🎀',
  monochrome: '⬛',
  bright: '🌈',
  mixed: '🎨'
}
