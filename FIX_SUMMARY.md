# TrainLens Dashboard 修复完成

## 已修复的核心问题

### 1. ✅ 路径问题
- **修复前**: app.py 使用当前目录的 `metrics.jsonl`，启动命令不传 `--log` 参数
- **修复后**: 
  - 定义 `PROJECT_ROOT = Path(__file__).resolve().parent.parent`
  - 定义 `LOG_FILE = PROJECT_ROOT / "runs" / "current" / "metrics.jsonl"`
  - 启动时传递 `--log` 参数为 `LOG_FILE` 的绝对路径
  - subprocess.Popen 设置 `cwd=str(PROJECT_ROOT)`

### 2. ✅ 参数名不匹配
- **修复前**: app.py 传 `--train-dir`, `--val-dir`, `--batch-size`
- **修复后**: 改为 `--train`, `--val`, `--batch` 匹配 mock_train.py

### 3. ✅ 字段名不匹配
- **修复前**: app.py 读取 `train_acc`, `val_acc`
- **修复后**: 改为读取 `acc`, `best_acc`, `best_loss` 匹配 mock_train.py 输出

### 4. ✅ 添加进度轮盘
- 使用 Plotly `go.Indicator` 实现仪表盘
- 显示 0-100% 进度
- 标题显示 "Epoch X / Total"

### 5. ✅ 添加实时曲线
- **Loss 曲线**: Train Loss, Val Loss, Best Loss
- **Accuracy 曲线**: Acc, Best Acc
- 使用 `go.Scatter` 实现折线图

### 6. ✅ 添加指标卡片
- Current Acc / Best Acc
- Current Loss / Best Loss
- 使用 `st.metric` 显示

### 7. ✅ 添加调试信息
- 侧边栏显示：
  - PROJECT_ROOT 路径
  - LOG_FILE 路径
  - 日志文件是否存在
  - 日志文件大小
  - 当前训练 PID
  - 读取的 metrics 行数

### 8. ✅ 显示启动命令
- 在 expander 中显示完整的启动命令
- 方便调试和验证

### 9. ✅ 清空旧日志
- 启动前创建 `runs/current/` 目录
- 清空 `metrics.jsonl` 内容

### 10. ✅ 优化刷新频率
- 训练运行时每 0.5 秒刷新一次
- 更快速的实时更新

## 修改的文件

### trainlens_app/app.py
完全重写，主要修改：

1. **路径管理**
2. **启动命令修正** - 匹配 mock_train.py 参数
3. **进度轮盘** - Plotly Indicator 仪表盘
4. **Loss 和 Accuracy 曲线** - 独立图表
5. **读取 metrics 函数** - 容错处理
6. **调试信息面板** - 显示关键路径和状态

## 验收测试步骤

1. **启动 Dashboard**
   - 双击 `start_trainlens.bat`
   - 浏览器打开 http://localhost:8501

2. **检查调试信息**
   - 侧边栏查看 PROJECT_ROOT 和 LOG_FILE 路径

3. **点击 Start Training**
   - 状态变为 "Training Running (PID: xxxxx)"
   - 展开 "Last Training Command" 查看完整命令

4. **观察实时更新**（1-2秒内）
   - ✅ 进度轮盘出现，从 0% 开始增长
   - ✅ Metrics count 显示行数
   - ✅ Current Acc / Best Acc 显示数字
   - ✅ Current Loss / Best Loss 显示数字
   - ✅ Loss 曲线开始绘制
   - ✅ Accuracy 曲线开始绘制
   - ✅ Training History 表格显示数据

5. **等待训练完成**
   - 进度轮盘达到 100%
   - Epoch 显示 20/20

## 预期效果

### Dashboard 布局
- 左侧：配置面板 + 启动按钮 + 调试信息
- 右侧：进度轮盘 + 指标卡片 + Loss/Acc 曲线 + 数据表

### 进度轮盘
- 圆形仪表盘，0-100% 范围
- 蓝色进度条
- 中央显示百分比
- 标题显示 "Epoch X / Total"

### 曲线图
- Loss: Train Loss, Val Loss, Best Loss
- Accuracy: Acc, Best Acc
- 带标记点，鼠标悬停显示数值
