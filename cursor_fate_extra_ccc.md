# Fate Extra CCC 游戏解包
_Exported on 3/24/2026 at 18:04:12 GMT+8 from Cursor (2.6.20)_

---

**User**

你好，我在尝试解包 Fate Extra CCC 游戏，从中整理游戏剧情文本，游戏CG 和角色语音。请你读取一下@data。然后我们一步步来解包 

---

**Cursor**


正在查看工作区中的 `data` 目录及相关结构，以便我们一步步解包 Fate Extra CCC 的资源。




已用 UTF-8 浏览了你本地的 `BBAgent\data`（该目录在 `.gitignore` 里，工具里默认搜不到，所以我用终端直接列了目录）。下面是客观现状和**下一步**建议。

---

## `data` 里现在有什么

| 路径（逻辑名） | 内容要点 |
|----------------|----------|
| **FateExtraCCC汉化完成版月研4** | 约 **1.06 GB** 的 `.iso`（PSP 汉化版本体）+ 说明 docx |
| **月研4 高清纹理包 2024.05.17更新** | 纹理更新包目录（具体 zip/文件在子层，可再展开用） |
| **模拟器** | PPSSPP 安装包、教程 PDF 等 |
| **FECCC金手指** | 金手指 ini + 教程 docx |
| **解包** | 三个子目录：**CG**（已有大量文件）、**文本**（0 个文件）、**语音**（0 个文件） |

**CG：** 在 `解包\CG` 下已有约 **12.8 万** 个文件；抽样路径里是 **月研高清纹理** 那套结构（`textures.ini`、`*.ktx2`、字体预览等）。这是**模拟器用的高清贴图线**，很适合整理 CG/UI/立绘，但不是从 `GAME.DNS` 里刚解出来的“原始 PSP 资源树”。

**文本 / 语音：** 目前还是空的，说明 **主资源包还没按“剧本/音频”分类解出来**，或解在了别处。

---

## 关键：`GAME.DNS` 其实已经在磁盘上了

在你这台机器上，除了 ISO 里会有一份大资源包外，PPSSPP 的存档目录里已经有一份**约 1.03 GB** 的 `GAME.DNS`（体量和你笔记里的 CPK 大包一致），路径形如：

`data\模拟器\ppsspp 1.17.1_win\memstick\PSP\SAVEDATA\NPJH50505USERID\GAME.DNS`

可以和 `resources_get.md` 里写的 **CRI CPK（`CpkHeader` / AT3 等）** 路线对齐：**下一步最省事的是直接拿这份 `GAME.DNS` 当解包输入**，不必先拆 ISO（除非你希望留一份“只读镜像里拷出来的”备份）。

---

## 建议的「一步步」顺序（与你要的三类资源对应）

1. **第一步（当前最该做）**  
   用 **QuickBMS + `cpk.bms`**，或 **CriPakTools / CPK Browser**，把上述 **`GAME.DNS` 解到一个新目录**（例如 `解包\GAME_DNS_out`，避免和现有上万 `ktx2` 混在一起）。

2. **第二步**  
   在输出目录里按扩展名粗分：  
   - 语音：`.at3`、`.adx`、`.hca`、`RIFF/WAVE` 等 → 归到 **`解包\语音`**，再用 **vgmstream / ffmpeg** 批量转 WAV 方便听。  
   - 图像：`.gim`、`.tm2` 等与 `ktx2` 区别对待（原始底图 vs 你已有一套高清纹理）。

3. **第三步**  
   文本：在全目录 **按 UTF-8/Shift-JIS 搜可读中文**（汉化版有时反而容易定位）；若只有二进制，再针对具体脚本格式做表结构分析——这步通常比语音慢。

4. **并行线（CG）**  
   你要「能直接用的 CG」：继续在 **`解包\CG`（ktx2）** 里整理即可；要和剧情时间轴严格对齐，再对照从 `GAME.DNS` 解出的文件名/目录习惯。

---

如果你愿意，**下一消息我们就做第 1 步**：你告诉我本机是否已安装 **QuickBMS**（或想用 **CriPakTools**），我可以根据你的选择写出**具体操作顺序**（选中哪个脚本、输出目录填哪里、`GAME.DNS` 用存档里那份还是坚持从 ISO 解压 `PSP_GAME\INSDIR\`）。若你希望我直接在仓库里加一个小脚本（例如：解包后按扩展名分拣到 `语音/`、`文本候选/`），也可以说一声我按你的目录习惯来写。

---

**User**

在进行以上解包步骤之前，我希望先将 CG 整理好，因为汉化组直接提供了高清材质包，所以我们不用从 DNS 文件中进行，解包，我已经将汉化组提供的高请纹理包解压到了@data/解包/CG/高清CG解压 ，问题是，目前的解包全部都是 ktx2 或者 zim 文件。分析一下人物立绘和游戏CG（插画）可能保存到了哪些文件夹中？如何将 ktx2 转化为我们常用的 png 或者 jpg 格式？

如果你需要下载新的软件或者包，可以下载到@agent_workspace ，这是专门提供给你的工作区

---

**Cursor**


分析 `高清CG解压` 的目录结构并查看你工作区里已有的 KTX2 转换方案；随后说明立绘/CG 的可能位置及转换步骤。




正在添加 `zim_to_png.py`，并更新批处理与指南：KTX 4.4+ 使用 `ktx extract --transcode rgba8`（不再使用已移除的 `convert` 子命令）。




## 目录里大概就是什么

根据 `data\解包\CG\高清CG解压` 下的**真实子目录名和数量**，可以这样理解（文件名多是哈希，分类主要靠**文件夹名**）：

| 目录 | 数量级 | 更可能对应 |
|------|--------|------------|
| **`tex_chara`** | ~780 个 `.ktx2` | **角色向整张贴图**（如 `alice`、`6th_blue_effects`），更接近单张立绘/大贴图 |
| **`tile_chara`** | ~2.4 万 `.ktx2` | **按衣柜/角色切的小图块**（如 `closet\gil\golden\`），GPU 切片，用来拼立绘和差分 |
| **`tile_bg`** | ~8.5 万 `.ktx2` | **背景 / 场景 CG 图块**（含 `chapter_start` 等）；全屏插画在 PSP 管线里常被**切成很多块** |
| **`tex_place`** | ~613 个 `.ktx2` | **地点场景**中等贴图（子文件夹多为场景名，如教室） |
| **`bb_channel`** | ~276 个 | BB 频道相关画面 |
| **`effects` / `tile_effects`** | 战斗与演出特效 | 一般不算「立绘/CG」归档核心 |
| **`ui`** | ~1.5 万 | 菜单、图标、字体等界面资源 |
| **`hanhuaban`** | 331 个 **`.zim`** | 汉化组增量包；PPSSPP 的 **ZIMG** 格式（你扫到的魔数是 `ZIMG`），多用于**汉化补丁相关贴图**，和 `ui` 交叉对照有用 |

**整理顺序建议**：先做 **`tex_chara` + `tile_chara`（人物）** → 再 **`tile_bg` + `tex_place`（场景/CG）** → 最后 **`hanhuaban`（zim）** 与 **`ui`**。全屏 CG 不要指望「一张 png 对应一张 ktx2」，大块图往往在 `tile_bg` 里按块拆开。

---

## KTX2 → PNG / JPG

- **PNG**：已在你指定的 **`agent_workspace`** 里装好 **KTX-Software 4.4.2**（`KTX-Software-4.4.2-Windows-x64\bin\ktx.exe`）。  
  **4.4 起没有 `ktx convert`**，要用：

  ```bat
  ktx extract --transcode rgba8 "输入.ktx2" "输出.png"
  ```

- 批量：运行 `agent_workspace\convert_hd_cg_ktx2_to_png.bat`（可选参数只转某一子目录，例如 `tex_chara`）。默认输出到 `data\解包\CG\converted_png\`。
- **JPG**：`ktx` 这条链路**直接出 PNG**；需要 JPG 时应在 PNG 上再转（**会丢透明通道**）。立绘/CG 想留透明就请**全程 PNG**。

---

## ZIM → PNG / JPG

`.zim` 是 PPSSPP 的 **ZIM 格式**（与 [PPSSPP `ZIMLoad`  
](https://github.com/hrydgard/ppsspp/blob/master/Common/Data/Format/ZIMLoad.h) 一致）。你这份 **`hanhuaban` 里抽样均为未压缩 RGBA**；若为 zlib/zstd 压缩，脚本里也已按标志位分支处理。

已在 `agent_workspace` 添加 **`zim_to_png.py`**，并已在本机对 **331 个** `hanhuaban\*.zim` 试跑成功。

```bat
pip install pillow
python agent_workspace\zim_to_png.py "data\解包\CG\高清CG解压\hanhuaban" -o "data\解包\CG\converted_png\hanhuaban"
```

要 **JPEG** 时加 `--jpg`（透明会合成到**白底**）。若将来遇到 **zstd** 压缩的 zim，再：`pip install zstandard`。

---

## 文档与顺手修复

- 已更新 **`agent_workspace\KTX2_Conversion_Guide.md`**，与当前路径和 **KTX 4.4 命令**一致。  
- 修正了 **`install_ktx.bat`** 里一行误触的 `束echo`。

**注意**：若对 **`tile_bg` 全量**转 PNG，文件数和磁盘占用会非常大，建议按子文件夹（如章节）分批转。若你愿意，下一步可以一起定一个「导出目录命名规范」（例如按角色/章节自动归档），再改批处理。

---

**User**

先为我转化 tex_chara 和 tile_chara，保存到@data/解包/CG/高清CG转化 

---

**Cursor**

我现在开始批量转换 `tex_chara` 和 `tile_chara`，并将结果保存到 `data\解包\CG\高清CG转化`；先检查是否已有同类长任务在跑，然后直接执行转换。

转换任务已启动（量比较大，约 `780 + 23851` 个文件），我会持续监控进度并在完成后给你结果。

进度正常，当前已开始写入目标目录（已生成一部分 `tex_chara` PNG）。由于总量接近 2.4 万张，我继续跑完后给你最终数量。

我发现转换速度偏慢（主要是每个文件都在刷警告日志），我将重启任务并**跳过已转文件**、屏蔽无关警告，这样会快很多。

刚才那次重启失败了：PowerShell 把 `ktx` 的警告当成错误中断了。我会立刻用更稳的方式继续跑（并保留已转换结果）。

转换已稳定继续执行，目前在 `tex_chara` 阶段；我继续盯着，完成后会给你最终统计。

我准备再提速一次：改成并行多进程转换（跳过已转文件），目标是尽快把两套目录一次性跑完。

`tex_chara` 已经全部转完（780/780），正在继续跑 `tile_chara`，我继续监控到结束。

当前进度：`tex_chara` 已完成，`tile_chara` 已完成约 1.1 万张；我继续跑到全部结束。

已完成转换，并按你要求保存到 `data\解包\CG\高清CG转化`。

- `tex_chara` → `PNG`：`780` 个
- `tile_chara` → `PNG`：`23851` 个
- 输出目录：
  - `data\解包\CG\高清CG转化\tex_chara`
  - `data\解包\CG\高清CG转化\tile_chara`

本次转换无失败（`fail=0`）。  
如果你愿意，下一步我可以帮你继续把这两批按“角色名/服装/场景标签”再做一层自动整理（比如生成索引清单 CSV）。

---

**User**

我看了一下，@data/解包/CG/高清CG转化/tex_chara 似乎是用在人物3D模型上的贴图，尔@data/解包/CG/高清CG转化/tile_chara 是人物的3D立绘，但是是一小块一小块的，需要拼起来。我需要你和我一起探索如何将人物立绘的 patch 拼起来，同时要考虑到同一个立绘可能又多个差分。我们可以先以把@data/解包/CG/高清CG转化/tile_chara/talk/bb的立绘拼起来我最基础的小目标。 

如果你搞清楚了应该如何拼接角色立绘，请解释给我。是直接从png的命名可以推测是拼法，还是PSP游戏有固有的立绘拼接逻辑，还是FateExtraCCC游戏中有相关的代码？

---

**Cursor**

这个目标很对，我先做两件事：一是分析 `tile_chara/talk/bb` 的图片尺寸与命名规律，二是查纹理包里的 `textures.ini` / PPSSPP 规则，看能不能直接恢复拼接坐标。随后给你一个可执行的拼接方案（先做 BB）。

我拿到一个关键结论：`talk/bb/body` 全是 `64x64` 瓦片，`face` 是 `128x128` 和 `64x64`，这说明它确实是“分块贴图”而非单张立绘。接下来我会读 `textures.ini` 看是否有坐标映射。

我这边判断：**仅靠文件名无法直接得到拼接坐标**，但我们可以先做一个“可视化探索”——把 `talk/bb` 按组自动生成联系图（contact sheet）和候选组合，先把“哪些是同一槽位/同一差分组”看清楚。我先写一个小脚本并跑出结果给你。

你这个判断很专业：`tex_chara` 更像模型贴图，`tile_chara` 才是对话立绘相关的拼块。

我先把 `talk/bb` 做了结构分析，结论是：

- `body`：`102` 张，全部 `64x64`
- `face`：`66` 张，其中 `46` 张 `128x128`、`20` 张 `64x64`
- 文件名是 `24` 位十六进制哈希，像 `0000000035a244daXXXXXXXX`
- `body` 的前 16 位全相同（`0000000035a244da`），`face` 有 3 个前缀组  
  这说明它们是“同一个纹理槽位下的不同内容版本”，不是“文件名里自带坐标”

我还生成了可视化联系图，方便你直观看差分组：

- `data/解包/CG/高清CG转化/tile_chara/talk/bb/_analysis/body_all.png`
- `data/解包/CG/高清CG转化/tile_chara/talk/bb/_analysis/face_all.png`
- 以及按前缀分组的 4 张图（`body_...png`、`face_...png`）

---

你问的核心问题，直接给结论：

1. **能不能仅从 PNG 文件名推测拼法？**  
   **不能准确。** 这些名字是 PPSSPP 纹理替换哈希键，本质是“地址/调色板/数据哈希”的标识，不含 `(x,y)` 拼接坐标。

2. **是不是 PSP 游戏有固有立绘拼接逻辑？**  
   **是。** 真实拼接发生在 PSP 的 GE 渲染命令里：每次绘制会给出顶点坐标、UV、混合顺序。也就是“运行时 drawcall 决定怎么拼”。

3. **Fate/CCC 代码里有没有相关逻辑？**  
   **有上层资源调用逻辑**（脚本/状态决定用哪组 body/face），但“具体怎么贴到屏幕上”大多走通用渲染管线，不会在纹理文件名里体现。

---

### 对 `talk/bb` 的最小可行拼接路线（靠谱且可复现）

- **先把“槽位”搞清楚**：你现在已经有 `body` 与 `face` 分组，这是第一步。
- **再拿运行时坐标**（关键）：用 PPSSPP 的帧调试/GE draw 信息，记录某一帧里 `bb` 的 body 和 face 各自绘制矩形。
- **最后批量重建差分**：固定 body 位置，枚举 face 差分做 alpha 合成。

如果你同意，下一步我可以直接帮你做一个“小型拼接器”：
- 输入：`body` 一张 + `face` 一张 + 你指定的偏移 `(x,y)`
- 输出：合成后的 BB 立绘预览
- 然后我们再通过少量样本快速反推出 `talk/bb` 的稳定偏移规则。

---

**User**

你能否能够获取到 PSP 的 GE 渲染命令？能否搜索类似的文档和教程，以此推测模型的拼接逻辑。

face 有 3 个前缀组，可能说明这是三种不同的表情差分。

---

**Cursor**

可以，我先去查 PPSSPP 官方与社区资料，确认**如何抓 GE 渲染命令 / drawcall**，然后结合你这个 `talk/bb` 案例给出可落地的拼接推断流程。

能，而且这条路是目前**最靠谱**的。

你的判断也很合理：`face` 有 3 个前缀组，**很可能**对应 3 套脸部资源池（可能是不同姿态/镜头/状态组），每组里再有多个表情差分。

## 结论先说

- **仅靠文件名（hash）不能还原拼接坐标**，因为它不含 `(x,y)`。
- 要还原立绘拼接，关键是拿到**运行时 GE 绘制信息**（drawcall 的顶点坐标、UV、纹理绑定顺序）。
- 这不是 Fate/CCC 独有黑魔法，而是 PSP GE 的通用绘制机制；CCC 只是“调用哪些 body/face 贴图”的上层逻辑在脚本里。

## 我能否“获取到 GE 渲染命令”？

- **可以获取思路和方法**，并且你本机可实操。
- 但我这里不能直接替你在图形界面里点击 PPSSPP 调试器，所以需要你在 PPSSPP 里操作几步，我来指导你怎么取证、怎么解读。

## 可用资料（你可以直接看）

- PPSSPP GE 调试流程：  
  [How to find a graphic issue with the GE debugger](https://github.com/hrydgard/ppsspp/wiki/How-to-find-a-graphic-issue-with-the-GE-debugger)
- PSP GE 架构与命令概念：  
  [The GE (Graphics Engine)](https://www.ppsspp.org/docs/psp-hardware/gpu/ge-overview/)
- 纹理替换 hash 机制说明（为什么 hash 不能给坐标）：  
  [Creating texture replacement packs](https://www.ppsspp.org/docs/reference/texture-replacement/)

## 针对 `talk/bb` 的最小实操流程（建议你现在就做）

1. 在 PPSSPP 打开一段 BB 对话立绘画面，暂停在目标表情。
2. 打开 `Debug -> GE Debugger`。
3. `Step Frame` 到该帧开头，再用 `Step Draw / Step Prim` 缩小到“刚画出 BB 立绘”的那几条 draw。
4. 记录该 draw 的：
   - 当前纹理（能对应到 `talk/bb/body` 或 `talk/bb/face`）
   - 顶点屏幕坐标（目标贴到屏幕哪里）
   - UV 范围（从纹理里取哪一块）
5. 对同一 body 换几种 face 重复抓取，看是否坐标固定、只换纹理 hash。

只要抓到 3~5 帧，我就能和你一起把 `talk/bb` 的拼接规则定出来（包括“同 body + face 差分”的组合逻辑）。

---

如果你愿意，下一步我可以给你一份**非常具体的记录模板**（每帧记哪些字段、如何命名），你按模板抓 5 条数据，我直接帮你反推出第一版自动拼接规则。

