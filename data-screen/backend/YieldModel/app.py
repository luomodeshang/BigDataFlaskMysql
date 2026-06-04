from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from flask_cors import CORS
from configparser import ConfigParser
import pymysql

from Get_CloseTime_Item import Get_TheClose_Item, classify_err_type
from main_yield import Output_normalize_PLC_single_workpiece

app = Flask(__name__)
CORS(app)

# 加载模型和特征
print("正在加载模型...")
model_x = joblib.load('trained_models/model_x.pkl')
model_y = joblib.load('trained_models/model_y.pkl')

with open('trained_models/features.txt', 'r') as f:
    features = [line.strip() for line in f.readlines()]
print("模型加载完成")


def connect_sql():
    config = ConfigParser()
    config.read('新建文本文档.ini')
    host = config.get('DEFAULT', 'Host')
    port = config.getint('DEFAULT', 'Port')
    database = config.get('DEFAULT', 'Database')
    user = config.get('DEFAULT', 'User')
    password = config.get('DEFAULT', 'Password')

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # 直接获取最新的一条有效数据（PLC_step != 0）
        sql = '''SELECT 
              Speed_X, Speed_Y, Speed_Z, Speed_R,
              positioing_error_X, positioing_error_Y,
              acceleration_X, acceleration_Y, acceleration_Z, acceleration_R,
              visual_error_X, visual_error_Y,
              fit_error_X, fit_error_Y,
              vibration_X, vibration_Z,
              noise_X,
              PLC_step,
              absolute_position_X, absolute_position_Y,
              offset_X, offset_Y, offset_R,
              Grating_feedback_X, Grating_feedback_Y,
              setting_red_circle_X, setting_red_circle_Y,
              setting_blue_circle_X, setting_blue_circle_Y,
              setting_yellow_square_X, setting_yellow_square_Y,
              setting_blue_square_X, setting_blue_square_Y,
              visual_scanning_pixel_coordinate_X, visual_scanning_pixel_coordinate_Y,
              visual_setting_pixel_coordinate_X, visual_setting_pixel_coordinate_Y,
              visual_scanning_world_coordinate_X, visual_scanning_world_coordinate_Y,
              creation_date
              FROM BK_DataModel
              WHERE PLC_step != 0
              ORDER BY creation_date DESC
              LIMIT 1'''

        cursor.execute(sql)
        row = cursor.fetchone()
        conn.close()

        return [row] if row else []

    except pymysql.Error as e:
        print(f"数据库连接错误: {e}")
        return None


@app.route('/api/realtime', methods=['GET'])
def get_realtime_data():
    try:
        # 获取最新数据
        data = connect_sql()

        if not data:
            return jsonify({"status": "error", "message": "无有效数据"})

        # 转换为字典格式
        columns = [
            'Speed_X', 'Speed_Y', 'Speed_Z', 'Speed_R',
            'positioing_error_X', 'positioing_error_Y',
            'acceleration_X', 'acceleration_Y', 'acceleration_Z', 'acceleration_R',
            'visual_error_X', 'visual_error_Y',
            'fit_error_X', 'fit_error_Y',
            'vibration_X', 'vibration_Z',
            'noise_X',
            'PLC_step',
            'absolute_position_X', 'absolute_position_Y',
            'offset_X', 'offset_Y', 'offset_R',
            'Grating_feedback_X', 'Grating_feedback_Y',
            'setting_red_circle_X', 'setting_red_circle_Y',
            'setting_blue_circle_X', 'setting_blue_circle_Y',
            'setting_yellow_square_X', 'setting_yellow_square_Y',
            'setting_blue_square_X', 'setting_blue_square_Y',
            'visual_scanning_pixel_X', 'visual_scanning_pixel_Y',
            'visual_setting_pixel_X', 'visual_setting_pixel_Y',
            'visual_scanning_world_X', 'visual_scanning_world_Y',
            'creation_date'
        ]

        # 获取最新数据
        latest_data = dict(zip(columns, data[0])) if data else {}

        return jsonify({
            "status": "success",
            "data": latest_data,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # 获取前端传递的时间段
        data = request.json

        # 转换时间格式
        def parse_time(time_str):
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            except:
                return datetime.strptime(time_str, '%Y-%m-%dT%H:%M')

        start_time = parse_time(data['start_time'])
        end_time = parse_time(data['end_time'])

        # 转换为字符串格式供您的函数使用
        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

        # 这里需要替换为您实际的数据获取函数
        # 假设我们有一个函数可以获取指定时间段的数据
        from main_yield import Output_normalize_PLC_single_workpiece, Yield_columns

        data = Output_normalize_PLC_single_workpiece(start_str, end_str)
        df = pd.DataFrame(data, columns=Yield_columns)

        # 确保特征顺序与训练时一致
        X = df[features]

        # 进行预测
        pred_x = model_x.predict(X)
        pred_y = model_y.predict(X)

        # 创建结果DataFrame
        results = pd.DataFrame({
            'pred_x': pred_x,
            'pred_y': pred_y
        })

        # 如果有真实值，可以计算误差
        if '贴合误差X' in df.columns and '贴合误差Y' in df.columns:
            results['actual_x'] = df['贴合误差X']
            results['actual_y'] = df['贴合误差Y']

        # 计算良率统计
        defect_count = len(results[(abs(results['pred_x']) > 150) | (abs(results['pred_y']) > 150)])
        total_count = len(results)
        yield_rate = (total_count - defect_count) / total_count * 100 if total_count > 0 else 0

        # 准备返回数据
        response = {
            'predictions': results.head(100).to_dict(orient='records'),  # 只返回前100条数据
            'yield_stats': {
                'total': total_count,
                'defect': defect_count,
                'yield_rate': round(yield_rate, 2)
            }
        }

        return jsonify({'success': True, 'data': response})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/diagnosis', methods=['GET'])
def get_diagnosis():
    try:
        print("Received diagnosis request")
        # 获取数据 - 现在使用 classify_err_type() 而不是 Get_TheClose_Item()
        result_dict, data_list = classify_err_type()  # 直接获取已分类的结果和数据

        # 确保数据格式正确
        if not isinstance(data_list, list):
            raise ValueError("Data list is not in correct format")
        if not isinstance(result_dict, dict):
            raise ValueError("Result dict is not in correct format")

        # 将数据转换为前端需要的格式
        data_keys = [
            'all定位误差X-1', 'all定位误差Y-1', 'all定位误差X-2', 'all定位误差Y-2',
            'all定位误差X-3', 'all定位误差Y-3', 'all定位误差X-4', 'all定位误差Y-4',
            'all物件坐标X-1', 'all物件坐标Y-1', 'all物理坐标X-1', 'all物理坐标Y-1',
            'catch定位误差X(移动到拍照位)', 'catch定位误差Y(移动到拍照位)',
            'catch光栅反馈X(移动到拍照位)', 'catch光栅反馈Y(移动到拍照位)',
            '视觉误差X', '视觉误差Y', 'catch复拍物件坐标X', 'catch复拍物件坐标Y',
            'catch复拍物理坐标X', 'catch复拍物理坐标Y', 'catchPLC坐标X', 'catchPLC坐标Y',
            'catch定位误差X', 'catch定位误差Y', 'catch光栅反馈X', 'catch光栅反馈Y',
            'releasePLC坐标X', 'releasePLC坐标Y', 'release定位误差X', 'release定位误差Y',
            'release光栅反馈X', 'release光栅反馈Y', '贴合误差X', '贴合误差Y',
            'release视觉坐标X(像素)', 'release视觉坐标Y(像素)'
        ]

        # 检查数据长度是否匹配
        if len(data_list) != len(data_keys):
            raise ValueError(f"Data length mismatch. Expected {len(data_keys)}, got {len(data_list)}")

        data_dict = dict(zip(data_keys, data_list))

        # 格式化诊断结果
        diagnosis_result = f"{result_dict['预测类别']} (置信度: {result_dict['置信度']})"

        response = {
            "status": "success",
            "result": diagnosis_result,
            "data": data_dict,
            "probabilities": result_dict['各类别概率']
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error in diagnosis: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



if __name__ == '__main__':
    app.run(debug=True, port=5000)