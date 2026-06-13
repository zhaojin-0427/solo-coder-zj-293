<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title"><span class="icon">⏰</span>过期预警</h1>
    </div>

    <div class="mb-16" style="display: flex; gap: 16px; flex-wrap: wrap; align-items: center;">
      <div>
        <label class="form-label text-sm" style="margin-bottom: 4px; display: block;">即将过期阈值</label>
        <select v-model="warningDays" class="form-control" style="width: auto;" @change="loadData">
          <option :value="7">7天内</option>
          <option :value="14">14天内</option>
          <option :value="30">30天内</option>
          <option :value="60">60天内</option>
          <option :value="90">90天内</option>
        </select>
      </div>
      <div>
        <label class="form-label text-sm" style="margin-bottom: 4px; display: block;">长期未使用阈值</label>
        <select v-model="unusedDays" class="form-control" style="width: auto;" @change="loadData">
          <option :value="15">超过15天</option>
          <option :value="30">超过30天</option>
          <option :value="60">超过60天</option>
          <option :value="90">超过90天</option>
          <option :value="180">超过180天</option>
        </select>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card" style="background: linear-gradient(135deg, #FEE2E2, #FECDD3);">
        <div class="stat-label">🚨 已过期</div>
        <div class="stat-value" style="color: #DC2626;">{{ expiredLenses.length }} 副</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #FEF3C7, #FEF9C3);">
        <div class="stat-label">⚠️ {{ warningDays }}天内即将过期</div>
        <div class="stat-value" style="color: #D97706;">{{ soonLenses.length }} 副</div>
      </div>
      <div class="stat-card" style="background: linear-gradient(135deg, #DBEAFE, #BFDBFE);">
        <div class="stat-label">🔔 长期未使用(>{{ unusedDays }}天)</div>
        <div class="stat-value" style="color: #2563EB;">{{ unusedLenses.length }} 副</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">✅ 状态正常</div>
        <div class="stat-value small">{{ normalCount }} 副</div>
      </div>
    </div>

    <div class="card mb-20" v-if="expiredLenses.length">
      <div class="card-title" style="color: var(--danger);">
        🚨 已过期镜片（请立即停止使用）
      </div>
      <div class="lens-grid">
        <div v-for="lens in expiredLenses" :key="lens.id" class="lens-card expired">
          <div class="lens-header">
            <div>
              <div class="lens-brand">{{ lens.brand }}</div>
              <div class="lens-model">{{ lens.model_name || '-' }} · {{ lens.power_sph }}D</div>
              <div class="mt-8">
                <span class="tag tag-red">已过期 {{ Math.abs(lens.days_until_expiry) }} 天</span>
                <span class="tag ml-8" :class="STATUS_MAP[lens.status]?.class">
                  {{ STATUS_MAP[lens.status]?.label }}
                </span>
              </div>
            </div>
          </div>
          <div class="lens-specs">
            <div>
              <div class="spec">有效期至</div>
              <div class="spec-value text-danger">{{ formatDate(lens.expiry_date) }}</div>
            </div>
            <div>
              <div class="spec">含水量</div>
              <div class="spec-value">{{ lens.water_content }}%</div>
            </div>
            <div>
              <div class="spec">累计佩戴</div>
              <div class="spec-value">{{ lens.total_wear_hours || 0 }}h</div>
            </div>
            <div>
              <div class="spec">最近佩戴</div>
              <div class="spec-value">{{ formatDate(lens.last_wear_date) || '从未' }}</div>
            </div>
          </div>
          <div class="lens-footer">
            <div class="text-sm text-danger">⚠️ 过期镜片请勿佩戴，可能导致眼部感染</div>
            <button class="btn btn-sm btn-danger" @click="markExpired(lens.id)">标记已过期</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-20" v-if="soonLenses.length">
      <div class="card-title" style="color: var(--warning);">
        ⚠️ {{ warningDays }}天内即将过期（建议尽快使用）
      </div>
      <div class="lens-grid">
        <div v-for="lens in soonLenses" :key="lens.id" class="lens-card expiring">
          <div class="lens-header">
            <div>
              <div class="lens-brand">{{ lens.brand }}</div>
              <div class="lens-model">{{ lens.model_name || '-' }} · {{ lens.power_sph }}D</div>
              <div class="mt-8">
                <span class="tag tag-yellow">剩 {{ lens.days_until_expiry }} 天</span>
                <span class="tag ml-8" :class="PURPOSE_MAP[lens.purpose]?.class">
                  {{ PURPOSE_MAP[lens.purpose]?.icon }} {{ PURPOSE_MAP[lens.purpose]?.label }}
                </span>
              </div>
            </div>
          </div>
          <div class="progress-bar">
            <div
              class="progress warning"
              :style="{ width: (100 - lens.days_until_expiry / warningDays * 100) + '%' }"
            ></div>
          </div>
          <div class="lens-specs">
            <div>
              <div class="spec">有效期至</div>
              <div class="spec-value text-warning">{{ formatDate(lens.expiry_date) }}</div>
            </div>
            <div>
              <div class="spec">购买日期</div>
              <div class="spec-value">{{ formatDate(lens.purchase_date) }}</div>
            </div>
            <div>
              <div class="spec">状态</div>
              <div class="spec-value">
                <span class="tag" :class="STATUS_MAP[lens.status]?.class">{{ STATUS_MAP[lens.status]?.label }}</span>
              </div>
            </div>
            <div>
              <div class="spec">累计佩戴</div>
              <div class="spec-value">{{ lens.total_wear_hours || 0 }}h</div>
            </div>
          </div>
          <div class="lens-footer">
            <div class="text-sm text-light">建议日戴≤{{ lens.daily_wear_limit }}h</div>
            <div class="lens-actions">
              <button v-if="lens.status === 'unopened'" class="btn btn-sm btn-success" @click="handleOpen(lens.id)">开封</button>
              <router-link :to="'/records'" class="btn btn-sm btn-primary">记录佩戴</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-20" v-if="unusedLenses.length">
      <div class="card-title" style="color: var(--info);">
        🔔 长期未使用镜片（>90天）
      </div>
      <table class="table">
        <thead>
          <tr>
            <th>镜片</th>
            <th>参数</th>
            <th>上次佩戴</th>
            <th>未使用天数</th>
            <th>有效期至</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lens in unusedLenses" :key="lens.id">
            <td>
              <div class="text-bold">{{ lens.brand }} {{ lens.model_name }}</div>
              <span class="tag tag-gray mt-8">{{ STATUS_MAP[lens.status]?.label }}</span>
            </td>
            <td>
              {{ lens.power_sph }}D · {{ lens.water_content }}% · {{ lens.base_curve }}mm
            </td>
            <td>{{ formatDate(lens.last_wear_date) || '从未佩戴' }}</td>
            <td>
              <span class="tag tag-blue">超过 {{ getUnusedDays(lens) }} 天</span>
            </td>
            <td :class="lens.is_expired ? 'text-danger' : ''">
              {{ formatDate(lens.expiry_date) }}
            </td>
            <td>
              <router-link :to="'/records'" class="btn btn-link btn-sm">去佩戴</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-if="!expiredLenses.length && !soonLenses.length && !unusedLenses.length">
      <div class="empty-state">
        <div class="empty-icon">🎉</div>
        <h3>太棒了！暂无任何预警</h3>
        <p>所有镜片状态正常，继续保持良好的护眼习惯哦~</p>
      </div>
    </div>

    <div class="alert alert-info mt-20">
      <div class="alert-icon">💡</div>
      <div class="alert-content">
        <div class="alert-title">镜片保存小贴士</div>
        <div class="alert-message" style="font-size: 13px; line-height: 1.8;">
          • 镜片应保存在阴凉干燥处，避免阳光直射<br>
          • 护理液开封后一般3个月内用完，注意护理液自身有效期<br>
          • 即使未过期，开封后也建议按产品说明周期更换（如月抛30天内）<br>
          • 佩戴前请检查镜片是否有破损、沉淀物
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getExpiringLenses, getUnusedLenses, getLensList, openLens, updateLens } from '@/api/lens'
import { STATUS_MAP, PURPOSE_MAP, formatDate } from '@/utils/constants'

const allExpiring = ref([])
const unusedLenses = ref([])
const allLenses = ref([])
const warningDays = ref(30)
const unusedDays = ref(30)

const expiredLenses = computed(() => {
  return allExpiring.value.filter(l => l.is_expired || l.days_until_expiry < 0)
})

const soonLenses = computed(() => {
  return allExpiring.value.filter(l => !l.is_expired && l.days_until_expiry >= 0 && l.days_until_expiry <= warningDays.value)
})

const normalCount = computed(() => {
  const today = new Date()
  const threshold = new Date(today.getTime() + warningDays.value * 86400000)
  return allLenses.value.filter(l => {
    const exp = new Date(l.expiry_date)
    return exp > threshold && l.status !== 'used_up' && l.status !== 'expired'
  }).length
})

const getUnusedDays = (lens) => {
  const refDate = lens.last_wear_date ? new Date(lens.last_wear_date) : new Date(l.created_at)
  return Math.floor((Date.now() - refDate.getTime()) / 86400000)
}

const loadData = async () => {
  try {
    const [exp, unused, all] = await Promise.all([
      getExpiringLenses(warningDays.value),
      getUnusedLenses(unusedDays.value),
      getLensList()
    ])
    allExpiring.value = Array.isArray(exp) ? exp : (exp.results || [])
    unusedLenses.value = Array.isArray(unused) ? unused : (unused.results || [])
    allLenses.value = Array.isArray(all) ? all : (all.results || [])
  } catch (e) {
    console.error(e)
  }
}

const markExpired = async (id) => {
  if (!confirm('确认将此镜片标记为「已过期」？')) return
  try {
    await updateLens(id, { status: 'expired' })
    loadData()
  } catch (e) {
    console.error(e)
  }
}

const handleOpen = async (id) => {
  try {
    await openLens(id)
    loadData()
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>
