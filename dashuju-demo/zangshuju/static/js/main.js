// 图表实例
let missingNormalChart = null;
let missingDataChart = null;
let filteringChart = null;
let outlierChart = null;
let normalizationChart = null;

// 归一化数据存储
let normalizationData = null;

// Tab切换功能
function showTab(tabName) {
    // 隐藏所有tab内容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 移除所有按钮的active状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 显示选中的tab
    document.getElementById(tabName).classList.add('active');
    
    // 激活对应的按钮
    event.target.classList.add('active');
    
    // 加载对应的数据
    switch(tabName) {
        case 'missing':
            loadMissingData();
            break;
        case 'filtering':
            loadFilteringData();
            break;
        case 'outlier':
            loadOutlierData();
            break;
        case 'normalization':
            loadNormalizationData();
            break;
    }
}

// 加载数据缺失数据
async function loadMissingData() {
    try {
        const response = await fetch('/api/missing_data');
        const data = await response.json();
        
        // 更新信息面板
        document.getElementById('missingTotal').textContent = data.total_count;
        document.getElementById('missingCount').textContent = data.missing_count;
        document.getElementById('missingRate').textContent = 
            ((data.missing_count / data.total_count) * 100).toFixed(2) + '%';
        
        // 准备图表数据
        const labels = data.timestamps;
        const normalData = data.normal_data;
        
        const missingData = data.missing_data.map((val, idx) => {
            if (val === null) return null;
            return val;
        });
        
        // 创建正常数据图表（上图）
        const ctxNormal = document.getElementById('missingNormalChart').getContext('2d');
        if (missingNormalChart) {
            missingNormalChart.destroy();
        }
        missingNormalChart = new Chart(ctxNormal, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '正常数据',
                        data: normalData,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '温度 (°C)',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            font: {
                                size: 14
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 15,
                                weight: 'bold'
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        titleFont: {
                            size: 16
                        },
                        bodyFont: {
                            size: 14
                        },
                        padding: 12
                    }
                }
            }
        });
        
        // 创建缺失数据图表（下图）
        const ctxMissing = document.getElementById('missingDataChart').getContext('2d');
        if (missingDataChart) {
            missingDataChart.destroy();
        }
        missingDataChart = new Chart(ctxMissing, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '缺失数据',
                        data: missingData,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        pointRadius: 2,
                        pointHoverRadius: 4,
                        borderWidth: 2.5,
                        spanGaps: false  // 关键：不连接缺失值之间的点，形成断断续续的效果
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '温度 (°C)',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            font: {
                                size: 14
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 15,
                                weight: 'bold'
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        titleFont: {
                            size: 16
                        },
                        bodyFont: {
                            size: 14
                        },
                        padding: 12
                    }
                }
            }
        });
    } catch (error) {
        console.error('加载数据缺失数据失败:', error);
    }
}

// 加载数据滤波数据
async function loadFilteringData() {
    try {
        const response = await fetch('/api/filtering_data');
        const data = await response.json();
        
        document.getElementById('filteringCount').textContent = data.timestamps.length;
        
        const labels = data.timestamps;
        const cleanData = data.clean_signal;
        const noisyData = data.noisy_data;
        const filteredData = data.filtered_data;
        
        const ctx = document.getElementById('filteringChart').getContext('2d');
        
        if (filteringChart) {
            filteringChart.destroy();
        }
        
        filteringChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '干净信号',
                        data: cleanData,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: '噪声数据',
                        data: noisyData,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: '滤波后数据',
                        data: filteredData,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '温度 (°C)',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            font: {
                                size: 14
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 15,
                                weight: 'bold'
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        titleFont: {
                            size: 16
                        },
                        bodyFont: {
                            size: 14
                        },
                        padding: 12
                    }
                }
            }
        });
    } catch (error) {
        console.error('加载数据滤波数据失败:', error);
    }
}

// 加载离群值数据
async function loadOutlierData() {
    try {
        const response = await fetch('/api/outlier_data');
        const data = await response.json();
        
        document.getElementById('outlierMean').textContent = data.mean.toFixed(2);
        document.getElementById('outlierStd').textContent = data.std.toFixed(2);
        document.getElementById('outlierUpper').textContent = data.threshold_upper.toFixed(2);
        document.getElementById('outlierLower').textContent = data.threshold_lower.toFixed(2);
        document.getElementById('outlierCount').textContent = data.detected_outliers.length;
        
        const labels = data.timestamps;
        const normalData = data.normal_data;
        const outlierData = data.outlier_data;
        
        // 创建离群值数据集（只显示离群值点）
        const outlierPoints = new Array(data.outlier_data.length).fill(null);
        data.outlier_indices.forEach(idx => {
            outlierPoints[idx] = data.outlier_data[idx];
        });
        
        const ctx = document.getElementById('outlierChart').getContext('2d');
        
        if (outlierChart) {
            outlierChart.destroy();
        }
        
        outlierChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '正常数据',
                        data: normalData,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: '包含离群值的数据',
                        data: outlierData,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: '离群值',
                        data: outlierPoints,
                        borderColor: 'rgb(255, 206, 86)',
                        backgroundColor: 'rgba(255, 206, 86, 0.8)',
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        showLine: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '温度 (°C)',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            font: {
                                size: 14
                            }
                        },
                        grid: {
                            color: function(context) {
                                if (context.tick.value === data.threshold_upper || 
                                    context.tick.value === data.threshold_lower) {
                                    return 'rgba(255, 0, 0, 0.5)';
                                }
                                return 'rgba(0, 0, 0, 0.1)';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 15,
                                weight: 'bold'
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        titleFont: {
                            size: 16
                        },
                        bodyFont: {
                            size: 14
                        },
                        padding: 12
                    }
                }
            }
        });
    } catch (error) {
        console.error('加载离群值数据失败:', error);
    }
}

// 加载归一化数据
async function loadNormalizationData() {
    try {
        const response = await fetch('/api/normalization_data');
        normalizationData = await response.json();
        
        updateNormalizationChart();
    } catch (error) {
        console.error('加载归一化数据失败:', error);
    }
}

// 更新归一化图表
function updateNormalizationChart() {
    if (!normalizationData) return;
    
    const method = document.getElementById('normalizationMethod').value;
    let dataSource;
    
    if (method === 'original') {
        dataSource = normalizationData.original;
    } else if (method === 'minmax') {
        dataSource = normalizationData.minmax_normalized;
    } else {
        dataSource = normalizationData.zscore_normalized;
    }
    
    const labels = normalizationData.timestamps;
    const datasets = [
        {
            label: '温度',
            data: dataSource.temperature,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            tension: 0.1,
            pointRadius: 0
        },
        {
            label: '压力',
            data: dataSource.pressure,
            borderColor: 'rgb(54, 162, 235)',
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            tension: 0.1,
            pointRadius: 0
        },
        {
            label: '湿度',
            data: dataSource.humidity,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.1)',
            tension: 0.1,
            pointRadius: 0
        },
        {
            label: '转速',
            data: dataSource.rotation,
            borderColor: 'rgb(255, 206, 86)',
            backgroundColor: 'rgba(255, 206, 86, 0.1)',
            tension: 0.1,
            pointRadius: 0
        }
    ];
    
    const ctx = document.getElementById('normalizationChart').getContext('2d');
    
    if (normalizationChart) {
        normalizationChart.destroy();
    }
    
    let yAxisLabel = '数值';
    if (method === 'minmax') {
        yAxisLabel = '归一化值 (0-1)';
    } else if (method === 'zscore') {
        yAxisLabel = '标准化值 (Z-score)';
    }
    
    normalizationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                y: {
                    title: {
                        display: true,
                        text: yAxisLabel,
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        font: {
                            size: 14
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 15,
                            weight: 'bold'
                        },
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    titleFont: {
                        size: 16
                    },
                    bodyFont: {
                        size: 14
                    },
                    padding: 12
                }
            }
        }
    });
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadMissingData();
});

