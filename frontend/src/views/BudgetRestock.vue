<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">💰</span>预算与补货管理</h1>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-secondary" @click="generateSuggestions">
          🔄 生成补货建议
        </button>
        <button class="btn btn-primary" @click="showPurchaseModal = true; editingPurchase = null; resetPurchaseForm()">
          ➕ 添加采购记录
        </button>
      </div>
    </div>

    <div class="stats-grid">
      <div :class="['stat-card', budgetStats.is_over_budget ? '' : 'primary']"
           :style="budgetStats.is_over_budget ? 'background: linear-gradient(135deg, #FEE2E2, #FECACA);' : ''">
        <div class="stat-label">本月消费</div>
        <div class="stat-value" :style="budgetStats.is_over_budget ? 'color: #DC2626;' : ''">
          ¥{{ budgetStats.total_spent_month || 0 }}
        </div>
        <div class="stat-sub">
          共 {{ budgetStats.total_purchases_month || 0 }} 笔采购
        </div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">年度消费</div>
        <div class="stat-value small">¥{{ budgetStats.total_spent_year || 0 }}</div>
        <div class="stat-sub">{{ budgetStats.total_purchases_year || 0 }} 笔采购</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">预算限额</div>
        <div class="stat-value small">
          ¥<input type="number" v-model.number="budgetLimit" @change="loadBudgetStats"
                  style="width: 100px; border: none; background: transparent; font-size: inherit; font-weight: inherit; color: inherit;">
        </div>
        <div class="stat-sub">
          <span v-if="budgetStats.budget_used_percent != null">
            已使用 {{ budgetStats.budget_used_percent }}%
          </span>
        </div>
      </div>
      <div v-if="budgetStats.is_over_budget" class="stat-card" style="background: linear-gradient(135deg, #FEE2E2, #FECACA);">
        <div class="stat-label">⚠️ 预算超支</div>
        <div class="stat-value" style="color: #DC2626;">
          ¥{{ (budgetStats.total_spent_month - budgetLimit).toFixed(2) }}
        </div>
        <div class="stat-sub">超出预算部分</div>
      </div>
      <div v-else class="stat-card yellow">
        <div class="stat-label">剩余预算</div>
        <div class="stat-value" style="color: #B45309;">
          ¥{{ (budgetLimit - budgetStats.total_spent_month).toFixed(2) }}
        </div>
        <div class="stat-sub">本月可用</div>
      </div>
    </div>

    <div v-if="budgetStats.is_over_budget" class="alert alert-danger mb-20">
      <div class="alert-icon">⚠️</div>
      <div class="alert-content">
        <div class="alert-title">预算超支提醒</div>
        <div class="alert-message">
          本月消费已超出预算 ¥{{ (budgetStats.total_spent_month - budgetLimit).toFixed(2) }}，建议控制后续采购支出。
        </div>
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="filterBrand" class="form-control" @change="loadPurchaseRecords">
        <option value="">全部品牌</option>
        <option v-for="b in brandList" :key="b" :value="b">{{ b }}</option>
      </select>
      <select v-model="filterChannel" class="form-control" @change="loadPurchaseRecords">
        <option value="">全部渠道</option>
        <option v-for="opt in PURCHASE_CHANNEL_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select v-model="filterPriority" class="form-control" @change="loadBudgetStats">
        <option value="">全部优先级</option>
        <option v-for="opt in RESTOCK_PRIORITY_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select v-model="filterMonth" class="form-control" @change="loadAllData">
        <option v-for="m in availableMonths" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>

    <div class="nav-tabs" style="margin-bottom: 20px;">
      <button class="nav-tab" :class="{ active: activeTab === 'purchases' }" @click="activeTab = 'purchases'">
        📋 采购记录
      </button>
      <button class="nav-tab" :class="{ active: activeTab === 'suggestions' }" @click="activeTab = 'suggestions'">
        💡 补货建议 ({{ restockSuggestions.length }})
      </button>
      <button class="nav-tab" :class="{ active: activeTab === 'analytics' }" @click="activeTab = 'analytics'">
        📊 消费分析
      </button>
      <button class="nav-tab" :class="{ active: activeTab === 'warnings' }" @click="activeTab = 'warnings'">
        ⚠️ 提醒预警 ({{ totalWarnings }})
      </button>
    </div>

    <div v-if="activeTab === 'purchases'">
      <div v-if="purchaseRecords.length" class="card">
        <div class="card-title">采购记录列表</div>
        <table class="table">
          <thead>
            <tr>
              <th>采购日期</th>
              <th>镜片</th>
              <th>渠道</th>
              <th>数量</th>
              <th>单价</th>
              <th>折扣</th>
              <th>运费</th>
              <th>实付</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in purchaseRecords" :key="record.id">
              <td>{{ formatDate(record.purchase_date) }}</td>
              <td>
                <div class="text-bold">{{ record.lens_brand }}</div>
                <div class="text-xs text-light">{{ record.lens_model }} {{ record.lens_color }}</div>
              </td>
              <td>{{ record.purchase_channel_display }}</td>
              <td>{{ record.quantity }} 片</td>
              <td>¥{{ record.unit_price }}</td>
              <td>{{ record.discount }}%</td>
              <td>¥{{ record.shipping_fee }}</td>
              <td class="text-bold">¥{{ record.actual_paid }}</td>
              <td>
                <span class="tag" :class="PAYMENT_STATUS_MAP[record.payment_status]?.class">
                  {{ PAYMENT_STATUS_MAP[record.payment_status]?.label }}
                </span>
              </td>
              <td>
                <button class="btn btn-sm btn-secondary" @click="editPurchase(record)">编辑</button>
                <button class="btn btn-sm btn-danger" @click="deletePurchase(record.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="card empty-state">
        <div class="empty-icon">📋</div>
        <h3>暂无采购记录</h3>
        <p>点击右上角「添加采购记录」开始记录您的彩瞳采购</p>
        <button class="btn btn-primary mt-12" @click="showPurchaseModal = true; editingPurchase = null; resetPurchaseForm()">
          立即添加
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'suggestions'">
      <div class="card mb-20">
        <div class="flex-between mb-16">
          <div class="card-title" style="margin-bottom: 0;">补货建议</div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-sm btn-secondary" @click="markAllActionTaken">全部标记已处理</button>
            <button class="btn btn-sm btn-secondary" @click="dismissAll">全部忽略</button>
          </div>
        </div>
        <div v-if="restockSuggestions.length" style="display: flex; flex-direction: column; gap: 12px;">
          <div v-for="sug in restockSuggestions" :key="sug.id"
               :class="['restock-suggestion', sug.severity]">
            <div style="display: flex; gap: 12px; align-items: flex-start;">
              <div style="font-size: 24px;">
                {{ RESTOCK_SUGGESTION_TYPE_MAP[sug.suggestion_type]?.icon }}
              </div>
              <div style="flex: 1;">
                <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
                  <span class="text-bold">{{ sug.title }}</span>
                  <span class="tag" :class="RESTOCK_SEVERITY_MAP[sug.severity]?.class">
                    {{ RESTOCK_SEVERITY_MAP[sug.severity]?.label }}
                  </span>
                  <span class="tag tag-pink">
                    {{ RESTOCK_SUGGESTION_TYPE_MAP[sug.suggestion_type]?.label }}
                  </span>
                </div>
                <div class="text-sm text-light">{{ sug.message }}</div>
                <div class="text-xs text-light mt-8" style="display: flex; gap: 16px;">
                  <span>镜片: {{ sug.lens_brand }} {{ sug.lens_model }}</span>
                  <span>当前库存: {{ sug.lens_remaining_stock }} 片</span>
                  <span v-if="sug.estimated_days_left != null">预计可用: {{ sug.estimated_days_left }} 天</span>
                  <span v-if="sug.suggested_quantity > 0">建议补货: {{ sug.suggested_quantity }} 片</span>
                  <span v-if="sug.suggested_date">建议日期: {{ formatDate(sug.suggested_date) }}</span>
                </div>
              </div>
              <div style="display: flex; gap: 4px;">
                <button class="btn btn-sm btn-success" @click="markActionTaken(sug.id)">已处理</button>
                <button class="btn btn-sm btn-secondary" @click="dismissSuggestion(sug.id)">忽略</button>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">✅</div>
          <p>暂无补货建议，所有镜片库存充足</p>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'analytics'">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
        <div class="card">
          <div class="card-title">📈 近12个月消费趋势</div>
          <div class="chart-container small" ref="monthlyTrendChartRef"></div>
        </div>
        <div class="card">
          <div class="card-title">🥧 各品牌花费占比</div>
          <div class="chart-container small" ref="brandPieChartRef"></div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
        <div class="card">
          <div class="card-title">🏷️ 各渠道价格对比</div>
          <div class="chart-container small" ref="channelPriceChartRef"></div>
        </div>
        <div class="card">
          <div class="card-title">🏆 品牌性价比排行</div>
          <table class="table" v-if="budgetStats.brand_value_ranking && budgetStats.brand_value_ranking.length">
            <thead>
              <tr>
                <th>排名</th>
                <th>品牌</th>
                <th>平均舒适</th>
                <th>每次成本</th>
                <th>性价比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(b, idx) in budgetStats.brand_value_ranking.slice(0, 6)" :key="b.lens_id">
                <td>
                  <span v-if="idx === 0">🥇</span>
                  <span v-else-if="idx === 1">🥈</span>
                  <span v-else-if="idx === 2">🥉</span>
                  <span v-else class="text-light">{{ idx + 1 }}</span>
                </td>
                <td class="text-bold">{{ b.brand }} {{ b.model }}</td>
                <td>{{ '⭐'.repeat(Math.round(b.avg_comfort)) }} {{ b.avg_comfort }}</td>
                <td>¥{{ b.cost_per_wear }}</td>
                <td>
                  <span class="tag tag-green">{{ b.value_score }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state" style="padding: 30px;">
            <p class="text-light">暂无数据</p>

          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">💸 各渠道消费统计</div>
        <table class="table" v-if="budgetStats.channel_spending && budgetStats.channel_spending.length">
          <thead>
            <tr>
              <th>渠道</th>
              <th>消费金额</th>
              <th>占比</th>
              <th>采购次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in budgetStats.channel_spending" :key="c.channel">
              <td class="text-bold">{{ c.channel }}</td>
              <td>¥{{ c.total.toFixed(2) }}</td>
              <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <div style="flex: 1; height: 8px; background: #E5E7EB; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; background: linear-gradient(90deg, #8B5CF6, #A78BFA); width: {{ c.percent }}%;"></div>
                  </div>
                  <span class="text-sm">{{ c.percent }}%</span>
                </div>
              </td>
              <td>{{ c.count }} 次</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 30px;">
          <p class="text-light">暂无数据</p>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'warnings'">
      <div v-if="budgetStats.running_out_soon && budgetStats.running_out_soon.length" class="card mb-20" style="border-left: 4px solid #EF4444;">
        <div class="card-title" style="color: #DC2626;">🚨 即将用完预警</div>
        <div v-if="budgetStats.running_out_soon.length" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px;">
          <div v-for="lens in budgetStats.running_out_soon" :key="lens.id"
               class="warning-card" style="background: #FEF2F2;">
            <div class="text-bold">{{ lens.brand }} {{ lens.model_name }}</div>
            <div class="text-sm text-light mt-4">
              {{ lens.color }} · {{ lens.power_sph }}D
            </div>
            <div class="mt-8">
              <span class="tag tag-red">{{ lens.restock_status?.label || '库存不足' }}</span>
              <span v-if="lens.estimated_days_left != null" class="tag tag-yellow ml-8">
                剩{{ lens.estimated_days_left }}天
              </span>
            </div>
            <div class="text-xs text-light mt-8">
              当前库存: {{ lens.remaining_stock }} 片 · 月均使用: {{ lens.monthly_usage_rate }} 次
            </div>
          </div>
        </div>
      </div>

      <div v-if="budgetStats.expiring_with_stock && budgetStats.expiring_with_stock.length" class="card mb-20" style="border-left: 4px solid #F59E0B;">
        <div class="card-title" style="color: #D97706;">⏰ 即将过期但仍有库存提醒</div>
        <div class="alert alert-warning mb-16">
          <div class="alert-icon">💡</div>
          <div class="alert-content">
            <div class="alert-message">以下镜片即将过期但仍有库存，请优先使用，避免重复购买造成浪费！</div>
          </div>
        </div>
        <table class="table" v-if="budgetStats.expiring_with_stock.length">
          <thead>
            <tr>
              <th>镜片</th>
              <th>度数</th>
              <th>剩余库存</th>
              <th>有效期至</th>
              <th>剩余天数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lens in budgetStats.expiring_with_stock" :key="lens.id">
              <td>
                <div class="text-bold">{{ lens.brand }}</div>
                <div class="text-xs text-light">{{ lens.model_name }}</div>
              </td>
              <td>{{ lens.power_sph }}D</td>
              <td>
                <span class="tag tag-blue">{{ lens.remaining_stock }} 片</span>
              </td>
              <td>{{ formatDate(lens.expiry_date) }}</td>
              <td>
                <span class="tag tag-yellow">{{ lens.days_until_expiry }} 天</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="budgetStats.low_comfort_high_cost && budgetStats.low_comfort_high_cost.length" class="card mb-20" style="border-left: 4px solid #F97316;">
        <div class="card-title" style="color: #EA580C;">😣 低舒适高花费预警</div>
        <div class="alert alert-warning mb-16">
          <div class="alert-icon">💸</div>
          <div class="alert-content">
            <div class="alert-message">以下镜片舒适度低但花费较高，建议考虑更换品牌。</div>
          </div>
        </div>
        <table class="table" v-if="budgetStats.low_comfort_high_cost.length">
          <thead>
            <tr>
              <th>镜片</th>
              <th>平均舒适</th>
              <th>累计花费</th>
              <th>每次成本</th>
              <th>剩余库存</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in budgetStats.low_comfort_high_cost" :key="item.lens_id">
              <td>
                <div class="text-bold">{{ item.brand }}</div>
                <div class="text-xs text-light">{{ item.model }}</div>
              </td>
              <td>
                <span class="text-danger">{{ '⭐'.repeat(Math.round(item.avg_comfort || 0)) }} {{ item.avg_comfort }}</span>
              </td>
              <td class="text-danger">¥{{ item.total_spent.toFixed(2) }}</td>
              <td>¥{{ item.cost_per_wear }}</td>
              <td>{{ item.remaining_stock }} 片</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="totalWarnings === 0" class="card empty-state">
        <div class="empty-icon">✅</div>
        <h3>暂无预警</h3>
        <p>所有镜片状态良好，继续保持！</p>
      </div>
    </div>

    <div v-if="showPurchaseModal" class="modal-overlay" @click.self="showPurchaseModal = false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ editingPurchase ? '编辑采购记录' : '添加采购记录' }}</div>
          <button class="modal-close" @click="showPurchaseModal = false">×</button>
        </div>
        <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">关联镜片 *</label>
              <select v-model="purchaseForm.lens" class="form-control">
                <option value="">请选择镜片</option>
                <option v-for="l in lensList" :key="l.id" :value="l.id">
                  {{ l.brand }} {{ l.model_name }} - {{ l.power_sph }}D
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">采购日期 *</label>
              <input v-model="purchaseForm.purchase_date" type="date" class="form-control">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">购买渠道 *</label>
              <select v-model="purchaseForm.purchase_channel" class="form-control">
                <option v-for="opt in PURCHASE_CHANNEL_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">自定义渠道</label>
              <input v-model="purchaseForm.custom_channel" class="form-control" placeholder="选择'其他'时可填写">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">采购数量(片) *</label>
              <input v-model.number="purchaseForm.quantity" type="number" class="form-control" placeholder="2">
            </div>
            <div class="form-group">
              <label class="form-label">单价(元) *</label>
              <input v-model.number="purchaseForm.unit_price" type="number" step="0.01" class="form-control" placeholder="99.00">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">折扣(%)</label>
              <input v-model.number="purchaseForm.discount" type="number" step="0.01" class="form-control" placeholder="100" value="100">
            </div>
            <div class="form-group">
              <label class="form-label">运费(元)</label>
              <input v-model.number="purchaseForm.shipping_fee" type="number" step="0.01" class="form-control" placeholder="0">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">优惠券金额(元)</label>
              <input v-model.number="purchaseForm.coupon_amount" type="number" step="0.01" class="form-control" placeholder="0">
            </div>
            <div class="form-group">
              <label class="form-label">付款状态</label>
              <select v-model="purchaseForm.payment_status" class="form-control">
                <option v-for="opt in PAYMENT_STATUS_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">订单号</label>
              <input v-model="purchaseForm.order_number" class="form-control" placeholder="可选">
            </div>
            <div class="form-group">
              <label class="form-label">预算月份</label>
              <input v-model="purchaseForm.budget_month" class="form-control" placeholder="YYYY-MM，自动根据采购日期生成">
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">备注</label>
            <textarea v-model="purchaseForm.notes" class="form-control" placeholder="可选"></textarea>
          </div>

          <div class="card mt-16" style="background: #F5F3FF;">
            <div class="card-title" style="margin-bottom: 0; color: #7C3AED;">💰 价格计算</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;">
              <div>
                <div class="text-sm text-light">商品总额</div>
                <div class="text-lg text-bold">¥{{ calculatedTotal.toFixed(2) }}</div>
              </div>
              <div>
                <div class="text-sm text-light">实付金额</div>
                <div class="text-lg text-bold text-primary">¥{{ calculatedActualPaid.toFixed(2) }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPurchaseModal = false">取消</button>
          <button class="btn btn-primary" @click="savePurchase">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getLensList } from '@/api/lens'
import { useBudgetData } from '@/composables/useTravelBudgetData'
import {
  formatDate, PURCHASE_CHANNEL_OPTIONS, PAYMENT_STATUS_OPTIONS, PAYMENT_STATUS_MAP,
  RESTOCK_SUGGESTION_TYPE_MAP, RESTOCK_SEVERITY_MAP, RESTOCK_PRIORITY_OPTIONS
} from '@/utils/constants'

const {
  blocks,
  loading,
  filterBrand,
  filterChannel,
  filterPriority,
  filterMonth,
  budgetLimit,
  activeTab,
  totalWarnings,
  brandList,
  loadAll,
  reload,
  refresh,
  loadBudgetStats: _loadBudgetStats,
  loadPurchaseRecords: _loadPurchaseRecords,
  loadAllData: _loadAllData,
  generateSuggestions: _generateSuggestions,
  markActionTaken: _markActionTaken,
  dismissSuggestion: _dismissSuggestion,
  markAllActionTaken: _markAllActionTaken,
  dismissAll: _dismissAll,
  createPurchase,
  updatePurchase,
  deletePurchase: _deletePurchase,
} = useBudgetData()

const budgetStats = computed(() => blocks.budgetStats.data.value)
const restockSuggestions = computed(() => blocks.restockSuggestions.data.value)
const purchaseRecords = computed(() => blocks.purchaseRecords.data.value)
const availableMonths = computed(() => blocks.monthList.data.value)

const lensList = ref([])

const showPurchaseModal = ref(false)
const editingPurchase = ref(null)

const defaultPurchaseForm = {
  lens: '',
  purchase_date: '',
  purchase_channel: 'taobao',
  custom_channel: '',
  quantity: 2,
  unit_price: 0,
  discount: 100,
  shipping_fee: 0,
  coupon_amount: 0,
  payment_status: 'paid',
  order_number: '',
  budget_month: '',
  notes: ''
}
const purchaseForm = ref({ ...defaultPurchaseForm })

const monthlyTrendChartRef = ref(null)
const brandPieChartRef = ref(null)
const channelPriceChartRef = ref(null)
let monthlyTrendChart = null, brandPieChart = null, channelPriceChart = null

const calculatedTotal = computed(() => {
  const discountMultiplier = (purchaseForm.value.discount || 100) / 100
  return (purchaseForm.value.unit_price || 0) * (purchaseForm.value.quantity || 0) * discountMultiplier
})

const calculatedActualPaid = computed(() => {
  return calculatedTotal.value + (purchaseForm.value.shipping_fee || 0) - (purchaseForm.value.coupon_amount || 0)
})

const resetPurchaseForm = () => {
  purchaseForm.value = { ...defaultPurchaseForm }
  purchaseForm.value.purchase_date = new Date().toISOString().split('T')[0]
}

const loadLensList = async () => {
  try {
    const res = await getLensList()
    lensList.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e) {
    console.error(e)
  }
}

watch(availableMonths, (months) => {
  if (!filterMonth.value && Array.isArray(months) && months.length) {
    filterMonth.value = months[0]
  }
}, { immediate: true })

const loadBudgetStats = async () => {
  await _loadBudgetStats()
  await nextTick()
  renderCharts()
}

const loadPurchaseRecords = async () => {
  await _loadPurchaseRecords()
}

const loadAllData = async () => {
  await _loadAllData()
  await nextTick()
  renderCharts()
}

const handleGenerateSuggestions = async () => {
  const result = await _generateSuggestions()
  if (result.ok) {
    alert('补货建议已生成！')
  } else {
    alert('生成失败，请重试')
  }
}

const generateSuggestions = handleGenerateSuggestions

const editPurchase = (record) => {
  editingPurchase.value = record
  purchaseForm.value = {
    ...record,
    lens: record.lens
  }
  showPurchaseModal.value = true
}

const savePurchase = async () => {
  if (!purchaseForm.value.lens || !purchaseForm.value.purchase_date || !purchaseForm.value.unit_price) {
    alert('请填写必填项：关联镜片、采购日期、单价')
    return
  }
  const payload = { ...purchaseForm.value }
  let result
  if (editingPurchase.value) {
    result = await updatePurchase(editingPurchase.value.id, payload)
  } else {
    result = await createPurchase(payload)
  }
  if (result.ok) {
    showPurchaseModal.value = false
    await reload('monthList')
    await loadLensList()
  } else {
    alert('保存失败，请检查表单数据')
  }
}

const handleDeletePurchase = async (id) => {
  if (!confirm('确定要删除这条采购记录吗？镜片库存会相应减少。')) return
  const result = await _deletePurchase(id)
  if (result.ok) {
    await loadLensList()
  }
}

const deletePurchase = handleDeletePurchase

const handleMarkActionTaken = async (id) => {
  await _markActionTaken(id)
}

const markActionTaken = handleMarkActionTaken

const handleDismissSuggestion = async (id) => {
  await _dismissSuggestion(id)
}

const dismissSuggestion = handleDismissSuggestion

const handleMarkAllActionTaken = async () => {
  if (!confirm('确定要将所有补货建议标记为已处理吗？')) return
  await _markAllActionTaken()
}

const markAllActionTaken = handleMarkAllActionTaken

const handleDismissAll = async () => {
  if (!confirm('确定要忽略所有补货建议吗？')) return
  await _dismissAll()
}

const dismissAll = handleDismissAll

const renderCharts = () => {
  renderMonthlyTrendChart()
  renderBrandPieChart()
  renderChannelPriceChart()
}

const renderMonthlyTrendChart = () => {
  if (!monthlyTrendChartRef.value || !budgetStats.value.monthly_trend?.length) return
  if (!monthlyTrendChart) monthlyTrendChart = echarts.init(monthlyTrendChartRef.value)
  const data = budgetStats.value.monthly_trend
  monthlyTrendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['消费金额', '采购次数'], top: 0 },
    grid: { left: 50, right: 60, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.month.slice(5) + '月'),
      axisLabel: { fontSize: 11 }
    },
    yAxis: [
      { type: 'value', name: '元' },
      { type: 'value', name: '次' }
    ],
    series: [
      {
        name: '消费金额',
        type: 'bar',
        data: data.map(d => d.total_spent),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#8B5CF6' },
            { offset: 1, color: '#A78BFA' }
          ]),
          borderRadius: [6, 6, 0, 0]
        }
      },
      {
        name: '采购次数',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(d => d.purchase_count),
        smooth: true,
        itemStyle: { color: '#F472B6' },
        lineStyle: { width: 3 }
      }
    ]
  })
}

const renderBrandPieChart = () => {
  if (!brandPieChartRef.value || !budgetStats.value.brand_spending?.length) return
  if (!brandPieChart) brandPieChart = echarts.init(brandPieChartRef.value)
  const data = budgetStats.value.brand_spending
  const colors = ['#8B5CF6', '#F472B6', '#60A5FA', '#34D399', '#FBBF24', '#F97316', '#6366F1']
  brandPieChart.setOption({
    tooltip: { trigger: 'item', formatter: p => `${p.name}<br/>¥${p.value} (${p.percent}%)` },
    legend: { type: 'scroll', bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
      label: { formatter: '{b}\n{d}%', fontSize: 11 },
      data: data.map((d, i) => ({
        name: d.brand,
        value: d.total,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  })
}

const renderChannelPriceChart = () => {
  if (!channelPriceChartRef.value || !budgetStats.value.channel_price_comparison?.length) return
  if (!channelPriceChart) channelPriceChart = echarts.init(channelPriceChartRef.value)
  const data = budgetStats.value.channel_price_comparison
  channelPriceChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['平均价格', '最低价格', '最高价格'], top: 0 },
    grid: { left: 100, right: 50, top: 40, bottom: 30 },
    xAxis: { type: 'value', name: '元' },
    yAxis: {
      type: 'category',
      data: [...data].reverse().map(d => d.channel),
      axisLabel: { fontSize: 11 }
    },
    series: [
      {
        name: '平均价格',
        type: 'bar',
        data: [...data].reverse().map(d => d.avg_price),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#34D399' },
            { offset: 1, color: '#10B981' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        label: { show: true, position: 'right', formatter: '¥{c}' },
        barWidth: 14
      },
      {
        name: '最低价格',
        type: 'bar',
        data: [...data].reverse().map(d => d.min_price),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#60A5FA' },
            { offset: 1, color: '#3B82F6' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        barWidth: 14
      },
      {
        name: '最高价格',
        type: 'bar',
        data: [...data].reverse().map(d => d.max_price),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#F472B6' },
            { offset: 1, color: '#EC4899' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        barWidth: 14
      }
    ]
  })
}

onMounted(async () => {
  await loadLensList()
  await loadAllData()
  window.addEventListener('resize', () => {
    monthlyTrendChart?.resize()
    brandPieChart?.resize()
    channelPriceChart?.resize()
  })
})
</script>

<style scoped>
.restock-suggestion {
  padding: 16px;
  border-radius: 10px;
  background: #F9FAFB;
  border-left: 4px solid #D1D5DB;
}

.restock-suggestion.critical {
  background: #FEF2F2;
  border-left-color: #EF4444;
}

.restock-suggestion.important {
  background: #FFFBEB;
  border-left-color: #F59E0B;
}

.restock-suggestion.normal {
  background: #EFF6FF;
  border-left-color: #3B82F6;
}

.warning-card {
  padding: 16px;
  border-radius: 10px;
}
</style>
