═══════════════════════════════════════════════
TrainLens 数据集格式说明
═══════════════════════════════════════════════

TrainLens 支持标准的 ImageFolder 格式数据集。

═══════════════════════════════════════════════
一、目录结构
═══════════════════════════════════════════════

正确的目录结构：

dataset/
  train/
    class1/
      image001.jpg
      image002.jpg
      image003.png
      ...
    class2/
      image001.jpg
      image002.jpg
      ...
    class3/
      image001.jpg
      ...
  val/
    class1/
      image001.jpg
      image002.jpg
      ...
    class2/
      image001.jpg
      ...
    class3/
      image001.jpg
      ...

重要说明：
- 图片必须放在 类别文件夹 中
- 类别文件夹名称即为类别标签
- 训练集和验证集的类别名称应该一致

═══════════════════════════════════════════════
二、支持的图片格式
═══════════════════════════════════════════════

- .jpg / .jpeg
- .png
- .bmp
- .gif

文件名不限，但建议使用有意义的命名。

═══════════════════════════════════════════════
三、示例：猫狗分类数据集
═══════════════════════════════════════════════

dataset/
  train/
    cat/
      cat_001.jpg
      cat_002.jpg
      cat_003.jpg
      ... (共 500 张)
    dog/
      dog_001.jpg
      dog_002.jpg
      dog_003.jpg
      ... (共 500 张)
  val/
    cat/
      cat_val_001.jpg
      cat_val_002.jpg
      ... (共 100 张)
    dog/
      dog_val_001.jpg
      dog_val_002.jpg
      ... (共 100 张)

在 Dashboard 侧边栏配置：
- Train Directory: ./dataset/train
- Validation Directory: ./dataset/val

═══════════════════════════════════════════════
四、常见错误
═══════════════════════════════════════════════

❌ 错误 1：图片直接放在 train 目录下

dataset/
  train/
    image001.jpg  ← 错误！
    image002.jpg
  val/
    image001.jpg

正确做法：必须先创建类别文件夹

─────────────────────────────────────────────

❌ 错误 2：缺少类别文件夹

dataset/
  train/
    all_images/  ← 错误！只有一个文件夹
      cat001.jpg
      dog001.jpg

正确做法：按类别分开

dataset/
  train/
    cat/
      cat001.jpg
    dog/
      dog001.jpg

─────────────────────────────────────────────

❌ 错误 3：训练集和验证集类别不一致

dataset/
  train/
    cat/
    dog/
  val/
    cat/
    bird/  ← 错误！与训练集不一致

正确做法：保持类别一致

dataset/
  train/
    cat/
    dog/
  val/
    cat/
    dog/

─────────────────────────────────────────────

❌ 错误 4：文件格式不支持

dataset/
  train/
    cat/
      cat001.tif  ← 错误！不支持 .tif
      cat002.webp ← 错误！不支持 .webp

支持格式：.jpg, .jpeg, .png, .bmp, .gif

─────────────────────────────────────────────

❌ 错误 5：路径包含中文

dataset/
  train/
    猫/  ← 可能导致兼容性问题
    狗/

建议：使用英文目录名
  cat/
  dog/

═══════════════════════════════════════════════
五、数据集准备建议
═══════════════════════════════════════════════

1. 训练集和验证集比例
   - 推荐 80:20 或 70:30
   - 例如：训练 800 张，验证 200 张

2. 每个类别样本数
   - 尽量平衡（样本数接近）
   - 不平衡比例 < 5:1 为佳
   - 使用 Dataset Inspector 检查不平衡比例

3. 图片质量
   - 分辨率适中（不要太大或太小）
   - 格式统一（推荐 .jpg）
   - 避免损坏的图片

4. 目录命名
   - 使用英文
   - 简洁明了
   - 避免特殊字符

═══════════════════════════════════════════════
六、使用 Dataset Inspector 检查
═══════════════════════════════════════════════

1. 启动 Dashboard（双击 start_trainlens.bat）

2. 在侧边栏配置：
   - Train Directory: ./dataset/train
   - Validation Directory: ./dataset/val

3. 点击 "Dataset Inspector" Tab

4. 检查统计信息：
   - Train Images 数量是否正确
   - Val Images 数量是否正确
   - Classes 数量是否正确
   - Imbalance Ratio（不平衡比例）

5. 查看类别分布图表
   - 每个类别的样本数
   - 训练集和验证集的分布

6. 预览随机图片
   - 检查图片是否正常加载
   - 验证类别标签是否正确

═══════════════════════════════════════════════
七、快速创建测试数据集
═══════════════════════════════════════════════

如果你还没有数据集，可以使用项目自带的示例：

dataset/
  train/
    cat/  (10 张测试图片)
    dog/  (15 张测试图片)
  val/
    cat/  (3 张测试图片)
    dog/  (5 张测试图片)

这个示例数据集可以用来：
- 测试 TrainLens 功能
- 学习正确的目录结构
- 验证训练脚本

═══════════════════════════════════════════════
八、从其他格式转换
═══════════════════════════════════════════════

如果你的数据集是其他格式（如 COCO, YOLO, CSV），
需要先转换为 ImageFolder 格式。

转换脚本示例（Python）：

import shutil
from pathlib import Path

# 假设你有一个 CSV 文件：image_name, label
# image001.jpg, cat
# image002.jpg, dog

import pandas as pd

df = pd.read_csv('labels.csv')

for idx, row in df.iterrows():
    img_name = row['image_name']
    label = row['label']

    # 创建目标目录
    target_dir = Path(f'dataset/train/{label}')
    target_dir.mkdir(parents=True, exist_ok=True)

    # 复制图片
    src = Path(f'raw_images/{img_name}')
    dst = target_dir / img_name
    shutil.copy(src, dst)

═══════════════════════════════════════════════
九、总结
═══════════════════════════════════════════════

TrainLens 使用的 ImageFolder 格式：

✓ 简单直观
✓ 与 PyTorch 兼容
✓ 易于手动整理
✓ 支持任意类别数
✓ 支持常见图片格式

关键点：
1. 图片必须在类别文件夹中
2. 类别文件夹名称 = 类别标签
3. 训练集和验证集结构一致
4. 使用 Dataset Inspector 验证

如有问题，请参考：
- README_使用说明.txt
- docs/DATASET_INSPECTOR.md
