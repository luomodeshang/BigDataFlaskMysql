import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, KFold
from sklearn.pipeline import make_pipeline
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import os
import joblib  # 用于保存和加载模型

# ==============================================
# 初始化设置
# ==============================================
# 创建保存目录
os.makedirs('trained_models', exist_ok=True)
os.makedirs('analysis_results', exist_ok=True)

# 设置可视化风格
plt.rcParams.update({
    'font.sans-serif': 'SimHei',  # 中文显示
    'axes.unicode_minus': False,  # 负号显示
    'figure.dpi': 150,  # 图形分辨率
    'savefig.dpi': 300,  # 保存分辨率
    'savefig.bbox': 'tight',  # 保存时裁剪空白
    'figure.figsize': (10, 6)  # 默认图形大小
})
sns.set_style("whitegrid", {
    'font.sans-serif': ['simhei', 'Arial'],
    'grid.linestyle': '--',
    'grid.alpha': 0.4
})

# ==============================================
# 数据加载函数
# ==============================================
def load_data():
    """从主程序加载并预处理数据"""
    from main_yield import Output_normalize_PLC_single_workpiece, Yield_columns
    print("\n正在加载数据...")

    # 获取原始数据
    data = Output_normalize_PLC_single_workpiece('2025-08-14 09:20:20','2025-12-28 15:50:12')
    df = pd.DataFrame(data, columns=Yield_columns)

    # 数据质量检查
    print(f"\n数据加载完成，形状: {df.shape}")
    print("前3行数据示例:")
    print(df.head(3))

    # 保存原始数据副本
    df.to_csv('analysis_results/raw_data.csv', index=False)
    print("原始数据已保存至: analysis_results/raw_data.csv")

    return df

# ==============================================
# 模型训练与保存函数
# ==============================================
def train_and_save_models(df):
    """训练并保存X和Y误差的预测模型"""
    print("\n" + "=" * 50)
    print("开始训练模型")
    print("=" * 50)

    # 数据准备
    features = [col for col in df.columns if col not in ['贴合误差X', '贴合误差Y']]
    X = df[features]
    y_x = df['贴合误差X']
    y_y = df['贴合误差Y']

    # 标准化处理
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 定义模型
    model_x = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model_y = make_pipeline(StandardScaler(), Ridge(alpha=1.0))

    # 训练X误差模型
    print("\n>>> 训练贴合误差X模型...")
    model_x.fit(X, y_x)
    y_pred_x = model_x.predict(X)
    rmse_x = np.sqrt(mean_squared_error(y_x, y_pred_x))
    r2_x = r2_score(y_x, y_pred_x)
    print(f"训练集RMSE: {rmse_x:.4f}")
    print(f"训练集R²: {r2_x:.4f}")

    # 训练Y误差模型
    print("\n>>> 训练贴合误差Y模型...")
    model_y.fit(X, y_y)
    y_pred_y = model_y.predict(X)
    rmse_y = np.sqrt(mean_squared_error(y_y, y_pred_y))
    r2_y = r2_score(y_y, y_pred_y)
    print(f"训练集RMSE: {rmse_y:.4f}")
    print(f"训练集R²: {r2_y:.4f}")

    # 保存模型
    joblib.dump(model_x, 'trained_models/model_x.pkl')
    joblib.dump(model_y, 'trained_models/model_y.pkl')
    print("\n模型已保存至trained_models目录:")
    print("- model_x.pkl (贴合误差X预测模型)")
    print("- model_y.pkl (贴合误差Y预测模型)")

    # 保存特征列表（用于验证时确保输入顺序一致）
    with open('trained_models/features.txt', 'w') as f:
        f.write('\n'.join(features))

# ==============================================
# 主程序
# ==============================================
if __name__ == "__main__":
    print("=" * 50)
    print("工业贴合误差模型训练系统")
    print("=" * 50)

    try:
        # 1. 数据加载
        df = load_data()

        # 2. 训练并保存模型
        train_and_save_models(df)

        print("\n" + "=" * 50)
        print("模型训练完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n错误发生: {str(e)}")
        raise