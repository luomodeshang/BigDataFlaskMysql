<template>
  <nav class="navbar">
    <div class="navbar-left">
      <div class="navbar-brand">BK数字孪生误差误差分析平台</div>
      <div class="system-status" :class="systemStatus">
        <span class="status-indicator"></span>
        {{ statusText }}
      </div>
    </div>
    <div class="navbar-links">
      <router-link to="/realtime" class="nav-link" active-class="active">
        <i class="fas fa-bug"></i>
        <span>实时监测</span>
      </router-link>

      <router-link to="/prediction" class="nav-link" active-class="active">
        <i class="fas fa-chart-line"></i>
        <span>误差预测</span>
      </router-link>

      <router-link to="/yield" class="nav-link" active-class="active">
        <i class="fas fa-percentage"></i>
        <span>良品率分析</span>
      </router-link>

      <router-link to="/diagnosis" class="nav-link" active-class="active">
        <i class="fas fa-bug"></i>
        <span>故障诊断</span>
      </router-link>



    </div>
    <div class="navbar-right">
      <div class="current-time">{{ currentTime }}</div>
    </div>
  </nav>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'NavBar',
  setup() {
    const currentTime = ref('')
    const systemStatus = ref('normal') // normal/warning/error
    const statusText = ref('系统运行正常')

    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }

    onMounted(() => {
      updateTime()
      const timer = setInterval(updateTime, 1000)

      // 模拟系统状态变化
      const statusTimer = setInterval(() => {
        const statuses = ['normal', 'warning', 'error']
        const randomStatus = statuses[Math.floor(Math.random() * statuses.length)]
        systemStatus.value = randomStatus
        statusText.value =
          randomStatus === 'normal' ? '系统运行正常' :
          randomStatus === 'warning' ? '系统存在警告' : '系统发生故障'
      }, 10000)

      onBeforeUnmount(() => {
        clearInterval(timer)
        clearInterval(statusTimer)
      })
    })

    return {
      currentTime,
      systemStatus,
      statusText
    }
  }
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 2rem;
  background-color: #2c3e50;
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.navbar-brand {
  font-size: 1.3rem;
  font-weight: bold;
  color: #ffffff;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  padding: 0.3rem 0.8rem;
  border-radius: 1rem;
  background-color: rgba(255, 255, 255, 0.1);
}

.status-indicator {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
}

.system-status.normal .status-indicator {
  background-color: #42b983;
  box-shadow: 0 0 5px #42b983;
}

.system-status.warning .status-indicator {
  background-color: #e6a23c;
  box-shadow: 0 0 5px #e6a23c;
}

.system-status.error .status-indicator {
  background-color: #f56c6c;
  box-shadow: 0 0 5px #f56c6c;
}

.navbar-links {
  display: flex;
  gap: 0.8rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.nav-link.active {
  background-color: #42b983;
  font-weight: 500;
}

.nav-link i {
  font-size: 1rem;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.current-time {
  font-size: 0.9rem;
  opacity: 0.8;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }

  .navbar-left, .navbar-links {
    width: 100%;
    justify-content: center;
  }

  .navbar-brand {
    font-size: 1.1rem;
  }

  .nav-link {
    padding: 0.5rem;
    font-size: 0.85rem;
  }
}
</style>
