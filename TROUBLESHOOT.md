# TrainLens 调试故障排查

## 🚨 你看到的问题

截图显示你在看"任务"输出，这不是正确的日志位置。

## ✅ 正确的排查步骤

### 步骤 1：查看 Extension Host 日志（最重要！）

1. 在**主 VS Code 窗口**（开发 TrainLens 的窗口）
2. 按 **Ctrl+Shift+U** 打开"输出"面板
3. 在输出面板**右上角的下拉菜单**中选择 **"Extension Host"**
4. 你应该看到：
   ```
   TrainLens extension activated
   TrainLens command registered: trainlens.openDashboard
   ```

**如果看不到这些日志：**
- Extension 没有激活
- 跳到步骤 5

**如果看到这些日志：**
- Extension 已激活
- 跳到步骤 2

---

### 步骤 2：测试命令是否注册

在 **Extension Development Host 窗口**（调试窗口）：
1. 按 **Ctrl+Shift+P** 打开命令面板
2. 输入 `trainlens`
3. 看是否能找到 `TrainLens: Open Dashboard`

**如果找不到：**
- 命令没注册
- 跳到步骤 5

**如果找到了：**
- 点击执行
- 跳到步骤 3

---

### 步骤 3：测试 Dashboard 是否打开

执行命令后：

**如果提示需要打开文件夹：**
1. 点击"打开文件夹"
2. 选择 `C:\Users\gsy_666\Desktop\TrainLens`
3. 再次执行命令

**如果 Dashboard 打开了：**
- 跳到步骤 4

**如果 Dashboard 没打开：**
- 查看主窗口的 Extension Host 日志，找错误消息

---

### 步骤 4：测试 Start Training 按钮

在 Dashboard 中：
1. 点击 **Start Training** 按钮
2. 立即切换到主窗口查看 Extension Host 输出

**应该看到：**
```
TrainLens received message from webview: start
TrainLens handleWebviewMessage: start
TrainLens: Start training requested
TrainLens: startTraining called with state: {...}
TrainLens: Spawning Python process
```

---

## 📸 请提供截图

1. **主窗口的 Extension Host 输出**（查看 → 输出 → Extension Host）
2. **Extension Development Host 命令面板**（Ctrl+Shift+P 输入 trainlens）
3. **Dashboard Developer Tools Console**（右键 → 检查 → Console）

这样我能精确定位问题！
