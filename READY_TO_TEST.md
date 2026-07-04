# ✅ TrainLens Dashboard 已就绪

## 安装完成状态

**虚拟环境**: ✅ 已创建并配置  
**依赖安装**: ✅ 全部成功  
- NumPy: 1.26.4  
- Pandas: 3.0.3  
- Streamlit: 1.58.0  
- Plotly: 6.8.0  
- psutil: 7.2.2  

**NumPy 兼容性问题**: ✅ 已通过虚拟环境解决

---

## 🚀 启动 Dashboard

### 方法 1: 使用启动脚本（推荐）

双击 `start_trainlens.bat` 即可启动。脚本会自动：
1. 检测 Python 环境
2. 激活虚拟环境（首次运行会自动创建）
3. 安装/更新依赖
4. 启动 Streamlit Dashboard
5. 在浏览器中打开 http://localhost:8501

### 方法 2: 手动启动

```bash
# 激活虚拟环境
venv\Scripts\activate

# 启动 Dashboard
streamlit run trainlens_app\app.py
```

---

## 📋 使用步骤

1. **启动 Dashboard**
   - 双击 `start_trainlens.bat`
   - 等待浏览器自动打开

2. **配置训练参数**（侧边栏）
   - Script Path: `scripts/mock_train.py`（默认）
   - Train Directory: `./dataset/train`
   - Validation Directory: `./dataset/val`
   - Epochs: `20`
   - Learning Rate: `0.001`
   - Batch Size: `16`
   - Device: `auto`

3. **启动训练**
   - 点击 **▶️ Start Training** 按钮
   - 观察状态从 "Training Idle" 变为 "Training Running"
   - 显示进程 PID

4. **监控训练**
   - 实时更新的指标卡片：Progress, Epoch, Train Acc, Val Acc, Train Loss
   - 实时更新的 Plotly 图表（Loss 曲线 + Accuracy 曲线）
   - 训练历史数据表

5. **停止训练**（可选）
   - 点击 **🛑 Stop Training** 按钮
   - 进程被安全终止

---

## 🎯 功能验证清单

请测试以下功能：

- [ ] Dashboard 成功启动（http://localhost:8501）
- [ ] 侧边栏显示所有配置选项
- [ ] 点击 Start Training 成功启动 mock_train.py
- [ ] 状态显示为 "Training Running" 并显示 PID
- [ ] Progress 百分比实时更新（0% -> 100%）
- [ ] Epoch 显示实时更新（1/20 -> 20/20）
- [ ] Train Accuracy 实时更新
- [ ] Val Accuracy 实时更新
- [ ] Train Loss 实时更新
- [ ] Loss 曲线图实时绘制（红色 Train Loss + 青色 Val Loss）
- [ ] Accuracy 曲线图实时绘制（红色 Train Acc + 青色 Val Acc）
- [ ] 训练历史数据表显示所有 epoch 数据
- [ ] 点击 Stop Training 成功停止进程
- [ ] 关闭浏览器再打开，配置被保存（trainlens_config.json）
- [ ] metrics.jsonl 文件被正确创建和写入

---

## 📊 预期结果

### metrics.jsonl 格式
训练运行时，`metrics.jsonl` 应包含如下格式的数据：

```json
{"epoch":1,"train_loss":0.812,"train_acc":0.761,"val_loss":0.744,"val_acc":0.781,"progress":5.0,"timestamp":"2026-07-05T..."}
{"epoch":2,"train_loss":0.698,"train_acc":0.823,"val_loss":0.665,"val_acc":0.842,"progress":10.0,"timestamp":"2026-07-05T..."}
```

### Dashboard 效果
- **5 个指标卡片** 横排显示：Progress / Epoch / Train Acc / Val Acc / Train Loss
- **2 个图表** 并排显示：Loss 曲线（左）+ Accuracy 曲线（右）
- **1 个数据表** 显示完整训练历史
- **每秒自动刷新** 当训练运行时

---

## 🔧 故障排查

### Dashboard 无法启动
1. 确认 Python 已安装：`python --version`
2. 删除 `venv` 文件夹，重新运行 bat 文件
3. 手动创建虚拟环境并安装依赖

### 训练无法启动
1. 检查 `scripts/mock_train.py` 文件存在
2. 检查终端是否有 Python 错误信息
3. 手动测试训练脚本

### 图表不更新
1. 检查 `metrics.jsonl` 文件是否被创建
2. 查看文件内容是否有数据写入
3. 刷新浏览器页面（F5）

---

## 🎉 测试成功标准

如果以下全部达成，说明 TrainLens Dashboard 工作正常：

1. ✅ Dashboard 在浏览器中打开
2. ✅ 点击 Start Training 后进程启动
3. ✅ 指标和图表每秒自动刷新
4. ✅ 训练完成后显示 20/20 epochs
5. ✅ metrics.jsonl 包含 20 行数据
6. ✅ 关闭重开后配置被保存

---

## 📞 反馈

测试完成后，请反馈：
1. Dashboard 是否成功启动？
2. 训练是否正常运行？
3. 图表是否实时更新？
4. 有任何错误或异常吗？
