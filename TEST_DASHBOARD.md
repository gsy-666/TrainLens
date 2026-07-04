# TrainLens Dashboard 测试指南

## ✅ 已完成的工作

1. **创建了 Streamlit Dashboard** (`trainlens_app/app.py`)
   - 实时监控训练进度、Loss、Accuracy
   - 交互式 Plotly 图表
   - 进程管理（启动/停止训练）
   - 配置持久化
   - 训练历史数据表

2. **创建了启动脚本** (`start_trainlens.bat`)
   - 一键启动
   - 自动检测并安装依赖

3. **更新了文档** (`README.md`)
   - 完整的使用说明
   - 集成指南
   - 故障排查

## 🧪 如何测试

### 方法 1：使用批处理文件（推荐）

1. 双击 `start_trainlens.bat`
2. 等待浏览器自动打开 `http://localhost:8501`
3. 在侧边栏配置训练参数
4. 点击 **Start Training** 按钮
5. 观察实时更新的指标和图表

### 方法 2：手动启动

```bash
# 安装依赖（首次运行）
pip install -r trainlens_app/requirements.txt

# 启动 Dashboard
streamlit run trainlens_app/app.py
```

## 📋 测试清单

- [ ] Dashboard 成功启动并在浏览器中打开
- [ ] 侧边栏显示训练配置表单
- [ ] 点击 "Start Training" 启动 mock_train.py
- [ ] 实时显示进度百分比
- [ ] 实时显示当前 Epoch
- [ ] 实时显示 Train/Val Accuracy
- [ ] 实时显示 Train Loss
- [ ] Loss 曲线实时更新
- [ ] Accuracy 曲线实时更新
- [ ] 训练历史数据表正确显示
- [ ] 点击 "Stop Training" 成功停止训练
- [ ] 配置保存到 trainlens_config.json
- [ ] 下次启动自动加载上次配置

## ⚠️ 已知问题

### NumPy 版本冲突

如果遇到 "NumPy 1.x cannot be run in NumPy 2.x" 错误：

```bash
pip install "numpy<2.0.0" --force-reinstall
```

已在 `requirements.txt` 中添加 `numpy<2.0.0` 约束。

### 权限错误

如果 pip 安装失败（WinError 5 访问拒绝），以管理员身份运行：

```bash
# 右键点击 "命令提示符" -> "以管理员身份运行"
pip install -r trainlens_app/requirements.txt
```

## 🎯 默认配置

```json
{
  "script_path": "scripts/mock_train.py",
  "train_dir": "./dataset/train",
  "val_dir": "./dataset/val",
  "epochs": 20,
  "lr": 0.001,
  "batch_size": 16,
  "device": "auto"
}
```

## 📊 验证 metrics.jsonl

训练运行时，应该看到 `metrics.jsonl` 文件被创建，内容类似：

```json
{"epoch":1,"train_loss":0.812,"train_acc":0.761,"val_loss":0.744,"val_acc":0.781,"progress":5.0,"timestamp":"2026-07-05T10:30:00"}
{"epoch":2,"train_loss":0.698,"train_acc":0.823,"val_loss":0.665,"val_acc":0.842,"progress":10.0,"timestamp":"2026-07-05T10:30:01"}
```

## 🚀 下一步

测试通过后，可以：

1. 使用真实训练脚本替换 `mock_train.py`
2. 调整 Dashboard UI 样式
3. 添加更多监控指标
4. 创建简化版 VS Code 插件作为启动器

## 💡 测试反馈

请测试后反馈：
- Dashboard 是否成功启动？
- 训练是否能正常开始？
- 图表是否实时更新？
- 有任何错误消息吗？
