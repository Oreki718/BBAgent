# -*- coding: utf-8 -*-
"""
桌宠 - 桌面宠物
启动后出现在屏幕右下角，置顶显示。支持 Idle / Drag 状态，长按拖动，点击显示「怎么啦？」。
右键弹出菜单，可选择退出。
"""
import sys
import os
import tkinter as tk
from tkinter import font as tkfont

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# 资源路径：打包成 exe 时使用 PyInstaller 解压目录，否则使用脚本所在目录
if getattr(sys, "frozen", False):
    _base_dir = sys._MEIPASS
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_base_dir, "assets")
IDLE_IMAGE_PATH = os.path.join(ASSETS_DIR, "Idle.png")
DRAG_IMAGE_PATH = os.path.join(ASSETS_DIR, "Drag.png")

# 透明色（用于无边框时抠掉窗口背景，选一个图片里不会出现的颜色）
TRANSPARENT_COLOR = "#010101"
# 对应的 RGB 元组，供 PIL 合成透明背景用
TRANSPARENT_RGB = (1, 1, 1)

# 窗口上下留白（像素），避免 Windows 透明窗口对高图顶部/底部裁剪
PAD_V = 20

# 桌宠最大尺寸：不超过屏幕高度的六分之一（大于此尺寸时才缩小）
# 具体值在 _load_images 中按当前屏幕高度计算

# 长按判定时间（毫秒）
LONG_PRESS_MS = 400

# 气泡显示时长（毫秒）
BUBBLE_DURATION_MS = 2500


class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except Exception:
            pass

        self.state = "Idle"  # "Idle" | "Drag"
        self._long_press_id = None
        self._press_x = self._press_y = 0
        self._win_x = self._win_y = 0
        self._bubble_id = None

        # 加载图片（保持引用防止被回收）
        self._photo_idle = None
        self._photo_drag = None
        self._load_images()

        # 主显示：窗口比图片高 PAD_V（上下留白），人物在画布内垂直居中，避免顶部/底部被系统裁剪
        self._win_w = self._w
        self._win_h = self._h + PAD_V
        self.root.geometry(f"{self._win_w}x{self._win_h}")
        self.canvas = tk.Canvas(
            self.root,
            width=self._win_w,
            height=self._win_h,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0,
        )
        self.canvas.config(scrollregion=(0, 0, self._win_w, self._win_h))
        self.canvas.pack(fill=tk.BOTH, expand=False)
        self._show_image("Idle")

        # 初始位置：屏幕右下角
        self._place_bottom_right()

        # 绑定鼠标
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<Button-3>", self._on_right_click)

        # 气泡窗口（延迟创建）
        self._bubble_window = None

    def _load_images(self):
        if not os.path.isfile(IDLE_IMAGE_PATH):
            raise FileNotFoundError(f"找不到 Idle 图片: {IDLE_IMAGE_PATH}")
        if not os.path.isfile(DRAG_IMAGE_PATH):
            raise FileNotFoundError(f"找不到 Drag 图片: {DRAG_IMAGE_PATH}")
        # 最大尺寸 = 屏幕高度的六分之一，仅当桌宠大于此尺寸时才缩小
        self.root.update_idletasks()
        screen_h = self.root.winfo_screenheight()
        max_size = max(1, screen_h // 6)
        if _HAS_PIL:
            self._photo_idle, (self._w, self._h) = self._load_and_resize_pil(
                IDLE_IMAGE_PATH, max_size
            )
            self._photo_drag, _ = self._load_and_resize_pil(DRAG_IMAGE_PATH, max_size)
        else:
            self._photo_idle = tk.PhotoImage(file=IDLE_IMAGE_PATH)
            self._photo_drag = tk.PhotoImage(file=DRAG_IMAGE_PATH)
            ow, oh = self._photo_idle.width(), self._photo_idle.height()
            self._w, self._h = ow, oh
            if ow > max_size or oh > max_size:
                scale = min(max_size / ow, max_size / oh)
                self._w = int(ow * scale)
                self._h = int(oh * scale)
                self._photo_idle = self._photo_idle.subsample(
                    max(1, ow // self._w), max(1, oh // self._h)
                )
                self._photo_drag = self._photo_drag.subsample(
                    max(1, self._photo_drag.width() // self._w),
                    max(1, self._photo_drag.height() // self._h),
                )

    def _load_and_resize_pil(self, path: str, max_size: int):
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        if w > max_size or h > max_size:
            ratio = min(max_size / w, max_size / h)
            nw, nh = int(w * ratio), int(h * ratio)
            resample = getattr(Image, "Resampling", Image).LANCZOS
            img = img.resize((nw, nh), resample)
            w, h = nw, nh
        # 透明背景 PNG：合成到纯色底上再转 PhotoImage，避免 Windows 下 alpha 裁剪/显示异常
        bg = Image.new("RGB", (w, h), TRANSPARENT_RGB)
        if img.mode == "RGBA" and img.split()[3] is not None:
            bg.paste(img, (0, 0), img.split()[3])
        else:
            bg.paste(img, (0, 0))
        return ImageTk.PhotoImage(bg), (w, h)

    def _show_image(self, state: str):
        # 图片在画布内水平居中、垂直居中（上下留 PAD_V 空间，避免被裁剪）
        cx = self._w // 2
        cy = (PAD_V + self._h) // 2
        if state == "Idle":
            self.canvas.delete("pet")
            self.canvas.create_image(
                cx, cy, image=self._photo_idle, tags=("pet",)
            )
        else:
            self.canvas.delete("pet")
            self.canvas.create_image(
                cx, cy, image=self._photo_drag, tags=("pet",)
            )

    def _place_bottom_right(self, margin_x=40, margin_y=40):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - self._win_w - margin_x
        y = sh - self._win_h - margin_y
        self.root.geometry(f"+{x}+{y}")

    def _on_press(self, event):
        self._press_x = event.x_root
        self._press_y = event.y_root
        self._win_x = self.root.winfo_x()
        self._win_y = self.root.winfo_y()
        if self.state == "Idle":
            self._long_press_id = self.root.after(
                LONG_PRESS_MS, self._on_long_press
            )

    def _on_long_press(self):
        self._long_press_id = None
        if self.state != "Idle":
            return
        self.state = "Drag"
        self._show_image("Drag")

    def _on_release(self, event):
        if self._long_press_id is not None:
            self.root.after_cancel(self._long_press_id)
            self._long_press_id = None
            # 判定为点击（未进入拖动）
            if self.state == "Idle":
                self._show_bubble()
            return
        if self.state == "Drag":
            self.state = "Idle"
            self._show_image("Idle")

    def _on_motion(self, event):
        if self.state != "Drag":
            return
        dx = event.x_root - self._press_x
        dy = event.y_root - self._press_y
        self._press_x = event.x_root
        self._press_y = event.y_root
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _on_right_click(self, event):
        """右键弹出菜单栏，选择退出."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="退出", command=self._quit)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _quit(self):
        """退出程序."""
        if self._long_press_id is not None:
            self.root.after_cancel(self._long_press_id)
        if self._bubble_id is not None:
            self.root.after_cancel(self._bubble_id)
        if self._bubble_window is not None:
            try:
                self._bubble_window.destroy()
            except Exception:
                pass
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def _show_bubble(self):
        if self._bubble_id is not None:
            self.root.after_cancel(self._bubble_id)
            self._bubble_id = None
        if self._bubble_window is not None:
            try:
                self._bubble_window.destroy()
            except Exception:
                pass
            self._bubble_window = None

        # 气泡小窗口：半透明黑底 + 「怎么啦？」
        bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.wm_attributes("-topmost", True)
        bubble.wm_attributes("-alpha", 0.85)
        bubble.configure(bg="#333333")

        text = "怎么啦？"
        f = tkfont.Font(family="Microsoft YaHei", size=12, weight="normal")
        pad_x, pad_y = 12, 8
        label = tk.Label(
            bubble,
            text=text,
            font=f,
            fg="white",
            bg="#333333",
            padx=pad_x,
            pady=pad_y,
        )
        label.pack()

        # 放在桌宠上方居中
        bubble.update_idletasks()
        bw = label.winfo_reqwidth() + pad_x * 2
        bh = label.winfo_reqheight() + pad_y * 2
        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        pet_w = self._win_w
        bx = pet_x + (pet_w - bw) // 2
        by = pet_y - bh - 8
        # 避免超出屏幕顶部
        if by < 0:
            by = pet_y + self._win_h + 8
        bubble.geometry(f"{bw}x{bh}+{bx}+{by}")
        self._bubble_window = bubble

        def close_bubble():
            self._bubble_id = None
            try:
                self._bubble_window.destroy()
            except Exception:
                pass
            self._bubble_window = None

        self._bubble_id = self.root.after(BUBBLE_DURATION_MS, close_bubble)
        bubble.bind("<Button-1>", lambda e: close_bubble())

    def run(self):
        self.root.mainloop()


def main():
    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()
