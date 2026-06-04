import numpy as np
import torch
import torch.nn as nn
import joblib
import re


# 1. 定义与训练时相同的神经网络结构
class FaultClassifier(nn.Module):
    def __init__(self, input_dim, num_classes):
        super(FaultClassifier, self).__init__()
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 32)
        self.fc4 = nn.Linear(32, num_classes)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x


# 2. 加载模型和相关文件
def load_model_and_resources():
    """加载模型、标准化器和类别映射"""
    try:
        # 加载标准化器和类别映射
        scaler = joblib.load('pytorch_scaler.save')
        class_mapping = joblib.load('pytorch_class_mapping.save')

        # 初始化模型
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = FaultClassifier(input_dim=len(scaler.mean_), num_classes=len(class_mapping)).to(device)

        # 加载模型权重
        model.load_state_dict(torch.load('best_fault_classifier.pth', map_location=device))
        model.eval()

        return model, scaler, class_mapping, device

    except Exception as e:
        raise RuntimeError(f"加载模型失败: {str(e)}")


# 3. 预测函数
def predict_sample(input_text, model, scaler, class_mapping, device):
    """对输入的样本数据进行分类"""
    try:
        # 处理输入数据（支持空格/制表符/换行分隔）
        sample_data = [float(x) for x in re.split(r'[\s,]+', input_text.strip()) if x]

        # 检查输入特征数量是否正确
        if len(sample_data) != len(scaler.mean_):
            raise ValueError(f"输入特征数量应为 {len(scaler.mean_)}，但得到 {len(sample_data)}")

        # 标准化数据
        sample_scaled = scaler.transform([sample_data])
        sample_tensor = torch.FloatTensor(sample_scaled).to(device)

        # 预测
        with torch.no_grad():
            output = model(sample_tensor)
            probabilities = torch.softmax(output, dim=1)[0]
            _, predicted_class = torch.max(output, 1)

        # 获取结果
        class_idx = predicted_class.item()
        class_name = class_mapping[class_idx]
        confidence = probabilities[class_idx].item() * 100

        # 所有类别的概率
        prob_dict = {
            class_mapping[i]: f"{prob.item() * 100:.2f}%"
            for i, prob in enumerate(probabilities)
        }

        return {
            "预测类别": class_name,
            "置信度": f"{confidence:.2f}%",
            "各类别概率": prob_dict
        }

    except Exception as e:
        return {"错误": str(e)}


# 4. 主程序
# if __name__ == "__main__":
    # 加载模型和资源
print("正在加载模型...")
model, scaler, class_mapping, device = load_model_and_resources()
print("模型加载成功!")

# 示例输入数据（直接从表格复制的格式）
sample_input = """
-0.11529541 -0.004997253 -0.144790649 -0.004997253 -0.144790649 
-0.010000229 -0.116798401 -0.010000229 1291.573 1036.069 9.941 
2.24 0.12470245361328125 -0.004997253 106.1 120.6 0.22356796264648438 
-0.009536266 1294.903 1036.222 9.718 2.25 45.2 106.9 -0.815299988 
-0.004997253 46.1 106.9 -50 122.8 -3 7.62939453125e-06 -47 122.8 
-1.5 -2 2173.5 839
"""

temp=[106.18470001220703, 120.625, 230.6551971435547, 120.625, 230.6551971435547, 28.5, 112.94319915771484, 28.5, 0, 0, 0, 0, 112.94319915771484, 28.5, 0.0, 0.0, 4.128917694091797, 0.07907909899950027, 1511.505, 1003.439, -4.811, -0.008, 180.3, 109.1, 180.33518981933594, 109.05500030517578, -1, -1, -50.0, 77.5, -50.0, 77.5, -1, -1, 18.0, 1.0, 2208.0, 842.0]
def convert_to_sample_input(data_list):
    # 将所有数值转换为字符串并用空格连接
    return ' '.join(map(str, data_list))
temp=convert_to_sample_input(temp)
print(temp)
# 去除多余空白字符
sample_input = ' '.join(sample_input.split())

# 进行预测
print("\n正在预测样本...")
result = predict_sample(temp, model, scaler, class_mapping, device)

# 打印结果
print("\n=== 预测结果 ===")
if "错误" in result:
    print(f"错误: {result['错误']}")
else:
    print(f"预测类别: {result['预测类别']}")
    print(f"置信度: {result['置信度']}")
    print("\n各类别概率:")
    for cls, prob in result['各类别概率'].items():
        print(f"{cls}: {prob}")