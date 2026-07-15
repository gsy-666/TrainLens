# TrainLens 图片标注器使用指南

## 功能概述

TrainLens 图片标注器是一个集成在 Dashboard 中的缺陷检测标注工具，支持：

- ✅ 矩形框标注（YOLO 格式）
- ✅ 缺陷类别管理
- ✅ 实时可视化预览
- ✅ 自动生成带框的标注图片
- ✅ 按类别分类浏览标注结果

---

## 使用场景

**适合：缺陷检测、质量检测、目标检测等任务**

示例：
- 工业缺陷检测（划痕、裂纹、气泡、污渍）
- 产品质量检测（瑕疵、损坏、变形）
- 表面检测（锈蚀、磨损、凹陷）

---

## 快速开始

### 1. 打开标注器

启动 TrainLens 后，点击顶部的 **"🏷️ Image Annotator"** 选项卡

### 2. 定义缺陷类别

在 **"Class Management"** 区域：

```
输入类别名称 → 点击 "➕ Add Class"
```

示例类别：
- `scratch` (划痕)
- `crack` (裂纹)
- `bubble` (气泡)
- `stain` (污渍)

每个类别会自动分配一个编号（从 0 开始）。

### 3. 选择图片

在 **"Select Image to Annotate"** 区域：
- 从下拉框选择要标注的图片
- 支持训练集和验证集中的所有图片

### 4. 添加标注

在 **"➕ Add New Annotation"** 区域输入：

| 参数 | 说明 | 范围 | 示例 |
|------|------|------|------|
| **Class** | 缺陷类别 | - | scratch |
| **X Center** | 框中心 X 坐标 | 0-1 | 0.5 (图片中间) |
| **Y Center** | 框中心 Y 坐标 | 0-1 | 0.3 |
| **Width** | 框宽度 | 0-1 | 0.2 (占图片 20%) |
| **Height** | 框高度 | 0-1 | 0.15 |

点击 **"✅ Add Annotation"** 保存。

---

## 坐标系统说明

YOLO 格式使用**归一化坐标**（0-1 范围）：

```
(0, 0) ────────────────────── (1, 0)
  │                              │
  │                              │
  │        (0.5, 0.5)            │
  │           ●                  │
  │                              │
(0, 1) ────────────────────── (1, 1)
```

### 坐标示例

**居中的小框：**
```
X Center: 0.5
Y Center: 0.5
Width: 0.2
Height: 0.2
```

**左上角的框：**
```
X Center: 0.15
Y Center: 0.15
Width: 0.3
Height: 0.3
```

**右下角的框：**
```
X Center: 0.85
Y Center: 0.85
Width: 0.3
Height: 0.3
```

---

## 可视化预览

在 **"Preview with Annotations"** 区域：
- 自动显示图片和所有标注框
- 不同类别使用不同颜色
- 框上方显示类别名称

---

## 管理标注

### 查看已有标注

在 **"Existing Annotations"** 区域：
- 列出当前图片的所有标注
- 显示详细坐标信息
- 点击 🗑️ 删除不需要的标注

### 生成所有可视化图片

在 **"Export Summary"** 区域：
- 点击 **"🖼️ Generate All Visualizations"** 按钮
- 自动为所有已标注的图片生成带框的可视化图片

---

## 按类别浏览

在 **"📊 Annotation Gallery - Browse by Class"** 区域：

1. **查看统计信息**：每个类别的标注图片数量
2. **选择类别**：从下拉框选择要查看的缺陷类别
3. **浏览图片**：3列网格显示该类别的所有标注图片

这样你可以快速查看：
- 某种缺陷有多少个标注实例
- 标注框的位置和大小是否合理
- 是否有漏标或误标

---

## 文件结构

标注完成后会自动生成以下文件：

```
你的项目目录/
├── annotations/
│   ├── classes.txt                    # 类别列表
│   ├── image001.txt                   # YOLO 格式标注
│   ├── image002.txt
│   ├── visualizations/                # 可视化图片
│   │   ├── image001_annotated.jpg
│   │   ├── image002_annotated.jpg
│   │   └── ...
│   └── gallery/                       # 按类别分类
│       ├── scratch/                   # 划痕类
│       │   ├── image001_annotated.jpg
│       │   └── image005_annotated.jpg
│       ├── crack/                     # 裂纹类
│       │   └── image002_annotated.jpg
│       └── ...
```

---

## 标注文件格式

### classes.txt
```
scratch
crack
bubble
stain
```

### image001.txt (YOLO 格式)
```
0 0.500000 0.300000 0.200000 0.150000
2 0.750000 0.600000 0.100000 0.080000
```

每行格式：
```
类别ID X中心 Y中心 宽度 高度
```

---

## 训练脚本接入

标注完成后，可以在训练脚本中读取标注数据：

```python
from pathlib import Path

# 读取类别列表
classes_file = Path("annotations/classes.txt")
classes = classes_file.read_text().strip().split('\n')
print(f"Classes: {classes}")

# 读取某张图片的标注
annotation_file = Path("annotations/image001.txt")
with open(annotation_file, 'r') as f:
    for line in f:
        class_id, x_center, y_center, width, height = map(float, line.split())
        class_name = classes[int(class_id)]
        print(f"Class: {class_name}, Box: ({x_center}, {y_center}, {width}, {height})")
```

---

## 常见问题

### Q: 如何快速标注中心位置的缺陷？
A: 使用 `X Center = 0.5, Y Center = 0.5` 作为中心点。

### Q: 标注框太大/太小怎么办？
A: 调整 Width 和 Height 参数。建议先标注几张，看可视化效果，再批量标注。

### Q: 如何删除某个类别？
A: 在 Class Management 区域，点击类别右侧的 🗑️ 按钮。

### Q: 如何清空所有标注重新开始？
A: 删除整个 `annotations/` 文件夹即可。

### Q: 标注文件可以用于 YOLO 训练吗？
A: 可以！格式完全兼容 YOLOv5/YOLOv8 等框架。

### Q: 可以导出为其他格式吗？
A: 当前只支持 YOLO 格式。如需 COCO 或 Pascal VOC 格式，可以使用格式转换工具。

---

## 最佳实践

### 1. 先定义完整的类别列表
在开始标注前，确定所有可能的缺陷类型。

### 2. 保持标注一致性
- 同一类型的缺陷使用相同的类别
- 框的大小尽量包含整个缺陷区域，留一点边距

### 3. 定期查看 Gallery
- 使用 "📊 Annotation Gallery" 检查标注质量
- 确认每个类别的标注数量均衡

### 4. 及时生成可视化
- 标注几张图片后，点击 "Generate All Visualizations"
- 检查标注框是否准确

### 5. 备份标注数据
- 定期备份 `annotations/` 文件夹
- 尤其是在进行大量标注后

---

## 总结

TrainLens 图片标注器提供了：
1. **简单的标注界面**：输入坐标即可添加标注
2. **实时可视化**：立即看到标注效果
3. **自动分类**：按类别组织标注图片
4. **Gallery 浏览**：快速查看每个类别的标注结果
5. **YOLO 格式**：直接用于训练

非常适合小规模缺陷检测项目的数据准备工作！
