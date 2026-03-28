# -*- coding: utf-8 -*-
"""
手动将 tile patch（如 tile_chara 下同一服装文件夹中的 PNG）拼成一张图。

依赖: pip install pillow

用法:
  python scripts/joint_patches.py
  python scripts/joint_patches.py "D:/.../tile_chara/closet/nero/bridal"

保存:
  指定基底文件名后，同目录写入:
  - <名>.json  二维列表，每格为文件名字符串或 null（空格）
  - <名>.png   按网格拼接的 RGBA 图像
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageEnhance, ImageTk
except ImportError:
    print("需要 Pillow: pip install pillow", file=sys.stderr)
    sys.exit(1)


def _load_folder_images(folder: Path) -> tuple[list[Path], int, int]:
    """返回 (按名排序的 png 路径列表, 最大宽, 最大高)。"""
    paths = sorted(folder.glob("*.png")) + sorted(folder.glob("*.PNG"))
    if not paths:
        return [], 64, 64
    mw = mh = 0
    for p in paths:
        with Image.open(p) as im:
            w, h = im.size
            mw, mh = max(mw, w), max(mh, h)
    return paths, max(mw, 1), max(mh, 1)


class PatchPuzzleApp:
    THUMB = 72
    PALETTE_COLS = 4

    def __init__(self, root: tk.Tk, initial_folder: Path | None) -> None:
        self.root = root
        self.root.title("Patch 拼图 — joint_patches")
        self.folder: Path | None = None
        self.patch_paths: list[Path] = []
        self.cell_w = 64
        self.cell_h = 64
        self.rows = 12
        self.cols = 12
        # grid[r][c] = filename str or None
        self.grid: list[list[str | None]] = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.selected_name: str | None = None
        # (文件绝对路径 str, 是否变暗) -> PhotoImage
        self._thumb_photo_cache: dict[tuple[str, bool], ImageTk.PhotoImage] = {}
        self._palette_widgets: list[tk.Widget] = []
        self._palette_labels: dict[str, tk.Label] = {}

        self._build_ui()

        if initial_folder and initial_folder.is_dir():
            self.open_folder(initial_folder)

    def _build_ui(self) -> None:
        menubar = tk.Menu(self.root)
        fm = tk.Menu(menubar, tearoff=0)
        fm.add_command(label="打开文件夹…", command=self._menu_open_folder)
        fm.add_command(label="保存拼图…", command=self._menu_save)
        fm.add_separator()
        fm.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=fm)

        gm = tk.Menu(menubar, tearoff=0)
        gm.add_command(label="设置网格行列…", command=self._dialog_grid_size)
        gm.add_command(label="清空网格", command=self._clear_grid)
        menubar.add_cascade(label="网格", menu=gm)
        self.root.config(menu=menubar)

        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, width=320)
        main.add(left, weight=0)

        ttk.Label(left, text="素材（点击选择）").pack(anchor=tk.W)
        pal_wrap = ttk.Frame(left)
        pal_wrap.pack(fill=tk.BOTH, expand=True)
        self.palette_canvas = tk.Canvas(
            pal_wrap, width=self.THUMB * self.PALETTE_COLS + 24, highlightthickness=0
        )
        pscroll = ttk.Scrollbar(pal_wrap, orient=tk.VERTICAL, command=self.palette_canvas.yview)
        self.palette_inner = ttk.Frame(self.palette_canvas)
        self.palette_inner.bind(
            "<Configure>",
            lambda e: self.palette_canvas.configure(scrollregion=self.palette_canvas.bbox("all")),
        )
        self.palette_canvas.create_window((0, 0), window=self.palette_inner, anchor=tk.NW)
        self.palette_canvas.configure(yscrollcommand=pscroll.set)
        self.palette_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pscroll.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_palette_wheel(e):
            self.palette_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        self.palette_canvas.bind("<MouseWheel>", _on_palette_wheel)
        self.palette_inner.bind("<MouseWheel>", _on_palette_wheel)

        right = ttk.Frame(main)
        main.add(right, weight=1)

        self.status = ttk.Label(right, text="未加载文件夹")
        self.status.pack(anchor=tk.W, padx=4, pady=2)

        grid_frame = ttk.Frame(right)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.grid_canvas = tk.Canvas(grid_frame, bg="#2b2b2b", highlightthickness=0)
        gscroll_y = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL, command=self.grid_canvas.yview)
        gscroll_x = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL, command=self.grid_canvas.xview)
        self.grid_canvas.configure(
            yscrollcommand=gscroll_y.set, xscrollcommand=gscroll_x.set, scrollregion=(0, 0, 800, 600)
        )
        self.grid_canvas.grid(row=0, column=0, sticky="nsew")
        gscroll_y.grid(row=0, column=1, sticky="ns")
        gscroll_x.grid(row=1, column=0, sticky="ew")
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        self.grid_canvas.bind("<Button-1>", self._on_grid_click)
        self.grid_canvas.bind("<Button-3>", self._on_grid_right_click)
        self.grid_canvas.bind("<Configure>", lambda e: self._redraw_grid())

        hint = (
            "左键：将当前选中的 patch 放入格子；右键：清除格子。"
            " 网格尺寸在「网格」菜单中修改。"
        )
        ttk.Label(right, text=hint, wraplength=520).pack(anchor=tk.W, padx=4, pady=4)

    def _menu_open_folder(self) -> None:
        d = filedialog.askdirectory(title="选择 patch 文件夹")
        if d:
            self.open_folder(Path(d))

    def open_folder(self, folder: Path) -> None:
        self.folder = folder.resolve()
        self.patch_paths, mw, mh = _load_folder_images(self.folder)
        self.cell_w, self.cell_h = mw, mh
        self._thumb_photo_cache.clear()
        if not self.patch_paths:
            messagebox.showwarning("无图片", f"文件夹中没有 PNG：\n{self.folder}")
            self.status.config(text=f"无 PNG：{self.folder}")
            return
        self._fill_palette()
        self._redraw_grid()
        self.status.config(
            text=f"已加载 {len(self.patch_paths)} 张 | 单格最大 {self.cell_w}×{self.cell_h} | {self.folder}"
        )

    def _thumb_photo(self, path: Path, dim: bool) -> ImageTk.PhotoImage:
        key = (str(path.resolve()), dim)
        if key in self._thumb_photo_cache:
            return self._thumb_photo_cache[key]
        im = Image.open(path).convert("RGBA")
        im.thumbnail((self.THUMB, self.THUMB), Image.Resampling.LANCZOS)
        if dim:
            r, g, b, a = im.split()
            rgb = Image.merge("RGB", (r, g, b))
            rgb = ImageEnhance.Brightness(rgb).enhance(0.38)
            r2, g2, b2 = rgb.split()
            im = Image.merge("RGBA", (r2, g2, b2, a))
        ph = ImageTk.PhotoImage(im)
        self._thumb_photo_cache[key] = ph
        return ph

    def _used_patch_names(self) -> set[str]:
        return {n for row in self.grid for n in row if n}

    def _sync_palette_dim(self) -> None:
        """已放入网格的素材在左侧显示为变暗缩略图。"""
        if not self.folder or not self._palette_labels:
            return
        used = self._used_patch_names()
        for name, lb in self._palette_labels.items():
            p = self.folder / name
            if not p.is_file():
                continue
            ph = self._thumb_photo(p, dim=name in used)
            lb.config(image=ph)
            lb.image = ph  # 防止 PhotoImage 被回收

    def _fill_palette(self) -> None:
        for w in self._palette_widgets:
            w.destroy()
        self._palette_widgets.clear()
        self._palette_labels.clear()
        row = col = 0
        for p in self.patch_paths:
            name = p.name
            fr = ttk.Frame(self.palette_inner, relief=tk.RIDGE, borderwidth=1)
            fr.grid(row=row, column=col, padx=2, pady=2, sticky=tk.NW)
            ph = self._thumb_photo(p, dim=False)
            lb = tk.Label(fr, image=ph, cursor="hand2")
            lb.image = ph  # noqa: keep ref
            lb.pack()
            self._palette_labels[name] = lb
            short = name if len(name) <= 18 else name[:15] + "…"
            ttk.Label(fr, text=short, font=("", 8)).pack()
            fr.bind("<Button-1>", lambda e, n=name: self._select_patch(n))
            lb.bind("<Button-1>", lambda e, n=name: self._select_patch(n))
            self._palette_widgets.append(fr)
            col += 1
            if col >= self.PALETTE_COLS:
                col = 0
                row += 1
        self._sync_palette_dim()

    def _select_patch(self, name: str) -> None:
        self.selected_name = name
        self.status.config(text=f"已选: {name} | 左键网格放置")

    def _cell_at_event(self, event) -> tuple[int, int] | None:
        x = self.grid_canvas.canvasx(event.x)
        y = self.grid_canvas.canvasy(event.y)
        c = int(x // self.cell_w)
        r = int(y // self.cell_h)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None

    def _on_grid_click(self, event) -> None:
        pos = self._cell_at_event(event)
        if not pos:
            return
        r, c = pos
        if not self.selected_name:
            messagebox.showinfo("提示", "请先在左侧点击一张 patch 选中。")
            return
        self.grid[r][c] = self.selected_name
        self._redraw_grid()

    def _on_grid_right_click(self, event) -> None:
        pos = self._cell_at_event(event)
        if not pos:
            return
        r, c = pos
        self.grid[r][c] = None
        self._redraw_grid()

    def _clear_grid(self) -> None:
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self._redraw_grid()

    def _dialog_grid_size(self) -> None:
        d = tk.Toplevel(self.root)
        d.title("网格大小")
        ttk.Label(d, text="行数").grid(row=0, column=0, padx=6, pady=6)
        ttk.Label(d, text="列数").grid(row=1, column=0, padx=6, pady=6)
        er = ttk.Entry(d, width=8)
        ec = ttk.Entry(d, width=8)
        er.insert(0, str(self.rows))
        ec.insert(0, str(self.cols))
        er.grid(row=0, column=1, padx=6, pady=6)
        ec.grid(row=1, column=1, padx=6, pady=6)

        def apply() -> None:
            try:
                nr = max(1, int(er.get()))
                nc = max(1, int(ec.get()))
            except ValueError:
                messagebox.showerror("错误", "请输入正整数")
                return
            old = self.grid
            orows, ocols = self.rows, self.cols
            self.rows, self.cols = nr, nc
            newg = [[None for _ in range(nc)] for _ in range(nr)]
            for r in range(min(orows, nr)):
                for c in range(min(ocols, nc)):
                    newg[r][c] = old[r][c]
            self.grid = newg
            d.destroy()
            self._redraw_grid()

        ttk.Button(d, text="确定", command=apply).grid(row=2, column=0, columnspan=2, pady=8)

    def _redraw_grid(self) -> None:
        self.grid_canvas.delete("all")
        self.grid_canvas._cell_images = []  # 防止 PhotoImage 被 GC
        if not self.folder:
            return
        w = self.cols * self.cell_w
        h = self.rows * self.cell_h
        self.grid_canvas.configure(scrollregion=(0, 0, w, h))
        for r in range(self.rows):
            for c in range(self.cols):
                x0, y0 = c * self.cell_w, r * self.cell_h
                x1, y1 = x0 + self.cell_w, y0 + self.cell_h
                self.grid_canvas.create_rectangle(
                    x0, y0, x1, y1, outline="#555", width=1, fill="#1e1e1e"
                )
                name = self.grid[r][c]
                if not name:
                    continue
                p = self.folder / name
                if not p.is_file():
                    continue
                try:
                    im = Image.open(p).convert("RGBA")
                    ph = ImageTk.PhotoImage(im)
                    self.grid_canvas.create_image(x0, y0, anchor=tk.NW, image=ph, tags="cell")
                    self.grid_canvas._cell_images.append(ph)
                except OSError:
                    pass
        self._sync_palette_dim()

    def _menu_save(self) -> None:
        if not self.folder:
            messagebox.showwarning("提示", "请先打开文件夹")
            return
        path = filedialog.asksaveasfilename(
            title="保存拼图（将同时写入 .json 与 .png）",
            defaultextension=".png",
            filetypes=[("PNG 图像", "*.png"), ("所有文件", "*.*")],
        )
        if not path:
            return
        base = Path(path)
        png_path = base.with_suffix(".png")
        json_path = base.with_suffix(".json")

        # 合成图：每格 cell_w x cell_h，RGBA
        out = Image.new("RGBA", (self.cols * self.cell_w, self.rows * self.cell_h), (0, 0, 0, 0))
        for r in range(self.rows):
            for c in range(self.cols):
                name = self.grid[r][c]
                if not name:
                    continue
                fp = self.folder / name
                if not fp.is_file():
                    continue
                im = Image.open(fp).convert("RGBA")
                x, y = c * self.cell_w, r * self.cell_h
                if im.size != (self.cell_w, self.cell_h):
                    # 小于则左上角对齐，大于则裁剪
                    tmp = Image.new("RGBA", (self.cell_w, self.cell_h), (0, 0, 0, 0))
                    tmp.paste(im, (0, 0))
                    im = tmp
                out.paste(im, (x, y))

        out.save(png_path)
        payload = {
            "folder": str(self.folder),
            "rows": self.rows,
            "cols": self.cols,
            "cell_width": self.cell_w,
            "cell_height": self.cell_h,
            "grid": self.grid,
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        messagebox.showinfo("已保存", f"{png_path}\n{json_path}")
        self.status.config(text=f"已保存 → {png_path.name} / {json_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="手动拼接 tile patch PNG")
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="patch 所在文件夹（可选，也可启动后在菜单中打开）",
    )
    args = parser.parse_args()
    initial = Path(args.folder).resolve() if args.folder else None

    root = tk.Tk()
    root.geometry("1100x720")
    PatchPuzzleApp(root, initial)
    root.mainloop()


if __name__ == "__main__":
    main()
