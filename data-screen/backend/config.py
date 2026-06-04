"""
后端配置文件
统一管理服务器、数据库等配置项

配置优先级: 环境变量 > .env 文件 > 默认值
"""
import os

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 未安装时跳过

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ 服务器配置 ============
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', 5008))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# ============ 数据库配置 ============
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'dataAnalysis'),
    'user': os.getenv('DB_USER', 'DataAnalysis'),
    'password': os.getenv('DB_PASSWORD', 'pRB8ZcByta5yM6SK'),
    'charset': 'utf8mb4',
}

# ============ 数据表配置 ============
TABLE_ORIGINAL = 'bk_datamodel'
TABLE_IMMEDIATE = 'bk_datamodel_immediate'

# ============ 阈值配置 ============
VIBRATION_THRESHOLD = 16.0
NOISE_THRESHOLD = 90.0
TEMPERATURE_THRESHOLD = 5.0

# ============ 模型配置 ============
MODEL_DIR = os.path.join(BASE_DIR, 'YieldModel', 'trained_models')
MODEL_X_PATH = os.path.join(MODEL_DIR, 'model_x.pkl')
MODEL_Y_PATH = os.path.join(MODEL_DIR, 'model_y.pkl')
FEATURES_PATH = os.path.join(MODEL_DIR, 'features.txt')

# ============ 日志配置 ============
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
