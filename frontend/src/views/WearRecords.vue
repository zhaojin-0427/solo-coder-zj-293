<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">📝</span>佩戴记录</h1>
      <button class="btn btn-primary" @click="showModal = true; editingRecord = null; resetForm()">
        ➕ 添加记录
      </button>
    </div>

    <div v-if="todayWarning" :class="['alert', alertClass]">
      <div class="alert-icon">{{ alertIcon }}</div>
      <div class="alert-content">
        <div class="alert-title">今日佩戴提醒</div>
        <div class="alert-message">{{ todayWarning.message }}</div>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-label">今日累计</div>
        <div class="stat-value small">{{ todayWarning?.total_hours || 0 }} 小时</div>
      </div>
      <div class="stat-card pink">
        <div class="stat-label">今日佩戴次数</div>
        <div class="stat-value small">{{ todayWarning?.record_count || 0 }} 次</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">总记录数</div>
        <div class="stat-value small">{{ totalRecords }} 次</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-label">总佩戴时长</div>
        <div class="stat-value small">{{ totalHours }} 小时</div>
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="filterLens" class="form-control" @change="loadRecords">
        <option value="">全部镜片</option>
        <option v-for="l in allLenses" :key="l.id" :value="l.id">
          {{ l.brand }} {{ l.model_name }} ({{ l.power_sph }}D)
        </option>
      </select>
      <input v-model="filterDateFrom" type="date" class="form-control" @change="loadRecords">
      <span class="text-light">至</span>
      <input v-model="filterDateTo" type="date" class="form-control" @change="loadRecords">
      <button class="btn btn-secondary" @click="clearFilters">清除筛选</button>
    </div>

    <div class="card">
      <div class="nav-tabs">
        <button class="nav-tab" :class="{ active: activeTab === 'table' }" @click="activeTab = 'table'">
          📋 列表视图
        </button>
        <button class="nav-tab" :class="{ active: activeTab === 'daily' }" @click="activeTab = 'daily'">
          📆 每日汇总
        </button>
        <button class="nav-tab" :class="{ active: activeTab === 'chart' }" @click="activeTab = 'chart'">
          📊 时长图表
        </button>
      </div>

      <div v-if="activeTab === 'table'">
        <table class="table" v-if="records.length">
          <thead>
            <tr>
              <th>日期</th>
              <th>镜片</th>
              <th>时长</th>
              <th>舒适度</th>
              <th>眼部反应</th>
              <th>备注</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ formatDate(r.wear_date) }}</td>
              <td>
                <div class="text-bold text-sm">{{ r.lens_brand }}</div>
                <div class="text-xs text-light">{{ r.lens_model || '' }} {{ r.lens_color || '' }}</div>
              </td>
              <td>
                <div class="text-bold">{{ r.duration_hours }}h</div>
                <div class="progress-bar" style="width: 80px;">
                  <div
                    class="progress"
                    :class="r.duration_hours > 10 ? 'danger' : r.duration_hours > 8 ? 'warning' : 'success'"
                    :style="{ width: Math.min(100, r.duration_hours / 12 * 100) + '%' }"
                  ></div>
                </div>
              </td>
              <td>
                <div class="rating">
                  <span v-for="i in 5" :key="i" class="star" :class="{ active: i <= r.comfort_level }">★</span>
                </div>
                <div class="text-xs text-light">{{ COMFORT_LABELS[r.comfort_level] }}</div>
              </td>
              <td>
                <span class="tag" :class="REACTION_MAP[r.eye_reaction]?.class">
                  {{ REACTION_MAP[r.eye_reaction]?.label }}
                </span>
              </td>
              <td class="text-sm text-light" style="max-width: 200px;">{{ r.notes || '-' }}</td>
              <td>
                <button class="btn btn-link btn-sm" @click="openEdit(r)">编辑</button>
                <button class="btn btn-link btn-sm text-danger" @click="handleDelete(r.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">📝</div>
          <h3>暂无佩戴记录</h3>
          <p>点击右上角「添加记录」开始追踪您的佩戴情况</p>
        </div>
      </div>

      <div v-if="activeTab === 'daily'">
        <table class="table" v-if="dailyTotals.length">
          <thead>
            <tr>
              <th>日期</th>
              <th>佩戴次数</th>
              <th>总时长</th>
              <th>平均舒适度</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in dailyTotals" :key="d.date">
              <td>{{ formatDate(d.date) }}</td>
              <td>{{ d.count }} 次</td>
              <td class="text-bold">{{ Number(d.total_hours).toFixed(1) }}h</td>
              <td>{{ d.avg_comfort ? '⭐'.repeat(Math.round(Number(d.avg_comfort))) : '-' }}</td>
              <td>
                <span v-if="d.total_hours > 10" class="tag tag-red">严重超时</span>
                <span v-else-if="d.total_hours > 8" class="tag tag-yellow">接近上限</span>
                <span v-else class="tag tag-green">正常</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state" style="padding: 40px;">
          <div class="empty-icon">📅</div>
          <p>暂无汇总数据</p>
        </div>
      </div>

      <div v-if="activeTab === 'chart'">
        <div class="chart-container" ref="hoursChartRef"></div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ editingRecord ? '编辑记录' : '添加佩戴记录' }}</div>
          <button class="modal-close" @click="showModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">选择镜片 *</label>
            <select v-model="form.lens" class="form-control">
              <option value="">请选择镜片...</option>
              <option v-for="l in availableLenses" :key="l.id" :value="l.id">
                {{ l.brand }} {{ l.model_name }} - {{ l.power_sph }}D
                ({{ STATUS_MAP[l.status]?.label }})
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">佩戴日期 *</label>
              <input v-model="form.wear_date" type="date" class="form-control">
            </div>
            <div class="form-group">
              <label class="form-label">佩戴时长(小时) *</label>
              <input v-model.number="form.duration_hours" type="number" step="0.5" min="0" class="form-control" placeholder="8">
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">舒适度评分 *</label>
            <div class="flex-between gap-12" style="display: flex;">
              <div v-for="i in 5" :key="i"
                   @click="form.comfort_level = i"
                   :style="{
                     flex: 1, padding: '12px', textAlign: 'center',
                     borderRadius: '10px', cursor: 'pointer', transition: 'all 0.2s',
                     background: form.comfort_level >= i ? 'linear-gradient(135deg, #FEF3C7, #FDE68A)' : '#F9FAFB',
                     border: form.comfort_level >= i ? '2px solid #F59E0B' : '2px solid transparent',
                     transform: form.comfort_level >= i ? 'translateY(-2px)' : 'none'
                   }">
                <div style="font-size: 24px;">{{ '⭐'.repeat(i) }}</div>
                <div class="text-xs mt-8" :class="getComfortClass(i)">{{ COMFORT_LABELS[i] }}</div>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">眼部反应</label>
            <select v-model="form.eye_reaction" class="form-control">
              <option v-for="opt in REACTION_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">备注</label>
            <textarea v-model="form.notes" class="form-control" placeholder="记录当天的感受、环境等..."></textarea>
          </div>
          <div v-if="form.duration_hours > 8" class="alert alert-warning">
            <div class="alert-icon">⚠️</div>
            <div class="alert-message">单次佩戴时长超过 8 小时，建议适当减少佩戴时间，让眼睛休息。</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="handleSave">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getLensList } from '@/api/lens'
import {
  getRecordList, createRecord, updateRecord, deleteRecord, getDailyTotals, getTodayWarning
} from '@/api/record'
import {
  STATUS_MAP, REACTION_MAP, STATUS_OPTIONS, REACTION_OPTIONS, PURPOSE_OPTIONS,
  COMFORT_LABELS, formatDate, todayString, getComfortClass
} from '@/utils/constants'

const records = ref([])
const allLenses = ref([])
const dailyTotals = ref([])
const todayWarning = ref(null)
const showModal = ref(false)
const editingRecord = ref(null)
const activeTab = ref('table')
const filterLens = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const hoursChartRef = ref(null)
let chartInstance = null

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

const totalRecords = computed(() => records.value.length)
const totalHours = computed(() => records.value.reduce((s, r) => s + r.duration_hours, 0).toFixed(1))

const availableLenses = computed(() => {
  return allLenses.value.filter(l => l.status !== 'used_up' && l.status !== 'expired')
})

const defaultForm = {
  lens: '', wear_date: todayString(), duration_hours: 8,
  comfort_level: 4, eye_reaction: 'none', notes: ''
}
const form = ref({ ...defaultForm })

const resetForm = () => {
  form.value = { ...defaultForm }
}

const clearFilters = () => {
  filterLens.value = ''
  filterDateFrom.value = ''
  filterDateTo.value = ''
  loadRecords()
}

const loadRecords = async () => {
  try {
    const params = {}
    if (filterLens.value) params.lens_id = filterLens.value
    if (filterDateFrom.value) params.date_from = filterDateFrom.value
    if (filterDateTo.value) params.date_to = filterDateTo.value
    const res = await getRecordList(params)
    records.value = Array.isArray(res) ? res : (res.results || [])

    const dailyParams = {}
    if (filterDateFrom.value) dailyParams.date_from = filterDateFrom.value
    if (filterDateTo.value) dailyParams.date_to = filterDateTo.value
    dailyTotals.value = await getDailyTotals(dailyParams)

    await nextTick()
    if (activeTab.value === 'chart') renderChart()
  } catch (e) {
    console.error(e)
  }
}

const loadLenses = async () => {
  try {
    const res = await getLensList()
    allLenses.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e) {
    console.error(e)
  }
}

const loadWarning = async () => {
  try {
    todayWarning.value = await getTodayWarning()
  } catch (e) {
    console.error(e)
  }
}

const renderChart = () => {
  if (!hoursChartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(hoursChartRef.value)
  }
  const data = [...dailyTotals.value].reverse()
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date ? d.date.slice(5) : ''),
      axisLabel: { fontSize: 11, rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: '小时',
      min: 0,
      max: 14
    },
    series: [{
      type: 'bar',
      data: data.map(d => Number(d.total_hours || 0)),
      itemStyle: {
        color: (params) => {
          const v = params.value
          if (v > 10) return '#EF4444'
          if (v > 8) return '#F59E0B'
          return '#8B5CF6'
        },
        borderRadius: [6, 6, 0, 0]
      },
      markLine: {
        data: [
          { yAxis: 8, name: '建议上限', lineStyle: { color: '#F59E0B', type: 'dashed' } },
          { yAxis: 12, name: '危险阈值', lineStyle: { color: '#EF4444', type: 'dashed' } }
        ],
        label: { formatter: '{b}' }
      }
    }]
  })
}

watch(activeTab, (val) => {
  if (val === 'chart') {
    nextTick(renderChart)
  }
})

const openEdit = (record) => {
  editingRecord.value = record
  form.value = {
    lens: record.lens,
    wear_date: record.wear_date,
    duration_hours: record.duration_hours,
    comfort_level: record.comfort_level,
    eye_reaction: record.eye_reaction,
    notes: record.notes || ''
  }
  showModal.value = true
}

const handleSave = async () => {
  if (!form.value.lens || !form.value.wear_date || !form.value.duration_hours) {
    alert('请填写必填项：镜片、日期、时长')
    return
  }
  try {
    const payload = {
      lens: form.value.lens,
      wear_date: form.value.wear_date,
      duration_hours: form.value.duration_hours,
      comfort_level: form.value.comfort_level,
      eye_reaction: form.value.eye_reaction,
      notes: form.value.notes
    }
    if (editingRecord.value) {
      await updateRecord(editingRecord.value.id, payload)
    } else {
      await createRecord(payload)
    }
    showModal.value = false
    loadRecords()
    loadWarning()
  } catch (e) {
    console.error(e)
    alert('保存失败')
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定删除这条记录？')) return
  try {
    await deleteRecord(id)
    loadRecords()
    loadWarning()
  } catch (e) {
    console.error(e)
  }
}

onMounted(async () => {
  await Promise.all([loadRecords(), loadLenses(), loadWarning()])
  window.addEventListener('resize', () => chartInstance?.resize())
})
</script>
