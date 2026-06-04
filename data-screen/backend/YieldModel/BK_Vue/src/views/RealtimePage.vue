<template>
  <div class="realtime-container">
    <h1 class="page-title">设备实时监测</h1>

    <div class="control-panel">
      <button @click="toggleMonitoring" :class="{ 'active': isMonitoring }" class="monitor-btn">
        <i :class="isMonitoring ? 'fas fa-stop' : 'fas fa-play'"></i>
        {{ isMonitoring ? '停止监测' : '开始监测' }}
      </button>

      <div class="status-indicator" :class="{ 'active': isMonitoring }">
        <span class="pulse"></span>
        {{ isMonitoring ? '实时监测中' : '监测已停止' }}
      </div>

      <span class="update-status">
        <i class="fas fa-clock"></i>
        最后更新: {{ lastUpdate || '暂无数据' }}
      </span>

      <div class="refresh-rate">
        <i class="fas fa-sync-alt"></i>
        刷新频率:
        <select v-model="refreshInterval" @change="updateRefreshRate">
          <option value="500">0.5秒</option>
          <option value="1000">1秒</option>
          <option value="2000">2秒</option>
        </select>
      </div>
    </div>

    <div class="charts-container">
      <div class="chart-card">
        <h3>定位误差趋势</h3>
        <div class="chart-wrapper">
          <canvas ref="positionErrorChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h3>振动指标监控</h3>
        <div class="chart-wrapper">
          <canvas ref="vibrationChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h3>误差分布雷达图</h3>
        <div class="chart-wrapper">
          <canvas ref="errorRadarChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h3>综合指标仪表盘</h3>
        <div class="chart-wrapper">
          <canvas ref="gaugeChart"></canvas>
        </div>
      </div>
    </div>

    <div class="data-grid">
      <div class="data-category" v-for="(category, index) in groupedData" :key="index">
        <h3>{{ category.name }}</h3>
        <div class="data-item" v-for="item in category.items" :key="item.key">
          <span class="data-label">
            <i v-if="isWarningValue(item.key, item.value)" class="fas fa-exclamation-triangle warning-icon"></i>
            {{ item.label }}:
          </span>
          <span class="data-value" :class="{'warning': isWarningValue(item.key, item.value)}">
            <span class="value-animation">{{ formatValue(item.value) }}</span>
          </span>
          <span class="data-unit" v-if="getUnit(item.key)">{{ getUnit(item.key) }}</span>
        </div>
      </div>
    </div>

    <div class="raw-data-toggle" @click="showRawData = !showRawData">
      <i :class="showRawData ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
      {{ showRawData ? '隐藏原始数据' : '显示原始数据' }}
    </div>

    <transition name="slide">
      <div class="data-display" v-if="showRawData">
        <pre>{{ formattedData }}</pre>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, markRaw, nextTick, onMounted, onUnmounted } from 'vue';
import Chart from 'chart.js/auto';

export default {
  name: 'RealtimePage',
  setup() {
    const positionErrorChart = ref(null);
    const vibrationChart = ref(null);
    const errorRadarChart = ref(null);
    const gaugeChart = ref(null);

    return {
      positionErrorChart,
      vibrationChart,
      errorRadarChart,
      gaugeChart
    };
  },
  data() {
    return {
      isMonitoring: false,
      realtimeData: {},
      lastUpdate: null,
      refreshInterval: 500,
      interval: null,
      interpolationInterval: null,
      showRawData: false,
      chartsInitialized: false,
      warningThresholds: {
        'fit_error_X': 50,
        'fit_error_Y': 50,
        'vibration_X': 2.5,
        'vibration_Z': 2.5,
        'noise_X': 75,
        'positioing_error_X': 30,
        'positioing_error_Y': 30,
        'visual_error_X': 15,
        'visual_error_Y': 15
      },
      units: {
        'Speed_X': 'mm/s',
        'Speed_Y': 'mm/s',
        'Speed_Z': 'mm/s',
        'Speed_R': 'rpm',
        'positioing_error_X': 'μm',
        'positioing_error_Y': 'μm',
        'acceleration_X': 'm/s²',
        'acceleration_Y': 'm/s²',
        'acceleration_Z': 'm/s²',
        'acceleration_R': 'rad/s²',
        'visual_error_X': 'px',
        'visual_error_Y': 'px',
        'fit_error_X': 'μm',
        'fit_error_Y': 'μm',
        'vibration_X': 'g',
        'vibration_Z': 'g',
        'noise_X': 'dB'
      },
      previousData: null,
      interpolationSteps: 5,
      currentInterpolation: 0,
      chartDataHistory: {
        positionError: { x: [], y: [] },
        vibration: { x: [], z: [] }
      }
    }
  },
  computed: {
    formattedData() {
      // 过滤掉不需要显示的视觉坐标数据
      const filteredData = { ...this.realtimeData };
      const excludeKeys = [
        'visual_scanning_pixel_coordinate_X',
        'visual_scanning_pixel_coordinate_Y',
        'visual_setting_pixel_coordinate_X',
        'visual_setting_pixel_coordinate_Y',
        'visual_scanning_world_coordinate_X',
        'visual_scanning_world_coordinate_Y'
      ];
      
      excludeKeys.forEach(key => {
        delete filteredData[key];
      });
      
      return JSON.stringify(filteredData, null, 2);
    },
    groupedData() {
      return [
        {
          name: '运动控制',
          items: this.getDataItems([
            'Speed_X', 'Speed_Y', 'Speed_Z', 'Speed_R',
            'PLC_step',
            'absolute_position_X', 'absolute_position_Y',
            'offset_X', 'offset_Y', 'offset_R'
          ])
        },
        {
          name: '误差监测',
          items: this.getDataItems([
            'positioing_error_X', 'positioing_error_Y',
            'visual_error_X', 'visual_error_Y',
            'fit_error_X', 'fit_error_Y'
          ])
        },
        {
          name: '物理指标',
          items: this.getDataItems([
            'acceleration_X', 'acceleration_Y', 'acceleration_Z', 'acceleration_R',
            'vibration_X', 'vibration_Z',
            'noise_X'
          ])
        },
        {
          name: '视觉系统',
          items: this.getDataItems([
            'Grating_feedback_X', 'Grating_feedback_Y'
          ])
        }
      ]
    },
    interpolatedData() {
      if (!this.previousData || this.currentInterpolation === 0) {
        return this.realtimeData;
      }

      const interpolated = {};
      const progress = this.currentInterpolation / this.interpolationSteps;

      Object.keys(this.realtimeData).forEach(key => {
        if (typeof this.realtimeData[key] === 'number' && typeof this.previousData[key] === 'number') {
          interpolated[key] = this.previousData[key] +
            (this.realtimeData[key] - this.previousData[key]) * progress;
        } else {
          interpolated[key] = this.realtimeData[key];
        }
      });

      return interpolated;
    }
  },
  methods: {
    async toggleMonitoring() {
      if (this.isMonitoring) {
        clearInterval(this.interval);
        clearInterval(this.interpolationInterval);
        this.isMonitoring = false;
      } else {
        await this.fetchData();
        this.interval = setInterval(this.fetchData, this.refreshInterval);
        this.isMonitoring = true;
      }
    },
    updateRefreshRate() {
      if (this.isMonitoring) {
        clearInterval(this.interval);
        this.interval = setInterval(this.fetchData, this.refreshInterval);
      }
    },
    async fetchData() {
      try {
        const mockData = this.generateMockData();
        const response = await fetch('http://localhost:5000/api/realtime');
        const data = await response.json().catch(() => mockData);

        if (data.status === 'success' || data.timestamp) {
          this.previousData = {...this.realtimeData};
          this.realtimeData = data.data || data;
          this.lastUpdate = new Date().toLocaleTimeString();
          this.currentInterpolation = 0;
          this.startInterpolation();
        }
      } catch (error) {
        console.error('获取数据失败:', error);
        this.previousData = {...this.realtimeData};
        this.realtimeData = this.generateMockData();
        this.lastUpdate = new Date().toLocaleTimeString();
        this.currentInterpolation = 0;
        this.startInterpolation();
      }
    },
    startInterpolation() {
      clearInterval(this.interpolationInterval);
      const stepInterval = this.refreshInterval / this.interpolationSteps;

      this.interpolationInterval = setInterval(() => {
        if (this.currentInterpolation < this.interpolationSteps) {
          this.currentInterpolation++;
          this.updateCharts();
        } else {
          clearInterval(this.interpolationInterval);
        }
      }, stepInterval);
    },
    generateMockData() {
      const mockData = {};
      const now = new Date();
      const timeFactor = now.getSeconds() / 60;

      Object.keys(this.units).forEach(key => {
        let baseValue, fluctuation;

        if (key.includes('error') || key.includes('vibration')) {
          baseValue = 5 + Math.random() * 20;
          fluctuation = Math.sin(timeFactor * Math.PI * 4) * 15;
        } else {
          baseValue = Math.random() * 10;
          fluctuation = Math.sin(timeFactor * Math.PI * 2) * 5;
        }

        mockData[key] = parseFloat((baseValue + fluctuation).toFixed(3));
      });

      mockData.PLC_step = Math.floor(Math.random() * 100);
      mockData.absolute_position_X = (Math.random() * 1000).toFixed(3);
      mockData.absolute_position_Y = (Math.random() * 1000).toFixed(3);

      return mockData;
    },
    async initCharts() {
      await nextTick();

      try {
        // 定位误差趋势图
        const positionErrorCtx = this.$refs.positionErrorChart?.getContext('2d');
        if (positionErrorCtx) {
          this.positionErrorChart = markRaw(new Chart(positionErrorCtx, {
            type: 'line',
            data: {
              labels: Array(20).fill(''),
              datasets: [
                {
                  label: 'X轴定位误差',
                  data: Array(20).fill(0),
                  borderColor: '#FF6B6B',
                  backgroundColor: 'rgba(255, 107, 107, 0.1)',
                  tension: 0.4,
                  fill: true,
                  borderWidth: 2,
                  pointRadius: 0,
                  pointHoverRadius: 4
                },
                {
                  label: 'Y轴定位误差',
                  data: Array(20).fill(0),
                  borderColor: '#4ECDC4',
                  backgroundColor: 'rgba(78, 205, 196, 0.1)',
                  tension: 0.4,
                  fill: true,
                  borderWidth: 2,
                  pointRadius: 0,
                  pointHoverRadius: 4
                }
              ]
            },
            options: {
              responsive: true,
              maintainAspectRatio: true,
              animation: { duration: 300 },
              plugins: {
                legend: {
                  position: 'top',
                  labels: {
                    color: '#333',
                    font: {
                      size: 12,
                      family: "'Roboto', sans-serif"
                    }
                  }
                },
                tooltip: {
                  mode: 'index',
                  intersect: false,
                  backgroundColor: 'rgba(0, 0, 0, 0.7)',
                  titleFont: {
                    family: "'Roboto', sans-serif"
                  },
                  bodyFont: {
                    family: "'Roboto', sans-serif"
                  },
                  callbacks: {
                    label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(2)} μm`
                  }
                }
              },
              scales: {
                y: { 
                  beginAtZero: true, 
                  title: { 
                    display: true, 
                    text: '误差值 (μm)',
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 12
                    }
                  },
                  grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                  },
                  ticks: {
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 10
                    }
                  }
                },
                x: { 
                  grid: { 
                    display: false 
                  },
                  ticks: {
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 10
                    }
                  }
                }
              }
            }
          }));
        }

        // 振动指标监控图
        const vibrationCtx = this.$refs.vibrationChart?.getContext('2d');
        if (vibrationCtx) {
          this.vibrationChart = markRaw(new Chart(vibrationCtx, {
            type: 'bar',
            data: {
              labels: ['X轴振动', 'Z轴振动'],
              datasets: [{
                label: '振动值 (g)',
                data: [0, 0],
                backgroundColor: [
                  'rgba(255, 159, 64, 0.7)',
                  'rgba(75, 192, 192, 0.7)'
                ],
                borderColor: [
                  'rgb(255, 159, 64)',
                  'rgb(75, 192, 192)'
                ],
                borderWidth: 1
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: true,
              plugins: {
                legend: {
                  position: 'top',
                  labels: {
                    color: '#333',
                    font: {
                      size: 12,
                      family: "'Roboto', sans-serif"
                    }
                  }
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: '振动值 (g)',
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 12
                    }
                  },
                  grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                  },
                  ticks: {
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 10
                    }
                  }
                },
                x: {
                  grid: {
                    display: false
                  },
                  ticks: {
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 10
                    }
                  }
                }
              }
            }
          }));
        }

        // 误差分布雷达图
        const errorRadarCtx = this.$refs.errorRadarChart?.getContext('2d');
        if (errorRadarCtx) {
          this.errorRadarChart = markRaw(new Chart(errorRadarCtx, {
            type: 'radar',
            data: {
              labels: ['X轴定位误差', 'Y轴定位误差', 'X轴贴合误差', 'Y轴贴合误差', 'X轴视觉误差', 'Y轴视觉误差'],
              datasets: [{
                label: '当前误差值',
                data: [0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                pointBackgroundColor: 'rgb(54, 162, 235)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(54, 162, 235)'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: true,
              plugins: {
                legend: {
                  position: 'top',
                  labels: {
                    color: '#333',
                    font: {
                      size: 12,
                      family: "'Roboto', sans-serif"
                    }
                  }
                }
              },
              scales: {
                r: {
                  angleLines: {
                    color: 'rgba(0, 0, 0, 0.1)'
                  },
                  grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                  },
                  pointLabels: {
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 10
                    }
                  },
                  ticks: {
                    color: '#666',
                    font: {
                      family: "'Roboto', sans-serif",
                      size: 10
                    },
                    backdropColor: 'transparent'
                  }
                }
              }
            }
          }));
        }

        // 综合指标仪表盘
        const gaugeCtx = this.$refs.gaugeChart?.getContext('2d');
        if (gaugeCtx) {
          this.gaugeChart = markRaw(new Chart(gaugeCtx, {
            type: 'doughnut',
            data: {
              labels: ['正常指标', '警告指标', '危险指标'],
              datasets: [{
                data: [80, 15, 5],
                backgroundColor: [
                  'rgba(46, 204, 113, 0.8)',
                  'rgba(241, 196, 15, 0.8)',
                  'rgba(231, 76, 60, 0.8)'
                ],
                borderColor: [
                  'rgb(46, 204, 113)',
                  'rgb(241, 196, 15)',
                  'rgb(231, 76, 60)'
                ],
                borderWidth: 1,
                circumference: 180,
                rotation: 270
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: true,
              plugins: {
                legend: {
                  position: 'bottom',
                  labels: {
                    color: '#333',
                    font: {
                      size: 11,
                      family: "'Roboto', sans-serif"
                    }
                  }
                },
                tooltip: {
                  callbacks: {
                    label: (context) => `${context.label}: ${context.parsed}%`
                  }
                }
              },
              cutout: '70%'
            }
          }));
        }

        this.chartsInitialized = true;
      } catch (error) {
        console.error('图表初始化失败:', error);
        this.chartsInitialized = false;
      }
    },
    updateCharts() {
      if (!this.chartsInitialized) return;

      const data = this.interpolatedData;
      const now = new Date().toLocaleTimeString();

      try {
        // 更新定位误差趋势图
        if (this.positionErrorChart?.data?.datasets) {
          const labels = this.positionErrorChart.data.labels;
          labels.push(now);
          if (labels.length > 20) labels.shift();

          this.positionErrorChart.data.datasets[0].data.push(data.positioing_error_X || 0);
          this.positionErrorChart.data.datasets[1].data.push(data.positioing_error_Y || 0);

          if (this.positionErrorChart.data.datasets[0].data.length > 20) {
            this.positionErrorChart.data.datasets.forEach(d => d.data.shift());
          }
          this.positionErrorChart.update('none');
        }

        // 更新振动指标监控图
        if (this.vibrationChart?.data?.datasets) {
          this.vibrationChart.data.datasets[0].data = [
            data.vibration_X || 0,
            data.vibration_Z || 0
          ];
          this.vibrationChart.update('none');
        }

        // 更新误差分布雷达图
        if (this.errorRadarChart?.data?.datasets) {
          this.errorRadarChart.data.datasets[0].data = [
            data.positioing_error_X || 0,
            data.positioing_error_Y || 0,
            data.fit_error_X || 0,
            data.fit_error_Y || 0,
            data.visual_error_X || 0,
            data.visual_error_Y || 0
          ];
          this.errorRadarChart.update('none');
        }

        // 更新综合指标仪表盘
        if (this.gaugeChart?.data?.datasets) {
          // 根据警告阈值计算指标状态
          let normal = 0;
          let warning = 0;
          let danger = 0;
          
          Object.keys(this.warningThresholds).forEach(key => {
            if (typeof data[key] === 'number') {
              const value = Math.abs(data[key]);
              if (value > this.warningThresholds[key] * 1.2) {
                danger++;
              } else if (value > this.warningThresholds[key]) {
                warning++;
              } else {
                normal++;
              }
            }
          });
          
          const total = normal + warning + danger;
          if (total > 0) {
            this.gaugeChart.data.datasets[0].data = [
              Math.round((normal / total) * 100),
              Math.round((warning / total) * 100),
              Math.round((danger / total) * 100)
            ];
            this.gaugeChart.update('none');
          }
        }

      } catch (error) {
        console.error('更新图表失败:', error);
        this.chartsInitialized = false;
      }
    },
    getDataItems(keys) {
      return keys.map(key => ({
        key,
        label: this.formatLabel(key),
        value: this.interpolatedData[key] ?? 'N/A'
      }));
    },
    formatLabel(key) {
      const labels = {
        'Speed_X': 'X轴速度',
        'Speed_Y': 'Y轴速度',
        'Speed_Z': 'Z轴速度',
        'Speed_R': '旋转速度',
        'positioing_error_X': 'X轴定位误差',
        'positioing_error_Y': 'Y轴定位误差',
        'fit_error_X': 'X轴贴合误差',
        'fit_error_Y': 'Y轴贴合误差',
        'vibration_X': 'X轴振动',
        'vibration_Z': 'Z轴振动',
        'noise_X': '工作噪音',
        'PLC_step': 'PLC步数',
        'visual_error_X': 'X轴视觉误差',
        'visual_error_Y': 'Y轴视觉误差',
        'Grating_feedback_X': '光栅反馈X',
        'Grating_feedback_Y': '光栅反馈Y'
      };
      return labels[key] || key;
    },
    formatValue(value) {
      return typeof value === 'number' ? value.toFixed(3) : value;
    },
    isWarningValue(key, value) {
      return typeof value === 'number' &&
             this.warningThresholds[key] &&
             Math.abs(value) > this.warningThresholds[key];
    },
    getUnit(key) {
      return this.units[key];
    },
    destroyCharts() {
      [this.positionErrorChart, this.vibrationChart,
       this.errorRadarChart, this.gaugeChart].forEach(chart => {
        if (chart?.destroy) chart.destroy();
      });
      this.chartsInitialized = false;
    }
  },
  async mounted() {
    await this.initCharts();
    this.fetchData();
  },
  beforeUnmount() {
    this.destroyCharts();
    clearInterval(this.interval);
    clearInterval(this.interpolationInterval);
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');

.realtime-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Roboto', sans-serif;
  color: #333;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.page-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
  font-weight: 700;
  position: relative;
  padding-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 3px;
  background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
}

.control-panel {
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  padding: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
  border-radius: 12px;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.monitor-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #4ECDC4, #44A08D);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  font-size: 0.95rem;
}

.monitor-btn.active {
  background: linear-gradient(135deg, #FF6B6B, #C44D58);
}

.monitor-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: #f1f2f6;
  border-radius: 20px;
  font-size: 0.9em;
  color: #7f8c8d;
  font-weight: 500;
}

.status-indicator.active {
  background-color: rgba(78, 205, 196, 0.15);
  color: #44A08D;
}

.status-indicator.active .pulse {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #4ECDC4;
  box-shadow: 0 0 0 0 rgba(78, 205, 196, 0.7);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(78, 205, 196, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 10px rgba(78, 205, 196, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(78, 205, 196, 0);
  }
}

.update-status, .refresh-rate {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
  color: #555;
  background: rgba(0, 0, 0, 0.03);
  padding: 8px 12px;
  border-radius: 6px;
}

.refresh-rate select {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background-color: white;
  cursor: pointer;
  font-family: 'Roboto', sans-serif;
  font-size: 0.9em;
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 25px;
  margin: 30px 0;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  height: 320px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
}

.chart-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #2c3e50;
  font-weight: 600;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-card h3::before {
  content: '📊';
  font-size: 1.2em;
}

.chart-wrapper {
  width: 100%;
  height: calc(100% - 40px);
  position: relative;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px;
  margin: 30px 0;
}

.data-category {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.data-category::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
}

.data-category:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.data-category h3 {
  margin-top: 0;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
  color: #2c3e50;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
}

.data-item {
  display: flex;
  margin: 15px 0;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px dashed #f1f2f6;
}

.data-item:last-child {
  border-bottom: none;
}

.data-label {
  flex: 1;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
}

.warning-icon {
  color: #FF6B6B;
  font-size: 0.9em;
}

.data-value {
  margin: 0 8px;
  font-family: 'Roboto Mono', monospace;
  position: relative;
  font-weight: 500;
  font-size: 0.95rem;
}

.value-animation {
  display: inline-block;
  transition: all 0.3s ease;
}

.data-value.warning {
  color: #FF6B6B;
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.data-unit {
  color: #7f8c8d;
  font-size: 0.8em;
  min-width: 30px;
  text-align: right;
  font-weight: 500;
}

.raw-data-toggle {
  margin: 25px 0 15px;
  color: #4ECDC4;
  cursor: pointer;
  text-align: center;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  font-weight: 500;
  padding: 10px;
  border-radius: 8px;
  background: rgba(78, 205, 196, 0.1);
}

.raw-data-toggle:hover {
  color: #44A08D;
  background: rgba(78, 205, 196, 0.2);
  transform: translateY(-2px);
}

.data-display {
  background-color: #2c3e50;
  border: 1px solid #34495e;
  border-radius: 8px;
  padding: 20px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Roboto Mono', monospace;
  font-size: 0.85em;
  color: #ecf0f1;
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
}

.slide-enter-from, .slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding: 0 20px;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
  color: #ecf0f1;
}

@media (max-width: 1024px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .data-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .realtime-container {
    padding: 15px;
  }
  
  .control-panel {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .chart-card {
    height: 280px;
  }
  
  .data-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.5rem;
  }
  
  .chart-card {
    padding: 15px;
    height: 250px;
  }
  
  .data-category {
    padding: 15px;
  }
}
</style>