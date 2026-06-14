<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">🏠</span>首页概览</h1>
    </div>

    <div v-if="todayWarning" :class="['alert', alertClass]">
      <div class="alert-icon">{{ alertIcon }}</div>
      <div class="alert-content">
        <div class="alert-title">今日佩戴提醒</div>
        <div class="alert-message">{{ todayWarning.message }}</div>
        <div class="progress-bar mt-8">
          <div
            class="progress"
            :class="progressClass"
            :style="{ width: progressWidth + '%' }"
          ></div>
        </div>
        <div class="text-xs text-light mt-8">
          已佩戴 {{ todayWarning.total_hours }}h / 建议上限 {{ todayWarning.warning_threshold }}h
        </div>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-label">镜片总数</div>
        <div class="stat-value">{{ overview.total_lenses || 0 }}</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">在用镜片</div>
        <div class="stat-value">{{ overview.active_lenses || 0 }}</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">累计佩戴时长</div>
        <div class="stat-value small">{{ overview.total_hours || 0 }} 小时</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-label">平均舒适度</div>
        <div class="stat-value small">
          <span v-if="overview.avg_comfort">{{ '⭐'.repeat(Math.round(overview.avg_comfort)) }}</span>
          <span v-else>-</span>
          <span class="text-sm text-light ml-8">{{ overview.avg_comfort || '-' }}</span>
        </div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEF3C7, #FEF9C3);">
        <div class="stat-label">⚠️ 即将过期</div>
        <div class="stat-value" style="color: #D97706;">{{ overview.expiring_count || 0 }} 副</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEE2E2, #FECDD3);">
        <div class="stat-label">🚨 已过期未处理</div>
        <div class="stat-value" style="color: #DC2626;">{{ overview.expired_count || 0 }} 副</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FCE7F3, #FBCFE8);">
        <div class="stat-label">💄 搭配计划</div>
        <div class="stat-value" style="color: #BE185D;">{{ outfitStats.total_plans || 0 }} 个</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #DBEAFE, #BFDBFE);">
        <div class="stat-label">⏳ 待执行</div>
        <div class="stat-value" style="color: #1D4ED8;">{{ outfitStats.pending_plans || 0 }} 个</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEF3C7, #FEF9C3);">
        <div class="stat-label">⭐ 平均搭配分</div>
        <div class="stat-value" style="color: #B45309;">{{ outfitStats.avg_match_score || 0 }}</div>
      </div>
    </div>

    <div v-if="overduePlans.length" class="card mb-20" style="border-left: 4px solid #EF4444;">
      <div class="flex-between mb-16">
        <div class="card-title" style="margin-bottom: 0; color: #DC2626;">
          ⚠️ 逾期未执行计划提醒（{{ overduePlans.length }}）
        </div>
        <router-link to="/outfit-plans" class="btn btn-link text-sm">查看全部 →</router-link>
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div v-for="plan in overduePlans.slice(0, 3)" :key="plan.id"
             class="flex-between"
             style="padding: 10px; background: #FEF2F2; border-radius: 6px;">
          <div>
            <span class="text-bold">{{ getSceneIcon(plan.scene_name) }} {{ plan.scene_name_display }}</span>
            <span class="text-sm text-light ml-8">{{ formatDate(plan.expected_wear_date) }}</span>
            <span class="text-sm ml-8">{{ renderStars(plan.match_score) }}</span>
          </div>
          <span class="tag tag-red">已逾期</span>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
      <div class="card">
        <div class="card-title">📈 近30天舒适度趋势</div>
        <div class="chart-container small" ref="comfortChartRef"></div>
      </div>

      <div class="card">
        <div class="card-title">💡 护眼小贴士</div>
        <div v-if="tips.length">
          <div v-for="(tip, idx) in tips.slice(0, 4)" :key="idx" :class="['tip-card', tip.level]">
            <div class="tip-title">{{ tip.title }}</div>
            <div class="tip-content">{{ tip.content }}</div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 30px 10px;">
          <div class="empty-icon">💭</div>
          <p>暂无提示</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div class="card">
        <div class="flex-between mb-16">
          <div class="card-title" style="margin-bottom: 0;">⏰ 过期预警</div>
          <router-link to="/expiry" class="btn btn-link text-sm">查看全部 →</router-link>
        </div>
        <div v-if="expiringLenses.length">
          <div v-for="lens in expiringLenses.slice(0, 4)" :key="lens.id"
               class="flex-between"
               style="padding: 12px; background: #FAFAFA; border-radius: 8px; margin-bottom: 8px;">
            <div>
              <div class="text-bold">{{ lens.brand }} {{ lens.model_name }}</div>
              <div class="text-sm text-light">{{ formatDate(lens.expiry_date) }}到期</div>
            </div>
            <span class="tag" :class="lens.is_expired ? 'tag-red' : 'tag-yellow'">
              {{ lens.is_expired ? '已过期' : `剩${lens.days_until_expiry}天` }}
            </span>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 30px 10px;">
          <div class="empty-icon">✅</div>
          <p>暂无即将过期的镜片</p>
        </div>
      </div>

      <div class="card">
        <div class="flex-between mb-16">
          <div class="card-title" style="margin-bottom: 0;">📋 最近佩戴记录</div>
          <router-link to="/records" class="btn btn-link text-sm">查看全部 →</router-link>
        </div>
        <table class="table" v-if="recentRecords.length">
          <thead>
            <tr>
              <th>日期</th>
              <th>镜片</th>
              <th>时长</th>
              <th>舒适度</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in recentRecords.slice(0, 5)" :key="r.id">
              <td>{{ formatDate(r.wear_date) }}</td>
              <td class="text-sm">{{ r.lens_brand }}</td>
              <td>{{ r.duration_hours }}h</td>
              <td>{{ '⭐'.repeat(r.comfort_level) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px 10px;">
          <div class="empty-icon">📝</div>
          <p>暂无佩戴记录</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div class="card">
        <div class="flex-between mb-16">
          <div class="card-title" style="margin-bottom: 0;">📅 近期搭配计划</div>
          <router-link to="/outfit-plans" class="btn btn-link text-sm">查看全部 →</router-link>
        </div>
        <div v-if="upcomingPlans.length">
          <div v-for="plan in upcomingPlans.slice(0, 4)" :key="plan.id"
               class="flex-between"
               style="padding: 12px; background: #FAFAFA; border-radius: 8px; margin-bottom: 8px;">
            <div>
              <div class="text-bold">
                {{ getSceneIcon(plan.scene_name) }} {{ plan.scene_name_display }}
              </div>
              <div class="text-sm text-light">
                {{ formatDate(plan.expected_wear_date) }} · {{ plan.expected_duration_hours }}h · {{ renderStars(plan.match_score) }}
              </div>
              <div v-if="plan.lens_brand" class="text-sm text-light mt-4">
                👁️ {{ plan.lens_brand }} {{ plan.lens_model }}
              </div>
            </div>
            <span class="tag" :class="OUTFIT_STATUS_MAP[plan.status]?.class">
              {{ OUTFIT_STATUS_MAP[plan.status]?.icon }} {{ OUTFIT_STATUS_MAP[plan.status]?.label }}
            </span>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 30px 10px;">
          <div class="empty-icon">💄</div>
          <p>暂无近期搭配计划</p>
          <router-link to="/outfit-plans" class="btn btn-primary btn-sm mt-8">创建计划</router-link>
        </div>
      </div>

      <div class="card">
        <div class="flex-between mb-16">
          <div class="card-title" style="margin-bottom: 0;">🏆 常用妆容风格</div>
          <router-link to="/stats" class="btn btn-link text-sm">更多统计 →</router-link>
        </div>
        <div v-if="outfitStats.top_makeup_styles && outfitStats.top_makeup_styles.length">
          <div v-for="(style, idx) in outfitStats.top_makeup_styles.slice(0, 5)" :key="style.style"
               class="flex-between"
               style="padding: 10px 12px; background: #FAFAFA; border-radius: 8px; margin-bottom: 6px;">
            <div>
              <span v-if="idx === 0">🥇</span>
              <span v-else-if="idx === 1">🥈</span>
              <span v-else-if="idx === 2">🥉</span>
              <span v-else class="text-light">{{ idx + 1 }}.</span>
              <span class="ml-8 text-bold">{{ style.style }}</span>
            </div>
            <span class="tag tag-pink">{{ style.count }} 次</span>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 30px 10px;">
          <div class="empty-icon">🎨</div>
          <p>暂无妆容风格统计</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import * as echarts from 'echarts'
import { getStatsOverview, getComfortTrend, getEyeTips } from '@/api/stats'
import { getExpiringLenses } from '@/api/lens'
import { getTodayWarning, getRecordList } from '@/api/record'
import { getUpcomingPlans, getOverduePlans, getOutfitPlanStats } from '@/api/outfitPlan'
import { formatDate, renderStars, OUTFIT_STATUS_MAP, SCENE_ICON_MAP } from '@/utils/constants'

const overview = ref({})
const todayWarning = ref(null)
const tips = ref([])
const expiringLenses = ref([])
const recentRecords = ref([])
const upcomingPlans = ref([])
const overduePlans = ref([])
const outfitStats = ref({})
const comfortChartRef = ref(null)
let chartInstance = null

const getSceneIcon = (scene) => SCENE_ICON_MAP[scene] || '📌'

const alertClass = computed(() => {
  if (!todayWarning.value) return ''
  return {
    normal: 'alert-success',
    warning: 'alert-warning',
    danger: 'alert-danger'
  }[todayWarning.value.status] || 'alert-info'
})

const alertIcon = computed(() => {
  if (!todayWarning.value) return '✅'
  return {
    normal: '✅',
    warning: '⚠️',
    danger: '🚨'
  }[todayWarning.value.status] || 'ℹ️'
})

const progressWidth = computed(() => {
  if (!todayWarning.value) return 0
  return Math.min(100, (todayWarning.value.total_hours / todayWarning.value.warning_threshold) * 100)
})

const progressClass = computed(() => {
  if (!todayWarning.value) return 'success'
  return {
    normal: 'success',
    warning: 'warning',
    danger: 'danger'
  }[todayWarning.value.status] || 'success'
})

const loadData = async () => {
  try {
    const [ov, warn, tp, exp, rec, trend, upcoming, overdue, outfitSt] = await Promise.all([
      getStatsOverview(),
      getTodayWarning().catch(() => null),
      getEyeTips(),
      getExpiringLenses(30),
      getRecordList({ page_size: 10 }),
      getComfortTrend(30),
      getUpcomingPlans(7),
      getOverduePlans(),
      getOutfitPlanStats()
    ])
    overview.value = ov
    todayWarning.value = warn
    tips.value = tp
    expiringLenses.value = Array.isArray(exp) ? exp : (exp.results || [])
    recentRecords.value = Array.isArray(rec) ? rec : (rec.results || [])
    upcomingPlans.value = Array.isArray(upcoming) ? upcoming : (upcoming.results || [])
    overduePlans.value = Array.isArray(overdue) ? overdue : (overdue.results || [])
    outfitStats.value = outfitSt || {}
    renderComfortChart(trend || [])
  } catch (e) {
    console.error(e)
  }
}

const renderComfortChart = (data) => {
  if (!comfortChartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(comfortChartRef.value)
  }
  const dates = data.map(d => d.date ? d.date.slice(5) : '').filter(Boolean)
  const comforts = data.map(d => Number(d.avg_comfort || 0))
  const hours = data.map(d => Number(d.total_hours || 0))

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['舒适度', '佩戴时长'], top: 0 },
    grid: { left: 40, right: 50, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: [
      { type: 'value', min: 0, max: 5, name: '舒适度' },
      { type: 'value', min: 0, name: '小时' }
    ],
    series: [
      {
        name: '舒适度',
        type: 'line',
        data: comforts,
        smooth: true,
        itemStyle: { color: '#8B5CF6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
            { offset: 1, color: 'rgba(139, 92, 246, 0.02)' }
          ])
        }
      },
      {
        name: '佩戴时长',
        type: 'bar',
        yAxisIndex: 1,
        data: hours,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#F472B6' },
            { offset: 1, color: '#FBCFE8' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      }
    ]
  })
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => chartInstance?.resize())
})
</script>
