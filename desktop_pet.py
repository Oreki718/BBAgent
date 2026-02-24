# -*- coding: utf-8 -*-
"""
桌宠 - 桌面宠物
启动后出现在屏幕右下角，置顶显示。支持 Idle / Drag 状态，长按拖动，点击随机显示台词。
右键弹出菜单，可选择退出。
"""
import sys
import os
import json
import random
import tkinter as tk
from tkinter import font as tkfont

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# 多屏虚拟屏幕范围（Windows）；非 Windows 或获取失败时为 None，用 Tk 的 screen 信息
def _get_virtual_screen_bounds():
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        user32 = ctypes.windll.user32
        vx = user32.GetSystemMetrics(76)
        vy = user32.GetSystemMetrics(77)
        vw = user32.GetSystemMetrics(78)
        vh = user32.GetSystemMetrics(79)
        return (vx, vy, vw, vh)
    except Exception:
        return None

# 资源路径：打包成 exe 时使用 PyInstaller 解压目录，否则使用脚本所在目录
if getattr(sys, "frozen", False):
    _base_dir = sys._MEIPASS
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_base_dir, "assets")
WORDS_DIR = os.path.join(_base_dir, "words")
LINES_JSON_PATH = os.path.join(WORDS_DIR, "lines.json")
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
        self._close_bubble()
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
        self._close_bubble()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def _close_bubble(self):
        """关闭台词气泡（取消定时并销毁窗口）。"""
        if self._bubble_id is not None:
            self.root.after_cancel(self._bubble_id)
            self._bubble_id = None
        if self._bubble_window is not None:
            try:
                self._bubble_window.destroy()
            except Exception:
                pass
            self._bubble_window = None

    def _get_random_line(self) -> str:
        """从 words/lines.json 的 lines 数组中随机取一句；文件不存在或为空时返回默认台词。"""
        default = "怎么啦？"
        try:
            if not os.path.isfile(LINES_JSON_PATH):
                return default
            with open(LINES_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            lines = data.get("lines")
            if not lines or not isinstance(lines, list):
                return default
            lines = [str(s).strip() for s in lines if s]
            return random.choice(lines) if lines else default
        except Exception:
            return default

    def _show_bubble(self):
        self._close_bubble()

        # 气泡小窗口：半透明黑底 + 随机台词，按屏幕宽度与桌宠位置限制宽度并自动换行
        text = self._get_random_line()
        bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.wm_attributes("-topmost", True)
        bubble.wm_attributes("-alpha", 0.85)
        bubble.configure(bg="#333333")
        f = tkfont.Font(family="Microsoft YaHei", size=12, weight="normal")
        pad_x, pad_y = 12, 8
        self.root.update_idletasks()
        v = _get_virtual_screen_bounds()
        if v is not None:
            vx, vy, vw, vh = v
            sw, sh = vw, vh
        else:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            vx = vy = 0
            vw, vh = sw, sh
        pet_x = self.root.winfo_rootx()
        pet_y = self.root.winfo_rooty()
        pet_w = self._win_w
        margin = 40
        pet_center = pet_x + pet_w // 2
        left_room = pet_center - vx - margin
        right_room = (vx + vw) - margin - pet_center
        max_bubble_w = min(vw - 2 * margin, 2 * min(left_room, right_room))
        max_bubble_w = max(120, max_bubble_w)
        wraplength_px = max_bubble_w - pad_x * 2
        label = tk.Label(
            bubble,
            text=text,
            font=f,
            fg="white",
            bg="#333333",
            padx=pad_x,
            pady=pad_y,
            wraplength=wraplength_px,
            justify=tk.LEFT,
        )
        label.pack()

        bubble.update_idletasks()
        bw = min(label.winfo_reqwidth() + pad_x * 2, max_bubble_w)
        bh = label.winfo_reqheight() + pad_y * 2
        bx = pet_x + (pet_w - bw) // 2
        by = pet_y - bh - 8
        if by < vy:
            by = pet_y + self._win_h + 8
        bx = max(vx, min(bx, vx + vw - bw))
        by = max(vy, min(by, vy + vh - bh))
        bubble.geometry(f"{bw}x{bh}+{bx}+{by}")
        self._bubble_window = bubble

        def reapply_position():
            if self._bubble_window is not None and self._bubble_window.winfo_exists():
                self._bubble_window.geometry(f"+{bx}+{by}")
        self.root.after(0, reapply_position)

        def on_enter(_e):
            if self._bubble_id is not None:
                self.root.after_cancel(self._bubble_id)
                self._bubble_id = None

        def on_leave(_e):
            if self._bubble_window is not None and self._bubble_id is None:
                self._bubble_id = self.root.after(BUBBLE_DURATION_MS, self._close_bubble)

        self._bubble_id = self.root.after(BUBBLE_DURATION_MS, self._close_bubble)
        bubble.bind("<Enter>", on_enter)
        bubble.bind("<Leave>", on_leave)
        bubble.bind("<Button-1>", lambda e: self._close_bubble())

    def run(self):
        self.root.mainloop()


def main():
    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()
