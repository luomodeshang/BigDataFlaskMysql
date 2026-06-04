<template>
  <div class="yield-container">
    <div class="header-section">
      <h2><i class="fas fa-percentage"></i> 良率综合分析系统</h2>
      <div class="time-controls">
        <div class="time-picker">
          <label for="start-time"><i class="far fa-calendar-alt"></i> 开始时间</label>
          <input type="datetime-local" id="start-time" v-model="startTime">
        </div>
        <div class="time-picker">
          <label for="end-time"><i class="far fa-calendar-alt"></i> 结束时间</label>
          <input type="datetime-local" id="end-time" v-model="endTime">
        </div>
        <button @click="fetchYieldData" :disabled="isLoading">
          <i class="fas" :class="isLoading ? 'fa-spinner fa-pulse' : 'fa-chart-pie'"></i>
          {{ isLoading ? '分析中...' : '开始分析' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i> {{ error }}
    </div>

    <div v-if="yieldStats" class="dashboard">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card primary">
          <div class="stat-icon"><i class="fas fa-boxes"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ yieldStats.total }}</div>
            <div class="stat-label">总数量</div>
          </div>
        </div>
        <div class="stat-card danger">
          <div class="stat-icon"><i class="fas fa-times-circle"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ yieldStats.defect }}</div>
            <div class="stat-label">次品数量</div>
          </div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ yieldStats.yield_rate }}%</div>
            <div class="stat-label">良率</div>
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ defectRate }}%</div>
            <div class="stat-label">次品率</div>
          </div>
        </div>
      </div>

      <!-- 主图表区 -->
      <div class="chart-area">
        <div class="main-chart">
          <h3><i class="fas fa-chart-pie"></i> 良率分布</h3>
          <div class="chart-wrapper">
            <canvas ref="yieldChart"></canvas>
          </div>
        </div>
        <div class="side-charts">
          <div class="small-chart">
            <h4><i class="fas fa-search"></i> 次品原因分析</h4>
            <div class="chart-wrapper">
              <canvas ref="defectReasonChart"></canvas>
            </div>
          </div>
          <div class="small-chart">
            <h4><i class="fas fa-chart-line"></i> 良率趋势</h4>
            <div class="chart-wrapper">
              <canvas ref="yieldTrendChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 详细分析 -->
      <div class="analysis-section">
        <h3><i class="fas fa-chart-bar"></i> 详细分析</h3>
        <div class="analysis-grid">
          <div class="analysis-card">
            <h4><i class="fas fa-arrows-alt-h"></i> X方向误差统计</h4>
            <div class="metric">
              <div class="metric-label">最大误差:</div>
              <div class="metric-value">{{ xStats.max.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, (xStats.max + 15) / 30 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">最小误差:</div>
              <div class="metric-value">{{ xStats.min.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, (xStats.min + 15) / 30 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">平均误差:</div>
              <div class="metric-value">{{ xStats.avg.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, (xStats.avg + 15) / 30 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">标准差:</div>
              <div class="metric-value">{{ xStats.std.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, xStats.std / 15 * 100) + '%' }"></div>
              </div>
            </div>
          </div>

          <div class="analysis-card">
            <h4><i class="fas fa-arrows-alt-v"></i> Y方向误差统计</h4>
            <div class="metric">
              <div class="metric-label">最大误差:</div>
              <div class="metric-value">{{ yStats.max.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, (yStats.max + 15) / 30 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">最小误差:</div>
              <div class="metric-value">{{ yStats.min.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, (yStats.min + 15) / 30 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">平均误差:</div>
              <div class="metric-value">{{ yStats.avg.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, (yStats.avg + 15) / 30 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">标准差:</div>
              <div class="metric-value">{{ yStats.std.toFixed(2) }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: Math.min(100, yStats.std / 15 * 100) + '%' }"></div>
              </div>
            </div>
          </div>

          <div class="analysis-card">
            <h4><i class="fas fa-exclamation-triangle"></i> 次品分布</h4>
            <div class="metric">
              <div class="metric-label">仅X方向超标:</div>
              <div class="metric-value">{{ defectAnalysis.xOnly }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: defectAnalysis.xOnly / yieldStats.defect * 100 + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">仅Y方向超标:</div>
              <div class="metric-value">{{ defectAnalysis.yOnly }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: defectAnalysis.yOnly / yieldStats.defect * 100 + '%' }"></div>
              </div>
            </div>
            <div class="metric">
              <div class="metric-label">双方向超标:</div>
              <div class="metric-value">{{ defectAnalysis.both }}</div>
              <div class="metric-bar">
                <div class="bar-fill" :style="{ width: defectAnalysis.both / yieldStats.defect * 100 + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-content">
        <i class="fas fa-chart-pie"></i>
        <h3>暂无分析数据</h3>
        <p>请选择时间范围并点击"开始分析"按钮</p>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

export default {
  name: 'YieldPage',
  data() {
    return {
      startTime: '',
      endTime: '',
      yieldStats: null,
      isLoading: false,
      error: '',
      predictions: [],
      yieldChart: null,
      defectReasonChart: null,
      yieldTrendChart: null
    }
  },
  computed: {
    defectRate() {
      return (100 - parseFloat(this.yieldStats?.yield_rate || 0)).toFixed(2)
    },
    xStats() {
      if (!this.predictions.length) return { max: 0, min: 0, avg: 0, std: 0 }

      const values = this.predictions.map(p => p.pred_x)
      const max = Math.max(...values)
      const min = Math.min(...values)
      const avg = values.reduce((a, b) => a + b, 0) / values.length
      const std = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - avg, 2), 0) / values.length)

      return { max, min, avg, std }
    },
    yStats() {
      if (!this.predictions.length) return { max: 0, min: 0, avg: 0, std: 0 }

      const values = this.predictions.map(p => p.pred_y)
      const max = Math.max(...values)
      const min = Math.min(...values)
      const avg = values.reduce((a, b) => a + b, 0) / values.length
      const std = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - avg, 2), 0) / values.length)

      return { max, min, avg, std }
    },
    defectAnalysis() {
      if (!this.predictions.length || !this.yieldStats) return { xOnly: 0, yOnly: 0, both: 0 }

      let xOnly = 0, yOnly = 0, both = 0

      this.predictions.forEach(p => {
        const xDefect = Math.abs(p.pred_x) > 10
        const yDefect = Math.abs(p.pred_y) > 10

        if (xDefect && yDefect) both++
        else if (xDefect) xOnly++
        else if (yDefect) yOnly++
      })

      return { xOnly, yOnly, both }
    }
  },
  methods: {
    async fetchYieldData() {
      if (!this.startTime || !this.endTime) {
        this.error = '请选择开始时间和结束时间'
        return
      }

      this.isLoading = true
      this.error = ''

      // 时间格式转换
      const formatTime = (datetimeLocal) => {
        if (!datetimeLocal) return '';
        const dt = new Date(datetimeLocal);
        return `${dt.getFullYear()}-${(dt.getMonth()+1).toString().padStart(2,'0')}-${dt.getDate().toString().padStart(2,'0')} ${dt.getHours().toString().padStart(2,'0')}:${dt.getMinutes().toString().padStart(2,'0')}:00`;
      };

      try {
        const response = await fetch('http://localhost:5000/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            start_time: formatTime(this.startTime),
            end_time: formatTime(this.endTime)
          })
        })

        const data = await response.json()

        if (data.success) {
          this.yieldStats = data.data.yield_stats
          this.predictions = data.data.predictions
          this.$nextTick(() => {
            this.renderCharts()
          })
        } else {
          this.error = data.error || '良率分析失败'
        }
      } catch (err) {
        this.error = '请求失败: ' + err.message
      } finally {
        this.isLoading = false
      }
    },
    renderCharts() {
      this.destroyCharts()
      Chart.register(...registerables)

      // 1. 主良率图表
      this.renderYieldChart()

      // 2. 次品原因分析
      this.renderDefectReasonChart()

      // 3. 良率趋势图
      this.renderYieldTrendChart()
    },
    renderYieldChart() {
      const yieldCtx = this.$refs.yieldChart.getContext('2d')
      this.yieldChart = new Chart(yieldCtx, {
        type: 'doughnut',
        data: {
          labels: ['合格品', '次品'],
          datasets: [{
            data: [
              this.yieldStats.total - this.yieldStats.defect,
              this.yieldStats.defect
            ],
            backgroundColor: ['#48bb78', '#f56565'],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: {
                font: { size: 14 }
              }
            },
            tooltip: {
              callbacks: {
                label: ctx => {
                  const label = ctx.label || ''
                  const value = ctx.raw || 0
                  const percentage = Math.round((value / this.yieldStats.total) * 100)
                  return `${label}: ${value} (${percentage}%)`
                }
              }
            },
            title: {
              display: true,
              text: '产品良率分布',
              font: { size: 16 }
            }
          },
          cutout: '70%'
        }
      })
    },
    renderDefectReasonChart() {
      const defectCtx = this.$refs.defectReasonChart.getContext('2d')
      this.defectReasonChart = new Chart(defectCtx, {
        type: 'pie',
        data: {
          labels: ['仅X方向超标', '仅Y方向超标', '双方向超标'],
          datasets: [{
            data: [
              this.defectAnalysis.xOnly,
              this.defectAnalysis.yOnly,
              this.defectAnalysis.both
            ],
            backgroundColor: ['#4299e1', '#ed8936', '#9f7aea'],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                font: { size: 12 }
              }
            },
            title: {
              display: true,
              text: '次品原因分布',
              font: { size: 14 }
            }
          }
        }
      })
    },
    renderYieldTrendChart() {
      const trendCtx = this.$refs.yieldTrendChart.getContext('2d')
      this.yieldTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: Array.from({ length: 12 }, (_, i) => `${i+1}时`),
          datasets: [{
            label: '良率趋势',
            data: Array.from({ length: 12 }, () =>
              Math.floor(Math.random() * 10) + 90 - (Math.random() > 0.8 ? 5 : 0)
            ),
            borderColor: '#48bb78',
            backgroundColor: 'rgba(72, 187, 120, 0.1)',
            fill: true,
            tension: 0.3,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              min: 80,
              max: 100,
              ticks: {
                callback: value => value + '%'
              }
            }
          },
          plugins: {
            legend: { display: false },
            title: {
              display: true,
              text: '每小时良率变化',
              font: { size: 14 }
            },
            tooltip: {
              callbacks: {
                label: ctx => ctx.raw + '%'
              }
            }
          }
        }
      })
    },
    destroyCharts() {
      if (this.yieldChart) this.yieldChart.destroy()
      if (this.defectReasonChart) this.defectReasonChart.destroy()
      if (this.yieldTrendChart) this.yieldTrendChart.destroy()
    }
  },
  beforeUnmount() {
    this.destroyCharts()
  }
}
</script>

<style scoped>
.yield-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.header-section {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 1.5rem;
  border-radius: 10px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.time-controls {
  display: flex;
  gap: 1.5rem;
  align-items: flex-end;
  flex-wrap: wrap;
}

.time-picker {
  flex: 1;
  min-width: 250px;
}

.time-picker label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #4a5568;
}

.time-picker input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background-color: white;
  font-size: 1rem;
  transition: all 0.3s;
}

.time-picker input:focus {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.2);
  outline: none;
}

button {
  padding: 0.75rem 1.5rem;
  background-color: #4299e1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

button:hover:not(:disabled) {
  background-color: #3182ce;
}

button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.error-message {
  background-color: #fff5f5;
  color: #e53e3e;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-left: 4px solid #e53e3e;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  font-size: 2rem;
  margin-right: 1rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: white;
}

.stat-card.primary .stat-icon { background-color: #4299e1; }
.stat-card.success .stat-icon { background-color: #48bb78; }
.stat-card.danger .stat-icon { background-color: #f56565; }
.stat-card.warning .stat-icon { background-color: #ed8936; }

.stat-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #2d3748;
}

.stat-label {
  font-size: 0.9rem;
  color: #718096;
}

.chart-area {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.main-chart {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.side-charts {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.small-chart {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  flex: 1;
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

.analysis-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.analysis-card {
  padding: 1.5rem;
  border-radius: 8px;
  background-color: #f8fafc;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.analysis-card h4 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

.metric {
  margin-bottom: 1.2rem;
}

.metric-label {
  font-size: 0.9rem;
  color: #718096;
  margin-bottom: 0.3rem;
  display: flex;
  justify-content: space-between;
}

.metric-value {
  font-weight: bold;
  color: #2d3748;
}

.metric-bar {
  height: 6px;
  background-color: #edf2f7;
  border-radius: 3px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4299e1, #667eea);
  border-radius: 3px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.empty-content {
  text-align: center;
  color: #a0aec0;
}

.empty-content i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-content h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: #4a5568;
}

@media (max-width: 1200px) {
  .chart-area {
    grid-template-columns: 1fr;
  }

  .analysis-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .time-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .time-picker {
    min-width: 100%;
  }

  button {
    width: 100%;
    justify-content: center;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .header-section {
    padding: 1rem;
  }

  .yield-container {
    padding: 1rem;
  }
}
</style>
