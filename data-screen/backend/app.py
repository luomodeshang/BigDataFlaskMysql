"""
工业大数据分析云平台 - Flask 后端
精简版：仅保留大屏所需的API接口
"""
import sys
import io
import os
import math
import logging
import random
from datetime import datetime, timedelta
import pymysql
from configparser import ConfigParser
from collections import deque

from flask import Flask, jsonify, render_template
from flask_cors import CORS

# 设置标准输出编码为UTF-8（解决Windows中文乱码问题）
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# ==================== 配置常量 ====================
VIBRATION_THRESHOLD = 16.0
NOISE_THRESHOLD = 90.0
TEMPERATURE_THRESHOLD = 5.0
MAX_WAVE_POINTS = 30
wave_buffer = deque(maxlen=MAX_WAVE_POINTS)

# ==================== 数据获取模块 ====================
try:
    from data_fetcher import (
        Connect_SQL, 
        Output_normalize_PLC_single_workpiece, 
        Yield_columns,
        calculate_yield_from_data,
        calculate_production_stats_from_db,
        get_vibration_history_from_db,
        init_database_index
    )
    DATA_FETCHER_AVAILABLE = True
    logging.info("数据获取模块加载成功，将使用真实数据库数据")
except Exception as e:
    logging.error(f"数据获取模块加载失败: {e}")
    DATA_FETCHER_AVAILABLE = False
    Yield_columns = []

# 数据库列配置
DB_COLUMNS = (init_database_index() + ['creation_date']) if DATA_FETCHER_AVAILABLE else []

# ==================== 工具函数 ====================
def normalize_ratio(value, threshold):
    """归一化比率计算"""
    if threshold <= 0:
        return 0.0
    ratio = value / threshold
    return round(max(0.0, ratio), 3)

def ensure_data_fetcher():
    """确保数据获取模块可用"""
    if not DATA_FETCHER_AVAILABLE:
        raise RuntimeError("数据获取模块未加载，无法读取真实数据")

def connect_sql(begin_time=None, end_time=None, table_name='bk_datamodel'):
    """连接MySQL数据库"""
    if DATA_FETCHER_AVAILABLE:
        try:
            return Connect_SQL(begin_time, end_time, table_name)
        except Exception as e:
            logging.error(f"通过数据获取模块连接数据库失败: {e}")
            return None
    return None

def row_to_dict(row):
    """将数据库行转换为字典"""
    if not row or not DB_COLUMNS:
        return {}
    result = {}
    length = min(len(DB_COLUMNS), len(row))
    for idx in range(length):
        result[DB_COLUMNS[idx]] = row[idx]
    return result

def fetch_normalized_data(begin_time, end_time, strict=True):
    """获取指定时间段的规范化数据"""
    ensure_data_fetcher()
    normalized = Output_normalize_PLC_single_workpiece(
        begin_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time.strftime('%Y-%m-%d %H:%M:%S')
    )
    if not normalized:
        if strict:
            raise RuntimeError("无法从数据库获取规范化数据")
        return []
    return normalized

def fetch_today_workpiece_count():
    """获取当天工件总数"""
    if not DATA_FETCHER_AVAILABLE:
        return None
    try:
        now = datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        normalized = Output_normalize_PLC_single_workpiece(
            day_start.strftime('%Y-%m-%d %H:%M:%S'),
            now.strftime('%Y-%m-%d %H:%M:%S')
        )
        if normalized:
            return len(normalized)
    except Exception as exc:
        logging.warning(f"获取当日工件数失败: {exc}")
    return None

# ==================== 虚拟数据管理器 ====================
class VirtualYieldManager:
    """生成并缓存虚拟的产量/良率数据"""
    def __init__(self):
        self.snapshot_date = None
        self.snapshot = None
        self.daily_series_cache = None
        self.daily_series_date = None
        self.last_real_count = None

    def _build_snapshot(self):
        base_total = random.randint(950, 1350)
        quality_rate = round(random.uniform(92.5, 98.5), 1)
        quality_products = int(base_total * quality_rate / 100)
        defect_count = base_total - quality_products
        real_count = fetch_today_workpiece_count()
        if real_count is None and self.last_real_count is not None:
            real_count = self.last_real_count
        if real_count is None:
            real_count = 0
        self.last_real_count = real_count
        return {
            "total_production": base_total,
            "quality_products": quality_products,
            "quality_rate": quality_rate,
            "defect_count": defect_count,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "real_workpiece_count": real_count
        }

    def get_snapshot(self):
        today = datetime.now().date()
        if self.snapshot is None or self.snapshot_date != today:
            self.snapshot = self._build_snapshot()
            self.snapshot_date = today
            self.daily_series_cache = None
            self.daily_series_date = None
        return self.snapshot

    def get_daily_series(self, days=30):
        today = datetime.now().date()
        if (self.daily_series_cache is None or 
            self.daily_series_date != today or 
            len(self.daily_series_cache) != days):
            snapshot = self.get_snapshot()
            base_total = snapshot["total_production"]
            base_rate = snapshot["quality_rate"]
            series = []
            now = datetime.now()
            for offset in range(days - 1, -1, -1):
                day = now - timedelta(days=offset)
                date_label = day.strftime('%m/%d')
                total = max(200, int(base_total * random.uniform(0.82, 1.18)))
                rate = max(88.0, min(99.5, round(random.gauss(base_rate, 1.0), 1)))
                quality = int(total * rate / 100)
                series.append({
                    "date": date_label,
                    "total_production": total,
                    "quality_products": quality,
                    "quality_rate": rate
                })
            self.daily_series_cache = series
            self.daily_series_date = today
        return self.daily_series_cache[:days]

virtual_yield_manager = VirtualYieldManager()

def get_virtual_production_snapshot():
    return virtual_yield_manager.get_snapshot()

def get_virtual_daily_series(days=30):
    return virtual_yield_manager.get_daily_series(days)

# ==================== 模拟数据函数 ====================
def mock_production_snapshot():
    base_production = 12000
    base_quality_rate = 95.0
    daily_production = base_production + random.randint(-500, 800)
    quality_products = int(daily_production * (base_quality_rate + random.uniform(-2, 2)) / 100)
    quality_rate = round(quality_products / daily_production * 100, 1)
    return {
        "total_production": daily_production,
        "quality_products": quality_products,
        "quality_rate": quality_rate,
        "defect_count": daily_production - quality_products
    }

def mock_equipment_snapshot():
    """设备快照 - 5台设备，1台在线"""
    equipment_rate = 20.0
    energy_efficiency = 92.0 + random.uniform(-2, 2)
    return {
        "online_equipment": 1,
        "total_equipment": 5,
        "offline_equipment": 4,
        "equipment_rate": round(equipment_rate, 1),
        "energy_efficiency": round(energy_efficiency, 1)
    }

def mock_vibration_history(days=7):
    data = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - 1 - i)
        date_str = f"{date.month}/{date.day}"
        base_noise = 60 + 20 * math.sin(2 * math.pi * (datetime.now().hour + i * 24) / 24)
        noise = int(max(20, min(100, base_noise + random.uniform(-15, 15))))
        x_vibration = round(random.uniform(2, 7), 3)
        z_vibration = round(random.uniform(3, 9), 3)
        temperature = round(random.uniform(1, 3), 2)
        data.append({
            "date": date_str,
            "noise": noise,
            "x_vibration": x_vibration,
            "z_vibration": z_vibration,
            "temperature": temperature,
            "noise_ratio": normalize_ratio(noise, NOISE_THRESHOLD),
            "x_vibration_ratio": normalize_ratio(x_vibration, VIBRATION_THRESHOLD),
            "z_vibration_ratio": normalize_ratio(z_vibration, VIBRATION_THRESHOLD),
            "temperature_ratio": normalize_ratio(temperature, TEMPERATURE_THRESHOLD)
        })
    return data

def mock_device_status():
    """设备状态模拟 - 5台设备，1台在线"""
    return {
        "fault_count": 0,
        "running_hours": int((datetime.now() - datetime(2025, 10, 1)).total_seconds() / 3600),
        "maintenance_count": 12,
        "standby_count": 4,
        "online_count": 1,
        "total_count": 5
    }

# ==================== 数据获取函数 ====================
def fetch_equipment_stats():
    ensure_data_fetcher()
    end_time = datetime.now()
    begin_time = end_time - timedelta(hours=24)
    rows = connect_sql(
        begin_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time.strftime('%Y-%m-%d %H:%M:%S'),
        table_name='bk_datamodel'
    )
    if not rows:
        raise RuntimeError("无法从数据库获取设备数据")
    valid_records = len(rows)
    expected_records_per_hour = 120
    equipment_rate = min(100, (valid_records / (24 * expected_records_per_hour)) * 100)
    energy_efficiency = max(0, min(100, equipment_rate * 0.95))
    return {
        "online_equipment": 1,
        "equipment_rate": round(equipment_rate, 1),
        "energy_efficiency": round(energy_efficiency, 1)
    }

def fetch_device_status_stats():
    """设备状态统计 - 5台设备，1台在线，4台离线"""
    running_hours = int((datetime.now() - datetime(2025, 10, 1)).total_seconds() / 3600)
    return {
        "fault_count": 0,
        "running_hours": running_hours,
        "maintenance_count": 12,
        "standby_count": 4,
        "online_count": 1,
        "total_count": 5
    }

def seed_wave_buffer_from_history(history):
    if not history:
        return
    wave_buffer.clear()
    for item in history[-MAX_WAVE_POINTS:]:
        wave_buffer.append({
            "date": item["date"],
            "noise": item["noise"],
            "x_vibration": item["x_vibration"],
            "z_vibration": item["z_vibration"],
            "temperature": item["temperature"],
            "x_vibration_ratio": item.get("x_vibration_ratio", normalize_ratio(item["x_vibration"], VIBRATION_THRESHOLD)),
            "z_vibration_ratio": item.get("z_vibration_ratio", normalize_ratio(item["z_vibration"], VIBRATION_THRESHOLD)),
            "noise_ratio": item.get("noise_ratio", normalize_ratio(item["noise"], NOISE_THRESHOLD)),
            "temperature_ratio": item.get("temperature_ratio", normalize_ratio(item["temperature"], TEMPERATURE_THRESHOLD))
        })

def create_wave_point(base_sample):
    timestamp = datetime.now()
    base_noise = base_sample.get("noise", 60)
    base_x = base_sample.get("x_vibration", 4.0)
    base_z = base_sample.get("z_vibration", 6.0)
    base_temp = base_sample.get("temperature", 2.0)
    noise = max(15, min(120, base_noise + random.uniform(-3, 3)))
    x_vibration = max(0, base_x + random.uniform(-0.8, 0.8))
    z_vibration = max(0, base_z + random.uniform(-0.8, 0.8))
    temperature = max(0, base_temp + random.uniform(-0.2, 0.2))
    return {
        "date": timestamp.strftime('%H:%M:%S'),
        "noise": round(noise, 2),
        "x_vibration": round(x_vibration, 3),
        "z_vibration": round(z_vibration, 3),
        "temperature": round(temperature, 2),
        "noise_ratio": normalize_ratio(noise, NOISE_THRESHOLD),
        "x_vibration_ratio": normalize_ratio(x_vibration, VIBRATION_THRESHOLD),
        "z_vibration_ratio": normalize_ratio(z_vibration, VIBRATION_THRESHOLD),
        "temperature_ratio": normalize_ratio(temperature, TEMPERATURE_THRESHOLD)
    }

# ==================== 路由：页面 ====================
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

# ==================== 路由：大屏API ====================
@app.route('/api/production')
def get_production_data():
    """获取产量数据API"""
    try:
        snapshot = get_virtual_production_snapshot()
        return jsonify(snapshot)
    except Exception as e:
        logging.warning(f"获取产量数据失败: {e}")
        return jsonify(mock_production_snapshot())

@app.route('/api/equipment')
def get_equipment_data():
    """获取设备数据API"""
    try:
        return jsonify(fetch_equipment_stats())
    except Exception as e:
        logging.warning(f"获取设备数据失败，使用模拟数据: {e}")
        return jsonify(mock_equipment_snapshot())

@app.route('/api/ranking')
def get_ranking_data():
    """获取生产线排行榜API"""
    try:
        normalized = fetch_normalized_data(datetime.now() - timedelta(hours=24), datetime.now(), strict=False)
        if normalized:
            yield_stats = calculate_yield_from_data(normalized)
            value = yield_stats['yield_rate']
        else:
            value = round(random.uniform(90, 98), 1)
        return jsonify([{"name": "生产线1", "value": value}])
    except Exception as e:
        logging.error(f"获取生产线排行榜失败: {e}")
        return jsonify([{"name": "生产线1", "value": round(random.uniform(90, 98), 1)}])

@app.route('/api/monthly')
def get_monthly_data():
    """获取月度数据API"""
    import calendar
    try:
        ensure_data_fetcher()
        now = datetime.now()
        months = []
        total_production = []
        quality_products = []
        quality_rates = []

        for offset in range(11, -1, -1):
            year = now.year
            month = now.month - offset
            while month <= 0:
                month += 12
                year -= 1
            month_start = datetime(year, month, 1)
            _, days_in_month = calendar.monthrange(year, month)
            month_end = month_start + timedelta(days=days_in_month)

            try:
                normalized = fetch_normalized_data(month_start, month_end, strict=False)
                stats = calculate_yield_from_data(normalized) if normalized else None
            except Exception:
                stats = None

            months.append(f"{month}月")
            if stats:
                total_production.append(stats['total'])
                quality_products.append(stats['quality'])
                quality_rates.append(stats['yield_rate'])
            else:
                total_production.append(0)
                quality_products.append(0)
                quality_rates.append(0.0)

        return jsonify({
            "months": months,
            "total_production": total_production,
            "quality_products": quality_products,
            "quality_rates": quality_rates
        })
    except Exception as e:
        logging.error(f"获取月度数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vibration')
def get_vibration_data():
    """获取振动监测数据API"""
    try:
        ensure_data_fetcher()
        data = get_vibration_history_from_db(days=7)
        if not data:
            raise RuntimeError("无法从数据库获取振动数据")
        return jsonify(data)
    except Exception as e:
        logging.warning(f"获取振动数据失败，使用模拟数据: {e}")
        return jsonify(mock_vibration_history(days=7))

@app.route('/api/realtime_vibration')
def get_realtime_vibration_data():
    """获取实时振动监测数据API"""
    try:
        ensure_data_fetcher()
        now = datetime.now()
        rows = connect_sql(
            (now - timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S'),
            now.strftime('%Y-%m-%d %H:%M:%S'),
            table_name='bk_datamodel'
        )
        latest_row = rows[-1] if rows else None
        if latest_row:
            base_sample = {
                "noise": int(latest_row[16]) if len(latest_row) > 16 and latest_row[16] else 0,
                "x_vibration": round(float(latest_row[14]), 3) if len(latest_row) > 14 and latest_row[14] else 0.0,
                "z_vibration": round(float(latest_row[15]), 3) if len(latest_row) > 15 and latest_row[15] else 0.0,
                "temperature": 0.0
            }
        else:
            base_sample = None
    except Exception as e:
        logging.warning(f"获取实时振动数据失败，使用模拟数据: {e}")
        base_sample = None
    
    if not base_sample:
        base_sample = mock_vibration_history(days=1)[-1]
    
    if not wave_buffer:
        try:
            history = get_vibration_history_from_db(days=7)
            if history:
                seed_wave_buffer_from_history(history)
        except Exception:
            seed_wave_buffer_from_history(mock_vibration_history(MAX_WAVE_POINTS))
    
    wave_point = create_wave_point(base_sample)
    wave_buffer.append(wave_point)
    while len(wave_buffer) < MAX_WAVE_POINTS:
        wave_buffer.append(create_wave_point(base_sample))
    return jsonify(list(wave_buffer))

@app.route('/api/connection_status')
def get_connection_status():
    """检查设备连接状态"""
    try:
        ensure_data_fetcher()
        now = datetime.now()
        rows = connect_sql(
            (now - timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S'),
            now.strftime('%Y-%m-%d %H:%M:%S'),
            table_name='bk_datamodel'
        )
        
        if rows and len(rows) > 0:
            latest_row = rows[-1]
            latest_time = latest_row[0] if latest_row[0] else now
            return jsonify({
                "edge_connected": True,
                "cloud_connected": True,
                "latest_data_time": str(latest_time),
                "data_count": len(rows),
                "message": "设备在线，数据正常上传"
            })
        else:
            return jsonify({
                "edge_connected": False,
                "cloud_connected": True,
                "latest_data_time": None,
                "data_count": 0,
                "message": "设备离线，10秒内无新数据"
            })
    except Exception as e:
        logging.error(f"检查连接状态失败: {e}")
        return jsonify({
            "edge_connected": False,
            "cloud_connected": False,
            "latest_data_time": None,
            "data_count": 0,
            "message": f"连接检查失败: {str(e)}"
        })

@app.route('/api/device_status')
def get_device_status_data():
    """获取设备状态数据API"""
    try:
        return jsonify(fetch_device_status_stats())
    except Exception as e:
        logging.warning(f"获取设备状态数据失败，使用模拟数据: {e}")
        return jsonify(mock_device_status())

@app.route('/api/device_efficiency')
def get_device_efficiency_data():
    """获取设备效率排行榜数据API"""
    try:
        ensure_data_fetcher()
        rows = connect_sql(
            (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            table_name='bk_datamodel'
        )
        if not rows:
            return jsonify({"status": "error", "message": "无法获取设备效率数据"}), 500
        
        efficiency_map = {}
        for row in rows:
            if len(row) > 35:
                plc_step = str(row[17])
                fit_error = max(abs(row[34] or 0), abs(row[35] or 0))
                efficiency_map.setdefault(plc_step, []).append(fit_error)

        devices = []
        for plc_step, errors in efficiency_map.items():
            avg_error = sum(errors) / len(errors)
            efficiency = max(0, min(100, 100 - avg_error))
            devices.append({
                "device_id": f"PLC步骤 {plc_step}",
                "line": "生产线1",
                "efficiency": round(efficiency, 2)
            })

        devices.sort(key=lambda x: x["efficiency"], reverse=True)
        return jsonify(devices[:10])
    except Exception as e:
        logging.error(f"获取设备效率数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/quality_analysis')
def get_quality_analysis_data():
    """获取质量分析数据API"""
    try:
        snapshot = get_virtual_production_snapshot()
        quality_rate = snapshot["quality_rate"]
        defect_rate = round(100 - quality_rate, 2)
        return jsonify({
            "quality_rate": quality_rate,
            "defect_rate": defect_rate,
            "rework_rate": round(defect_rate * 0.2, 2),
            "scrap_rate": round(defect_rate * 0.1, 2),
            "pass_rate": quality_rate
        })
    except Exception as e:
        logging.error(f"获取质量分析数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/production_daily')
def get_daily_production_data():
    """获取每日产量数据API"""
    try:
        data = get_virtual_daily_series(30)
        return jsonify(data)
    except Exception as e:
        logging.error(f"获取每日产量数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/industrial_pie_data')
def get_industrial_pie_data():
    """获取工业大数据饼图数据API"""
    try:
        ensure_data_fetcher()
        stats = calculate_production_stats_from_db(days=1)
        if not stats:
            raise RuntimeError("无法获取产量统计数据")
        quality_rate = stats['yield_rate']
    except Exception as e:
        logging.warning(f"获取工业饼图数据失败，使用模拟数据: {e}")
        quality_rate = round(random.uniform(90, 98), 1)
    
    defect_rate = 100 - quality_rate
    modules = [
        ("设备运行", max(1, min(40, quality_rate))),
        ("数据采集", max(1, min(20, quality_rate * 0.2))),
        ("质量检测", max(1, min(20, quality_rate * 0.25))),
        ("能耗监控", max(1, min(10, quality_rate * 0.15))),
        ("故障预警", max(1, defect_rate * 0.6)),
        ("维护管理", max(1, defect_rate * 0.4))
    ]
    x_data = [name for name, _ in modules]
    series_data = [{"name": name, "value": round(value, 1)} for name, value in modules]
    return jsonify({"xData": x_data, "seriesData": series_data})

@app.route('/api/realtime')
def get_realtime_data():
    """获取实时数据API - 聚合数据"""
    try:
        try:
            production_stats = get_virtual_production_snapshot()
        except Exception:
            production_stats = mock_production_snapshot()
        try:
            equipment_stats = fetch_equipment_stats()
        except Exception:
            equipment_stats = mock_equipment_snapshot()
        vibration_data = []
        try:
            vibration_data = get_vibration_history_from_db(days=1)
        except Exception:
            vibration_data = mock_vibration_history(days=1)
        try:
            device_status = fetch_device_status_stats()
        except Exception:
            device_status = mock_device_status()
        return jsonify({
            "production": production_stats,
            "equipment": equipment_stats,
            "vibration": vibration_data[-1:] if vibration_data else [],
            "device_status": device_status
        })
    except Exception as e:
        logging.error(f"获取综合实时数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5008)
