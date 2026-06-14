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
      <div class="stat-card" style="background: linear-gradient(135deg, #E0E7FF, #C7D2FE);">
        <div class="stat-label">✈️ 近期出行</div>
        <div class="stat-value" style="color: #4338CA;">{{ upcomingTravelPlans.length || 0 }} 次</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEE2E2, #FECACA);">
        <div class="stat-label">🚨 高风险出行</div>
        <div class="stat-value" style="color: #B91C1C;">{{ upcomingTravelPlans.filter(p => p.risk_level === 'high').length || 0 }} 次</div>
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

    <div v-if="restockSuggestions.length" class="card mb-20" style="border-left: 4px solid #8B5CF6;">
      <div class="flex-between mb-16">
        <div class="card-title" style="margin-bottom: 0; color: #7C3AED;">
          💡 近期补货提醒（{{ restockSuggestions.length }}）
        </div>
        <router-link to="/budget" class="btn btn-link text-sm">查看全部 →</router-link>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div v-for="sug in restockSuggestions.slice(0, 3)" :key="sug.id"
             :class="['restock-suggestion-item', sug.severity]">
          <div style="display: flex; gap: 12px; align-items: flex-start;">
            <div style="font-size: 20px;">
              {{ RESTOCK_SUGGESTION_TYPE_MAP[sug.suggestion_type]?.icon }}
            </div>
            <div style="flex: 1;">
              <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
                <span class="text-bold">{{ sug.title }}</span>
                <span class="tag" :class="RESTOCK_SEVERITY_MAP[sug.severity]?.class">
                  {{ RESTOCK_SEVERITY_MAP[sug.severity]?.label }}
                </span>
              </div>
              <div class="text-sm text-light">{{ sug.message }}</div>
              <div class="text-xs text-light mt-4">
                镜片: {{ sug.lens_brand }} {{ sug.lens_model }} · 库存: {{ sug.lens_remaining_stock }} 片
                <span v-if="sug.estimated_days_left != null"> · 预计可用: {{ sug.estimated_days_left }} 天</span>
              </div>
            </div>
            <div style="display: flex; gap: 4px;">
              <button class="btn btn-sm btn-success" @click="handleMarkActionTaken(sug.id)">已处理</button>
              <button class="btn btn-sm btn-secondary" @click="handleDismissSuggestion(sug.id)">忽略</button>
            </div>
          </div>
        </div>
        <div v-if="restockSuggestions.length > 3" class="text-sm text-light text-center mt-8">
          还有 {{ restockSuggestions.length - 3 }} 条补货提醒...
        </div>
      </div>
    </div>

    <div v-if="upcomingTravelPlans.length" class="card mb-20" style="border-left: 4px solid #6366F1;">
      <div class="flex-between mb-16">
        <div class="card-title" style="margin-bottom: 0; color: #4338CA;">
          ✈️ 近期出行携带提醒（{{ upcomingTravelPlans.length }}）
        </div>
        <router-link to="/travel" class="btn btn-link text-sm">查看全部 →</router-link>
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div v-for="plan in upcomingTravelPlans.slice(0, 4)" :key="plan.id"
             class="flex-between"
             style="padding: 10px 12px; background: #EEF2FF; border-radius: 6px;">
          <div>
            <span class="text-bold">✈️ {{ plan.name }}</span>
            <span class="text-sm text-light ml-8">→ {{ plan.destination }}</span>
            <span class="text-sm text-light ml-8">{{ formatDate(plan.start_date) }} ~ {{ formatDate(plan.end_date) }}</span>
            <span class="text-sm text-light ml-8">共{{ plan.duration_days }}天</span>
          </div>
          <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
            <span class="tag" :class="TRAVEL_STATUS_MAP[plan.status]?.class">
              {{ TRAVEL_STATUS_MAP[plan.status]?.icon }} {{ TRAVEL_STATUS_MAP[plan.status]?.label }}
            </span>
            <span class="tag" :class="TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.class">
              {{ TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.icon }} {{ TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.label }}
            </span>
            <span class="tag tag-blue">镜片{{ plan.total_lens_quantity || 0 }}片</span>
            <span class="tag" :class="(plan.supplies_checked_count === plan.supplies_total_count && plan.supplies_total_count > 0) ? 'tag-green' : 'tag-yellow'">
              用品{{ plan.supplies_checked_count || 0 }}/{{ plan.supplies_total_count || 0 }}
            </span>
            <router-link :to="'/travel?plan_id=' + plan.id" class="btn btn-sm btn-primary">查看</router-link>
          </div>
        </div>
      </div>
      <div v-if="upcomingTravelPlans.length > 4" class="text-sm text-light text-center mt-8">
        还有 {{ upcomingTravelPlans.length - 4 }} 次出行计划...
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
import { computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useDashboardData, dashboardComfortChartOption } from '@/composables/useDashboardData'
import { createChart } from '@/composables/useCharts'
import { formatDate, renderStars, OUTFIT_STATUS_MAP, SCENE_ICON_MAP, RESTOCK_SUGGESTION_TYPE_MAP, RESTOCK_SEVERITY_MAP, TRAVEL_STATUS_MAP, TRAVEL_RISK_LEVEL_MAP } from '@/utils/constants'

const {
  blocks,
  loadAll,
  handleMarkActionTaken,
  handleDismissSuggestion,
  alertClass,
  alertIcon,
  progressWidth,
  progressClass,
} = useDashboardData()

const overview = computed(() => blocks.overview.data.value)
const todayWarning = computed(() => blocks.todayWarning.data.value)
const tips = computed(() => blocks.tips.data.value)
const expiringLenses = computed(() => blocks.expiringLenses.data.value)
const recentRecords = computed(() => blocks.recentRecords.data.value)
const upcomingPlans = computed(() => blocks.upcomingPlans.data.value)
const overduePlans = computed(() => blocks.overduePlans.data.value)
const outfitStats = computed(() => blocks.outfitStats.data.value)
const restockSuggestions = computed(() => blocks.restockSuggestions.data.value)
const upcomingTravelPlans = computed(() => blocks.upcomingTravelPlans.data.value)

const getSceneIcon = (scene) => SCENE_ICON_MAP[scene] || '📌'

const {
  chartRef: comfortChartRef,
  setOption: setComfortChartOption,
  resize: resizeComfortChart,
  dispose: disposeComfortChart,
} = createChart(dashboardComfortChartOption)

let resizeHandler = null

watch(() => blocks.comfortTrend.data.value, (val) => {
  if (val) setComfortChartOption(val)
})

onMounted(async () => {
  await loadAll()
  setComfortChartOption(blocks.comfortTrend.data.value)
  resizeHandler = () => resizeComfortChart()
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
  disposeComfortChart()
})
</script>

<style scoped>
.restock-suggestion-item {
  padding: 12px;
  border-radius: 8px;
  background: #F5F3FF;
  border-left: 4px solid #8B5CF6;
}

.restock-suggestion-item.critical {
  background: #FEF2F2;
  border-left-color: #EF4444;
}

.restock-suggestion-item.important {
  background: #FFFBEB;
  border-left-color: #F59E0B;
}

.restock-suggestion-item.normal {
  background: #EFF6FF;
  border-left-color: #3B82F6;
}
</style>
