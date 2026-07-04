# TrainLens V1.3 - Dataset Inspector 测试指南

## 测试环境

已创建测试数据集：
```
dataset/
  train/
    cat/  (10 张图片)
    dog/  (15 张图片)
  val/
    cat/  (3 张图片)
    dog/  (5 张图片)
```

## 快速测试步骤

### 1. 启动 Dashboard

```bash
start_trainlens.bat
```

等待浏览器自动打开 `http://localhost:8501`

### 2. 配置数据集路径

在侧边栏中设置：
- **Train Directory**: `./dataset/train`
- **Validation Directory**: `./dataset/val`

### 3. 打开 Dataset Inspector

点击第三个 Tab: **🔍 Dataset Inspector**

### 4. 验证统计数据

应该看到以下内容：

**汇总卡片（4 个）：**
- Train Images: **25** (10 + 15)
- Val Images: **8** (3 + 5)
- Classes: **2** (cat, dog)
- Imbalance Ratio: **1.50** (15/10)

**类别分布表格：**
| Class | Train | Val | Total |
|-------|-------|-----|-------|
| cat   | 10    | 3   | 13    |
| dog   | 15    | 5   | 20    |

**分组柱状图：**
- X 轴显示 cat 和 dog
- 蓝色柱（Train）: cat=10, dog=15
- 红色柱（Val）: cat=3, dog=5

**随机图片预览：**
- 显示 8 张训练图片
- 4x2 网格布局
- 每张图片标注 cat 或 dog

### 5. 测试 Refresh 功能

点击 **🔄 Refresh Dataset Stats** 按钮

**预期结果：**
- 统计数据重新计算（数值相同）
- 随机图片重新抽样（图片可能不同）

## 功能验收清单

### ✅ 基础功能

- [ ] Dashboard 成功启动
- [ ] Dataset Inspector Tab 正常显示
- [ ] 自动读取侧边栏路径
- [ ] 显示当前配置的路径

### ✅ 统计数据

- [ ] Train Images = 25
- [ ] Val Images = 8
- [ ] Classes = 2
- [ ] Imbalance Ratio = 1.50

### ✅ 类别分布

- [ ] 表格显示 cat 和 dog 两行
- [ ] cat: Train=10, Val=3, Total=13
- [ ] dog: Train=15, Val=5, Total=20
- [ ] 表格格式清晰，无索引列

### ✅ 可视化图表

- [ ] 分组柱状图正确渲染
- [ ] 蓝色柱（Train）高度正确
- [ ] 红色柱（Val）高度正确
- [ ] 悬停显示具体数值
- [ ] 图表可交互（缩放、平移）

### ✅ 图片预览

- [ ] 显示 8 张图片
- [ ] 4x2 网格布局
- [ ] 每张图片有类别标签（cat 或 dog）
- [ ] 图片清晰可见
- [ ] 颜色正确（cat: 橙色调, dog: 蓝色调）

### ✅ 刷新功能

- [ ] 点击 Refresh 按钮后页面更新
- [ ] 统计数据保持正确
- [ ] 随机图片重新抽样

### ✅ 错误处理

- [ ] 修改路径为不存在的目录，显示警告
- [ ] 删除所有类别目录，显示 "No valid ImageFolder structure" 提示
- [ ] 处理空数据集时不崩溃

## 高级测试场景

### 场景 1: 空数据集

```bash
# 临时移走图片
mv dataset dataset_backup
mkdir -p dataset/train dataset/val
```

在侧边栏保持路径不变，点击 Refresh

**预期结果：**
- 显示警告: "⚠️ No valid ImageFolder structure detected"
- 不崩溃，不显示错误 traceback

```bash
# 恢复
rm -rf dataset
mv dataset_backup dataset
```

### 场景 2: 只有训练集

```bash
# 临时移走验证集
mv dataset/val dataset/val_backup
```

**预期结果：**
- Train Images = 25
- Val Images = 0
- Classes = 2
- Val 列全部为 0

```bash
# 恢复
mv dataset/val_backup dataset/val
```

### 场景 3: 严重不平衡数据集

添加第三个类别，样本极少：

```bash
mkdir -p dataset/train/bird dataset/val/bird
# 创建 1 张 bird 图片（使用 Python）
```

**预期结果：**
- Classes = 3
- Imbalance Ratio = 15.00 (15/1)
- 表格显示 bird 行
- 图表显示 bird 柱（很矮）

### 场景 4: 不同路径格式

测试以下路径格式都能正常工作：
- 相对路径: `./dataset/train`
- 绝对路径: `C:/Users/gsy_666/Desktop/TrainLens/dataset/train`
- 反斜杠: `dataset\train` (Windows)

## 与训练流程集成测试

### 1. 检查数据集 → 训练

1. 打开 Dataset Inspector，确认数据集正常
2. 切换到 Current Training Tab
3. 配置训练参数，点击 Start Training
4. 训练过程中切换回 Dataset Inspector
5. 验证数据集统计依然正确显示

**预期结果：** Dataset Inspector 不受训练进程影响

### 2. 训练中修改数据集路径

1. 开始训练
2. 在侧边栏修改 Train Directory
3. 切换到 Dataset Inspector
4. 点击 Refresh

**预期结果：** Dataset Inspector 显示新路径的统计

## 性能测试

### 大数据集测试

创建大数据集（可选）：

```python
# 创建 10 个类别，每类 1000 张图片
for i in range(10):
    for j in range(1000):
        create_test_image(f'dataset/train/class{i}/img_{j}.jpg', ...)
```

**预期结果：**
- 扫描时间 < 5 秒
- Dashboard 不卡顿
- 图表正常渲染
- 随机抽样正常

## 文档验证

### 检查文档完整性

- [ ] `docs/DATASET_INSPECTOR.md` 存在
- [ ] 包含完整的使用说明
- [ ] 包含 ImageFolder 格式说明
- [ ] 包含故障排除章节

### 检查 README 更新

- [ ] 标题更新为 V1.3
- [ ] Features 章节包含 V1.3 - Dataset Inspector
- [ ] Dashboard Layout 提到 Dataset Inspector Tab
- [ ] Example Usage 包含 Dataset Inspector 使用步骤
- [ ] Troubleshooting 包含 Dataset Inspector 问题

### 检查版本文档

- [ ] `V1.3_FEATURES.md` 存在
- [ ] 包含所有新增功能说明
- [ ] 包含测试清单
- [ ] 包含验收标准

## 常见问题排查

### 问题 1: PIL 未安装

**症状：** `ImportError: No module named 'PIL'`

**解决：**
```bash
source venv/Scripts/activate
pip install Pillow
```

### 问题 2: 图片不显示

**症状：** 显示 "Failed to load image"

**检查：**
1. 图片文件是否存在
2. 图片格式是否支持
3. 文件权限是否正常

### 问题 3: Imbalance Ratio 显示 inf

**症状：** Imbalance Ratio = inf

**原因：** 某个类别样本数为 0

**解决：** 检查数据集，确保每个类别至少有 1 张图片

## 总结

完成以上所有测试后，TrainLens V1.3 Dataset Inspector 功能验收通过。

用户可以：
✅ 在训练前快速检查数据集质量  
✅ 识别类别不平衡问题  
✅ 验证数据集结构正确  
✅ 预览图片确认标注  
✅ 实时刷新数据集统计  
