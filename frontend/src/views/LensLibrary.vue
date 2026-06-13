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
      <input v-model="filterBrand" class="form-control" placeholder="🔍 搜索品牌..." @input="debouncedLoad">
    </div>

    <div v-if="lenses.length" class="lens-grid">
      <div v-for="lens in lenses" :key="lens.id"
           class="lens-card"
           :class="{ expired: lens.is_expired, expiring: !lens.is_expired && lens.days_until_expiry <= 30 }">
        <div class="lens-header">
          <div>
            <div class="lens-brand">{{ lens.brand }}</div>
            <div class="lens-model">{{ lens.model_name || '经典款' }} {{ lens.color ? '· ' + lens.color : '' }}</div>
            <div class="mt-8 flex-wrap gap-8" style="display: flex;">
              <span class="tag" :class="STATUS_MAP[lens.status]?.class">{{ STATUS_MAP[lens.status]?.label }}</span>
              <span class="tag" :class="PURPOSE_MAP[lens.purpose]?.class">
                {{ PURPOSE_MAP[lens.purpose]?.icon }} {{ PURPOSE_MAP[lens.purpose]?.label }}
              </span>
              <span v-if="lens.is_expired" class="tag tag-red">已过期</span>
              <span v-else-if="lens.days_until_expiry <= 30" class="tag tag-yellow">
                剩{{ lens.days_until_expiry }}天
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

        <div class="lens-footer">
          <div class="text-sm text-light">
            建议日戴≤{{ lens.daily_wear_limit }}h
          </div>
          <div class="lens-actions">
            <button v-if="lens.status === 'unopened'" class="btn btn-sm btn-success" @click="handleOpen(lens.id)">开封</button>
            <button v-if="lens.status === 'opened'" class="btn btn-sm btn-secondary" @click="handleUsedUp(lens.id)">用完</button>
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
        <div class="modal-body">
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
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="handleSave">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getLensList, createLens, updateLens, deleteLens, openLens, markLensUsedUp
} from '@/api/lens'
import {
  STATUS_MAP, PURPOSE_MAP, STATUS_OPTIONS, PURPOSE_OPTIONS, formatDate, renderStars
} from '@/utils/constants'

const lenses = ref([])
const showModal = ref(false)
const editingLens = ref(null)
const filterStatus = ref('')
const filterPurpose = ref('')
const filterBrand = ref('')

const defaultForm = {
  brand: '', model_name: '', color: '',
  power_sph: 0, power_cyl: 0,
  water_content: 38, base_curve: 8.6, diameter: 14.0,
  purchase_date: '', expiry_date: '', open_date: '',
  purpose: 'daily', status: 'unopened',
  pair_count: 2, used_count: 0, notes: ''
}
const form = ref({ ...defaultForm })

const resetForm = () => {
  form.value = { ...defaultForm }
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
    if (filterBrand.value) params.brand = filterBrand.value
    const res = await getLensList(params)
    lenses.value = Array.isArray(res) ? res : (res.results || [])
  } catch (e) {
    console.error(e)
  }
}

const openEdit = (lens) => {
  editingLens.value = lens
  form.value = {
    ...lens,
    open_date: lens.open_date || '',
  }
  showModal.value = true
}

const handleSave = async () => {
  if (!form.value.brand || !form.value.purchase_date || !form.value.expiry_date) {
    alert('请填写必填项：品牌、购买日期、有效期')
    return
  }
  try {
    if (editingLens.value) {
      await updateLens(editingLens.value.id, form.value)
    } else {
      await createLens(form.value)
    }
    showModal.value = false
    loadLenses()
  } catch (e) {
    console.error(e)
    alert('保存失败')
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

onMounted(loadLenses)
</script>
