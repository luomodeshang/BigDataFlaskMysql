import tkinter as tk
from tkinter import ttk
import pyautogui
from pynput import mouse
import numpy as np
import cv2
import threading
import time


class ColorPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("屏幕取色工具")
        self.root.geometry("400x300")

        # 创建界面元素
        self.create_widgets()

        # 共享数据
        self.latest_data = {
            "position": (0, 0),
            "rgb": (0, 0, 0),
            "hsv": (0, 0, 0)
        }

        # 启动鼠标监听线程
        self.running = True
        self.mouse_thread = threading.Thread(target=self.start_mouse_listener, daemon=True)
        self.mouse_thread.start()

        # 启动UI更新
        self.update_ui()

        # 窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # 位置信息
        ttk.Label(self.root, text="鼠标位置:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.pos_label = ttk.Label(self.root, text="(0, 0)")
        self.pos_label.grid(row=0, column=1, sticky="w")

        # RGB值
        ttk.Label(self.root, text="RGB值:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.rgb_label = ttk.Label(self.root, text="0, 0, 0")
        self.rgb_label.grid(row=1, column=1, sticky="w")

        # HSV值
        ttk.Label(self.root, text="HSV值:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.hsv_label = ttk.Label(self.root, text="0, 0, 0")
        self.hsv_label.grid(row=2, column=1, sticky="w")

        # 颜色预览
        ttk.Label(self.root, text="颜色预览:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.color_canvas = tk.Canvas(self.root, width=100, height=100, bg="#000000")
        self.color_canvas.grid(row=3, column=1, sticky="w", pady=5)

        # 十六进制颜色值
        ttk.Label(self.root, text="十六进制:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.hex_label = ttk.Label(self.root, text="#000000")
        self.hex_label.grid(row=4, column=1, sticky="w")

        # 控制按钮
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(self.control_frame, text="复制RGB", command=self.copy_rgb).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="复制HSV", command=self.copy_hsv).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="复制HEX", command=self.copy_hex).pack(side="left", padx=5)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("移动鼠标开始取色...")
        ttk.Label(self.root, textvariable=self.status_var).grid(row=6, column=0, columnspan=2, sticky="ew", padx=10)

    def start_mouse_listener(self):
        def on_move(x, y):
            try:
                # 获取屏幕颜色
                screenshot = pyautogui.screenshot()
                r, g, b = screenshot.getpixel((x, y))

                # 转换为HSV
                pixel_bgr = np.uint8([[[b, g, r]]])
                pixel_hsv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2HSV)
                h, s, v = pixel_hsv[0][0]

                # 更新数据
                self.latest_data = {
                    "position": (x, y),
                    "rgb": (r, g, b),
                    "hsv": (h, s, v)
                }

            except Exception as e:
                print(f"Error: {e}")

        with mouse.Listener(on_move=on_move) as listener:
            while self.running:
                time.sleep(0.01)
            listener.stop()

    def update_ui(self):
        if not self.running:
            return

        # 更新位置信息
        x, y = self.latest_data["position"]
        self.pos_label.config(text=f"({x}, {y})")

        # 更新RGB值
        r, g, b = self.latest_data["rgb"]
        self.rgb_label.config(text=f"{r:3d}, {g:3d}, {b:3d}")

        # 更新HSV值
        h, s, v = self.latest_data["hsv"]
        self.hsv_label.config(text=f"{h:3d}, {s:3d}, {v:3d}")

        # 更新颜色预览
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_canvas.config(bg=hex_color)
        self.hex_label.config(text=hex_color)

        # 每50毫秒更新一次
        self.root.after(50, self.update_ui)

    def copy_rgb(self):
        r, g, b = self.latest_data["rgb"]
        self.root.clipboard_clear()
        self.root.clipboard_append(f"{r}, {g}, {b}")
        self.status_var.set("已复制RGB值到剪贴板")

    def copy_hsv(self):
        h, s, v = self.latest_data["hsv"]
        self.root.clipboard_clear()
        self.root.clipboard_append(f"{h}, {s}, {v}")
        self.status_var.set("已复制HSV值到剪贴板")

    def copy_hex(self):
        r, g, b = self.latest_data["rgb"]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.root.clipboard_clear()
        self.root.clipboard_append(hex_color)
        self.status_var.set("已复制HEX值到剪贴板")

    def on_close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorPickerApp(root)
    root.mainloop()