# BBAgent · 桌宠

桌面宠物小应用：启动后出现在屏幕右下角，置顶显示，支持拖拽与互动。

## 功能

- **置顶显示**：窗口始终在最前，不遮挡时也可看到桌宠
- **两种状态**：Idle（待机） / Drag（拖动），对应 `assets/Idle.png` 与 `assets/Drag.png`
- **长按左键拖动**：长按约 0.4 秒进入拖动状态，可移动到屏幕任意位置
- **点击互动**：Idle 下短按点击会弹出「怎么啦？」气泡（半透明黑底）
- **尺寸自适应**：若桌宠大于屏幕高度的 1/6，则自动缩小至不超过 1/6
- **退出**：右键弹出菜单，选择「退出」关闭程序

## 环境与依赖

- Python 3.x（标准库 `tkinter`）
- 可选： [Pillow](https://pypi.org/project/Pillow/)（用于更清晰的缩放），未安装时使用 tkinter 内置缩放

## 运行方式

### 直接运行

```bash
python desktop_pet.py
```

### 打包为 exe（推荐使用 Anaconda `games` 环境）

```bash
conda activate games
pip install pyinstaller Pillow   # 若未安装
pyinstaller desktop_pet.spec --noconfirm
```

生成的可执行文件在 `dist/DesktopPet.exe`，双击即可运行，无需单独携带 `assets` 文件夹。

## 项目结构

```
BBAgent/
├── assets/           # 桌宠图片（Idle.png、Drag.png）
├── desktop_pet.py   # 主程序
├── desktop_pet.spec # PyInstaller 打包配置
└── README.md
```

## 许可证

MIT
