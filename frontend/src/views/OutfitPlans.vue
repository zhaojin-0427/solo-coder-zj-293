<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">💄</span>妆容搭配计划</h1>
      <button class="btn btn-primary" @click="openCreateModal">
        ➕ 新建搭配计划
      </button>
    </div>

    <div v-if="overduePlans.length" class="card mb-20" style="border-left: 4px solid #EF4444;">
      <div class="card-title" style="color: #DC2626;">
        ⚠️ 逾期未执行计划（{{ overduePlans.length }}）
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div v-for="plan in overduePlans.slice(0, 3)" :key="plan.id"
             class="flex-between"
             style="padding: 10px; background: #FEF2F2; border-radius: 6px;">
          <div>
            <span class="text-bold">{{ getSceneIcon(plan.scene_name) }} {{ plan.scene_name_display }}</span>
            <span class="text-sm text-light ml-8">{{ formatDate(plan.expected_wear_date) }}</span>
          </div>
          <div class="flex gap-8">
            <button class="btn btn-sm btn-success" @click="handleMarkCompleted(plan)">标记执行</button>
            <button class="btn btn-sm btn-ghost" @click="handleMarkCancelled(plan.id)">取消</button>
          </div>
        </div>
        <div v-if="overduePlans.length > 3" class="text-sm text-light text-center">
          还有 {{ overduePlans.length - 3 }} 条逾期计划...
        </div>
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="filterStatus" class="form-control" @change="loadPlans">
        <option v-for="opt in OUTFIT_STATUS_OPTIONS" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <select v-model="filterScene" class="form-control" @change="loadPlans">
        <option value="">全部场景</option>
        <option v-for="opt in SCENE_OPTIONS" :key="opt.value" :value="opt.value">
          {{ getSceneIcon(opt.value) }} {{ opt.label }}
        </option>
      </select>
      <select v-model="filterMakeup" class="form-control" @change="loadPlans">
        <option value="">全部妆容风格</option>
        <option v-for="opt in MAKEUP_STYLE_OPTIONS" :key="opt.value" :value="opt.value">
          {{ getMakeupIcon(opt.value) }} {{ opt.label }}
        </option>
      </select>
      <input v-model="filterDate" type="date" class="form-control" @change="loadPlans">
      <button class="btn btn-secondary" @click="showCalendar = !showCalendar">
        📅 {{ showCalendar ? '列表视图' : '日历视图' }}
      </button>
      <button class="btn btn-ghost" @click="resetFilters">重置筛选</button>
    </div>

    <div v-if="showCalendar" class="card mb-20">
      <div class="card-title">📆 搭配计划日历</div>
      <div class="calendar-nav">
        <button class="btn btn-sm btn-ghost" @click="prevMonth">←</button>
        <span class="text-bold">{{ currentMonthStr }}</span>
        <button class="btn btn-sm btn-ghost" @click="nextMonth">→</button>
      </div>
      <div class="calendar-grid">
        <div class="calendar-header">日</div>
        <div class="calendar-header">一</div>
        <div class="calendar-header">二</div>
        <div class="calendar-header">三</div>
        <div class="calendar-header">四</div>
        <div class="calendar-header">五</div>
        <div class="calendar-header">六</div>
        <div v-for="(day, idx) in calendarDays" :key="idx"
             :class="['calendar-day', {
               'other-month': day.otherMonth,
               'today': day.isToday,
               'has-plans': day.plans && day.plans.length > 0
             }]"
             @click="day.plans && day.plans.length > 0 && selectDate(day.date)">
          <div class="day-number">{{ day.day }}</div>
          <div v-if="day.plans && day.plans.length > 0" class="day-plans">
            <div v-for="p in day.plans.slice(0, 2)" :key="p.id" class="day-plan"
                 :class="`status-${p.status}`">
              <span class="text-xs">{{ getSceneIcon(p.scene_name) }} {{ p.scene_name }}</span>
            </div>
            <div v-if="day.plans.length > 2" class="text-xs text-light">
              +{{ day.plans.length - 2 }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!showCalendar && plans.length" class="plan-grid">
      <div v-for="plan in plans" :key="plan.id" class="plan-card"
           :class="{ 'plan-completed': plan.status === 'completed', 'plan-cancelled': plan.status === 'cancelled' }">
        <div class="plan-header">
          <div>
            <div class="plan-scene">
              <span class="mr-4">{{ getSceneIcon(plan.scene_name) }}</span>
              <span class="text-bold">{{ plan.scene_name_display }}</span>
            </div>
            <div class="text-sm text-light mt-4">{{ formatDate(plan.expected_wear_date) }}</div>
          </div>
          <span class="tag" :class="OUTFIT_STATUS_MAP[plan.status]?.class">
            {{ OUTFIT_STATUS_MAP[plan.status]?.icon }} {{ OUTFIT_STATUS_MAP[plan.status]?.label }}
          </span>
        </div>

        <div class="plan-details">
          <div class="detail-row">
            <span class="detail-label">妆容风格:</span>
            <span>{{ getMakeupIcon(plan.makeup_style) }} {{ plan.makeup_style_display }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">服饰色系:</span>
            <span>{{ getColorIcon(plan.clothing_color) }} {{ plan.clothing_color_display }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">光线环境:</span>
            <span>{{ plan.lighting_display }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">预计时长:</span>
            <span>{{ plan.expected_duration_hours }} 小时</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">搭配评分:</span>
            <span>{{ renderStars(plan.match_score) }}</span>
          </div>
        </div>

        <div class="plan-lenses">
          <div v-if="plan.lens" class="lens-item">
            <div class="text-xs text-light">推荐镜片</div>
            <div class="text-sm text-bold">👁️ {{ plan.lens_brand }} {{ plan.lens_model }}</div>
          </div>
          <div v-if="plan.backup_lens" class="lens-item backup">
            <div class="text-xs text-light">备选镜片</div>
            <div class="text-sm">🔄 {{ plan.backup_lens_brand }} {{ plan.backup_lens_model }}</div>
          </div>
        </div>

        <div v-if="plan.tag_labels && plan.tag_labels.length" class="plan-tags">
          <span v-for="tag in plan.tag_labels" :key="tag.key"
                class="tag tag-sm"
                :class="OUTFIT_TAG_MAP[tag.key]?.class">
            {{ OUTFIT_TAG_MAP[tag.key]?.icon }} {{ tag.label }}
          </span>
        </div>

        <div v-if="plan.status === 'completed' && plan.wear_record" class="plan-comparison">
          <div class="comparison-title">📊 执行对比</div>
          <div class="comparison-row">
            <span>预计时长: {{ plan.expected_duration_hours }}h</span>
            <span>实际: {{ plan.actual_duration_hours }}h</span>
            <span :class="plan.duration_diff > 0 ? 'text-danger' : 'text-success'">
              {{ plan.duration_diff > 0 ? '+' : '' }}{{ plan.duration_diff }}h
            </span>
          </div>
          <div class="comparison-row">
            <span>搭配评分: {{ renderStars(plan.match_score) }}</span>
            <span>舒适度: {{ renderStars(plan.actual_comfort_level) }}</span>
            <span :class="plan.comfort_diff > 0 ? 'text-success' : (plan.comfort_diff < 0 ? 'text-danger' : '')">
              {{ plan.comfort_diff > 0 ? '+' : '' }}{{ plan.comfort_diff }}
            </span>
          </div>
        </div>

        <div v-if="plan.notes" class="plan-notes">
          <div class="text-xs text-light">备注</div>
          <div class="text-sm">{{ plan.notes }}</div>
        </div>

        <div class="plan-actions">
          <template v-if="plan.status === 'pending'">
            <button class="btn btn-sm btn-success" @click="handleMarkCompleted(plan)">
              ✅ 标记执行
            </button>
            <button class="btn btn-sm btn-ghost" @click="handleMarkCancelled(plan.id)">
              ❌ 取消
            </button>
          </template>
          <template v-else-if="plan.status === 'completed' && !plan.wear_record">
            <button class="btn btn-sm btn-primary" @click="openLinkRecordModal(plan)">
              🔗 关联佩戴记录
            </button>
          </template>
          <button class="btn btn-sm btn-secondary" @click="openEditModal(plan)">
            ✏️ 编辑
          </button>
          <button class="btn btn-sm btn-danger" @click="handleDelete(plan.id)">
            🗑️ 删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="!showCalendar && !plans.length" class="card empty-state">
      <div class="empty-icon">💄</div>
      <h3>还没有搭配计划</h3>
      <p>创建您的第一个妆容搭配计划，让每次佩戴都更加完美！</p>
      <button class="btn btn-primary mt-12" @click="openCreateModal">立即创建</button>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <div class="modal-title">{{ editingPlan ? '编辑搭配计划' : '新建搭配计划' }}</div>
          <button class="modal-close" @click="showModal = false">×</button>
        </div>
        <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">场景名称 *</label>
              <select v-model="form.scene_name" class="form-control" @change="onSceneChange">
                <option v-for="opt in SCENE_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ getSceneIcon(opt.value) }} {{ opt.label }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">自定义场景</label>
              <input v-model="form.custom_scene_name" class="form-control"
                     placeholder="选择'其他'时可填写自定义场景"
                     :disabled="form.scene_name !== 'other'">
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">妆容风格 *</label>
              <select v-model="form.makeup_style" class="form-control" @change="onMakeupChange">
                <option v-for="opt in MAKEUP_STYLE_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ getMakeupIcon(opt.value) }} {{ opt.label }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">自定义妆容</label>
              <input v-model="form.custom_makeup_style" class="form-control"
                     placeholder="选择'自定义风格'时可填写"
                     :disabled="form.makeup_style !== 'custom'">
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">服饰色系 *</label>
              <select v-model="form.clothing_color" class="form-control">
                <option v-for="opt in CLOTHING_COLOR_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ getColorIcon(opt.value) }} {{ opt.label }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">光线环境 *</label>
              <select v-model="form.lighting" class="form-control">
                <option v-for="opt in LIGHTING_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">推荐镜片</label>
              <select v-model="form.lens" class="form-control">
                <option :value="null">请选择镜片</option>
                <option v-for="lens in availableLenses" :key="lens.id" :value="lens.id">
                  {{ lens.brand }} {{ lens.model_name || '经典款' }} ({{ lens.power_sph }}D)
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">备选镜片</label>
              <select v-model="form.backup_lens" class="form-control">
                <option :value="null">请选择备选镜片</option>
                <option v-for="lens in availableLenses" :key="lens.id" :value="lens.id">
                  {{ lens.brand }} {{ lens.model_name || '经典款' }} ({{ lens.power_sph }}D)
                </option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">预计佩戴日期 *</label>
              <input v-model="form.expected_wear_date" type="date" class="form-control">
            </div>
            <div class="form-group">
              <label class="form-label">预计佩戴时长(小时) *</label>
              <input v-model.number="form.expected_duration_hours" type="number"
                     class="form-control" min="0.5" max="24" step="0.5">
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">搭配评分 (1-5)</label>
            <div class="rating-input">
              <span v-for="s in 5" :key="s"
                    class="rating-star"
                    :class="{ active: s <= form.match_score }"
                    @click="form.match_score = s">
                {{ s <= form.match_score ? '⭐' : '☆' }}
              </span>
              <span class="ml-12 text-light">{{ form.match_score }} 分</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">备注</label>
            <textarea v-model="form.notes" class="form-control" rows="3"
                      placeholder="记录妆容要点、搭配灵感等..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="handleSubmit" :disabled="!isFormValid">
            {{ editingPlan ? '保存修改' : '创建计划' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showLinkModal" class="modal-overlay" @click.self="showLinkModal = false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">关联佩戴记录</div>
          <button class="modal-close" @click="showLinkModal = false">×</button>
        </div>
        <div class="modal-body">
          <p class="text-sm text-light mb-12">选择一条佩戴记录与此搭配计划关联：</p>
          <div v-if="availableRecords.length" class="record-list">
            <div v-for="record in availableRecords" :key="record.id"
                 :class="['record-item', { selected: selectedRecordId === record.id }]"
                 @click="selectedRecordId = record.id">
              <div>
                <div class="text-bold">{{ formatDate(record.wear_date) }}</div>
                <div class="text-sm text-light">
                  {{ record.lens_brand }} · {{ record.duration_hours }}h · {{ renderStars(record.comfort_level) }}
                </div>
              </div>
              <div v-if="selectedRecordId === record.id" class="text-success">✓</div>
            </div>
          </div>
          <div v-else class="empty-state" style="padding: 20px;">
            <p class="text-light">暂无可用的佩戴记录</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showLinkModal = false">取消</button>
          <button class="btn btn-primary" @click="handleLinkRecord" :disabled="!selectedRecordId">
            确认关联
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  getOutfitPlanList, createOutfitPlan, updateOutfitPlan, deleteOutfitPlan,
  markPlanCompleted, markPlanCancelled, linkWearRecord,
  getUpcomingPlans, getOverduePlans, getCalendarData, getOutfitPlanStats
} from '@/api/outfitPlan'

const route = useRoute()
import { getLensList } from '@/api/lens'
import { getRecordList } from '@/api/record'
import {
  formatDate, renderStars,
  SCENE_OPTIONS, MAKEUP_STYLE_OPTIONS, CLOTHING_COLOR_OPTIONS, LIGHTING_OPTIONS,
  OUTFIT_STATUS_MAP, OUTFIT_STATUS_OPTIONS, OUTFIT_TAG_MAP,
  SCENE_ICON_MAP, MAKEUP_ICON_MAP, COLOR_ICON_MAP
} from '@/utils/constants'

const plans = ref([])
const overduePlans = ref([])
const availableLenses = ref([])
const availableRecords = ref([])
const allRecords = ref([])

const filterStatus = ref('')
const filterScene = ref('')
const filterMakeup = ref('')
const filterDate = ref('')

const showModal = ref(false)
const showLinkModal = ref(false)
const editingPlan = ref(null)
const linkingPlan = ref(null)
const selectedRecordId = ref(null)

const showCalendar = ref(false)
const currentMonth = ref(new Date())
const calendarDays = ref([])
const calendarData = ref({})

const form = ref({
  scene_name: 'daily',
  custom_scene_name: '',
  makeup_style: 'natural',
  custom_makeup_style: '',
  clothing_color: 'neutral',
  lighting: 'natural_day',
  lens: null,
  backup_lens: null,
  expected_wear_date: new Date().toISOString().split('T')[0],
  expected_duration_hours: 8,
  match_score: 4,
  notes: ''
})

const currentMonthStr = computed(() => {
  const d = currentMonth.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月`
})

const isFormValid = computed(() => {
  return form.value.scene_name &&
         form.value.makeup_style &&
         form.value.clothing_color &&
         form.value.lighting &&
         form.value.expected_wear_date &&
         form.value.expected_duration_hours > 0 &&
         form.value.match_score >= 1
})

const getSceneIcon = (scene) => SCENE_ICON_MAP[scene] || '📌'
const getMakeupIcon = (style) => MAKEUP_ICON_MAP[style] || '🎨'
const getColorIcon = (color) => COLOR_ICON_MAP[color] || '⚪'

const onSceneChange = () => {
  if (form.value.scene_name !== 'other') {
    form.value.custom_scene_name = ''
  }
}

const onMakeupChange = () => {
  if (form.value.makeup_style !== 'custom') {
    form.value.custom_makeup_style = ''
  }
}

const loadPlans = async () => {
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterScene.value) params.scene = filterScene.value
    if (filterMakeup.value) params.makeup_style = filterMakeup.value
    if (filterDate.value) params.expected_date = filterDate.value

    const data = await getOutfitPlanList(params)
    plans.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    console.error(e)
  }
}

const loadOverduePlans = async () => {
  try {
    const data = await getOverduePlans()
    overduePlans.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    console.error(e)
  }
}

const loadLenses = async () => {
  try {
    const data = await getLensList()
    availableLenses.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    console.error(e)
  }
}

const loadRecords = async () => {
  try {
    const data = await getRecordList({ page_size: 100 })
    allRecords.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    console.error(e)
  }
}

const loadCalendarData = async () => {
  try {
    const year = currentMonth.value.getFullYear()
    const month = currentMonth.value.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)

    const data = await getCalendarData({
      date_from: firstDay.toISOString().split('T')[0],
      date_to: lastDay.toISOString().split('T')[0]
    })
    calendarData.value = data || {}
    generateCalendarDays()
  } catch (e) {
    console.error(e)
  }
}

const generateCalendarDays = () => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const today = new Date()

  const days = []
  const startPadding = firstDay.getDay()
  const prevMonthLastDay = new Date(year, month, 0).getDate()

  for (let i = startPadding - 1; i >= 0; i--) {
    const date = new Date(year, month - 1, prevMonthLastDay - i)
    days.push({
      day: prevMonthLastDay - i,
      date: date.toISOString().split('T')[0],
      otherMonth: true,
      isToday: false,
      plans: calendarData.value[date.toISOString().split('T')[0]] || []
    })
  }

  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = new Date(year, month, i)
    const dateStr = date.toISOString().split('T')[0]
    days.push({
      day: i,
      date: dateStr,
      otherMonth: false,
      isToday: date.toDateString() === today.toDateString(),
      plans: calendarData.value[dateStr] || []
    })
  }

  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = new Date(year, month + 1, i)
    days.push({
      day: i,
      date: date.toISOString().split('T')[0],
      otherMonth: true,
      isToday: false,
      plans: calendarData.value[date.toISOString().split('T')[0]] || []
    })
  }

  calendarDays.value = days
}

const prevMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
  loadCalendarData()
}

const nextMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
  loadCalendarData()
}

const selectDate = (dateStr) => {
  filterDate.value = dateStr
  showCalendar.value = false
  loadPlans()
}

const resetFilters = () => {
  filterStatus.value = ''
  filterScene.value = ''
  filterMakeup.value = ''
  filterDate.value = ''
  loadPlans()
}

const openCreateModal = (preselectedLensId = null) => {
  editingPlan.value = null
  form.value = {
    scene_name: 'daily',
    custom_scene_name: '',
    makeup_style: 'natural',
    custom_makeup_style: '',
    clothing_color: 'neutral',
    lighting: 'natural_day',
    lens: preselectedLensId || null,
    backup_lens: null,
    expected_wear_date: new Date().toISOString().split('T')[0],
    expected_duration_hours: 8,
    match_score: 4,
    notes: ''
  }
  showModal.value = true
}

const openEditModal = (plan) => {
  editingPlan.value = plan
  form.value = {
    scene_name: plan.scene_name,
    custom_scene_name: plan.custom_scene_name || '',
    makeup_style: plan.makeup_style,
    custom_makeup_style: plan.custom_makeup_style || '',
    clothing_color: plan.clothing_color,
    lighting: plan.lighting,
    lens: plan.lens,
    backup_lens: plan.backup_lens,
    expected_wear_date: plan.expected_wear_date,
    expected_duration_hours: plan.expected_duration_hours,
    match_score: plan.match_score,
    notes: plan.notes || ''
  }
  showModal.value = true
}

const handleSubmit = async () => {
  try {
    const submitData = { ...form.value }
    if (editingPlan.value) {
      await updateOutfitPlan(editingPlan.value.id, submitData)
    } else {
      await createOutfitPlan(submitData)
    }
    showModal.value = false
    loadPlans()
    loadOverduePlans()
    loadCalendarData()
  } catch (e) {
    console.error(e)
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定要删除这个搭配计划吗？')) return
  try {
    await deleteOutfitPlan(id)
    loadPlans()
    loadOverduePlans()
    loadCalendarData()
  } catch (e) {
    console.error(e)
  }
}

const handleMarkCompleted = async (plan) => {
  if (!confirm('确定要标记此计划为已执行吗？')) return
  try {
    await markPlanCompleted(plan.id)
    loadPlans()
    loadOverduePlans()
    loadCalendarData()
  } catch (e) {
    console.error(e)
    const errorMsg = e?.response?.data?.error
      || e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join('; ')
      || '操作失败，请重试'
    alert(`标记失败：${errorMsg}`)
  }
}

const handleMarkCancelled = async (id) => {
  if (!confirm('确定要取消这个计划吗？')) return
  try {
    await markPlanCancelled(id)
    loadPlans()
    loadOverduePlans()
    loadCalendarData()
  } catch (e) {
    console.error(e)
  }
}

const openLinkRecordModal = (plan) => {
  linkingPlan.value = plan
  selectedRecordId.value = null
  availableRecords.value = allRecords.value.filter(r => !r.outfit_plan)
  showLinkModal.value = true
}

const handleLinkRecord = async () => {
  if (!linkingPlan.value || !selectedRecordId.value) return
  try {
    await linkWearRecord(linkingPlan.value.id, selectedRecordId.value)
    showLinkModal.value = false
    loadPlans()
  } catch (e) {
    console.error(e)
    const errorMsg = e?.response?.data?.error
      || e?.response?.data?.detail
      || Object.values(e?.response?.data || {}).flat().join('; ')
      || '关联失败，请重试'
    alert(`关联失败：${errorMsg}`)
  }
}

const loadAll = async () => {
  await Promise.all([
    loadPlans(),
    loadOverduePlans(),
    loadLenses(),
    loadRecords(),
    loadCalendarData()
  ])
}

onMounted(() => {
  loadAll().then(() => {
    const lensId = route.query.lens_id
    if (lensId) {
      openCreateModal(Number(lensId))
    }
  })
})

defineExpose({
  openCreateModal
})
</script>

<style scoped>
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.plan-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #eee;
  transition: all 0.2s;
}

.plan-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.plan-completed {
  opacity: 0.75;
  background: linear-gradient(135deg, #F0FDF4, #FFFFFF);
}

.plan-cancelled {
  opacity: 0.6;
  background: #F9FAFB;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.plan-scene {
  font-size: 16px;
}

.plan-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.detail-label {
  color: #6B7280;
  font-weight: 500;
}

.plan-lenses {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px;
  background: #F9FAFB;
  border-radius: 8px;
}

.lens-item {
  flex: 1;
}

.lens-item.backup {
  opacity: 0.8;
}

.plan-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.tag-sm {
  font-size: 11px;
  padding: 2px 8px;
}

.plan-comparison {
  background: linear-gradient(135deg, #EEF2FF, #F5F3FF);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.comparison-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
  color: #4F46E5;
}

.comparison-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 2px 0;
}

.plan-notes {
  background: #FFFBEB;
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 3px solid #F59E0B;
}

.plan-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.rating-input {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-star {
  font-size: 24px;
  cursor: pointer;
  opacity: 0.5;
  transition: all 0.2s;
}

.rating-star.active {
  opacity: 1;
  transform: scale(1.1);
}

.rating-star:hover {
  transform: scale(1.15);
}

.calendar-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
  font-size: 16px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  background: #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.calendar-header {
  background: #F3F4F6;
  padding: 8px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
  color: #6B7280;
}

.calendar-day {
  background: #fff;
  min-height: 80px;
  padding: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.calendar-day:hover {
  background: #F9FAFB;
}

.calendar-day.other-month {
  background: #F9FAFB;
  color: #D1D5DB;
}

.calendar-day.today {
  background: #EEF2FF;
}

.calendar-day.has-plans {
  background: linear-gradient(135deg, #FEF3C7, #FEF9C3);
}

.day-number {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
}

.day-plans {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.day-plan {
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.day-plan.status-pending {
  background: #FEF3C7;
  color: #92400E;
}

.day-plan.status-completed {
  background: #D1FAE5;
  color: #065F46;
}

.day-plan.status-cancelled {
  background: #E5E7EB;
  color: #6B7280;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.record-item {
  padding: 12px;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
}

.record-item:hover {
  border-color: #8B5CF6;
}

.record-item.selected {
  border-color: #8B5CF6;
  background: #F5F3FF;
}

.modal-lg {
  max-width: 700px;
}
</style>
