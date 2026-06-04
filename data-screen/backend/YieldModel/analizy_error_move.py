# 分析拍照片差问题

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体，防止乱码
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 读取CSV文件
file_path = 'data_Photo_偏移检测.csv'
data = pd.read_csv(file_path)

# 检查数据
print("数据前几行：")
print(data.head())

# 确定组别（根据第一列的值）
group_column = 'all定位误差X-1'
groups = data[group_column].unique()

# 遍历每组数据
for group in groups:
    group_data = data[data[group_column] == group]

    # 提取倒数第三和第四列（贴合误差X和贴合误差Y）
    error_x = group_data.iloc[:, -3]  # 倒数第三列
    error_y = group_data.iloc[:, -4]  # 倒数第四列

    # 创建可视化
    plt.figure(figsize=(10, 6))

    # 绘制散点图
    plt.scatter(range(len(error_x)), error_x, label='贴合误差Y', color='red', marker='o')
    plt.scatter(range(len(error_y)), error_y, label='贴合误差X', color='blue', marker='x')

    # 添加标题和标签
    plt.title(f'贴合误差可视化 (组别: {group})')
    plt.xlabel('数据点序号')
    plt.ylabel('误差值')
    plt.legend()
    plt.grid(True)

    # 显示图形
    plt.show()

    # 打印统计信息
    print(f"\n组别 {group} 的贴合误差统计信息：")
    print(f"贴合误差X - 平均值: {error_x.mean():.4f}, 标准差: {error_x.std():.4f}")
    print(f"贴合误差Y - 平均值: {error_y.mean():.4f}, 标准差: {error_y.std():.4f}")
