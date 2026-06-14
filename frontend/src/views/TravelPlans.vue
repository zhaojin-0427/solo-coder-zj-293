<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">✈️</span>彩瞳旅行清单</h1>
      <button class="btn btn-primary" @click="openCreateForm">
        ➕ 新建旅行方案
      </button>
    </div>

    <div class="filter-bar">
      <select v-model="filterStatus" class="form-control" @change="loadPlans">
        <option v-for="opt in TRAVEL_STATUS_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select v-model="filterRiskLevel" class="form-control" @change="loadPlans">
        <option v-for="opt in TRAVEL_RISK_LEVEL_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select v-model="filterMonth" class="form-control" @change="loadPlans">
        <option v-for="opt in TRAVEL_MONTH_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <input v-model="filterDestination" class="form-control" placeholder="🔍 搜索目的地..." @input="debouncedLoad">
    </div>

    <div v-if="upcomingHighRiskPlans.length" class="card mb-20" style="border-left: 4px solid #EF4444;">
      <div class="card-title" style="color: #DC2626; margin-bottom: 12px;">
        ⚠️ 高风险出行提醒（{{ upcomingHighRiskPlans.length }}）
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div v-for="plan in upcomingHighRiskPlans.slice(0, 3)" :key="plan.id"
             class="flex-between"
             style="padding: 10px; background: #FEF2F2; border-radius: 6px;">
          <div>
            <span class="text-bold">✈️ {{ plan.name }}</span>
            <span class="text-sm text-light ml-8">→ {{ plan.destination }}</span>
            <span class="text-sm text-light ml-8">{{ formatDate(plan.start_date) }} ~ {{ formatDate(plan.end_date) }}</span>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <span class="tag tag-red">{{ TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.icon }} {{ TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.label }}</span>
            <button class="btn btn-sm btn-primary" @click="openDetail(plan)">查看</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="plans.length" class="travel-grid">
      <div v-for="plan in plans" :key="plan.id"
           class="travel-card"
           :class="{
             'risk-high': plan.risk_level === 'high',
             'risk-medium': plan.risk_level === 'medium'
           }"
           @click="openDetail(plan)">
        <div class="travel-header">
          <div class="travel-title">
            <span class="travel-name">{{ plan.name }}</span>
            <span class="tag" :class="TRAVEL_STATUS_MAP[plan.status_info?.key || plan.status]?.class">
              {{ plan.status_info?.icon || TRAVEL_STATUS_MAP[plan.status]?.icon }}
              {{ plan.status_info?.label || TRAVEL_STATUS_MAP[plan.status]?.label }}
            </span>
          </div>
          <span class="tag" :class="TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.class">
            {{ TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.icon }}
            {{ TRAVEL_RISK_LEVEL_MAP[plan.risk_level]?.label }}
          </span>
        </div>

        <div class="travel-info">
          <div class="info-row">
            <span>📍</span>
            <span class="text-bold">{{ plan.destination }}</span>
          </div>
          <div class="info-row">
            <span>📅</span>
            <span>{{ formatDate(plan.start_date) }} ~ {{ formatDate(plan.end_date) }}</span>
            <span class="text-sm text-light ml-8">共{{ plan.duration_days }}天</span>
          </div>
          <div class="info-row">
            <span>{{ TRAVEL_CLIMATE_MAP[plan.climate]?.icon }}</span>
            <span>{{ TRAVEL_CLIMATE_MAP[plan.climate]?.label }}</span>
            <span class="ml-12">{{ TRAVEL_TRANSPORT_MAP[plan.transport]?.icon }}</span>
            <span>{{ TRAVEL_TRANSPORT_MAP[plan.transport]?.label }}</span>
            <span class="ml-12">{{ TRAVEL_LUGGAGE_MAP[plan.luggage]?.icon }}</span>
            <span>{{ TRAVEL_LUGGAGE_MAP[plan.luggage]?.label }}</span>
          </div>
          <div class="info-row">
            <span>{{ TRAVEL_WEAR_SCENE_MAP[plan.planned_wear_scene]?.icon }}</span>
            <span>{{ plan.planned_wear_scene_display }}</span>
          </div>
        </div>

        <div class="travel-stats">
          <div class="stat">
            <div class="stat-num">{{ plan.primary_lens_count || 0 }}</div>
            <div class="stat-label">主带镜片</div>
          </div>
          <div class="stat">
            <div class="stat-num">{{ plan.backup_lens_count || 0 }}</div>
            <div class="stat-label">备用镜片</div>
          </div>
          <div class="stat">
            <div class="stat-num">{{ plan.total_lens_quantity || 0 }}</div>
            <div class="stat-label">镜片总数</div>
          </div>
          <div class="stat">
            <div class="stat-num">{{ plan.supplies_checked_count || 0 }}/{{ plan.supplies_total_count || 0 }}</div>
            <div class="stat-label">用品准备</div>
          </div>
        </div>

        <div v-if="plan.suggestions_and_risks?.risks?.length" class="travel-risks">
          <div v-for="(risk, idx) in plan.suggestions_and_risks.risks.slice(0, 2)" :key="idx"
               :class="['risk-item', risk.level]">
            <span class="risk-icon">{{ risk.level === 'danger' ? '🚨' : '⚠️' }}</span>
            <span class="risk-text">{{ risk.title }}</span>
          </div>
          <div v-if="plan.suggestions_and_risks.risks.length > 2" class="text-xs text-light">
            还有 {{ plan.suggestions_and_risks.risks.length - 2 }} 项风险提醒...
          </div>
        </div>

        <div class="travel-footer">
          <button class="btn btn-sm btn-secondary" @click.stop="openEditForm(plan)">编辑</button>
          <button class="btn btn-sm btn-danger" @click.stop="handleDelete(plan.id)">删除</button>
        </div>
      </div>
    </div>

    <div v-else class="card empty-state">
      <div class="empty-icon">✈️</div>
      <h3>还没有旅行方案</h3>
      <p>点击右上角「新建旅行方案」开始规划您的彩瞳携带清单</p>
      <button class="btn btn-primary mt-12" @click="openCreateForm">立即创建</button>
    </div>

    <div v-if="showDetail && detailPlan" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal" style="max-width: 860px;">
        <div class="modal-header">
          <div class="modal-title">
            ✈️ {{ detailPlan.name }}
            <span class="tag ml-8" :class="TRAVEL_STATUS_MAP[detailPlan.status]?.class">
              {{ detailPlan.status_info?.icon || TRAVEL_STATUS_MAP[detailPlan.status]?.icon }}
              {{ detailPlan.status_info?.label || TRAVEL_STATUS_MAP[detailPlan.status]?.label }}
            </span>
            <span class="tag ml-8" :class="TRAVEL_RISK_LEVEL_MAP[detailPlan.risk_level]?.class">
              {{ TRAVEL_RISK_LEVEL_MAP[detailPlan.risk_level]?.icon }}
              {{ TRAVEL_RISK_LEVEL_MAP[detailPlan.risk_level]?.label }}
            </span>
          </div>
          <button class="modal-close" @click="showDetail = false">×</button>
        </div>
        <div class="modal-body" style="max-height: 75vh; overflow-y: auto;">

          <div class="stats-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="stat-card primary">
              <div class="stat-label">目的地</div>
              <div class="stat-value small">📍 {{ detailPlan.destination }}</div>
            </div>
            <div class="stat-card green">
              <div class="stat-label">行程日期</div>
              <div class="stat-value small">{{ formatDate(detailPlan.start_date) }} ~ {{ formatDate(detailPlan.end_date) }}</div>
            </div>
            <div class="stat-card yellow">
              <div class="stat-label">共</div>
              <div class="stat-value small">{{ detailPlan.duration_days }} 天</div>
            </div>
            <div class="stat-card pink">
              <div class="stat-label">佩戴场景</div>
              <div class="stat-value small">{{ detailPlan.planned_wear_scene_display }}</div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 16px;">
            <div class="info-box">
              <div class="info-title">🌤️ 气候环境</div>
              <div class="info-value">{{ TRAVEL_CLIMATE_MAP[detailPlan.climate]?.icon }} {{ TRAVEL_CLIMATE_MAP[detailPlan.climate]?.label }}</div>
            </div>
            <div class="info-box">
              <div class="info-title">🚗 交通方式</div>
              <div class="info-value">{{ TRAVEL_TRANSPORT_MAP[detailPlan.transport]?.icon }} {{ TRAVEL_TRANSPORT_MAP[detailPlan.transport]?.label }}</div>
            </div>
            <div class="info-box">
              <div class="info-title">🧳 行李限制</div>
              <div class="info-value">{{ TRAVEL_LUGGAGE_MAP[detailPlan.luggage]?.icon }} {{ TRAVEL_LUGGAGE_MAP[detailPlan.luggage]?.label }}</div>
            </div>
          </div>

          <div v-if="detailPlan.notes" class="card mt-16">
            <div class="card-title">📝 备注</div>
            <div class="text-sm">{{ detailPlan.notes }}</div>
          </div>

          <div v-if="detailPlan.suggestions_and_risks" class="mt-16">
            <div v-if="detailPlan.suggestions_and_risks.risks?.length" class="card mb-12" style="border-left: 4px solid #EF4444;">
              <div class="card-title" style="color: #DC2626;">
                🚨 风险提醒（{{ detailPlan.suggestions_and_risks.risks.length }}）
              </div>
              <div style="display: flex; flex-direction: column; gap: 8px;">
                <div v-for="(risk, idx) in detailPlan.suggestions_and_risks.risks" :key="idx"
                     :class="['risk-item', risk.level]"
                     style="padding: 10px; border-radius: 6px;">
                  <div class="text-bold text-sm">
                    {{ risk.level === 'danger' ? '🚨' : '⚠️' }} {{ risk.title }}
                  </div>
                  <div class="text-sm text-light mt-4">{{ risk.message }}</div>
                </div>
              </div>
            </div>

            <div v-if="detailPlan.suggestions_and_risks.suggestions?.length" class="card" style="border-left: 4px solid #3B82F6;">
              <div class="card-title" style="color: #1D4ED8;">
                💡 智能建议（{{ detailPlan.suggestions_and_risks.suggestions.length }}）
              </div>
              <div style="display: flex; flex-direction: column; gap: 8px;">
                <div v-for="(sug, idx) in detailPlan.suggestions_and_risks.suggestions" :key="idx"
                     :class="['risk-item', sug.level]"
                     style="padding: 10px; border-radius: 6px;">
                  <div class="text-bold text-sm">
                    {{ sug.level === 'warning' ? '⚠️' : '💡' }} {{ sug.title }}
                  </div>
                  <div class="text-sm text-light mt-4">{{ sug.message }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="card mt-16">
            <div class="flex-between mb-12">
              <div class="card-title" style="margin-bottom: 0;">👁️ 携带镜片（{{ detailPlan.lens_items?.length || 0 }}）</div>
            </div>
            <div v-if="detailPlan.lens_items?.length" style="display: flex; flex-direction: column; gap: 10px;">
              <div v-for="item in detailPlan.lens_items" :key="item.id"
                   class="lens-item-row"
                   :class="{ 'is-under-rest': item.lens_is_under_rest }">
                <div class="lens-item-left">
                  <span class="tag" :class="TRAVEL_LENS_ROLE_MAP[item.role]?.class">
                    {{ TRAVEL_LENS_ROLE_MAP[item.role]?.icon }} {{ TRAVEL_LENS_ROLE_MAP[item.role]?.label }}
                  </span>
                  <span class="text-bold ml-8">{{ item.lens_brand }} {{ item.lens_model }}</span>
                  <span v-if="item.lens_color" class="text-sm text-light ml-8">{{ item.lens_color }}</span>
                  <span class="tag tag-blue ml-8">× {{ item.quantity }}片</span>
                </div>
                <div class="lens-item-right">
                  <span v-if="item.lens_status" class="tag" :class="STATUS_MAP[item.lens_status]?.class">
                    {{ STATUS_MAP[item.lens_status]?.label }}
                  </span>
                  <span v-if="item.lens_days_until_expiry != null"
                        class="tag" :class="item.lens_days_until_expiry <= 30 ? 'tag-yellow' : 'tag-green'">
                    有效期剩{{ item.lens_days_until_expiry }}天
                  </span>
                  <span v-if="item.lens_avg_comfort != null" class="tag tag-pink">
                    舒适{{ item.lens_avg_comfort }}分
                  </span>
                  <span v-if="item.lens_care_method" class="tag" :class="CARE_METHOD_MAP[item.lens_care_method]?.class">
                    {{ CARE_METHOD_MAP[item.lens_care_method]?.label }}
                  </span>
                  <span v-if="item.lens_is_under_rest" class="tag tag-red">停戴中</span>
                </div>
              </div>
            </div>
            <div v-else class="text-light text-center" style="padding: 20px;">尚未添加携带镜片</div>
          </div>

          <div class="card mt-16">
            <div class="flex-between mb-12">
              <div class="card-title" style="margin-bottom: 0;">
                🧴 随身用品（{{ detailPlan.supplies_checked_count || 0 }}/{{ detailPlan.supplies_total_count || 0 }}已准备）
              </div>
            </div>
            <div v-if="detailPlan.supplies?.length" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
              <div v-for="supply in detailPlan.supplies" :key="supply.id"
                   class="supply-item"
                   :class="{ checked: supply.is_checked }">
                <span style="font-size: 18px;">{{ TRAVEL_SUPPLY_TYPE_MAP[supply.supply_type]?.icon }}</span>
                <span class="ml-8" :class="{ 'text-light': !supply.is_checked }">
                  {{ supply.supply_type_display }}
                  <span v-if="supply.quantity" class="text-sm text-light ml-4">({{ supply.quantity }})</span>
                </span>
                <span class="ml-auto">
                  {{ supply.is_checked ? '✅' : '⬜' }}
                </span>
              </div>
            </div>
            <div v-else class="text-light text-center" style="padding: 20px;">尚未添加随身用品</div>
          </div>

          <div v-if="detailPlan.daily_plans?.length" class="card mt-16">
            <div class="card-title">📅 每日佩戴安排（{{ detailPlan.daily_plans.length }}天）</div>
            <table class="table">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>行程</th>
                  <th>主要活动</th>
                  <th>计划佩戴</th>
                  <th>预计时长</th>
                  <th>备注</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="dp in detailPlan.daily_plans" :key="dp.id">
                  <td>{{ formatDate(dp.plan_date) }}</td>
                  <td>{{ dp.day_label || '-' }}</td>
                  <td>{{ dp.planned_activity || '-' }}</td>
                  <td>{{ dp.lens_brand ? dp.lens_brand + ' ' + dp.lens_model : '未安排' }}</td>
                  <td>{{ dp.expected_duration_hours }}h</td>
                  <td class="text-sm text-light">{{ dp.notes || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetail = false">关闭</button>
          <button class="btn btn-warning" v-if="detailPlan.status !== 'completed' && detailPlan.status !== 'cancelled'"
                  @click="handleMarkCompleted(detailPlan.id)">标记完成</button>
          <button class="btn btn-danger" v-if="detailPlan.status !== 'completed' && detailPlan.status !== 'cancelled'"
                  @click="handleMarkCancelled(detailPlan.id)">取消行程</button>
          <button class="btn btn-primary" @click="openEditForm(detailPlan); showDetail = false;">编辑方案</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal" style="max-width: 900px;">
        <div class="modal-header">
          <div class="modal-title">{{ editingPlan ? '编辑旅行方案' : '新建旅行方案' }}</div>
          <button class="modal-close" @click="showForm = false">×</button>
        </div>
        <div class="modal-body" style="max-height: 75vh; overflow-y: auto;">

          <div class="nav-tabs" style="margin-bottom: 16px;">
            <button class="nav-tab" :class="{ active: formTab === 'basic' }" @click="formTab = 'basic'">基本信息</button>
            <button class="nav-tab" :class="{ active: formTab === 'lenses' }" @click="formTab = 'lenses'">携带镜片</button>
            <button class="nav-tab" :class="{ active: formTab === 'supplies' }" @click="formTab = 'supplies'">随身用品</button>
            <button class="nav-tab" :class="{ active: formTab === 'daily' }" @click="formTab = 'daily'">每日安排</button>
          </div>

          <div v-if="formTab === 'basic'">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">旅行名称 *</label>
                <input v-model="form.name" class="form-control" placeholder="如：三亚国庆游、日本出差...">
              </div>
              <div class="form-group">
                <label class="form-label">目的地 *</label>
                <input v-model="form.destination" class="form-control" placeholder="如：三亚、东京、巴黎...">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">出发日期 *</label>
                <input v-model="form.start_date" type="date" class="form-control">
              </div>
              <div class="form-group">
                <label class="form-label">返回日期 *</label>
                <input v-model="form.end_date" type="date" class="form-control">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">气候环境</label>
                <select v-model="form.climate" class="form-control">
                  <option v-for="opt in TRAVEL_CLIMATE_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.icon }} {{ opt.label }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">交通方式</label>
                <select v-model="form.transport" class="form-control">
                  <option v-for="opt in TRAVEL_TRANSPORT_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.icon }} {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">行李限制</label>
                <select v-model="form.luggage" class="form-control">
                  <option v-for="opt in TRAVEL_LUGGAGE_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.icon }} {{ opt.label }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">计划佩戴场景</label>
                <select v-model="form.planned_wear_scene" class="form-control">
                  <option v-for="opt in TRAVEL_WEAR_SCENE_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.icon }} {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">自定义佩戴场景（可选）</label>
              <input v-model="form.custom_wear_scene" class="form-control" placeholder="填写后将覆盖上面的选择">
            </div>
            <div class="form-group">
              <label class="form-label">备注</label>
              <textarea v-model="form.notes" class="form-control" placeholder="可记录特殊要求、注意事项等..."></textarea>
            </div>
          </div>

          <div v-if="formTab === 'lenses'">
            <div class="alert alert-info" style="margin-bottom: 16px;">
              <div class="alert-icon">💡</div>
              <div class="alert-content">
                <div class="alert-title">选择携带镜片</div>
                <div class="alert-message" style="font-size: 12px;">从镜片库中选择主带和备用镜片，系统会根据镜片有效期、库存、舒适度等自动评估风险。</div>
              </div>
            </div>

            <div style="display: flex; gap: 8px; margin-bottom: 16px;">
              <select v-model="addLensRole" class="form-control" style="flex: 0 0 140px;">
                <option v-for="opt in TRAVEL_LENS_ROLE_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ opt.icon }} {{ opt.label }}
                </option>
              </select>
              <select v-model="addLensId" class="form-control" style="flex: 1;">
                <option value="">-- 从镜片库选择 --</option>
                <option v-for="l in availableLenses" :key="l.id" :value="l.id">
                  {{ l.brand }} {{ l.model_name }} {{ l.color ? '· ' + l.color : '' }}
                  ({{ l.power_sph }}D) · 库存{{ l.remaining_stock }}片 ·
                  {{ l.status === 'unopened' ? '未开封' : (l.status === 'opened' ? '已开封' : l.status) }}
                  <span v-if="l.in_upcoming_travel"> · 已在其他旅行中</span>
                </option>
              </select>
              <input v-model.number="addLensQuantity" type="number" min="1" class="form-control" style="flex: 0 0 100px;" placeholder="数量">
              <button class="btn btn-primary" @click="addLensItem" :disabled="!addLensId">添加</button>
            </div>

            <div v-if="form.lens_items.length" style="display: flex; flex-direction: column; gap: 8px;">
              <div v-for="(item, idx) in form.lens_items" :key="idx" class="lens-item-row">
                <div class="lens-item-left">
                  <span class="tag" :class="TRAVEL_LENS_ROLE_MAP[item.role]?.class">
                    {{ TRAVEL_LENS_ROLE_MAP[item.role]?.icon }} {{ TRAVEL_LENS_ROLE_MAP[item.role]?.label }}
                  </span>
                  <span class="text-bold ml-8">{{ getLensName(item.lens_id) }}</span>
                  <span class="tag tag-blue ml-8">× {{ item.quantity }}片</span>
                </div>
                <div class="lens-item-right">
                  <button class="btn btn-sm btn-danger" @click="removeLensItem(idx)">移除</button>
                </div>
              </div>
            </div>
            <div v-else class="text-light text-center" style="padding: 30px 10px;">
              还没有添加镜片，请从上方选择并添加
            </div>
          </div>

          <div v-if="formTab === 'supplies'">
            <div class="alert alert-info" style="margin-bottom: 16px;">
              <div class="alert-icon">🧴</div>
              <div class="alert-content">
                <div class="alert-title">选择随身用品</div>
                <div class="alert-message" style="font-size: 12px;">勾选需要携带的护理用品和辅助用品，系统会根据镜片类型自动提示必带用品。</div>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
              <label v-for="opt in TRAVEL_SUPPLY_TYPE_OPTIONS" :key="opt.value"
                     class="supply-checkbox"
                     :class="{ checked: isSupplyChecked(opt.value) }">
                <input type="checkbox" :checked="isSupplyChecked(opt.value)" @change="toggleSupply(opt.value)">
                <span class="supply-icon">{{ opt.icon }}</span>
                <span>{{ opt.label }}</span>
              </label>
            </div>

            <div style="margin-top: 16px;">
              <div class="text-sm text-light mb-8">自定义用品（每行一个，格式：名称,数量/规格）</div>
              <textarea v-model="customSuppliesText" class="form-control" rows="3"
                        placeholder="如：&#10;小瓶护理液,60ml&#10;备用镜盒,1个"></textarea>
            </div>
          </div>

          <div v-if="formTab === 'daily'">
            <div class="alert alert-info" style="margin-bottom: 16px;">
              <div class="alert-icon">📅</div>
              <div class="alert-content">
                <div class="alert-title">每日佩戴安排（可选）</div>
                <div class="alert-message" style="font-size: 12px;">设置行程期间每天的佩戴计划，包括活动安排、佩戴镜片和预计时长。留空将根据行程天数自动生成。</div>
              </div>
            </div>

            <div style="display: flex; gap: 8px; margin-bottom: 16px;">
              <button class="btn btn-secondary" @click="autoGenerateDailyPlans" :disabled="!form.start_date || !form.end_date">
                🔄 自动生成每日安排
              </button>
              <button class="btn btn-primary" @click="addDailyPlan">➕ 添加一天</button>
            </div>

            <div v-if="form.daily_plans.length" style="display: flex; flex-direction: column; gap: 10px;">
              <div v-for="(dp, idx) in form.daily_plans" :key="idx" class="card" style="padding: 12px; margin-bottom: 0;">
                <div class="flex-between mb-8">
                  <div class="text-bold">第{{ idx + 1 }}天</div>
                  <button class="btn btn-sm btn-danger" @click="removeDailyPlan(idx)">删除</button>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">日期</label>
                    <input v-model="dp.plan_date" type="date" class="form-control">
                  </div>
                  <div class="form-group">
                    <label class="form-label">行程标签</label>
                    <input v-model="dp.day_label" class="form-control" placeholder="如：出发日、观光日...">
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">主要活动</label>
                    <input v-model="dp.planned_activity" class="form-control" placeholder="如：海滩、逛街、宴会...">
                  </div>
                  <div class="form-group">
                    <label class="form-label">预计佩戴时长(小时)</label>
                    <input v-model.number="dp.expected_duration_hours" type="number" step="0.5" min="0" class="form-control">
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">计划佩戴镜片</label>
                    <select v-model="dp.expected_wear_lens_id" class="form-control">
                      <option value="">-- 不指定 --</option>
                      <option v-for="opt in form.lens_items" :key="opt.lens_id" :value="opt.lens_id">
                        {{ getLensName(opt.lens_id) }}
                      </option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label class="form-label">备注</label>
                    <input v-model="dp.notes" class="form-control" placeholder="可记录特殊注意事项...">
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-light text-center" style="padding: 30px 10px;">
              暂无每日安排，可点击上方按钮自动生成或手动添加
            </div>
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showForm = false">取消</button>
          <button class="btn btn-primary" @click="handleSave">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
import {
  getTravelPlanList, getTravelPlanDetail, createTravelPlan, updateTravelPlan, deleteTravelPlan,
  markTravelPlanCompleted, markTravelPlanCancelled
} from '@/api/travel'
import { getLensList } from '@/api/lens'
import {
  formatDate,
  TRAVEL_STATUS_MAP, TRAVEL_STATUS_OPTIONS,
  TRAVEL_RISK_LEVEL_MAP, TRAVEL_RISK_LEVEL_OPTIONS,
  TRAVEL_CLIMATE_MAP, TRAVEL_CLIMATE_OPTIONS,
  TRAVEL_TRANSPORT_MAP, TRAVEL_TRANSPORT_OPTIONS,
  TRAVEL_LUGGAGE_MAP, TRAVEL_LUGGAGE_OPTIONS,
  TRAVEL_WEAR_SCENE_MAP, TRAVEL_WEAR_SCENE_OPTIONS,
  TRAVEL_LENS_ROLE_MAP, TRAVEL_LENS_ROLE_OPTIONS,
  TRAVEL_SUPPLY_TYPE_MAP, TRAVEL_SUPPLY_TYPE_OPTIONS,
  TRAVEL_MONTH_OPTIONS,
  STATUS_MAP, CARE_METHOD_MAP
} from '@/utils/constants'

const plans = ref([])
const filterStatus = ref('')
const filterRiskLevel = ref('')
const filterMonth = ref('')
const filterDestination = ref('')
const availableLenses = ref([])

const showDetail = ref(false)
const detailPlan = ref(null)

const showForm = ref(false)
const editingPlan = ref(null)
const formTab = ref('basic')

const addLensRole = ref('primary')
const addLensId = ref('')
const addLensQuantity = ref(2)

const customSuppliesText = ref('')

const defaultForm = {
  name: '',
  destination: '',
  start_date: '',
  end_date: '',
  climate: 'temperate',
  transport: 'airplane',
  luggage: 'carry_on',
  planned_wear_scene: 'daily_sightseeing',
  custom_wear_scene: '',
  notes: '',
  status: 'planning',
  risk_level: 'low',
  lens_items: [],
  supplies: [],
  daily_plans: []
}
const form = ref({ ...defaultForm })

const upcomingHighRiskPlans = ref([])

let debounceTimer = null
const debouncedLoad = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadPlans, 300)
}

const loadPlans = async () => {
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterRiskLevel.value) params.risk_level = filterRiskLevel.value
    if (filterMonth.value) params.month = filterMonth.value
    if (filterDestination.value) params.destination = filterDestination.value
    const res = await getTravelPlanList(params)
    plans.value = Array.isArray(res) ? res : (res.results || [])
    upcomingHighRiskPlans.value = plans.value.filter(p =>
      (p.status === 'planning' || p.status === 'upcoming' || p.status === 'in_progress') &&
      p.risk_level === 'high'
    )
  } catch (e) {
    console.error(e)
  }
}

const loadAvailableLenses = async () => {
  try {
    const res = await getLensList()
    availableLenses.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e) {
    console.error(e)
  }
}

const getLensName = (lensId) => {
  const lens = availableLenses.value.find(l => l.id === lensId)
  if (!lens) return '未知镜片'
  return `${lens.brand} ${lens.model_name}${lens.color ? ' · ' + lens.color : ''} (${lens.power_sph}D)`
}

const openDetail = async (plan) => {
  try {
    const res = await getTravelPlanDetail(plan.id)
    detailPlan.value = res
    showDetail.value = true
  } catch (e) {
    console.error(e)
  }
}

const openCreateForm = () => {
  editingPlan.value = null
  form.value = JSON.parse(JSON.stringify(defaultForm))
  addLensRole.value = 'primary'
  addLensId.value = ''
  addLensQuantity.value = 2
  customSuppliesText.value = ''
  formTab.value = 'basic'
  if (route.query.lens_id) {
    form.value.lens_items.push({
      lens_id: parseInt(route.query.lens_id),
      role: 'primary',
      quantity: 2,
      notes: ''
    })
  }
  showForm.value = true
}

const openEditForm = (plan) => {
  editingPlan.value = plan
  form.value = {
    name: plan.name,
    destination: plan.destination,
    start_date: plan.start_date,
    end_date: plan.end_date,
    climate: plan.climate,
    transport: plan.transport,
    luggage: plan.luggage,
    planned_wear_scene: plan.planned_wear_scene,
    custom_wear_scene: plan.custom_wear_scene || '',
    notes: plan.notes || '',
    status: plan.status,
    risk_level: plan.risk_level,
    lens_items: (plan.lens_items || []).map(i => ({
      lens_id: i.lens_id,
      role: i.role,
      quantity: i.quantity,
      notes: i.notes || ''
    })),
    supplies: (plan.supplies || []).map(s => ({
      supply_type: s.supply_type,
      custom_name: s.custom_name || '',
      is_checked: s.is_checked,
      quantity: s.quantity || '',
      notes: s.notes || ''
    })),
    daily_plans: (plan.daily_plans || []).map(d => ({
      plan_date: d.plan_date,
      day_label: d.day_label || '',
      planned_activity: d.planned_activity || '',
      expected_wear_lens_id: d.expected_wear_lens_id,
      expected_duration_hours: d.expected_duration_hours || 8,
      notes: d.notes || ''
    }))
  }
  customSuppliesText.value = ''
  formTab.value = 'basic'
  showForm.value = true
}

const addLensItem = () => {
  if (!addLensId.value) return
  const exists = form.value.lens_items.find(
    i => i.lens_id === parseInt(addLensId.value) && i.role === addLensRole.value
  )
  if (exists) {
    exists.quantity += (addLensQuantity.value || 1)
  } else {
    form.value.lens_items.push({
      lens_id: parseInt(addLensId.value),
      role: addLensRole.value,
      quantity: addLensQuantity.value || 1,
      notes: ''
    })
  }
  addLensId.value = ''
  addLensQuantity.value = 2
}

const removeLensItem = (idx) => {
  form.value.lens_items.splice(idx, 1)
}

const isSupplyChecked = (type) => {
  return form.value.supplies.some(s => s.supply_type === type)
}

const toggleSupply = (type) => {
  const idx = form.value.supplies.findIndex(s => s.supply_type === type)
  if (idx >= 0) {
    form.value.supplies.splice(idx, 1)
  } else {
    form.value.supplies.push({
      supply_type: type,
      custom_name: '',
      is_checked: true,
      quantity: '',
      notes: ''
    })
  }
}

const addDailyPlan = () => {
  form.value.daily_plans.push({
    plan_date: '',
    day_label: '',
    planned_activity: '',
    expected_wear_lens_id: null,
    expected_duration_hours: 8,
    notes: ''
  })
}

const removeDailyPlan = (idx) => {
  form.value.daily_plans.splice(idx, 1)
}

const autoGenerateDailyPlans = () => {
  if (!form.value.start_date || !form.value.end_date) {
    alert('请先设置出发和返回日期')
    return
  }
  const start = new Date(form.value.start_date)
  const end = new Date(form.value.end_date)
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
  const labels = ['出发日', '观光日', '自由活动', '返程日']
  form.value.daily_plans = []
  for (let i = 0; i < days; i++) {
    const d = new Date(start)
    d.setDate(d.getDate() + i)
    let label = ''
    if (i === 0) label = '出发日'
    else if (i === days - 1) label = '返程日'
    else if (days <= 3) label = labels[i] || `第${i + 1}天`
    else label = `第${i + 1}天`

    form.value.daily_plans.push({
      plan_date: d.toISOString().slice(0, 10),
      day_label: label,
      planned_activity: '',
      expected_wear_lens_id: form.value.lens_items[0]?.lens_id || null,
      expected_duration_hours: 8,
      notes: ''
    })
  }
}

const handleSave = async () => {
  if (!form.value.name || !form.value.destination || !form.value.start_date || !form.value.end_date) {
    alert('请填写必填项：旅行名称、目的地、出发日期、返回日期')
    return
  }
  if (new Date(form.value.end_date) < new Date(form.value.start_date)) {
    alert('返回日期不能早于出发日期')
    return
  }

  if (customSuppliesText.value.trim()) {
    const lines = customSuppliesText.value.trim().split('\n').filter(l => l.trim())
    for (const line of lines) {
      const [name, qty] = line.split(',').map(s => s.trim())
      if (name) {
        form.value.supplies.push({
          supply_type: 'other',
          custom_name: name,
          is_checked: true,
          quantity: qty || '',
          notes: ''
        })
      }
    }
  }

  try {
    const payload = { ...form.value }
    if (editingPlan.value) {
      await updateTravelPlan(editingPlan.value.id, payload)
    } else {
      await createTravelPlan(payload)
    }
    showForm.value = false
    loadPlans()
  } catch (e) {
    console.error(e)
    const errorMsg = e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join('; ')
      || '保存失败，请检查表单数据后重试'
    alert(`保存失败：${errorMsg}`)
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定要删除这个旅行方案吗？')) return
  try {
    await deleteTravelPlan(id)
    loadPlans()
  } catch (e) {
    console.error(e)
  }
}

const handleMarkCompleted = async (id) => {
  if (!confirm('确认将此行程标记为已完成？')) return
  try {
    await markTravelPlanCompleted(id)
    showDetail.value = false
    loadPlans()
  } catch (e) {
    console.error(e)
  }
}

const handleMarkCancelled = async (id) => {
  if (!confirm('确认取消此行程？')) return
  try {
    await markTravelPlanCancelled(id)
    showDetail.value = false
    loadPlans()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadPlans()
  loadAvailableLenses()
})
</script>

<style scoped>
.travel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.travel-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #F3F4F6;
  cursor: pointer;
  transition: all 0.2s;
}

.travel-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.travel-card.risk-high {
  border: 2px solid #FECACA;
}

.travel-card.risk-medium {
  border: 2px solid #FEF3C7;
}

.travel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.travel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.travel-name {
  font-size: 16px;
  font-weight: 700;
  color: #1F2937;
}

.travel-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4B5563;
  flex-wrap: wrap;
}

.travel-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 12px;
  background: #F9FAFB;
  border-radius: 8px;
  margin-bottom: 12px;
}

.stat {
  text-align: center;
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  color: #7C3AED;
}

.stat-label {
  font-size: 11px;
  color: #9CA3AF;
  margin-top: 2px;
}

.travel-risks {
  margin-bottom: 12px;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 4px;
}

.risk-item.danger {
  background: #FEE2E2;
  color: #991B1B;
}

.risk-item.warning {
  background: #FEF3C7;
  color: #92400E;
}

.risk-item.info {
  background: #DBEAFE;
  color: #1E40AF;
}

.travel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #F3F4F6;
}

.info-box {
  background: #F9FAFB;
  padding: 12px;
  border-radius: 8px;
}

.info-title {
  font-size: 12px;
  color: #9CA3AF;
  margin-bottom: 4px;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #1F2937;
}

.lens-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #F9FAFB;
  border-radius: 8px;
}

.lens-item-row.is-under-rest {
  background: #FEF2F2;
}

.lens-item-left {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.lens-item-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.supply-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #F9FAFB;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.supply-item.checked {
  background: #ECFDF5;
  color: #065F46;
}

.supply-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #F9FAFB;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}

.supply-checkbox:hover {
  background: #F3F4F6;
}

.supply-checkbox.checked {
  background: #ECFDF5;
  color: #065F46;
}

.supply-checkbox input {
  width: 16px;
  height: 16px;
}

.supply-icon {
  font-size: 18px;
}
</style>
