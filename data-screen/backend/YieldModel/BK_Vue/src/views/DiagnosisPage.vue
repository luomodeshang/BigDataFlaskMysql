<template>
  <div class="diagnosis-container">
    <div class="header">
      <div class="title-section">
        <h1>设备故障诊断系统</h1>
        <p class="last-update">最后更新: {{ lastUpdateTime }}</p>
      </div>
      <div class="status-indicator" :class="diagnosisStatus">
        <i :class="statusIcon"></i>
        {{ statusText }}
        <span v-if="diagnosisStatus !== 'loading'" class="confidence">{{ confidence }}</span>
      </div>
    </div>

    <div class="content">
      <div class="diagnosis-section">
        <div class="diagnosis-result">
          <h2>
            <i class="fas fa-clipboard-check"></i> 诊断结果
            <span class="refresh-timer" @click="toggleAutoRefresh">
              <i :class="autoRefreshIcon"></i> {{ autoRefreshText }}
            </span>
          </h2>
          <div class="result-card" :class="resultCardClass">
            <div class="result-content">
              <p>{{ diagnosisResult }}</p>
              <div v-if="probabilities" class="probabilities">
                <div v-for="(prob, name) in probabilities" :key="name" class="probability-item">
                  <span class="prob-name">{{ name }}:</span>
                  <span class="prob-value">{{ prob }}</span>
                  <div class="prob-bar">
                    <div class="prob-bar-fill" :style="{ width: parseProbability(prob) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="quick-stats">
          <h2><i class="fas fa-chart-bar"></i> 关键指标</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ positioningErrorX[0] || 0 }}μm</div>
              <div class="stat-label">X轴最大误差</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ positioningErrorY[0] || 0 }}μm</div>
              <div class="stat-label">Y轴最大误差</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ rawData['视觉误差X'] || 0 }}μm</div>
              <div class="stat-label">视觉X误差</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ rawData['视觉误差Y'] || 0 }}μm</div>
              <div class="stat-label">视觉Y误差</div>
            </div>
          </div>
        </div>
      </div>

      <div class="data-visualization">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            <i :class="tab.icon"></i> {{ tab.label }}
          </button>
        </div>

        <div class="tab-content">
          <!-- 定位误差可视化 -->
          <div v-if="activeTab === 'positioning'" class="chart-container">
            <h3><i class="fas fa-bullseye"></i> 定位误差分析</h3>
            <div class="chart-row">
              <div class="chart-item">
                <h4>X轴定位误差 (μm)</h4>
                <line-chart
                  :data="positioningErrorX"
                  :colors="['#FF6384']"
                  :height="200"
                  :labels="['位置1', '位置2', '位置3', '位置4']"
                />
              </div>
              <div class="chart-item">
                <h4>Y轴定位误差 (μm)</h4>
                <line-chart
                  :data="positioningErrorY"
                  :colors="['#36A2EB']"
                  :height="200"
                  :labels="['位置1', '位置2', '位置3', '位置4']"
                />
              </div>
            </div>
            <div class="chart-row">
              <div class="chart-item full-width">
                <h4>X/Y轴误差对比</h4>
                <bar-chart
                  :data="xyErrorComparison"
                  :colors="['#FF6384', '#36A2EB']"
                  :height="250"
                  :labels="['位置1', '位置2', '位置3', '位置4']"
                />
              </div>
            </div>
          </div>

          <!-- 坐标数据可视化 -->
          <div v-if="activeTab === 'coordinates'" class="chart-container">
            <h3><i class="fas fa-map-marker-alt"></i> 坐标数据对比</h3>
            <div class="chart-row">
              <div class="chart-item">
                <h4>物件坐标 vs 物理坐标</h4>
                <scatter-chart
                  :data="objectVsPhysical"
                  :height="300"
                />
                <div class="chart-legend">
                  <span class="legend-item"><span class="legend-color" style="background-color: #FF6384;"></span> 物件坐标</span>
                  <span class="legend-item"><span class="legend-color" style="background-color: #36A2EB;"></span> 物理坐标</span>
                </div>
              </div>
              <div class="chart-item">
                <h4>PLC坐标 vs 光栅反馈</h4>
                <scatter-chart
                  :data="plcVsGrating"
                  :height="300"
                />
                <div class="chart-legend">
                  <span class="legend-item"><span class="legend-color" style="background-color: #FFCE56;"></span> PLC坐标</span>
                  <span class="legend-item"><span class="legend-color" style="background-color: #4BC0C0;"></span> 光栅反馈</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 视觉误差可视化 -->
          <div v-if="activeTab === 'vision'" class="chart-container">
            <h3><i class="fas fa-eye"></i> 视觉系统误差</h3>
            <div class="chart-row">
              <div class="chart-item">
                <h4>视觉误差X/Y (μm)</h4>
                <bar-chart
                  :data="visionErrors"
                  :colors="['#FF6384', '#36A2EB']"
                  :height="250"
                />
              </div>
              <div class="chart-item">
                <h4>贴合误差 (μm)</h4>
                <radar-chart
                  :data="fittingErrors"
                  :height="250"
                />
              </div>
            </div>
            <div class="chart-row">
              <div class="chart-item full-width">
                <h4>视觉误差趋势</h4>
                <line-chart
                  :data="visionErrorTrend"
                  :colors="['#FF6384', '#36A2EB']"
                  :height="250"
                  :labels="['5分钟前', '4分钟前', '3分钟前', '2分钟前', '1分钟前', '当前']"
                />
              </div>
            </div>
          </div>

          <!-- 原始数据表格 -->
          <div v-if="activeTab === 'raw'" class="raw-data-container">
            <h3><i class="fas fa-table"></i> 原始数据</h3>
            <div class="table-controls">
              <div class="search-box">
                <i class="fas fa-search"></i>
                <input v-model="searchQuery" placeholder="搜索数据..." />
              </div>
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th v-for="header in filteredHeaders" :key="header">
                      {{ header }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td v-for="header in filteredHeaders" :key="header">
                      {{ formatValue(rawData[header]) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="refresh-btn" @click="refreshData">
        <i class="fas fa-sync-alt"></i> 手动刷新
      </button>
      <button class="export-btn" @click="exportReport">
        <i class="fas fa-file-export"></i> 导出报告
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { saveAs } from 'file-saver'

export default {
  name: 'DiagnosisPage',
  setup() {
    const diagnosisData = ref(null)
    const activeTab = ref('positioning')
    const diagnosisResult = ref('等待诊断结果...')
    const rawData = ref({})
    const isLoading = ref(false)
    const lastUpdateTime = ref('')
    const autoRefresh = ref(true)
    const refreshInterval = ref(null)
    const searchQuery = ref('')
    const probabilities = ref(null)
    const errorHistory = ref({
      visionX: [],
      visionY: []
    })

    // 标签页配置
    const tabs = [
      { id: 'positioning', label: '定位误差', icon: 'fas fa-bullseye' },
      { id: 'coordinates', label: '坐标对比', icon: 'fas fa-map-marker-alt' },
      { id: 'vision', label: '视觉误差', icon: 'fas fa-eye' },
      { id: 'raw', label: '原始数据', icon: 'fas fa-table' }
    ]

    // 从后端获取诊断数据
    const fetchDiagnosisData = async () => {
      isLoading.value = true
      try {
        const response = await axios.get('/api/diagnosis')
        diagnosisResult.value = response.data.result
        rawData.value = response.data.data
        diagnosisData.value = response.data
        probabilities.value = response.data.probabilities

        // 更新最后更新时间
        lastUpdateTime.value = new Date().toLocaleTimeString()

        // 记录历史数据用于趋势图
        if (rawData.value['视觉误差X'] && rawData.value['视觉误差Y']) {
          errorHistory.value.visionX.push(rawData.value['视觉误差X'])
          errorHistory.value.visionY.push(rawData.value['视觉误差Y'])

          // 保持最多6个数据点
          if (errorHistory.value.visionX.length > 6) {
            errorHistory.value.visionX.shift()
            errorHistory.value.visionY.shift()
          }
        }
      } catch (error) {
        console.error('获取诊断数据失败:', error)
        diagnosisResult.value = '诊断失败: ' + error.message
      } finally {
        isLoading.value = false
      }
    }

    // 启动自动刷新
    const startAutoRefresh = () => {
      refreshInterval.value = setInterval(fetchDiagnosisData, 1000)
    }

    // 停止自动刷新
    const stopAutoRefresh = () => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
        refreshInterval.value = null
      }
    }

    // 切换自动刷新状态
    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value
      if (autoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    }

    // 刷新数据
    const refreshData = () => {
      if (!autoRefresh.value) {
        fetchDiagnosisData()
      }
    }

    // 导出报告
    const exportReport = () => {
      const blob = new Blob([generateReport()], { type: 'text/plain;charset=utf-8' })
      saveAs(blob, `诊断报告_${new Date().toISOString().slice(0,10)}.txt`)
    }

    // 生成报告内容
    const generateReport = () => {
      let report = `设备故障诊断报告\n生成时间: ${new Date().toLocaleString()}\n\n`
      report += `诊断结果: ${diagnosisResult.value}\n\n`
      report += '详细数据:\n'

      for (const [key, value] of Object.entries(rawData.value)) {
        report += `${key}: ${value}\n`
      }

      report += '\n概率分析:\n'
      for (const [name, prob] of Object.entries(probabilities.value || {})) {
        report += `${name}: ${prob}\n`
      }

      return report
    }

    // 格式化显示值
    const formatValue = (value) => {
      if (value === undefined || value === null) return 'N/A'
      if (typeof value === 'number') {
        // 如果是误差值，显示μm单位
        if (key.includes('误差') || key.includes('坐标')) {
          return value.toFixed(2) + 'μm'
        }
        return value.toFixed(2)
      }
      return value
    }

    // 解析概率值为数字
    const parseProbability = (probStr) => {
      if (!probStr) return 0
      const num = parseFloat(probStr)
      return isNaN(num) ? 0 : num
    }

    // 计算属性
    const diagnosisStatus = computed(() => {
      if (isLoading.value) return 'loading'
      if (!diagnosisResult.value || diagnosisResult.value.includes('等待')) return 'idle'
      if (diagnosisResult.value.includes('正常')) return 'normal'
      if (diagnosisResult.value.includes('警告')) return 'warning'
      return 'error'
    })

    const statusText = computed(() => {
      switch (diagnosisStatus.value) {
        case 'loading': return '诊断中...'
        case 'idle': return '待诊断'
        case 'normal': return '状态正常'
        case 'warning': return '存在警告'
        case 'error': return '发现故障'
        default: return '未知状态'
      }
    })

    const statusIcon = computed(() => {
      switch (diagnosisStatus.value) {
        case 'loading': return 'fas fa-spinner fa-spin'
        case 'idle': return 'fas fa-pause'
        case 'normal': return 'fas fa-check-circle'
        case 'warning': return 'fas fa-exclamation-triangle'
        case 'error': return 'fas fa-times-circle'
        default: return 'fas fa-question-circle'
      }
    })

    const confidence = computed(() => {
      if (!probabilities.value || !diagnosisData.value) return ''
      return diagnosisData.value.result.match(/\(置信度: (.*?)\)/)?.[1] || ''
    })

    const resultCardClass = computed(() => {
      return `result-${diagnosisStatus.value}`
    })

    const autoRefreshIcon = computed(() => {
      return autoRefresh.value ? 'fas fa-toggle-on' : 'fas fa-toggle-off'
    })

    const autoRefreshText = computed(() => {
      return autoRefresh.value ? '自动刷新: 开启' : '自动刷新: 关闭'
    })

    const filteredHeaders = computed(() => {
      if (!searchQuery.value) return Object.keys(rawData.value)
      return Object.keys(rawData.value).filter(key =>
        key.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })

    // 图表数据计算
    const positioningErrorX = computed(() => {
      return [
        rawData.value['all定位误差X-1'],
        rawData.value['all定位误差X-2'],
        rawData.value['all定位误差X-3'],
        rawData.value['all定位误差X-4']
      ].map(Number).filter(n => !isNaN(n))
    })

    const positioningErrorY = computed(() => {
      return [
        rawData.value['all定位误差Y-1'],
        rawData.value['all定位误差Y-2'],
        rawData.value['all定位误差Y-3'],
        rawData.value['all定位误差Y-4']
      ].map(Number).filter(n => !isNaN(n))
    })

    const xyErrorComparison = computed(() => {
      return {
        labels: ['X轴误差', 'Y轴误差'],
        datasets: [
          {
            label: '最大误差',
            data: [
              Math.max(...positioningErrorX.value),
              Math.max(...positioningErrorY.value)
            ],
            backgroundColor: ['#FF6384', '#36A2EB']
          }
        ]
      }
    })

    const objectVsPhysical = computed(() => {
      return {
        datasets: [
          {
            label: '物件坐标',
            data: [
              { x: rawData.value['all物件坐标X-1'], y: rawData.value['all物件坐标Y-1'] }
            ],
            backgroundColor: '#FF6384'
          },
          {
            label: '物理坐标',
            data: [
              { x: rawData.value['all物理坐标X-1'], y: rawData.value['all物理坐标Y-1'] }
            ],
            backgroundColor: '#36A2EB'
          }
        ]
      }
    })

    const plcVsGrating = computed(() => {
      return {
        datasets: [
          {
            label: 'PLC坐标',
            data: [
              { x: rawData.value['catchPLC坐标X'], y: rawData.value['catchPLC坐标Y'] },
              { x: rawData.value['releasePLC坐标X'], y: rawData.value['releasePLC坐标Y'] }
            ],
            backgroundColor: '#FFCE56'
          },
          {
            label: '光栅反馈',
            data: [
              { x: rawData.value['catch光栅反馈X'], y: rawData.value['catch光栅反馈Y'] },
              { x: rawData.value['release光栅反馈X'], y: rawData.value['release光栅反馈Y'] }
            ],
            backgroundColor: '#4BC0C0'
          }
        ]
      }
    })

    const visionErrors = computed(() => {
      return {
        labels: ['X轴误差', 'Y轴误差'],
        datasets: [
          {
            label: '视觉误差',
            data: [rawData.value['视觉误差X'], rawData.value['视觉误差Y']],
            backgroundColor: ['#FF6384', '#36A2EB']
          }
        ]
      }
    })

    const visionErrorTrend = computed(() => {
      return {
        datasets: [
          {
            label: '视觉X误差',
            data: errorHistory.value.visionX,
            backgroundColor: '#FF6384',
            borderColor: '#FF6384',
            fill: false
          },
          {
            label: '视觉Y误差',
            data: errorHistory.value.visionY,
            backgroundColor: '#36A2EB',
            borderColor: '#36A2EB',
            fill: false
          }
        ]
      }
    })

    const fittingErrors = computed(() => {
      return {
        labels: ['X轴误差', 'Y轴误差'],
        datasets: [
          {
            label: '贴合误差',
            data: [rawData.value['贴合误差X'], rawData.value['贴合误差Y']],
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)'
          }
        ]
      }
    })

    // 组件挂载时获取数据并启动自动刷新
    onMounted(() => {
      fetchDiagnosisData()
      startAutoRefresh()
    })

    // 组件卸载前清除定时器
    onBeforeUnmount(() => {
      stopAutoRefresh()
    })

    return {
      activeTab,
      tabs,
      diagnosisResult,
      rawData,
      probabilities,
      diagnosisStatus,
      statusText,
      statusIcon,
      confidence,
      resultCardClass,
      lastUpdateTime,
      autoRefresh,
      autoRefreshIcon,
      autoRefreshText,
      searchQuery,
      filteredHeaders,
      positioningErrorX,
      positioningErrorY,
      xyErrorComparison,
      objectVsPhysical,
      plcVsGrating,
      visionErrors,
      visionErrorTrend,
      fittingErrors,
      refreshData,
      exportReport,
      toggleAutoRefresh,
      formatValue,
      parseProbability
    }
  }
}
</script>

<style scoped>
.diagnosis-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Arial', sans-serif;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding: 15px 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
}

.title-section h1 {
  color: #2c3e50;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.last-update {
  margin: 5px 0 0;
  color: #7f8c8d;
  font-size: 13px;
}

.status-indicator {
  padding: 10px 20px;
  border-radius: 30px;
  font-weight: bold;
  color: white;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.status-indicator.loading {
  background-color: #3498db;
}

.status-indicator.idle {
  background-color: #95a5a6;
}

.status-indicator.normal {
  background-color: #2ecc71;
}

.status-indicator.warning {
  background-color: #f39c12;
}

.status-indicator.error {
  background-color: #e74c3c;
}

.confidence {
  margin-left: 10px;
  font-weight: normal;
  opacity: 0.9;
}

.content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 20px;
  margin-bottom: 20px;
}

.diagnosis-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.diagnosis-result {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.diagnosis-result h2 {
  color: #2c3e50;
  margin: 0 0 15px;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.diagnosis-result h2 i {
  margin-right: 8px;
  color: #7f8c8d;
}

.refresh-timer {
  font-size: 14px;
  font-weight: normal;
  color: #3498db;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.refresh-timer:hover {
  opacity: 0.8;
}

.result-card {
  padding: 20px;
  border-radius: 8px;
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.result-content {
  width: 100%;
}

.result-card p {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
}

.result-normal {
  background-color: rgba(46, 204, 113, 0.1);
  color: #27ae60;
  border-left: 5px solid #2ecc71;
}

.result-warning {
  background-color: rgba(241, 196, 15, 0.1);
  color: #f39c12;
  border-left: 5px solid #f1c40f;
}

.result-error {
  background-color: rgba(231, 76, 60, 0.1);
  color: #c0392b;
  border-left: 5px solid #e74c3c;
}

.result-loading {
  background-color: rgba(52, 152, 219, 0.1);
  color: #2980b9;
  border-left: 5px solid #3498db;
}

.probabilities {
  margin-top: 15px;
  text-align: left;
}

.probability-item {
  margin-bottom: 8px;
}

.prob-name {
  display: inline-block;
  width: 200px;
  font-weight: 500;
}

.prob-value {
  display: inline-block;
  width: 80px;
  text-align: right;
  margin-right: 10px;
  font-family: monospace;
}

.prob-bar {
  display: inline-block;
  width: calc(100% - 300px);
  height: 10px;
  background-color: #ecf0f1;
  border-radius: 5px;
  overflow: hidden;
}

.prob-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  border-radius: 5px;
  transition: width 0.5s ease;
}

.quick-stats {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.quick-stats h2 {
  color: #2c3e50;
  margin: 0 0 15px;
  font-size: 18px;
}

.quick-stats h2 i {
  margin-right: 8px;
  color: #7f8c8d;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.stat-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 13px;
  color: #7f8c8d;
}

.data-visualization {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.tabs {
  display: flex;
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.tabs button {
  padding: 10px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 15px;
  color: #7f8c8d;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tabs button:hover {
  color: #3498db;
}

.tabs button.active {
  color: #3498db;
  border-bottom-color: #3498db;
  font-weight: bold;
}

.tabs button i {
  font-size: 14px;
}

.chart-container {
  margin-bottom: 20px;
}

.chart-container h3 {
  margin: 0 0 15px;
  color: #2c3e50;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-container h3 i {
  color: #7f8c8d;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.chart-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

.chart-item.full-width {
  grid-column: span 2;
}

.chart-item h4 {
  margin: 0 0 15px;
  color: #34495e;
  font-size: 14px;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #7f8c8d;
}

.legend-color {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.raw-data-container h3 {
  margin: 0 0 15px;
  color: #2c3e50;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.raw-data-container h3 i {
  color: #7f8c8d;
}

.table-controls {
  margin-bottom: 15px;
  display: flex;
  justify-content: flex-end;
}

.search-box {
  position: relative;
  width: 250px;
}

.search-box i {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #95a5a6;
}

.search-box input {
  width: 100%;
  padding: 8px 15px 8px 35px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
  transition: all 0.3s;
}

.search-box input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.table-responsive {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #eee;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
  white-space: nowrap;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
  position: sticky;
  top: 0;
}

.data-table tr:hover {
  background-color: #f8f9fa;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 20px;
}

.actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
  font-weight: 500;
}

.refresh-btn {
  background-color: #3498db;
  color: white;
}

.refresh-btn:hover {
  background-color: #2980b9;
}

.export-btn {
  background-color: #2ecc71;
  color: white;
}

.export-btn:hover {
  background-color: #27ae60;
}

@media (max-width: 1200px) {
  .content {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .chart-row {
    grid-template-columns: 1fr;
  }

  .chart-item.full-width {
    grid-column: span 1;
  }

  .actions {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .tabs {
    overflow-x: auto;
    padding-bottom: 5px;
  }

  .tabs button {
    padding: 8px 15px;
    font-size: 14px;
  }
}
</style>
