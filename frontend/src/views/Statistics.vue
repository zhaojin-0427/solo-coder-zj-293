<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">📊</span>统计分析</h1>
    </div>

    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-label">镜片总数</div>
        <div class="stat-value">{{ overview.total_lenses || 0 }}</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">累计佩戴时长</div>
        <div class="stat-value small">{{ overview.total_hours || 0 }}h</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">佩戴次数</div>
        <div class="stat-value">{{ overview.total_records || 0 }}</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-label">平均舒适度</div>
        <div class="stat-value small">{{ overview.avg_comfort || 0 }} ⭐</div>
      </div>
    </div>

    <div class="stats-grid" style="margin-top: 0;">
      <div class="stat-card cyan">
        <div class="stat-label">护理执行率</div>
        <div class="stat-value small">{{ careStats.care_execution_rate || 0 }}%</div>
        <div class="stat-sub">近30天 {{ careStats.total_care_records_30d || 0 }} 次护理</div>
      </div>
      <div class="stat-card orange">
        <div class="stat-label">复查逾期</div>
        <div class="stat-value">{{ overview.checkup_overdue_count || 0 }}</div>
        <div class="stat-sub">需尽快安排眼科检查</div>
      </div>
      <div class="stat-card red">
        <div class="stat-label">护理逾期</div>
        <div class="stat-value">{{ overview.care_overdue_count || 0 }}</div>
        <div class="stat-sub">镜片需立即护理</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-label">停戴观察中</div>
        <div class="stat-value">{{ overview.rest_count || 0 }}</div>
        <div class="stat-sub">即将到期: {{ overview.care_soon_count || 0 }} 副</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">💄 搭配计划总数</div>
        <div class="stat-value">{{ outfitStats.total_plans || 0 }}</div>
        <div class="stat-sub">已完成: {{ outfitStats.completed_plans || 0 }} 个</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEF3C7, #FEF9C3);">
        <div class="stat-label">⭐ 平均搭配评分</div>
        <div class="stat-value" style="color: #B45309;">{{ outfitStats.avg_match_score || 0 }}</div>
        <div class="stat-sub">待执行: {{ outfitStats.pending_plans || 0 }} 个</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #E0E7FF, #C7D2FE);">
        <div class="stat-label">✈️ 旅行方案总数</div>
        <div class="stat-value" style="color: #4338CA;">{{ travelStats.total_plans || 0 }}</div>
        <div class="stat-sub">总出行: {{ travelStats.total_travel_days || 0 }} 天</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #D1FAE5, #A7F3D0);">
        <div class="stat-label">✅ 已完成行程</div>
        <div class="stat-value" style="color: #047857;">{{ travelStats.status_counts?.completed || 0 }}</div>
        <div class="stat-sub">进行中: {{ travelStats.status_counts?.in_progress || 0 }} 次</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEE2E2, #FECACA);">
        <div class="stat-label">🚨 风险提醒总数</div>
        <div class="stat-value" style="color: #B91C1C;">{{ travelStats.total_alerts || 0 }}</div>
        <div class="stat-sub">高风险行程: {{ travelStats.risk_counts?.high || 0 }} 次</div>
      </div>
    </div>

    <div v-if="budgetStats.is_over_budget" class="alert alert-danger mb-20">
      <div class="alert-icon">⚠️</div>
      <div class="alert-content">
        <div class="alert-title">预算超支提醒</div>
        <div class="alert-message">
          本月彩瞳消费已超出预算 ¥{{ ((budgetStats.total_spent_month || 0) - budgetLimit).toFixed(2) }}，
          建议控制后续采购支出。当前预算限额：¥{{ budgetLimit }}，已使用 {{ budgetStats.budget_used_percent || 0 }}%。
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">📈 月度消费趋势（近12个月）</div>
        <div v-if="budgetStats.monthly_trend?.length" class="chart-container small" ref="budgetMonthlyTrendChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">📊</div>
          <p>暂无消费数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🏆 品牌性价比排行</div>
        <div v-if="budgetStats.brand_value_ranking?.length" class="chart-container small" ref="brandValueChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🏆</div>
          <p>暂无性价比数据</p>
        </div>
      </div>
    </div>

    <div class="card mb-20">
      <div class="flex-between mb-16">
        <div class="card-title" style="margin-bottom: 0;">💰 品牌性价比详情</div>
        <div class="text-sm text-light">性价比 = 舒适度 / 单次佩戴成本</div>
      </div>
      <table class="table" v-if="budgetStats.brand_value_ranking?.length">
        <thead>
          <tr>
            <th>排名</th>
            <th>品牌</th>
            <th>型号</th>
            <th>平均舒适</th>
            <th>每次成本</th>
            <th>累计花费</th>
            <th>佩戴次数</th>
            <th>性价比</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(b, idx) in budgetStats.brand_value_ranking" :key="b.lens_id">
            <td>
              <span v-if="idx === 0">🥇</span>
              <span v-else-if="idx === 1">🥈</span>
              <span v-else-if="idx === 2">🥉</span>
              <span v-else class="text-light">{{ idx + 1 }}</span>
            </td>
            <td class="text-bold">{{ b.brand }}</td>
            <td class="text-sm text-light">{{ b.model }}</td>
            <td>{{ '⭐'.repeat(Math.round(b.avg_comfort)) }} {{ b.avg_comfort }}</td>
            <td>¥{{ b.cost_per_wear }}</td>
            <td>¥{{ b.total_spent.toFixed(2) }}</td>
            <td>{{ b.total_wears || 0 }} 次</td>
            <td>
              <span :class="b.value_score >= 7 ? 'tag tag-green' : b.value_score >= 4 ? 'tag tag-yellow' : 'tag tag-red'">
                {{ b.value_score }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state" style="padding: 30px;">
        <p class="text-light">暂无数据</p>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">🏆 品牌舒适度排行榜</div>
        <div v-if="brandStats.length" class="chart-container small" ref="brandChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🏆</div>
          <p>暂无品牌数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🧴 护理方式舒适度对比</div>
        <div v-if="careMethodComfort.length" class="chart-container small" ref="careMethodChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🧴</div>
          <p>暂无护理方式数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">💧 含水量适配度分析</div>
        <div v-if="waterStats.length" class="chart-container small" ref="waterChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">💧</div>
          <p>暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🎯 用途分布统计</div>
        <div v-if="purposeStats.length" class="chart-container small" ref="purposeChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🎯</div>
          <p>暂无数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">⏱️ 累计佩戴时长分布（按镜片）</div>
        <div v-if="lensHoursList.length" class="chart-container small" ref="hoursPieRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">⏱️</div>
          <p>暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🔔 护理与风险提醒统计</div>
        <div v-if="Object.keys(careStats.reminder_type_stats || {}).length" class="chart-container small" ref="reminderChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🔔</div>
          <p>暂无提醒数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">🏆 品牌舒适度详情表</div>
        <table class="table" v-if="brandStats.length">
          <thead>
            <tr>
              <th>排名</th>
              <th>品牌</th>
              <th>平均舒适</th>
              <th>佩戴次数</th>
              <th>累计时长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(b, idx) in brandStats" :key="b.brand">
              <td>
                <span v-if="idx === 0">🥇</span>
                <span v-else-if="idx === 1">🥈</span>
                <span v-else-if="idx === 2">🥉</span>
                <span v-else class="text-light">{{ idx + 1 }}</span>
              </td>
              <td class="text-bold">{{ b.brand }}</td>
              <td>
                <span :class="getComfortClass(Math.round(b.avg_comfort))">
                  {{ '⭐'.repeat(Math.round(b.avg_comfort)) }}
                </span>
                <span class="text-sm ml-8">{{ b.avg_comfort }}</span>
              </td>
              <td>{{ b.total_records }} 次</td>
              <td>{{ b.total_hours }}h</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无品牌数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🧴 护理方式详细对比</div>
        <table class="table" v-if="careMethodComfort.length">
          <thead>
            <tr>
              <th>护理方式</th>
              <th>镜片数</th>
              <th>平均舒适</th>
              <th>不适率</th>
              <th>总时长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in careMethodComfort" :key="c.care_method">
              <td class="text-bold">{{ c.care_method_display || '-' }}</td>
              <td>{{ c.lens_count }} 副</td>
              <td>
                <span :class="getComfortClass(Math.round(c.avg_comfort))">
                  {{ c.avg_comfort ? '⭐'.repeat(Math.round(c.avg_comfort)) : '-' }}
                </span>
                <span class="text-sm ml-8">{{ c.avg_comfort || '-' }}</span>
              </td>
              <td>
                <span class="tag" :class="getCareBadRateClass(c)">
                  {{ calcCareBadRate(c) }}%
                </span>
              </td>
              <td>{{ c.total_hours }}h</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无护理方式数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">💧 含水量详细分析</div>
        <table class="table" v-if="waterStats.length">
          <thead>
            <tr>
              <th>含水量区间</th>
              <th>镜片数</th>
              <th>平均舒适</th>
              <th>不适率</th>
              <th>总时长</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="w in waterStats" :key="w.range">
              <td class="text-bold">{{ w.range }}</td>
              <td>{{ w.lens_count }} 副</td>
              <td>
                <span :class="getComfortClass(Math.round(w.avg_comfort))">
                  {{ w.avg_comfort ? '⭐'.repeat(Math.round(w.avg_comfort)) : '-' }}
                </span>
                <span class="text-sm ml-8">{{ w.avg_comfort || '-' }}</span>
              </td>
              <td>
                <span class="tag" :class="getBadRateClass(w)">
                  {{ calcBadRate(w) }}%
                </span>
              </td>
              <td>{{ w.total_hours }}h</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">📋 护理记录统计概览</div>
        <table class="table" v-if="Object.keys(careStats.care_type_stats || {}).length">
          <thead>
            <tr>
              <th>护理类型</th>
              <th>次数</th>
              <th>占比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(count, type) in careStats.care_type_stats" :key="type">
              <td class="text-bold">{{ getCareTypeLabel(type) }}</td>
              <td>{{ count }} 次</td>
              <td>
                <span class="tag tag-blue">
                  {{ careStats.total_care_records ? Math.round(count / careStats.total_care_records * 100) : 0 }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无护理记录</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">🎨 最常用妆容风格</div>
        <div v-if="outfitStats.top_makeup_styles && outfitStats.top_makeup_styles.length" class="chart-container small" ref="makeupChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🎨</div>
          <p>暂无妆容风格数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">👁️ 不同场景下镜片使用次数</div>
        <div v-if="outfitStats.lens_usage_by_scene && outfitStats.lens_usage_by_scene.length" class="chart-container small" ref="sceneLensChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">👁️</div>
          <p>暂无场景镜片数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">⭐ 搭配评分排行</div>
        <div v-if="outfitStats.match_score_ranking && outfitStats.match_score_ranking.length" class="chart-container small" ref="matchScoreChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">⭐</div>
          <p>暂无评分排行数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🏷️ 搭配标签统计</div>
        <div v-if="Object.keys(outfitStats.tag_stats || {}).length" class="chart-container small" ref="tagStatsChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🏷️</div>
          <p>暂无标签数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">📊 搭配评分排行榜详情</div>
        <table class="table" v-if="outfitStats.match_score_ranking && outfitStats.match_score_ranking.length">
          <thead>
            <tr>
              <th>排名</th>
              <th>场景</th>
              <th>镜片</th>
              <th>搭配评分</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in outfitStats.match_score_ranking.slice(0, 10)" :key="item.id">
              <td>
                <span v-if="idx === 0">🥇</span>
                <span v-else-if="idx === 1">🥈</span>
                <span v-else-if="idx === 2">🥉</span>
                <span v-else class="text-light">{{ idx + 1 }}</span>
              </td>
              <td class="text-bold">{{ item.scene }}</td>
              <td class="text-sm">{{ item.lens }}</td>
              <td>{{ '⭐'.repeat(item.match_score) }} <span class="text-sm text-light ml-4">{{ item.match_score }}</span></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无评分排行数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🏷️ 标签分布详情</div>
        <table class="table" v-if="Object.keys(outfitStats.tag_stats || {}).length">
          <thead>
            <tr>
              <th>标签</th>
              <th>次数</th>
              <th>占比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(val, key) in outfitStats.tag_stats" :key="key" v-if="val.count > 0">
              <td class="text-bold">{{ val.label }}</td>
              <td>{{ val.count }} 次</td>
              <td>
                <span class="tag tag-blue">
                  {{ outfitStats.completed_plans ? Math.round(val.count / outfitStats.completed_plans * 100) : 0 }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无标签数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">👁️ 出行场景镜片使用次数排行</div>
        <div v-if="travelStats.lens_usage_ranking?.length" class="chart-container small" ref="travelLensChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">👁️</div>
          <p>暂无出行镜片数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">⭐ 旅行舒适度排行</div>
        <div v-if="travelStats.comfort_ranking?.length" class="chart-container small" ref="travelComfortChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">⭐</div>
          <p>暂无舒适度数据</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
      <div class="card">
        <div class="card-title">🚨 旅行风险提醒统计</div>
        <div v-if="travelStats.alert_type_stats && Object.keys(travelStats.alert_type_stats).length" class="chart-container small" ref="travelAlertChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🚨</div>
          <p>暂无风险提醒数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🧴 常用携带用品统计</div>
        <div v-if="travelStats.common_supplies?.length" class="chart-container small" ref="travelSupplyChartRef"></div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">🧴</div>
          <p>暂无用品统计数据</p>
        </div>
      </div>
    </div>

    <div class="card mb-20">
      <div class="flex-between mb-16">
        <div class="card-title" style="margin-bottom: 0;">✈️ 出行镜片使用详情</div>
        <div class="text-sm text-light">基于旅行方案中携带镜片统计</div>
      </div>
      <table class="table" v-if="travelStats.lens_usage_ranking?.length">
        <thead>
          <tr>
            <th>排名</th>
            <th>品牌</th>
            <th>型号</th>
            <th>出行次数</th>
            <th>总携带数量</th>
            <th>平均舒适度</th>
            <th>平均佩戴时长</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(l, idx) in travelStats.lens_usage_ranking.slice(0, 10)" :key="l.lens_id">
            <td>
              <span v-if="idx === 0">🥇</span>
              <span v-else-if="idx === 1">🥈</span>
              <span v-else-if="idx === 2">🥉</span>
              <span v-else class="text-light">{{ idx + 1 }}</span>
            </td>
            <td class="text-bold">{{ l.brand || '-' }}</td>
            <td class="text-sm text-light">{{ l.model || '-' }}</td>
            <td>{{ l.travel_count || l.count || 0 }} 次</td>
            <td>{{ l.total_quantity || 0 }} 片</td>
            <td>
              <span :class="getComfortClass(Math.round(l.avg_comfort))">
                {{ l.avg_comfort ? '⭐'.repeat(Math.round(l.avg_comfort)) : '-' }}
              </span>
              <span class="text-sm ml-8">{{ l.avg_comfort || '-' }}</span>
            </td>
            <td>{{ l.avg_duration_hours || 0 }}h</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state" style="padding: 30px;">
        <p class="text-light">暂无出行镜片数据</p>
      </div>
    </div>

    <div class="card mb-20">
      <div class="card-title">🌤️ 出行气候与目的地分布</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="text-sm text-bold mb-8">气候分布</div>
          <div v-if="travelStats.climate_stats && Object.keys(travelStats.climate_stats).length"
               style="display: flex; flex-direction: column; gap: 6px;">
            <div v-for="(count, climate) in travelStats.climate_stats" :key="climate" class="flex-between"
                 style="padding: 8px 12px; background: #F9FAFB; border-radius: 6px;">
              <span>
                <span class="mr-8">{{ TRAVEL_STATUS_MAP ? '' : '' }}</span>
                {{ climate }}
              </span>
              <span class="tag tag-indigo">{{ count }} 次</span>
            </div>
          </div>
          <div v-else class="text-sm text-light">暂无气候统计</div>
        </div>
        <div>
          <div class="text-sm text-bold mb-8">热门目的地 Top 5</div>
          <div v-if="travelStats.destination_stats?.length"
               style="display: flex; flex-direction: column; gap: 6px;">
            <div v-for="(d, idx) in travelStats.destination_stats.slice(0, 5)" :key="d.destination" class="flex-between"
                 style="padding: 8px 12px; background: #F9FAFB; border-radius: 6px;">
              <span>
                <span v-if="idx === 0">🥇</span>
                <span v-else-if="idx === 1">🥈</span>
                <span v-else-if="idx === 2">🥉</span>
                <span v-else class="text-light mr-8">{{ idx + 1 }}.</span>
                📍 {{ d.destination }}
              </span>
              <span class="tag tag-blue">{{ d.count }} 次</span>
            </div>
          </div>
          <div v-else class="text-sm text-light">暂无目的地统计</div>
        </div>
      </div>
    </div>

    <div class="card mb-20">
      <div class="card-title">🔔 长期未使用镜片提醒</div>
      <table class="table" v-if="unusedLenses.length">
        <thead>
          <tr>
            <th>镜片</th>
            <th>度数</th>
            <th>参数</th>
            <th>护理状态</th>
            <th>上次佩戴</th>
            <th>未使用</th>
            <th>有效期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lens in unusedLenses" :key="lens.id">
            <td>
              <div class="text-bold">{{ lens.brand }}</div>
              <div class="text-xs text-light">{{ lens.model_name || '-' }}</div>
            </td>
            <td>{{ lens.power_sph }}D</td>
            <td class="text-sm">{{ lens.water_content }}% · BC{{ lens.base_curve }}</td>
            <td>
              <span v-if="lens.care_status" class="tag" :class="getCareStatusTagClass(lens.care_status)">
                {{ getCareStatusLabel(lens.care_status) }}
              </span>
              <span v-else class="tag tag-gray">未设置</span>
            </td>
            <td>{{ formatDate(lens.last_wear_date) || '从未佩戴' }}</td>
            <td>
              <span class="tag tag-blue">超过 {{ getUnusedDays(lens) }} 天</span>
            </td>
            <td :class="lens.is_expired ? 'text-danger' : ''">
              {{ formatDate(lens.expiry_date) }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state" style="padding: 30px;">
        <div class="empty-icon">✨</div>
        <p>没有长期未使用的镜片，保持得很好！</p>
      </div>
    </div>

    <div class="card">
      <div class="card-title">💡 护眼小贴士</div>
      <div v-if="tips.length" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px;">
        <div v-for="(tip, idx) in tips" :key="idx" :class="['tip-card', tip.level]">
          <div class="tip-title">{{ tip.title }}</div>
          <div class="tip-content">{{ tip.content }}</div>
        </div>
      </div>
      <div v-else class="empty-state" style="padding: 30px;">
        <div class="empty-icon">💭</div>
        <p>暂无提示</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import {
  useStatisticsData,
  calcBadRate,
  getBadRateClass,
} from '@/composables/useStatisticsData'
import {
  formatDate, getComfortClass, CARE_STATUS_MAP, CARE_TYPE_OPTIONS,
  TRAVEL_STATUS_MAP, TRAVEL_SUPPLY_TYPE_MAP, TRAVEL_ALERT_TYPE_MAP,
} from '@/utils/constants'

const {
  blocks,
  budgetLimit,
  lensHoursList,
  charts,
  loadAll,
  renderAllCharts,
} = useStatisticsData()

const overview = computed(() => blocks.overview.data.value || {})
const brandStats = computed(() => blocks.brandStats.data.value || [])
const waterStats = computed(() => blocks.waterStats.data.value || [])
const purposeStats = computed(() => blocks.purposeStats.data.value || [])
const unusedLenses = computed(() => blocks.unusedLenses.data.value || [])
const tips = computed(() => blocks.tips.data.value || [])
const allRecords = computed(() => blocks.allRecords.data.value || [])
const allLenses = computed(() => blocks.allLenses.data.value || [])
const careStats = computed(() => blocks.careStats.data.value || {})
const careMethodComfort = computed(() => blocks.careMethodComfort.data.value || [])
const outfitStats = computed(() => blocks.outfitStats.data.value || {})
const budgetStats = computed(() => blocks.budgetStats.data.value || {})
const travelStats = computed(() => blocks.travelStats.data.value || {})

const brandChartRef = charts.brand.chartRef
const waterChartRef = charts.water.chartRef
const purposeChartRef = charts.purpose.chartRef
const hoursPieRef = charts.hoursPie.chartRef
const careMethodChartRef = charts.careMethod.chartRef
const reminderChartRef = charts.reminder.chartRef
const makeupChartRef = charts.makeup.chartRef
const sceneLensChartRef = charts.sceneLens.chartRef
const matchScoreChartRef = charts.matchScore.chartRef
const tagStatsChartRef = charts.tagStats.chartRef
const budgetMonthlyTrendChartRef = charts.budgetTrend.chartRef
const brandValueChartRef = charts.brandValue.chartRef
const travelLensChartRef = charts.travelLens.chartRef
const travelComfortChartRef = charts.travelComfort.chartRef
const travelAlertChartRef = charts.travelAlert.chartRef
const travelSupplyChartRef = charts.travelSupply.chartRef

const calcCareBadRate = calcBadRate
const getCareBadRateClass = getBadRateClass

const getUnusedDays = (lens) => {
  const refDate = lens.last_wear_date ? new Date(lens.last_wear_date) : new Date(lens.created_at)
  return Math.floor((Date.now() - refDate.getTime()) / 86400000)
}

const getCareStatusLabel = (status) => CARE_STATUS_MAP[status] || status
const getCareStatusTagClass = (status) => {
  const map = { normal: 'tag-green', rest: 'tag-purple', overdue: 'tag-red', soon: 'tag-yellow' }
  return map[status] || 'tag-gray'
}
const getCareTypeLabel = (type) => {
  const opt = CARE_TYPE_OPTIONS.find(o => o.value === type)
  return opt ? opt.label : type
}

onMounted(async () => {
  await loadAll()
  await renderAllCharts({
    alertTypeMap: TRAVEL_ALERT_TYPE_MAP,
    supplyTypeMap: TRAVEL_SUPPLY_TYPE_MAP,
  })
})
</script>
