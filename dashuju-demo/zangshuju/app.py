from flask import Flask, render_template, jsonify
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def convert_to_native(obj):
    """将numpy类型转换为Python原生类型，以便JSON序列化"""
    if obj is None:
        return None
    elif isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_to_native(item) for item in obj]
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_native(value) for key, value in obj.items()}
    else:
        return obj

def generate_timestamps(days=30, points_per_day=24):
    """生成时间戳"""
    start_date = datetime.now() - timedelta(days=days)
    timestamps = []
    for i in range(days * points_per_day):
        timestamps.append(start_date + timedelta(hours=i))
    return timestamps

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/missing_data')
def missing_data():
    """数据缺失演示数据"""
    try:
        timestamps = generate_timestamps(30, 24)
        
        # 生成正常数据
        base_temp = 25
        normal_data = [float(base_temp + 5 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 1)) 
                       for i in range(len(timestamps))]
        
        # 创建断断续续的缺失效果：将数据分成多个段，段之间用缺失值连接
        missing_data = []
        total_points = len(timestamps)
        missing_indices = []
        
        # 定义数据段的长度范围（每个段包含的数据点数）
        segment_min_length = 20  # 最小段长度
        segment_max_length = 60  # 最大段长度
        gap_min_length = 5       # 最小缺失长度
        gap_max_length = 15      # 最大缺失长度
        
        current_idx = 0
        segment_num = 0
        
        while current_idx < total_points:
            # 确定当前段的长度
            remaining_points = total_points - current_idx
            segment_length = min(
                np.random.randint(segment_min_length, segment_max_length + 1),
                remaining_points
            )
            
            # 添加当前段的数据
            for i in range(segment_length):
                if current_idx + i < total_points:
                    missing_data.append(normal_data[current_idx + i])
                else:
                    break
            
            current_idx += segment_length
            
            # 如果不是最后一段，添加缺失值（gap）
            if current_idx < total_points:
                gap_length = min(
                    np.random.randint(gap_min_length, gap_max_length + 1),
                    total_points - current_idx
                )
                
                # 记录缺失的索引
                for i in range(gap_length):
                    if current_idx + i < total_points:
                        missing_data.append(None)
                        missing_indices.append(current_idx + i)
                
                current_idx += gap_length
                segment_num += 1
        
        # 确保长度一致
        while len(missing_data) < total_points:
            missing_data.append(None)
            if len(missing_data) - 1 not in missing_indices:
                missing_indices.append(len(missing_data) - 1)
        
        missing_data = missing_data[:total_points]
        
        result = {
            'timestamps': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
            'normal_data': convert_to_native(normal_data),
            'missing_data': convert_to_native(missing_data),
            'missing_indices': convert_to_native(sorted(missing_indices)),
            'missing_count': int(len(missing_indices)),
            'total_count': int(len(timestamps))
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filtering_data')
def filtering_data():
    """数据滤波演示数据"""
    try:
        timestamps = generate_timestamps(7, 24)
        
        # 生成带噪声的数据
        clean_signal = [float(25 + 5 * np.sin(i * 2 * np.pi / 24)) for i in range(len(timestamps))]
        noise = np.random.normal(0, 3, len(timestamps))
        
        # 添加一些高频噪声
        high_freq_noise = [float(2 * np.sin(i * 10 * 2 * np.pi / 24)) for i in range(len(timestamps))]
        
        noisy_data = [float(clean_signal[i] + noise[i] + high_freq_noise[i]) for i in range(len(timestamps))]
        
        # 简单移动平均滤波
        window_size = 5
        filtered_data = []
        for i in range(len(noisy_data)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(noisy_data), i + window_size // 2 + 1)
            filtered_data.append(float(np.mean(noisy_data[start_idx:end_idx])))
        
        result = {
            'timestamps': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
            'clean_signal': convert_to_native(clean_signal),
            'noisy_data': convert_to_native(noisy_data),
            'filtered_data': convert_to_native(filtered_data)
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/outlier_data')
def outlier_data():
    """离群值演示数据"""
    try:
        timestamps = generate_timestamps(30, 24)
        
        # 生成正常数据
        normal_data = [float(25 + 5 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 1)) 
                       for i in range(len(timestamps))]
        
        # 添加离群值
        outlier_data = normal_data.copy()
        outlier_indices = np.random.choice(len(timestamps), size=int(len(timestamps) * 0.05), replace=False)
        outlier_indices = outlier_indices.tolist()
        
        for idx in outlier_indices:
            # 随机添加正或负的离群值
            if np.random.random() > 0.5:
                outlier_data[idx] = float(normal_data[idx] + np.random.uniform(15, 25))
            else:
                outlier_data[idx] = float(normal_data[idx] - np.random.uniform(15, 25))
        
        # 计算统计信息用于检测离群值
        mean_val = float(np.mean(normal_data))
        std_val = float(np.std(normal_data))
        threshold_upper = float(mean_val + 3 * std_val)
        threshold_lower = float(mean_val - 3 * std_val)
        
        detected_outliers = []
        for i, val in enumerate(outlier_data):
            if val > threshold_upper or val < threshold_lower:
                detected_outliers.append(i)
        
        result = {
            'timestamps': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
            'normal_data': convert_to_native(normal_data),
            'outlier_data': convert_to_native(outlier_data),
            'outlier_indices': convert_to_native(outlier_indices),
            'detected_outliers': convert_to_native(detected_outliers),
            'threshold_upper': threshold_upper,
            'threshold_lower': threshold_lower,
            'mean': mean_val,
            'std': std_val
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/normalization_data')
def normalization_data():
    """归一化演示数据"""
    try:
        timestamps = generate_timestamps(30, 24)
        
        # 生成不同量纲的数据
        # 温度数据（20-35度）
        temperature = [float(25 + 5 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 1)) 
                       for i in range(len(timestamps))]
        
        # 压力数据（100-200 kPa）
        pressure = [float(150 + 30 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 5)) 
                    for i in range(len(timestamps))]
        
        # 湿度数据（40-80%）
        humidity = [float(60 + 15 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 3)) 
                    for i in range(len(timestamps))]
        
        # 转速数据（1000-3000 rpm）
        rotation = [float(2000 + 500 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 50)) 
                    for i in range(len(timestamps))]
        
        # Min-Max归一化
        def min_max_normalize(data):
            min_val = min(data)
            max_val = max(data)
            if max_val == min_val:
                return [0.0] * len(data)
            return [float((x - min_val) / (max_val - min_val)) for x in data]
        
        # Z-score归一化
        def z_score_normalize(data):
            mean_val = float(np.mean(data))
            std_val = float(np.std(data))
            if std_val == 0:
                return [0.0] * len(data)
            return [float((x - mean_val) / std_val) for x in data]
        
        temp_minmax = min_max_normalize(temperature)
        pressure_minmax = min_max_normalize(pressure)
        humidity_minmax = min_max_normalize(humidity)
        rotation_minmax = min_max_normalize(rotation)
        
        temp_zscore = z_score_normalize(temperature)
        pressure_zscore = z_score_normalize(pressure)
        humidity_zscore = z_score_normalize(humidity)
        rotation_zscore = z_score_normalize(rotation)
        
        result = {
            'timestamps': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
            'original': {
                'temperature': convert_to_native(temperature),
                'pressure': convert_to_native(pressure),
                'humidity': convert_to_native(humidity),
                'rotation': convert_to_native(rotation)
            },
            'minmax_normalized': {
                'temperature': convert_to_native(temp_minmax),
                'pressure': convert_to_native(pressure_minmax),
                'humidity': convert_to_native(humidity_minmax),
                'rotation': convert_to_native(rotation_minmax)
            },
            'zscore_normalized': {
                'temperature': convert_to_native(temp_zscore),
                'pressure': convert_to_native(pressure_zscore),
                'humidity': convert_to_native(humidity_zscore),
                'rotation': convert_to_native(rotation_zscore)
            }
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5302)

