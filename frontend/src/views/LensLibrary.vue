<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">💎</span>镜片库</h1>
      <button class="btn btn-primary" @click="showModal = true; editingLens = null; resetForm()">
        ➕ 添加镜片
      </button>
    </div>

    <div class="filter-bar">
      <select v-model="filterStatus" class="form-control" @change="loadLenses">
        <option value="">全部状态</option>
        <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select v-model="filterPurpose" class="form-control" @change="loadLenses">
        <option value="">全部用途</option>
        <option v-for="opt in PURPOSE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select v-model="filterCareStatus" class="form-control" @change="loadLenses">
        <option v-for="opt in CARE_STATUS_FILTER_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <input v-model="filterBrand" class="form-control" placeholder="🔍 搜索品牌..." @input="debouncedLoad">
    </div>

    <div v-if="activeReminders.length" class="card mb-20" style="border-left: 4px solid #EF4444;">
      <div class="card-title" style="color: #DC2626; display: flex; justify-content: space-between; align-items: center;">
        <span>⚠️ 护理与风险提醒（{{ activeReminders.length }}）</span>
        <button class="btn btn-sm btn-secondary" @click="refreshReminders">刷新</button>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div v-for="rem in activeReminders.slice(0, 5)" :key="rem.id"
             :class="['reminder-item', rem.severity]">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
              <div class="text-bold" style="font-size: 14px;">
                <span class="mr-8">{{ REMINDER_TYPE_MAP[rem.reminder_type]?.icon }}</span>
                {{ rem.title }}
                <span class="tag ml-8" :class="SEVERITY_MAP[rem.severity]?.class">{{ SEVERITY_MAP[rem.severity]?.label }}</span>
              </div>
              <div class="text-sm text-light mt-4">{{ rem.message }}</div>
              <div class="text-xs text-light mt-4">
                镜片: {{ rem.lens_brand }} {{ rem.lens_model }}
                <span v-if="rem.target_date"> · 目标日期: {{ formatDate(rem.target_date) }}</span>
              </div>
            </div>
            <button class="btn btn-sm btn-ghost ml-12" @click="handleDismissReminder(rem.id)">忽略</button>
          </div>
        </div>
        <div v-if="activeReminders.length > 5" class="text-sm text-light text-center mt-8">
          还有 {{ activeReminders.length - 5 }} 条提醒...
        </div>
      </div>
    </div>

    <div v-if="lenses.length" class="lens-grid">
      <div v-for="lens in lenses" :key="lens.id"
           class="lens-card"
           :class="{
             expired: lens.is_expired,
             expiring: !lens.is_expired && lens.days_until_expiry <= 30,
             'care-danger': ['rest', 'replace_overdue', 'care_overdue', 'checkup_overdue'].includes(lens.care_status),
             'care-warning': ['replace_soon', 'care_soon', 'checkup_soon'].includes(lens.care_status)
           }">
        <div class="lens-header">
          <div>
            <div class="lens-brand">{{ lens.brand }}</div>
            <div class="lens-model">{{ lens.model_name || '经典款' }} {{ lens.color ? '· ' + lens.color : '' }}</div>
            <div class="mt-8 flex-wrap gap-8" style="display: flex;">
              <span class="tag" :class="STATUS_MAP[lens.status]?.class">{{ STATUS_MAP[lens.status]?.label }}</span>
              <span class="tag" :class="PURPOSE_MAP[lens.purpose]?.class">
                {{ PURPOSE_MAP[lens.purpose]?.icon }} {{ PURPOSE_MAP[lens.purpose]?.label }}
              </span>
              <span v-if="lens.care_method" class="tag" :class="CARE_METHOD_MAP[lens.care_method]?.class">
                {{ CARE_METHOD_MAP[lens.care_method]?.label }}
              </span>
              <span v-if="lens.is_expired" class="tag tag-red">已过期</span>
              <span v-else-if="lens.days_until_expiry <= 30" class="tag tag-yellow">
                剩{{ lens.days_until_expiry }}天
              </span>
              <span v-if="lens.care_status && lens.care_status !== 'normal'"
                    class="tag" :class="CARE_STATUS_MAP[lens.care_status]?.class">
                {{ CARE_STATUS_MAP[lens.care_status]?.icon }} {{ CARE_STATUS_MAP[lens.care_status]?.label }}
              </span>
              <span v-if="lens.remaining_stock != null" class="tag tag-blue">
                📦 库存: {{ lens.remaining_stock }}片
              </span>
              <span v-if="lens.restock_status" class="tag" :class="lens.restock_status.class">
                {{ lens.restock_status.label }}
              </span>
              <span v-if="lens.usage_frequency" class="tag" :class="USAGE_FREQUENCY_MAP[lens.usage_frequency]?.class">
                {{ USAGE_FREQUENCY_MAP[lens.usage_frequency]?.label }}
              </span>
            </div>
          </div>
        </div>

        <div class="lens-specs">
          <div>
            <div class="spec">度数</div>
            <div class="spec-value">{{ lens.power_sph }}D{{ lens.power_cyl ? ' / ' + lens.power_cyl + 'DC' : '' }}</div>
          </div>
          <div>
            <div class="spec">含水量</div>
            <div class="spec-value">{{ lens.water_content }}%</div>
          </div>
          <div>
            <div class="spec">基弧</div>
            <div class="spec-value">{{ lens.base_curve }}mm</div>
          </div>
          <div>
            <div class="spec">直径</div>
            <div class="spec-value">{{ lens.diameter }}mm</div>
          </div>
          <div>
            <div class="spec">购买日期</div>
            <div class="spec-value">{{ formatDate(lens.purchase_date) }}</div>
          </div>
          <div>
            <div class="spec">有效期至</div>
            <div class="spec-value">{{ formatDate(lens.expiry_date) }}</div>
          </div>
          <div v-if="lens.total_wear_hours">
            <div class="spec">累计佩戴</div>
            <div class="spec-value">{{ lens.total_wear_hours }}h</div>
          </div>
          <div v-if="lens.avg_comfort">
            <div class="spec">平均舒适</div>
            <div class="spec-value">{{ renderStars(Math.round(lens.avg_comfort)) }}</div>
          </div>
        </div>

        <div v-if="lens.care_status && lens.care_status !== 'normal'"
             :class="['care-alert', lens.care_status.includes('overdue') || lens.care_status === 'rest' ? 'danger' : 'warning']">
          <div v-if="lens.care_status === 'rest'">
            🛑 <strong>停戴观察中</strong>
            <span v-if="lens.rest_until_date">至 {{ formatDate(lens.rest_until_date) }}</span>
          </div>
          <div v-else-if="lens.care_status === 'replace_overdue'">
            🔴 <strong>已超过建议更换周期</strong>
            <span v-if="lens.days_until_replacement != null">（已逾期 {{ Math.abs(lens.days_until_replacement) }} 天）</span>
          </div>
          <div v-else-if="lens.care_status === 'care_overdue'">
            🔴 <strong>护理已逾期</strong>
            <span v-if="lens.next_care_date">（计划: {{ formatDate(lens.next_care_date) }}）</span>
          </div>
          <div v-else-if="lens.care_status === 'checkup_overdue'">
            🔴 <strong>复查已逾期</strong>
            <span v-if="lens.next_checkup_date">（计划: {{ formatDate(lens.next_checkup_date) }}）</span>
          </div>
          <div v-else-if="lens.care_status === 'replace_soon'">
            🟡 即将达到更换周期
            <span v-if="lens.days_until_replacement != null">（还剩 {{ lens.days_until_replacement }} 天）</span>
          </div>
          <div v-else-if="lens.care_status === 'care_soon'">
            🟡 即将需要护理
            <span v-if="lens.next_care_date">（{{ formatDate(lens.next_care_date) }}，还剩 {{ lens.days_until_next_care }} 天）</span>
          </div>
          <div v-else-if="lens.care_status === 'checkup_soon'">
            🟡 即将需要复查
            <span v-if="lens.next_checkup_date">（{{ formatDate(lens.next_checkup_date) }}，还剩 {{ lens.days_until_next_checkup }} 天）</span>
          </div>
        </div>

        <div v-if="lens.active_reminders && lens.active_reminders.length" class="care-alert info" style="margin-top: 8px;">
          <div v-for="rem in lens.active_reminders" :key="rem.id" class="text-sm" style="padding: 2px 0;">
            {{ REMINDER_TYPE_MAP[rem.reminder_type]?.icon }} {{ rem.title }}
          </div>
        </div>

        <div class="lens-footer">
          <div class="text-sm text-light">
            建议日戴≤{{ lens.daily_wear_limit }}h
            <span v-if="lens.care_solution_brand"> · {{ lens.care_solution_brand }}</span>
            <span v-if="lens.days_since_open != null"> · 已开封{{ lens.days_since_open }}天</span>
          </div>
          <div class="lens-actions">
            <button v-if="lens.status === 'unopened'" class="btn btn-sm btn-success" @click="handleOpen(lens.id)">开封</button>
            <button v-if="lens.status === 'opened'" class="btn btn-sm btn-secondary" @click="handleUsedUp(lens.id)">用完</button>
            <button v-if="lens.status === 'opened' && !lens.is_under_rest"
                    class="btn btn-sm btn-primary" @click="openCareActions(lens)">护理</button>
            <button v-if="lens.is_under_rest" class="btn btn-sm btn-warning" @click="handleEndRest(lens.id)">结束停戴</button>
            <button class="btn btn-sm btn-pink" @click="createOutfitPlan(lens.id)">💄 搭配</button>
            <button class="btn btn-sm btn-secondary" @click="openEdit(lens)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="handleDelete(lens.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="card empty-state">
      <div class="empty-icon">💎</div>
      <h3>还没有添加镜片</h3>
      <p>点击右上角「添加镜片」开始记录您的第一副彩瞳吧</p>
      <button class="btn btn-primary mt-12" @click="showModal = true; editingLens = null; resetForm()">立即添加</button>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ editingLens ? '编辑镜片' : '添加镜片' }}</div>
          <button class="modal-close" @click="showModal = false">×</button>
        </div>
        <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
          <div class="nav-tabs" style="margin-bottom: 16px;">
            <button class="nav-tab" :class="{ active: formTab === 'basic' }" @click="formTab = 'basic'">基本信息</button>
            <button class="nav-tab" :class="{ active: formTab === 'care' }" @click="formTab = 'care'">护理计划</button>
            <button class="nav-tab" :class="{ active: formTab === 'budget' }" @click="formTab = 'budget'">预算补货</button>
          </div>

          <div v-if="formTab === 'basic'">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">品牌 *</label>
                <input v-model="form.brand" class="form-control" placeholder="如：海俪恩、博士伦">
              </div>
              <div class="form-group">
                <label class="form-label">系列/型号</label>
                <input v-model="form.model_name" class="form-control" placeholder="如：萌生宠爱">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">颜色</label>
                <input v-model="form.color" class="form-control" placeholder="如：棕、灰、蓝">
              </div>
              <div class="form-group">
                <label class="form-label">用途</label>
                <select v-model="form.purpose" class="form-control">
                  <option v-for="opt in PURPOSE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">球镜度数 SPH (D) *</label>
                <input v-model.number="form.power_sph" type="number" step="0.25" class="form-control" placeholder="-3.00">
              </div>
              <div class="form-group">
                <label class="form-label">柱镜度数 CYL (D)</label>
                <input v-model.number="form.power_cyl" type="number" step="0.25" class="form-control" placeholder="散光用">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">含水量 (%) *</label>
                <input v-model.number="form.water_content" type="number" class="form-control" placeholder="38">
              </div>
              <div class="form-group">
                <label class="form-label">基弧 (mm) *</label>
                <input v-model.number="form.base_curve" type="number" step="0.1" class="form-control" placeholder="8.6">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">直径 (mm)</label>
                <input v-model.number="form.diameter" type="number" step="0.1" class="form-control" placeholder="14.0">
              </div>
              <div class="form-group">
                <label class="form-label">总片数</label>
                <input v-model.number="form.pair_count" type="number" class="form-control" placeholder="2">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">购买日期 *</label>
                <input v-model="form.purchase_date" type="date" class="form-control">
              </div>
              <div class="form-group">
                <label class="form-label">有效期至 *</label>
                <input v-model="form.expiry_date" type="date" class="form-control">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">开封日期</label>
                <input v-model="form.open_date" type="date" class="form-control">
              </div>
              <div class="form-group">
                <label class="form-label">状态</label>
                <select v-model="form.status" class="form-control">
                  <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">备注</label>
              <textarea v-model="form.notes" class="form-control" placeholder="可记录购买渠道、价格等..."></textarea>
            </div>
          </div>

          <div v-if="formTab === 'care'">
            <div class="alert alert-info" style="margin-bottom: 16px;">
              <div class="alert-icon">💡</div>
              <div class="alert-content">
                <div class="alert-title">护理计划设置</div>
                <div class="alert-message" style="font-size: 12px;">设置后系统将在接近护理/复查日期时提醒您，并根据佩戴记录自动生成护理建议。</div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">护理方式</label>
                <select v-model="form.care_method" class="form-control">
                  <option v-for="opt in CARE_METHOD_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">护理液品牌</label>
                <input v-model="form.care_solution_brand" class="form-control" placeholder="如：爱尔康、博士伦、海昌">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">开封后建议更换周期</label>
                <select v-model="form.replacement_days_after_open" class="form-control">
                  <option v-for="opt in REPLACEMENT_CYCLE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">下次护理日期</label>
                <input v-model="form.next_care_date" type="date" class="form-control">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">下次眼科复查日期</label>
                <input v-model="form.next_checkup_date" type="date" class="form-control">
              </div>
              <div class="form-group">
                <label class="form-label">停戴观察</label>
                <div style="display: flex; gap: 8px; align-items: center;">
                  <label style="display: flex; align-items: center; gap: 4px;">
                    <input type="checkbox" v-model="form.need_rest_observation">
                    <span>需要停戴</span>
                  </label>
                  <input v-if="form.need_rest_observation" v-model="form.rest_until_date"
                         type="date" class="form-control" style="flex: 1;" placeholder="停戴至">
                </div>
              </div>
            </div>
          </div>

          <div v-if="formTab === 'budget'">
            <div class="alert alert-info" style="margin-bottom: 16px;">
              <div class="alert-icon">💰</div>
              <div class="alert-content">
                <div class="alert-title">预算与补货设置</div>
                <div class="alert-message" style="font-size: 12px;">设置购买信息和补货参数，系统会根据库存和使用频率自动生成补货建议。</div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">购买渠道</label>
                <select v-model="form.purchase_channel" class="form-control">
                  <option v-for="opt in PURCHASE_CHANNEL_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">单价(元)</label>
                <input v-model.number="form.unit_price" type="number" step="0.01" class="form-control" placeholder="0.00">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">折扣(%)</label>
                <input v-model.number="form.discount" type="number" step="0.01" class="form-control" placeholder="100">
              </div>
              <div class="form-group">
                <label class="form-label">运费(元)</label>
                <input v-model.number="form.shipping_fee" type="number" step="0.01" class="form-control" placeholder="0.00">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">库存数量(片)</label>
                <input v-model.number="form.stock_quantity" type="number" class="form-control" placeholder="2">
              </div>
              <div class="form-group">
                <label class="form-label">常用程度</label>
                <select v-model="form.usage_frequency" class="form-control">
                  <option v-for="opt in USAGE_FREQUENCY_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">计划补货日期</label>
                <input v-model="form.planned_restock_date" type="date" class="form-control">
              </div>
              <div class="form-group">
                <label class="form-label">补货优先级</label>
                <select v-model="form.restock_priority" class="form-control">
                  <option v-for="opt in RESTOCK_PRIORITY_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">预算月份</label>
                <input v-model="form.budget_month" class="form-control" placeholder="YYYY-MM">
              </div>
              <div class="form-group">
                <label class="form-label">实付金额(元)</label>
                <input v-model.number="form.total_paid" type="number" step="0.01" class="form-control" placeholder="0.00">
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">补货备注</label>
              <textarea v-model="form.restock_notes" class="form-control" placeholder="记录补货相关的备注信息..."></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="handleSave">保存</button>
        </div>
      </div>
    </div>

    <div v-if="showCareActions" class="modal-overlay" @click.self="showCareActions = false">
      <div class="modal" style="max-width: 480px;">
        <div class="modal-header">
          <div class="modal-title">护理操作 - {{ currentCareLens?.brand }} {{ currentCareLens?.model_name }}</div>
          <button class="modal-close" @click="showCareActions = false">×</button>
        </div>
        <div class="modal-body">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <button class="btn btn-primary" style="padding: 20px 12px;" @click="handleMarkCareDone">
              <div style="font-size: 24px;">🧴</div>
              <div class="mt-8 text-bold">标记护理完成</div>
              <div class="text-xs text-light">更新下次护理日期</div>
            </button>
            <button class="btn btn-primary" style="padding: 20px 12px;" @click="handleMarkCheckupDone">
              <div style="font-size: 24px;">👁️</div>
              <div class="mt-8 text-bold">标记复查完成</div>
              <div class="text-xs text-light">更新下次复查日期</div>
            </button>
            <button class="btn btn-warning" style="padding: 20px 12px;" @click="showStartRest = true">
              <div style="font-size: 24px;">🛑</div>
              <div class="mt-8 text-bold">开始停戴观察</div>
              <div class="text-xs text-light">设置停戴天数</div>
            </button>
            <button class="btn btn-secondary" style="padding: 20px 12px;" @click="openCareDetail">
              <div style="font-size: 24px;">📋</div>
              <div class="mt-8 text-bold">查看护理记录</div>
              <div class="text-xs text-light">历史护理与提醒</div>
            </button>
          </div>

          <div v-if="showStartRest" class="mt-20" style="padding: 16px; background: #FEF3C7; border-radius: 10px;">
            <div class="text-bold mb-8">设置停戴天数</div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">停戴天数</label>
                <select v-model="restDays" class="form-control">
                  <option :value="1">1天</option>
                  <option :value="2">2天</option>
                  <option :value="3">3天（推荐）</option>
                  <option :value="5">5天</option>
                  <option :value="7">7天</option>
                  <option :value="14">14天</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">备注</label>
                <input v-model="restNotes" class="form-control" placeholder="可注明原因">
              </div>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary" @click="showStartRest = false">取消</button>
              <button class="btn btn-warning" @click="confirmStartRest">确认开始停戴</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCareDetail" class="modal-overlay" @click.self="showCareDetail = false">
      <div class="modal" style="max-width: 640px;">
        <div class="modal-header">
          <div class="modal-title">护理记录 - {{ currentCareLens?.brand }} {{ currentCareLens?.model_name }}</div>
          <button class="modal-close" @click="showCareDetail = false">×</button>
        </div>
        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
          <div v-if="currentCareLens">
            <div class="stats-grid" style="grid-template-columns: repeat(4, 1fr);">
              <div class="stat-card primary">
                <div class="stat-label">护理方式</div>
                <div class="stat-value small">{{ CARE_METHOD_MAP[currentCareLens.care_method]?.label || '未设置' }}</div>
              </div>
              <div class="stat-card green">
                <div class="stat-label">下次护理</div>
                <div class="stat-value small">{{ formatDate(currentCareLens.next_care_date) || '未设置' }}</div>
              </div>
              <div class="stat-card pink">
                <div class="stat-label">下次复查</div>
                <div class="stat-value small">{{ formatDate(currentCareLens.next_checkup_date) || '未设置' }}</div>
              </div>
              <div class="stat-card yellow">
                <div class="stat-label">更换周期</div>
                <div class="stat-value small">{{ currentCareLens.replacement_days_display || '未设置' }}</div>
              </div>
            </div>

            <div class="mt-20">
              <div class="card-title">护理历史</div>
              <table class="table" v-if="lensCareRecords.length">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>类型</th>
                    <th>备注</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="rec in lensCareRecords" :key="rec.id">
                    <td>{{ formatDate(rec.care_date) }}</td>
                    <td>{{ rec.care_type_display }}</td>
                    <td class="text-sm text-light">{{ rec.notes || '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="text-light text-center" style="padding: 20px;">暂无护理记录</div>
            </div>

            <div class="mt-20">
              <div class="card-title">提醒记录</div>
              <div v-if="lensReminders.length" style="display: flex; flex-direction: column; gap: 8px;">
                <div v-for="rem in lensReminders.slice(0, 10)" :key="rem.id"
                     :class="['reminder-item', rem.severity]"
                     :style="{ opacity: rem.is_dismissed ? 0.5 : 1 }">
                  <div class="text-bold text-sm">
                    <span class="mr-8">{{ REMINDER_TYPE_MAP[rem.reminder_type]?.icon }}</span>
                    {{ rem.title }}
                    <span v-if="rem.is_dismissed" class="tag tag-gray ml-8">已忽略</span>
                  </div>
                  <div class="text-xs text-light mt-4">{{ rem.message }}</div>
                </div>
              </div>
              <div v-else class="text-light text-center" style="padding: 20px;">暂无提醒记录</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
import {
  getLensList, createLens, updateLens, deleteLens, openLens, markLensUsedUp,
  markLensCareDone, markLensCheckupDone, startLensRest, endLensRest,
  getLensCareRecords, getLensReminders,
  getActiveCareReminders, dismissReminder
} from '@/api/lens'
import {
  STATUS_MAP, PURPOSE_MAP, STATUS_OPTIONS, PURPOSE_OPTIONS, formatDate, renderStars,
  CARE_METHOD_MAP, CARE_METHOD_OPTIONS, REPLACEMENT_CYCLE_OPTIONS,
  CARE_STATUS_MAP, CARE_STATUS_FILTER_OPTIONS,
  REMINDER_TYPE_MAP, SEVERITY_MAP,
  RESTOCK_STATUS_MAP, USAGE_FREQUENCY_MAP, USAGE_FREQUENCY_OPTIONS,
  PURCHASE_CHANNEL_OPTIONS, RESTOCK_PRIORITY_OPTIONS
} from '@/utils/constants'

const lenses = ref([])
const activeReminders = ref([])
const showModal = ref(false)
const editingLens = ref(null)
const filterStatus = ref('')
const filterPurpose = ref('')
const filterCareStatus = ref('')
const filterBrand = ref('')
const formTab = ref('basic')

const showCareActions = ref(false)
const currentCareLens = ref(null)
const showStartRest = ref(false)
const restDays = ref(3)
const restNotes = ref('')

const showCareDetail = ref(false)
const lensCareRecords = ref([])
const lensReminders = ref([])

const defaultForm = {
  brand: '', model_name: '', color: '',
  power_sph: 0, power_cyl: 0,
  water_content: 38, base_curve: 8.6, diameter: 14.0,
  purchase_date: '', expiry_date: '', open_date: '',
  purpose: 'daily', status: 'unopened',
  pair_count: 2, used_count: 0, notes: '',
  care_method: '', care_solution_brand: '',
  replacement_days_after_open: '',
  next_care_date: '', next_checkup_date: '',
  need_rest_observation: false, rest_until_date: '',
  purchase_channel: 'taobao',
  unit_price: 0,
  discount: 100,
  shipping_fee: 0,
  total_paid: 0,
  stock_quantity: 2,
  usage_frequency: 'occasional',
  planned_restock_date: '',
  restock_priority: 'medium',
  budget_month: '',
  restock_notes: ''
}
const form = ref({ ...defaultForm })

const resetForm = () => {
  form.value = { ...defaultForm }
  formTab.value = 'basic'
}

let debounceTimer = null
const debouncedLoad = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadLenses, 300)
}

const loadLenses = async () => {
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterPurpose.value) params.purpose = filterPurpose.value
    if (filterCareStatus.value) params.care_status = filterCareStatus.value
    if (filterBrand.value) params.brand = filterBrand.value
    const res = await getLensList(params)
    lenses.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e) {
    console.error(e)
  }
}

const loadActiveReminders = async () => {
  try {
    const res = await getActiveCareReminders()
    activeReminders.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e) {
    console.error(e)
  }
}

const refreshReminders = () => {
  loadActiveReminders()
  loadLenses()
}

const handleDismissReminder = async (id) => {
  try {
    await dismissReminder(id)
    loadActiveReminders()
    loadLenses()
  } catch (e) {
    console.error(e)
  }
}

const openEdit = (lens) => {
  editingLens.value = lens
  form.value = {
    ...lens,
    open_date: lens.open_date || '',
    next_care_date: lens.next_care_date || '',
    next_checkup_date: lens.next_checkup_date || '',
    rest_until_date: lens.rest_until_date || '',
    replacement_days_after_open: lens.replacement_days_after_open || '',
    care_method: lens.care_method || '',
    purchase_channel: lens.purchase_channel || 'taobao',
    unit_price: lens.unit_price || 0,
    discount: lens.discount || 100,
    shipping_fee: lens.shipping_fee || 0,
    total_paid: lens.total_paid || 0,
    stock_quantity: lens.stock_quantity || 2,
    usage_frequency: lens.usage_frequency || 'occasional',
    planned_restock_date: lens.planned_restock_date || '',
    restock_priority: lens.restock_priority || 'medium',
    budget_month: lens.budget_month || '',
    restock_notes: lens.restock_notes || '',
  }
  showModal.value = true
}

const handleSave = async () => {
  if (!form.value.brand || !form.value.purchase_date || !form.value.expiry_date) {
    alert('请填写必填项：品牌、购买日期、有效期')
    return
  }
  try {
    const payload = { ...form.value }
    if (payload.replacement_days_after_open === '') delete payload.replacement_days_after_open
    if (!payload.care_method) delete payload.care_method
    if (!payload.next_care_date) delete payload.next_care_date
    if (!payload.next_checkup_date) delete payload.next_checkup_date
    if (!payload.rest_until_date) delete payload.rest_until_date

    if (editingLens.value) {
      await updateLens(editingLens.value.id, payload)
    } else {
      await createLens(payload)
    }
    showModal.value = false
    loadLenses()
  } catch (e) {
    console.error(e)
    const errorMsg = e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join('; ')
      || '保存失败，请检查表单数据后重试'
    alert(`保存失败：${errorMsg}`)
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定要删除这副镜片吗？相关佩戴记录也会保留。')) return
  try {
    await deleteLens(id)
    loadLenses()
  } catch (e) {
    console.error(e)
  }
}

const handleOpen = async (id) => {
  try {
    await openLens(id)
    loadLenses()
  } catch (e) {
    console.error(e)
  }
}

const handleUsedUp = async (id) => {
  if (!confirm('标记为已用完？')) return
  try {
    await markLensUsedUp(id)
    loadLenses()
  } catch (e) {
    console.error(e)
  }
}

const openCareActions = (lens) => {
  currentCareLens.value = lens
  showCareActions.value = true
  showStartRest.value = false
  restDays.value = 3
  restNotes.value = ''
}

const handleMarkCareDone = async () => {
  if (!currentCareLens.value) return
  if (!confirm('确认标记本次护理完成？系统将自动设置下次护理日期为7天后。')) return
  try {
    await markLensCareDone(currentCareLens.value.id)
    showCareActions.value = false
    loadLenses()
    loadActiveReminders()
  } catch (e) {
    console.error(e)
    alert('操作失败')
  }
}

const handleMarkCheckupDone = async () => {
  if (!currentCareLens.value) return
  if (!confirm('确认标记本次眼科复查完成？系统将自动设置下次复查日期为半年后。')) return
  try {
    await markLensCheckupDone(currentCareLens.value.id)
    showCareActions.value = false
    loadLenses()
    loadActiveReminders()
  } catch (e) {
    console.error(e)
    alert('操作失败')
  }
}

const confirmStartRest = async () => {
  if (!currentCareLens.value) return
  try {
    await startLensRest(currentCareLens.value.id, {
      days: restDays.value,
      notes: restNotes.value
    })
    showCareActions.value = false
    showStartRest.value = false
    loadLenses()
    loadActiveReminders()
  } catch (e) {
    console.error(e)
    alert('操作失败')
  }
}

const handleEndRest = async (id) => {
  if (!confirm('确认结束停戴观察？')) return
  try {
    await endLensRest(id)
    loadLenses()
    loadActiveReminders()
  } catch (e) {
    console.error(e)
  }
}

const openCareDetail = async () => {
  showCareActions.value = false
  showCareDetail.value = true
  if (currentCareLens.value) {
    try {
      const [records, reminders] = await Promise.all([
        getLensCareRecords(currentCareLens.value.id),
        getLensReminders(currentCareLens.value.id, true)
      ])
      lensCareRecords.value = Array.isArray(records) ? records : (records.results || [])
      lensReminders.value = Array.isArray(reminders) ? reminders : (reminders.results || [])
    } catch (e) {
      console.error(e)
    }
  }
}

const createOutfitPlan = (lensId) => {
  router.push({
    path: '/outfit-plans',
    query: { lens_id: lensId }
  })
}

onMounted(() => {
  loadLenses()
  loadActiveReminders()
})
</script>
