import tkinter as tk
from datetime import datetime
import os


class TimeRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("时间记录器")

        # 按钮状态
        self.is_start = False
        self.start_time = None
        self.end_time = None

        # 创建界面元素
        self.create_widgets()

    def create_widgets(self):
        # 按钮
        self.button = tk.Button(
            self.root,
            text="开始",
            command=self.toggle_button,
            font=('Arial', 14),
            width=10,
            height=2,
            bg='#4CAF50',
            fg='white'
        )
        self.button.pack(pady=20)

        # 状态标签
        self.status_label = tk.Label(
            self.root,
            text="当前状态: 未开始",
            font=('Arial', 12)
        )
        self.status_label.pack()

    def toggle_button(self):
        if not self.is_start:
            # 开始记录
            self.is_start = True
            self.start_time = datetime.now()
            self.button.config(text="结束", bg='#F44336')
            self.status_label.config(text="当前状态: 记录中...")
        else:
            # 结束记录
            self.is_start = False
            self.end_time = datetime.now()
            self.button.config(text="开始", bg='#4CAF50')
            self.status_label.config(text="当前状态: 未开始")

            # 记录时间到文件
            self.record_to_file()

    def record_to_file(self):
        # 格式化时间
        start_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_str = self.end_time.strftime("%Y-%m-%d %H:%M:%S")

        # 写入文件
        filename = "time_records.txt"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"'{start_str}','{end_str}'\n")

        # 显示记录成功消息
        self.status_label.config(text=f"已记录: {start_str} 到 {end_str}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TimeRecorderApp(root)
    root.mainloop()