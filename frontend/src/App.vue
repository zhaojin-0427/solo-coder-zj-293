<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-icon">👁️</span>
        <span class="logo-text">彩瞳追踪</span>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <span class="nav-icon">🏠</span>
          <span>首页概览</span>
        </router-link>
        <router-link to="/lens" class="nav-item" active-class="active">
          <span class="nav-icon">💎</span>
          <span>镜片库</span>
        </router-link>
        <router-link to="/records" class="nav-item" active-class="active">
          <span class="nav-icon">📝</span>
          <span>佩戴记录</span>
        </router-link>
        <router-link to="/outfit-plans" class="nav-item" active-class="active">
          <span class="nav-icon">💄</span>
          <span>妆容搭配计划</span>
        </router-link>
        <router-link to="/comfort" class="nav-item" active-class="active">
          <span class="nav-icon">😊</span>
          <span>舒适度追踪</span>
        </router-link>
        <router-link to="/expiry" class="nav-item" active-class="active">
          <span class="nav-icon">⏰</span>
          <span>过期预警</span>
        </router-link>
        <router-link to="/stats" class="nav-item" active-class="active">
          <span class="nav-icon">📊</span>
          <span>统计分析</span>
        </router-link>
        <router-link to="/budget" class="nav-item" active-class="active">
          <span class="nav-icon">💰</span>
          <span>预算与补货</span>
        </router-link>
        <router-link to="/travel" class="nav-item" active-class="active">
          <span class="nav-icon">✈️</span>
          <span>旅行清单</span>
        </router-link>
      </nav>
    </aside>
    <main class="main-content">
      <router-view/>
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #7C3AED, #8B5CF6);
  padding: 24px 0;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  overflow-y: auto;
  box-shadow: 2px 0 12px rgba(139, 92, 246, 0.2);
}

.logo {
  padding: 0 24px 32px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
}

.logo-icon {
  font-size: 32px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.nav-menu {
  padding: 0 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  border-radius: 10px;
  margin-bottom: 4px;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.nav-item.active {
  background: white;
  color: var(--primary-dark);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-icon {
  font-size: 18px;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  min-height: 100vh;
}
</style>
