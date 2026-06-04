import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import matplotlib.pyplot as plt
from tqdm import tqdm

# 设置随机种子保证可重复性
torch.manual_seed(42)
np.random.seed(42)


# 1. 自定义数据集类
class FaultDataset(Dataset):
    def __init__(self, features, labels):
        self.features = features
        self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


# 2. 神经网络模型
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


# 3. 数据加载和预处理
def load_and_preprocess_data():
    """加载并预处理三类数据"""
    file_paths = {
        'good': 'data_good.csv',
        'photo_error': 'data_Photo_Error.csv',
        'x_error': 'data_X_Error.csv'
    }

    datasets = []

    # 尝试的编码格式列表（按优先级排序）
    encodings_to_try = ['gbk', 'gb2312', 'utf-8', 'latin-1', 'iso-8859-1', 'cp936']

    for label, (file_type, path) in enumerate(file_paths.items()):
        if os.path.exists(path):
            df = None
            encoding_used = None

            # 尝试不同的编码格式
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(path, encoding=encoding)
                    encoding_used = encoding
                    print(f"成功使用 {encoding} 编码读取 {file_type} 数据")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"使用 {encoding} 编码读取 {file_type} 数据时出错: {e}")
                    continue

            if df is not None:
                df['label'] = label  # 0: good, 1: photo_error, 2: x_error
                datasets.append(df)
                print(f"已加载 {file_type} 数据，形状: {df.shape}")
            else:
                print(f"错误: 无法读取文件 {path}，所有编码格式都失败")
        else:
            print(f"警告: 文件 {path} 未找到，跳过...")

    if not datasets:
        raise ValueError("未找到任何数据文件，请检查文件路径")

    # 合并数据
    data = pd.concat(datasets, ignore_index=True)
    print(f"合并后数据形状: {data.shape}")

    # 处理缺失值 (-1标记为缺失)
    data.replace(-1, np.nan, inplace=True)

    # 检查缺失值情况
    missing_values = data.isnull().sum()
    print("缺失值统计:")
    print(missing_values[missing_values > 0])

    # 计算每列的均值，忽略缺失值
    column_means = data.mean()

    # 填充缺失值
    data.fillna(column_means, inplace=True)

    print("数据预处理完成")
    return data


# 4. 准备训练数据
def prepare_data(data):
    """准备训练数据"""
    # 分离特征和标签
    X = data.drop('label', axis=1).values
    y = data['label'].values

    # 标准化特征
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 转换为PyTorch张量
    X_tensor = torch.FloatTensor(X_scaled)
    y_tensor = torch.LongTensor(y)

    return X_tensor, y_tensor, scaler


# 5. 训练函数
def train_model(model, train_loader, val_loader, criterion, optimizer, device, epochs=100):
    """训练模型"""
    best_val_acc = 0.0
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        # 训练阶段
        for inputs, labels in tqdm(train_loader, desc=f'Epoch {epoch + 1}/{epochs}'):
            inputs, labels = inputs.to(device), labels.to(device)

            # 前向传播
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            # 反向传播和优化
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # 统计
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_loss = running_loss / len(train_loader)
        train_acc = correct / total
        train_losses.append(train_loss)
        train_accs.append(train_acc)

        # 验证阶段
        val_loss, val_acc = evaluate_model(model, val_loader, criterion, device)
        val_losses.append(val_loss)
        val_accs.append(val_acc)

        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'best_fault_classifier.pth')

        print(f'Epoch {epoch + 1}/{epochs} - '
              f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, '
              f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')

    return train_losses, val_losses, train_accs, val_accs


# 6. 评估函数
def evaluate_model(model, loader, criterion, device):
    """评估模型性能"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    loss = running_loss / len(loader)
    acc = correct / total

    return loss, acc


# 7. 可视化训练过程
def plot_training_history(train_losses, val_losses, train_accs, val_accs):
    """绘制训练过程中的准确率和损失曲线"""
    plt.figure(figsize=(12, 4))

    # 准确率曲线
    plt.subplot(1, 2, 1)
    plt.plot(train_accs, label='Train Accuracy')
    plt.plot(val_accs, label='Validation Accuracy')
    plt.title('Model Accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend()

    # 损失曲线
    plt.subplot(1, 2, 2)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend()

    plt.tight_layout()
    plt.savefig('pytorch_training_history.png')
    print("\n已保存训练过程图表: pytorch_training_history.png")
    plt.show()


# 8. 主函数
def main():
    print("=== 机械故障分类神经网络 (PyTorch 实现) ===")

    # 检查GPU是否可用
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")

    # 1. 加载和预处理数据
    print("\n1. 正在加载和预处理数据...")
    data = load_and_preprocess_data()

    # 2. 准备训练数据
    print("\n2. 正在准备训练数据...")
    X_tensor, y_tensor, scaler = prepare_data(data)

    # 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(
        X_tensor, y_tensor, test_size=0.2, random_state=42)

    # 创建数据集和数据加载器
    train_dataset = FaultDataset(X_train, y_train)
    val_dataset = FaultDataset(X_val, y_val)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

    # 3. 初始化模型
    print("\n3. 正在初始化模型...")
    input_dim = X_train.shape[1]
    num_classes = len(torch.unique(y_tensor))
    model = FaultClassifier(input_dim, num_classes).to(device)

    # 打印模型摘要
    print(model)

    # 4. 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 5. 训练模型
    print("\n4. 正在训练模型...")
    train_losses, val_losses, train_accs, val_accs = train_model(
        model, train_loader, val_loader, criterion, optimizer, device, epochs=100)

    # 6. 评估最终模型
    print("\n5. 正在评估最终模型...")
    final_val_loss, final_val_acc = evaluate_model(model, val_loader, criterion, device)
    print(f"最终验证集准确率: {final_val_acc * 100:.2f}%")

    # 加载最佳模型并评估
    best_model = FaultClassifier(input_dim, num_classes).to(device)
    best_model.load_state_dict(torch.load('best_fault_classifier.pth'))
    best_val_loss, best_val_acc = evaluate_model(best_model, val_loader, criterion, device)
    print(f"最佳模型验证集准确率: {best_val_acc * 100:.2f}%")

    # 7. 保存模型和相关文件
    print("\n6. 正在保存模型和相关文件...")
    torch.save(model.state_dict(), 'final_fault_classifier.pth')
    print("已保存最终模型: final_fault_classifier.pth")

    torch.save(best_model.state_dict(), 'best_fault_classifier.pth')
    print("已保存最佳模型: best_fault_classifier.pth")

    joblib.dump(scaler, 'pytorch_scaler.save')
    print("已保存标准化器: pytorch_scaler.save")

    class_mapping = {
        0: "正常 (无误差)",
        1: "平台机械振动过高 (拍照误差)",
        2: "X轴电机丢步 (X误差)"
    }
    joblib.dump(class_mapping, 'pytorch_class_mapping.save')
    print("已保存类别映射: pytorch_class_mapping.save")

    # 8. 可视化训练过程
    print("\n7. 正在生成训练过程图表...")
    plot_training_history(train_losses, val_losses, train_accs, val_accs)

    print("\n=== 训练完成 ===")


if __name__ == "__main__":
    main()


# 9. 预测函数 (可在其他脚本中使用)
def predict_fault_type(new_data_path):
    """使用训练好的模型预测新数据的故障类型"""
    try:
        # 加载必要的文件
        scaler = joblib.load('pytorch_scaler.save')
        class_mapping = joblib.load('pytorch_class_mapping.save')

        # 初始化模型
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        input_dim = len(scaler.mean_)
        num_classes = len(class_mapping)
        model = FaultClassifier(input_dim, num_classes).to(device)

        # 加载最佳模型权重
        model.load_state_dict(torch.load('best_fault_classifier.pth', map_location=device))
        model.eval()

        # 加载新数据
        new_data = pd.read_csv(new_data_path)

        # 预处理
        new_data.replace(-1, np.nan, inplace=True)
        column_means = new_data.mean()
        new_data.fillna(column_means, inplace=True)

        # 标准化
        X_new = scaler.transform(new_data.values)
        X_new = torch.FloatTensor(X_new).to(device)

        # 预测
        with torch.no_grad():
            outputs = model(X_new)
            probabilities = torch.softmax(outputs, dim=1)
            _, predicted_classes = torch.max(outputs.data, 1)

        # 映射到故障类型
        results = []
        for i, class_idx in enumerate(predicted_classes.cpu().numpy()):
            confidence = probabilities[i][class_idx].item() * 100
            results.append(
                f"{class_mapping[class_idx]} (置信度: {confidence:.2f}%)"
            )

        return results

    except Exception as e:
        return f"预测时出错: {str(e)}"

# 示例使用预测函数
# 假设有一个新数据文件 'new_data.csv'
# predictions = predict_fault_type('new_data.csv')
# for i, pred in enumerate(predictions, 1):
#     print(f"样本 {i}: {pred}")