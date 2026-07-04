# TrainLens Dataset Inspector 使用文档

## 概述

Dataset Inspector 是 TrainLens V1.3 新增的数据集检查工具，用于在训练前快速检查数据集的质量和分布。

## 功能特性

### 1. 自动路径读取

- 自动读取侧边栏中的 **Train Directory** 和 **Validation Directory**
- 无需重复输入路径
- 支持相对路径和绝对路径

### 2. ImageFolder 格式支持

Dataset Inspector 支持标准的 ImageFolder 目录结构：

```
dataset/
  train/
    class1/
      img1.jpg
      img2.png
      img3.jpeg
    class2/
      img1.jpg
      img2.png
  val/
    class1/
      img1.jpg
    class2/
      img1.jpg
```

**支持的图片格式：**
- `.jpg` / `.jpeg`
- `.png`
- `.bmp`
- `.gif`
- 大小写不敏感（JPG, jpg, PNG, png 均可）

### 3. 数据集统计

#### 汇总指标（4 个卡片）

1. **Train Images**: 训练集总图片数
2. **Val Images**: 验证集总图片数
3. **Classes**: 类别总数
4. **Imbalance Ratio**: 类别不平衡比例
   - 计算公式：`最大类别样本数 / 最小类别样本数`
   - 理想值接近 1.0
   - 比例越大说明数据越不平衡

#### 类别分布表格

显示每个类别的详细统计：

| Class | Train | Val | Total |
|-------|-------|-----|-------|
| cat   | 500   | 100 | 600   |
| dog   | 450   | 90  | 540   |

### 4. 可视化图表

**Grouped Bar Chart（分组柱状图）**
- X 轴：类别名称
- Y 轴：图片数量
- 蓝色柱：训练集样本数
- 红色柱：验证集样本数
- 交互式图表，支持缩放和悬停查看详情

### 5. 随机图片预览

**功能：**
- 从训练集中随机抽取 8 张图片
- 以 4x2 网格展示
- 显示每张图片所属的类别
- 点击 **Refresh Dataset Stats** 按钮可重新随机抽样

**用途：**
- 快速检查图片加载是否正常
- 验证类别标签是否正确
- 检查图片质量和内容

### 6. 实时刷新

点击 **🔄 Refresh Dataset Stats** 按钮可以：
- 重新扫描数据集目录
- 更新统计数据
- 重新随机抽取预览图片

## 使用步骤

### 1. 启动 Dashboard

```bash
start_trainlens.bat
```

### 2. 配置数据集路径

在侧边栏中填写：
- **Train Directory**: `./dataset/train`
- **Validation Directory**: `./dataset/val`

### 3. 切换到 Dataset Inspector 标签

点击 **🔍 Dataset Inspector** 标签

### 4. 查看统计结果

Dashboard 会自动显示：
- 数据集汇总指标
- 类别分布表格
- 可视化图表
- 随机图片预览

### 5. 检查数据质量

根据统计结果检查：

#### ✅ 正常情况
- 所有类别都有训练和验证样本
- Imbalance Ratio 在 1.0 - 3.0 之间
- 随机图片清晰可见，类别正确

#### ⚠️ 需要注意
- Imbalance Ratio > 5.0：某些类别样本过少
- 某些类别只有训练集没有验证集
- 图片加载失败或显示异常

#### ❌ 错误情况
- Classes = 0：目录结构不正确
- Train Images = 0 或 Val Images = 0：路径错误或目录为空
- Imbalance Ratio = N/A：某些类别样本数为 0

## 常见问题

### Q1: 显示 "Both Train and Validation directories do not exist"

**原因：** 侧边栏中的路径不存在

**解决：**
1. 检查路径是否正确
2. 使用相对路径（相对于 TrainLens 项目根目录）
3. 或使用绝对路径

### Q2: Classes = 0，显示 "No valid ImageFolder structure detected"

**原因：** 目录结构不符合 ImageFolder 格式

**解决：**
确保目录结构为：
```
train/
  class_name/
    *.jpg
```
而不是：
```
train/
  *.jpg  # 错误：图片直接放在 train 下
```

### Q3: 某些类别在表格中没有显示

**原因：** 该类别目录下没有支持的图片格式

**解决：**
1. 检查图片文件扩展名（支持 jpg, jpeg, png, bmp, gif）
2. 确保文件不是隐藏文件
3. 确保文件权限正常

### Q4: 随机图片预览显示 "Failed to load image"

**原因：** 图片文件损坏或格式不支持

**解决：**
1. 手动打开该图片检查是否损坏
2. 使用图片工具（如 Pillow）批量验证数据集
3. 删除或修复损坏的图片

### Q5: Imbalance Ratio 很高怎么办？

**建议：**
1. **数据增强**：对少数类别进行数据增强
2. **重采样**：训练时使用 WeightedRandomSampler
3. **损失函数**：使用 Focal Loss 或加权交叉熵
4. **收集数据**：补充少数类别的样本

## 最佳实践

### 1. 训练前检查

在每次训练前使用 Dataset Inspector 检查：
- 数据集路径是否正确
- 类别数量是否符合预期
- 样本分布是否合理

### 2. 数据集版本管理

切换数据集版本后：
1. 修改侧边栏路径
2. 切换到 Dataset Inspector
3. 点击 Refresh 按钮
4. 验证新数据集统计

### 3. 不平衡数据集处理

如果 Imbalance Ratio > 5.0：
1. 记录各类别样本数
2. 在训练脚本中配置类别权重
3. 或使用过采样/欠采样策略

### 4. 快速验证标注

通过随机图片预览：
- 检查类别标签是否与图片内容匹配
- 发现标注错误及时修正
- 验证数据集质量

## 技术细节

### 扫描逻辑

```python
def scan_imagefolder_dataset(dataset_dir):
    """
    扫描 ImageFolder 格式目录
    返回: {class_name: [image_paths]}
    """
    # 遍历一级子目录（类别目录）
    for class_dir in dataset_dir.iterdir():
        if class_dir.is_dir():
            # 扫描支持的图片格式
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
                image_files.extend(class_dir.glob(ext))
```

### 统计计算

```python
total_train = sum(所有训练集类别的样本数)
total_val = sum(所有验证集类别的样本数)
num_classes = len(训练集和验证集的并集类别)
imbalance_ratio = max(类别样本数) / min(类别样本数)
```

### 图片采样

```python
# 从所有训练图片中随机抽取 8 张
sample_images = random.sample(all_train_images, 8)
```

## 与训练流程集成

Dataset Inspector 不影响训练流程：
- 仅用于数据集检查和可视化
- 不修改任何数据文件
- 不影响训练脚本的运行
- 可以在训练前、训练中、训练后随时使用

## 未来扩展

计划中的功能：
- [ ] 支持更多数据集格式（COCO, YOLO, CSV）
- [ ] 图片尺寸分布统计
- [ ] 图片亮度/对比度分布
- [ ] 数据集质量评分
- [ ] 导出数据集报告（PDF/HTML）

## 总结

Dataset Inspector 是训练前的必备工具：
- ✅ 快速检查数据集路径和结构
- ✅ 可视化类别分布和不平衡情况
- ✅ 预览图片验证标注质量
- ✅ 为训练超参数调整提供依据
