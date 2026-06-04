from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import time
import os

app = Flask(__name__)
CORS(app)

# 配置静态文件的MIME类型
@app.after_request
def set_js_mime_type(response):
    """设置JavaScript文件的正确MIME类型"""
    if request.path.endswith('.js'):
        response.mimetype = 'application/javascript'
    elif request.path.endswith('.css'):
        response.mimetype = 'text/css'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/usb/demo')
def usb_demo():
    """USB协议演示数据"""
    # 模拟USB数据传输
    data = {
        'speed': random.randint(480, 5000),  # Mbps
        'devices': [
            {'id': 1, 'name': 'USB设备1', 'status': 'connected', 'transfer_rate': random.randint(100, 500)},
            {'id': 2, 'name': 'USB设备2', 'status': 'connected', 'transfer_rate': random.randint(50, 200)},
        ],
        'connection_type': 'point_to_point',
        'latency': random.randint(1, 5)  # ms
    }
    return jsonify(data)

@app.route('/api/tcp/demo')
def tcp_demo():
    """TCP协议演示数据"""
    # 模拟TCP连接和数据传输
    data = {
        'connections': [
            {'id': 1, 'status': 'established', 'seq_num': random.randint(1000, 9999), 
             'ack_num': random.randint(1000, 9999), 'window_size': random.randint(1000, 65535)},
            {'id': 2, 'status': 'established', 'seq_num': random.randint(1000, 9999),
             'ack_num': random.randint(1000, 9999), 'window_size': random.randint(1000, 65535)},
        ],
        'reliability': 'high',
        'packets_sent': random.randint(100, 1000),
        'packets_acked': random.randint(95, 1000),
        'retransmissions': random.randint(0, 5)
    }
    return jsonify(data)

@app.route('/api/udp/demo')
def udp_demo():
    """UDP协议演示数据"""
    # 模拟UDP数据传输
    data = {
        'packets_sent': random.randint(100, 1000),
        'packets_received': random.randint(80, 950),  # 可能丢包
        'latency': random.randint(1, 10),  # ms
        'throughput': random.randint(100, 1000),  # Mbps
        'loss_rate': round(random.uniform(0, 0.2), 2)  # 丢包率
    }
    return jsonify(data)

@app.route('/api/modbus/demo')
def modbus_demo():
    """MODBUS协议演示数据"""
    # 模拟MODBUS主从通信
    data = {
        'master': {
            'id': 1,
            'requests': random.randint(10, 100)
        },
        'slaves': [
            {'id': 1, 'address': 1, 'status': 'active', 'registers': random.randint(0, 65535)},
            {'id': 2, 'address': 2, 'status': 'active', 'registers': random.randint(0, 65535)},
            {'id': 3, 'address': 3, 'status': 'active', 'registers': random.randint(0, 65535)},
        ],
        'request_response_time': random.randint(10, 50)  # ms
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5301)

