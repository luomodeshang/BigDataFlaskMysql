def read_file_lines(file_path):
    """按行读取文件内容，返回行列表"""
    try:
        with open(file_path, 'r') as file:
            # 读取所有行并去除每行首尾的空白字符
            lines = [line.strip() for line in file if line.strip()]
        return lines
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 未找到")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None


# 使用示例

file_path = 'time_records.txt'
file_lines = read_file_lines(file_path)

if file_lines:
    print("文件内容:")
    for i, line in enumerate(file_lines, 1):
        print(f"行 {i}: {line}")

    print(f"\n共读取 {len(file_lines)} 行")