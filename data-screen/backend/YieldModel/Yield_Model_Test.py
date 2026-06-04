import pandas as pd
import numpy as np
import joblib
from main_yield import Output_normalize_PLC_single_workpiece, Yield_columns


def load_models():
    """加载训练好的模型和特征列表"""
    print("正在加载模型...")
    model_x = joblib.load('trained_models/model_x.pkl')
    model_y = joblib.load('trained_models/model_y.pkl')

    with open('trained_models/features.txt', 'r') as f:
        features = [line.strip() for line in f.readlines()]

    print("模型加载完成")
    return model_x, model_y, features


def validate_models():
    """使用新数据验证模型"""
    try:
        # 1. 加载模型
        model_x, model_y, features = load_models()

        # 2. 加载新数据（使用与训练时相同的导入方式）
        print("\n正在加载验证数据...")
        data = Output_normalize_PLC_single_workpiece('2025-07-16 09:20:20','2025-12-28 15:50:12')
        df = pd.DataFrame(data, columns=Yield_columns)

        # 确保特征顺序与训练时一致
        X = df[features]

        # 3. 进行预测
        print("\n进行预测...")
        pred_x = model_x.predict(X)
        pred_y = model_y.predict(X)

        # 4. 输出结果
        results = pd.DataFrame({
            '预测贴合误差X': pred_x,
            '预测贴合误差Y': pred_y
        })

        # 如果有真实值，可以计算误差
        if '贴合误差X' in df.columns and '贴合误差Y' in df.columns:
            results['实际贴合误差X'] = df['贴合误差X']
            results['实际贴合误差Y'] = df['贴合误差Y']
            results['X误差差值'] = results['实际贴合误差X'] - results['预测贴合误差X']
            results['Y误差差值'] = results['实际贴合误差Y'] - results['预测贴合误差Y']

            rmse_x = np.sqrt(np.mean(results['X误差差值'] ** 2))
            rmse_y = np.sqrt(np.mean(results['Y误差差值'] ** 2))

            print("\n预测结果评估:")
            print(f"- X方向RMSE: {rmse_x:.4f}")
            print(f"- Y方向RMSE: {rmse_y:.4f}")

        # 保存预测结果
        results.to_csv('prediction_results.csv', index=False)
        print("\n预测结果已保存至prediction_results.csv")
        print("\n前5行预测结果:")
        print(results.head())

        return results

    except Exception as e:
        print(f"\n验证过程中发生错误: {str(e)}")
        raise


if __name__ == "__main__":
    print("=" * 50)
    print("工业贴合误差模型验证系统")
    print("=" * 50)

    validate_models()

    print("\n" + "=" * 50)
    print("验证完成！")
    print("=" * 50)