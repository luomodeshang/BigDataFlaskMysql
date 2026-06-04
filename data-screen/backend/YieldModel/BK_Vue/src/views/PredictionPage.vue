<template>
  <div class="prediction-container">
    <div class="header-section">
      <h2><i class="fas fa-chart-line"></i> 误差预测分析系统</h2>
      <div class="time-controls">
        <div class="time-picker">
          <label for="start-time"><i class="far fa-calendar-alt"></i> 开始时间</label>
          <input type="datetime-local" id="start-time" v-model="startTime">
        </div>
        <div class="time-picker">
          <label for="end-time"><i class="far fa-calendar-alt"></i> 结束时间</label>
          <input type="datetime-local" id="end-time" v-model="endTime">
        </div>
        <button @click="fetchPredictions" :disabled="isLoading">
          <i class="fas" :class="isLoading ? 'fa-spinner fa-pulse' : 'fa-search'"></i>
          {{ isLoading ? '分析中...' : '开始分析' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i> {{ error }}
    </div>

    <div v-if="predictions.length > 0" class="dashboard">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card primary">
          <div class="stat-icon"><i class="fas fa-boxes"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ predictions.length }}</div>
            <div class="stat-label">总样本数</div>
          </div>
        </div>
        <div class="stat-card danger">
          <div class="stat-icon"><i class="fas fa-times-circle"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ defectCount }}</div>
            <div class="stat-label">次品数量</div>
          </div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ yieldRate }}%</div>
            <div class="stat-label">预估良率</div>
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-icon"><i class="fas fa-arrows-alt-h"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ avgXError.toFixed(2) }}</div>
            <div class="stat-label">平均X误差</div>
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-icon"><i class="fas fa-arrows-alt-v"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ avgYError.toFixed(2) }}</div>
            <div class="stat-label">平均Y误差</div>
          </div>
        </div>
      </div>

      <!-- 主图表区 -->
      <div class="main-charts">
        <div class="chart-container">
          <h3><i class="fas fa-braille"></i> X/Y方向误差分布</h3>
          <div class="chart-wrapper">
            <canvas ref="scatterChart"></canvas>
          </div>
        </div>
        <div class="chart-container">
          <h3><i class="fas fa-chart-line"></i> 误差趋势分析</h3>
          <div class="chart-wrapper">
            <canvas ref="trendChart"></canvas>
          </div>
        </div>
      </div>

      <!-- 次级图表区 -->
      <div class="secondary-charts">
        <div class="chart-container">
          <h3><i class="fas fa-chart-bar"></i> X方向误差分布</h3>
          <div class="chart-wrapper">
            <canvas ref="xDistChart"></canvas>
          </div>
        </div>
        <div class="chart-container">
          <h3><i class="fas fa-chart-bar"></i> Y方向误差分布</h3>
          <div class="chart-wrapper">
            <canvas ref="yDistChart"></canvas>
          </div>
        </div>
      </div>

      <!-- 数据表格 -->
      <div class="data-section">
        <h3><i class="fas fa-table"></i> 详细数据 ({{ displayedPredictions.length }}条)</h3>
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>序号</th>
                <th>X预测误差</th>
                <th>Y预测误差</th>
                <th v-if="hasActualData">X实际误差</th>
                <th v-if="hasActualData">Y实际误差</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in displayedPredictions" :key="index">
                <td>{{ index + 1 }}</td>
                <td :class="{ 'defect': Math.abs(item.pred_x) > 10 }">
                  {{ item.pred_x.toFixed(2) }}
                </td>
                <td :class="{ 'defect': Math.abs(item.pred_y) > 10 }">
                  {{ item.pred_y.toFixed(2) }}
                </td>
                <td v-if="hasActualData">{{ item.actual_x?.toFixed(2) }}</td>
                <td v-if="hasActualData">{{ item.actual_y?.toFixed(2) }}</td>
                <td>
                  <span class="status-badge" :class="{
                    'defect-badge': Math.abs(item.pred_x) > 10 || Math.abs(item.pred_y) > 10,
                    'good-badge': Math.abs(item.pred_x) <= 10 && Math.abs(item.pred_y) <= 10
                  }">
                    {{ Math.abs(item.pred_x) > 10 || Math.abs(item.pred_y) > 10 ? '次品' : '良品' }}
                  </span>
                </td>
                <td>
                  <button class="detail-btn" @click="showDetail(item)">
                    <i class="fas fa-search"></i> 详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination">
          <button @click="loadMore" v-if="displayedPredictions.length < predictions.length">
            <i class="fas fa-plus"></i> 加载更多
          </button>
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
import zoomPlugin from 'chartjs-plugin-zoom/dist/chartjs-plugin-zoom.min.js'

export default {
  name: 'PredictionPage',
  data() {
    return {
      startTime: '',
      endTime: '',
      predictions: [],
      isLoading: false,
      error: '',
      hasActualData: false,
      scatterChart: null,
      trendChart: null,
      xDistChart: null,
      yDistChart: null,
      displayedCount: 50
    }
  },
  computed: {
    defectCount() {
      return this.predictions.filter(item =>
        Math.abs(item.pred_x) > 10 || Math.abs(item.pred_y) > 10
      ).length
    },
    yieldRate() {
      return ((this.predictions.length - this.defectCount) / this.predictions.length * 100).toFixed(2)
    },
    avgXError() {
      return this.predictions.reduce((sum, item) => sum + Math.abs(item.pred_x), 0) / this.predictions.length
    },
    avgYError() {
      return this.predictions.reduce((sum, item) => sum + Math.abs(item.pred_y), 0) / this.predictions.length
    },
    displayedPredictions() {
      return this.predictions.slice(0, this.displayedCount)
    }
  },
  methods: {
    async fetchPredictions() {
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
          this.predictions = data.data.predictions
          this.hasActualData = this.predictions.some(item => 'actual_x' in item)
          this.displayedCount = 50
          this.$nextTick(() => {
            this.renderCharts()
          })
        } else {
          this.error = data.error || '预测失败'
        }
      } catch (err) {
        this.error = '请求失败: ' + err.message
      } finally {
        this.isLoading = false
      }
    },
    renderCharts() {
      this.destroyCharts()
      Chart.register(...registerables, zoomPlugin)

      // 准备图表数据
      const labels = this.predictions.map((_, i) => i + 1)
      const xData = this.predictions.map(item => item.pred_x)
      const yData = this.predictions.map(item => item.pred_y)

      // 1. 散点图
      this.renderScatterChart()

      // 2. 趋势图
      this.renderTrendChart(labels, xData, yData)

      // 3. X方向分布图
      this.renderDistributionChart(this.$refs.xDistChart, xData, 'X方向误差分布', '#3498db')

      // 4. Y方向分布图
      this.renderDistributionChart(this.$refs.yDistChart, yData, 'Y方向误差分布', '#e74c3c')
    },
    renderScatterChart() {
      const scatterCtx = this.$refs.scatterChart.getContext('2d')
      this.scatterChart = new Chart(scatterCtx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: '正常数据',
            data: this.predictions
              .filter(item => Math.abs(item.pred_x) <= 10 && Math.abs(item.pred_y) <= 10)
              .map(item => ({ x: item.pred_x, y: item.pred_y })),
            backgroundColor: '#42b983',
            pointRadius: 5,
            pointHoverRadius: 7
          }, {
            label: '异常数据',
            data: this.predictions
              .filter(item => Math.abs(item.pred_x) > 10 || Math.abs(item.pred_y) > 10)
              .map(item => ({ x: item.pred_x, y: item.pred_y })),
            backgroundColor: '#ff6384',
            pointRadius: 7,
            pointHoverRadius: 9
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: { display: true, text: 'X方向误差' },
              min: -15,
              max: 15,
              grid: { color: 'rgba(0, 0, 0, 0.05)' }
            },
            y: {
              title: { display: true, text: 'Y方向误差' },
              min: -15,
              max: 15,
              grid: { color: 'rgba(0, 0, 0, 0.05)' }
            }
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: ctx => `X: ${ctx.parsed.x.toFixed(2)}, Y: ${ctx.parsed.y.toFixed(2)}`
              }
            },
            zoom: {
              zoom: {
                wheel: { enabled: true },
                pinch: { enabled: true },
                mode: 'xy'
              },
              pan: {
                enabled: true,
                mode: 'xy'
              }
            }
          }
        }
      })
    },
    renderTrendChart(labels, xData, yData) {
      const trendCtx = this.$refs.trendChart.getContext('2d')
      this.trendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'X方向误差',
              data: xData,
              borderColor: '#3498db',
              backgroundColor: 'rgba(52, 152, 219, 0.1)',
              tension: 0.1,
              pointRadius: 2,
              borderWidth: 2
            },
            {
              label: 'Y方向误差',
              data: yData,
              borderColor: '#e74c3c',
              backgroundColor: 'rgba(231, 76, 60, 0.1)',
              tension: 0.1,
              pointRadius: 2,
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          scales: {
            y: {
              title: { display: true, text: '误差值' },
              min: -15,
              max: 15,
              grid: { color: 'rgba(0, 0, 0, 0.05)' }
            },
            x: {
              title: { display: true, text: '样本序号' },
              grid: { color: 'rgba(0, 0, 0, 0.05)' }
            }
          },
          plugins: {
            legend: { position: 'top' },
            tooltip: {
              callbacks: {
                label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}`
              }
            },
            zoom: {
              zoom: {
                wheel: { enabled: true },
                pinch: { enabled: true },
                mode: 'xy'
              },
              pan: {
                enabled: true,
                mode: 'xy'
              }
            }
          }
        }
      })
    },
    renderDistributionChart(canvasRef, data, label, color) {
      const ctx = canvasRef.getContext('2d')
      const chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: Array.from({ length: 13 }, (_, i) => (i * 5 - 15).toString()),
          datasets: [{
            label: label,
            data: this.createHistogramData(data, -15, 15, 5),
            backgroundColor: color,
            borderColor: color,
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: { display: true, text: '误差范围' },
              grid: { display: false }
            },
            y: {
              title: { display: true, text: '数量' },
              beginAtZero: true,
              grid: { color: 'rgba(0, 0, 0, 0.05)' }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      })

      if (canvasRef === this.$refs.xDistChart) {
        this.xDistChart = chart
      } else {
        this.yDistChart = chart
      }
    },
    createHistogramData(data, min, max, step) {
      const bins = Math.ceil((max - min) / step)
      const histogram = Array(bins).fill(0)

      data.forEach(value => {
        const bin = Math.floor((value - min) / step)
        if (bin >= 0 && bin < bins) {
          histogram[bin]++
        }
      })

      return histogram
    },
    destroyCharts() {
      if (this.scatterChart) this.scatterChart.destroy()
      if (this.trendChart) this.trendChart.destroy()
      if (this.xDistChart) this.xDistChart.destroy()
      if (this.yDistChart) this.yDistChart.destroy()
    },
    loadMore() {
      this.displayedCount += 50
    },
    showDetail(item) {
      alert(`详细数据:\nX预测误差: ${item.pred_x.toFixed(2)}\nY预测误差: ${item.pred_y.toFixed(2)}`)
    }
  },
  beforeUnmount() {
    this.destroyCharts()
  }
}
</script>

<style scoped>
/* 完整样式请见GitHub仓库，这里提供关键样式 */
.prediction-container {
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
.stat-card.info .stat-icon { background-color: #667eea; }

.stat-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #2d3748;
}

.stat-label {
  font-size: 0.9rem;
  color: #718096;
}

.main-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.secondary-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.chart-container h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-wrapper {
  position: relative;
  height: 350px;
  width: 100%;
}

.data-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.table-responsive {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  padding: 12px 15px;
  text-align: center;
  border-bottom: 1px solid #edf2f7;
}

th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #4a5568;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
}

tr:hover {
  background-color: #f8fafc;
}

.defect {
  color: #e53e3e;
  font-weight: bold;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.good-badge {
  background-color: #f0fff4;
  color: #38a169;
}

.defect-badge {
  background-color: #fff5f5;
  color: #e53e3e;
}

.detail-btn {
  padding: 6px 12px;
  background-color: #edf2f7;
  color: #4a5568;
  border: none;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.detail-btn:hover {
  background-color: #e2e8f0;
}

.pagination {
  margin-top: 1.5rem;
  text-align: center;
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
  .main-charts,
  .secondary-charts {
    grid-template-columns: 1fr;
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
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .header-section {
    padding: 1rem;
  }

  .prediction-container {
    padding: 1rem;
  }
}
</style>
