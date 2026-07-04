═══════════════════════════════════════════════
TrainLens V1.4 - 使用说明
═══════════════════════════════════════════════

TrainLens 是一个实时训练监控工具，支持可视化训练曲线、实验管理和数据集检查。

═══════════════════════════════════════════════
一、第一次安装
═══════════════════════════════════════════════

1. 确保已安装 Python

   - 需要 Python 3.10 或 3.11
   - 下载地址：https://www.python.org/downloads/
   - 安装时务必勾选 "Add Python to PATH"

   验证 Python 是否安装成功：
   - 打开 cmd，输入：python --version
   - 应显示：Python 3.10.x 或 Python 3.11.x

2. 运行安装脚本

   双击 setup_trainlens.bat

   安装过程：
   - 检查 Python
   - 创建虚拟环境 .venv
   - 安装所有依赖包（numpy, pandas, streamlit, plotly, pillow 等）
   - 创建必要目录

   安装时间：约 2-5 分钟（取决于网速）

3. 安装完成

   看到 "安装完成！" 提示后，按任意键退出

═══════════════════════════════════════════════
二、启动 TrainLens
═══════════════════════════════════════════════

双击 start_trainlens.bat

Dashboard 会自动在浏览器中打开：http://localhost:8501

停止 Dashboard：
- 在命令行窗口按 Ctrl+C
- 或直接关闭命令行窗口

═══════════════════════════════════════════════
三、运行默认示例
═══════════════════════════════════════════════

1. 启动 Dashboard（双击 start_trainlens.bat）

2. 在侧边栏配置：
   - Script Path: scripts/mock_train.py
   - Train Directory: ./dataset/train
   - Validation Directory: ./dataset/val
   - Epochs: 10
   - Learning rate: 0.001
   - Batch size: 16
   - Device: auto

3. 点击 "Start Training" 按钮

4. 观察实时更新：
   - 进度轮盘（0-100%）
   - 准确率和损失曲线
   - 训练历史数据表

5. 训练完成后：
   - 自动保存到 runs/exp_001, exp_002 等
   - 在 "Experiment History" Tab 查看所有实验

═══════════════════════════════════════════════
四、接入自己的训练脚本
═══════════════════════════════════════════════

你的训练脚本需要遵守 TrainLens 协议：

1. 必需的命令行参数（7 个）

   --train       训练数据目录
   --val         验证数据目录
   --epochs      训练轮数
   --lr          学习率
   --batch       批大小
   --device      设备 (auto/cpu/cuda)
   --log         日志文件路径

2. 必需的 JSONL 输出

   每个 epoch 完成后写入一行 JSON：

   import json

   def write_metric(log_path, data):
       with open(log_path, 'a', encoding='utf-8') as f:
           f.write(json.dumps(data) + '\n')
           f.flush()  # 重要！

   # 训练循环
   for epoch in range(1, args.epochs + 1):
       train_loss = train_one_epoch(...)
       val_loss, val_acc = validate(...)

       metrics = {
           'epoch': epoch,
           'total_epoch': args.epochs,
           'progress': round(epoch / args.epochs * 100, 2),  # 0-100
           'train_loss': round(train_loss, 6),
           'val_loss': round(val_loss, 6),
           'acc': round(val_acc, 6),  # 0-1，不是 0-100
           'best_acc': round(best_acc, 6),
           'best_loss': round(best_loss, 6),
       }

       write_metric(args.log, metrics)

3. 完整示例

   参考项目中的：
   - examples/example_cv_train.py（完整 PyTorch 示例）
   - scripts/mock_train.py（轻量级模拟脚本）

4. 接入步骤

   1. 在你的 train.py 中添加上述 7 个参数
   2. 添加 JSONL 写入逻辑
   3. 在 Dashboard 侧边栏设置 Script Path 为你的 train.py
   4. 点击 Start Training

详细协议文档：docs/TRAIN_SCRIPT_PROTOCOL.md

═══════════════════════════════════════════════
五、数据集目录结构
═══════════════════════════════════════════════

TrainLens 支持标准 ImageFolder 格式：

dataset/
  train/
    class1/
      img001.jpg
      img002.jpg
      ...
    class2/
      img001.jpg
      img002.jpg
      ...
  val/
    class1/
      img001.jpg
      ...
    class2/
      img001.jpg
      ...

支持的图片格式：
- .jpg / .jpeg
- .png
- .bmp
- .gif

使用 Dataset Inspector：
1. 在侧边栏配置 Train Directory 和 Validation Directory
2. 点击 "Dataset Inspector" Tab
3. 查看类别分布、不平衡比例、随机图片预览

详细说明：docs/DATASET_INSPECTOR.md

═══════════════════════════════════════════════
六、常见问题
═══════════════════════════════════════════════

问题 1：Python 未安装或未找到

症状：
  setup_trainlens.bat 提示 "未找到 Python"

解决：
  1. 下载 Python 3.10 或 3.11
  2. 安装时勾选 "Add Python to PATH"
  3. 重启电脑
  4. 验证：打开 cmd，输入 python --version

─────────────────────────────────────────────

问题 2：端口 8501 被占用

症状：
  start_trainlens.bat 提示端口被占用

解决方法 1：
  关闭其他 Streamlit 应用或占用 8501 的程序

解决方法 2：
  使用其他端口启动：
  1. 激活虚拟环境：.venv\Scripts\activate.bat
  2. 启动：streamlit run trainlens_app\app.py --server.port 8502
  3. 浏览器访问：http://localhost:8502

─────────────────────────────────────────────

问题 3：依赖安装失败

症状：
  setup_trainlens.bat 安装依赖时报错

解决：
  使用国内镜像重新安装：
  1. 激活虚拟环境：.venv\Scripts\activate.bat
  2. 安装：pip install -r trainlens_app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

─────────────────────────────────────────────

问题 4：CUDA / GPU 不可用

症状：
  训练脚本提示 CUDA not available

说明：
  TrainLens 本身不需要 GPU，但你的训练脚本可能需要

解决：
  1. 如果不需要 GPU：在侧边栏设置 Device 为 "cpu"
  2. 如果需要 GPU：
     - 检查 NVIDIA 驱动是否安装
     - 安装 PyTorch with CUDA：
       pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

─────────────────────────────────────────────

问题 5：训练曲线不刷新

症状：
  点击 Start Training 后，Dashboard 没有显示数据

检查：
  1. 训练脚本是否正在运行（查看命令行窗口）
  2. 训练脚本是否写入 metrics.jsonl
  3. JSONL 格式是否正确
  4. 是否在每次写入后调用 f.flush()

调试：
  1. 检查 runs/current/metrics.jsonl 是否存在
  2. 打开文件查看内容是否符合格式
  3. 查看 runs/current/train.log 是否有错误信息

─────────────────────────────────────────────

问题 6：训练无法停止

症状：
  点击 Stop Training 后进程仍在运行

解决：
  1. 在 Dashboard 上方查看进程 PID
  2. 打开任务管理器
  3. 找到对应 PID 的 python.exe 进程
  4. 结束任务

─────────────────────────────────────────────

问题 7：虚拟环境损坏

症状：
  start_trainlens.bat 激活虚拟环境失败

解决：
  1. 删除 .venv 文件夹
  2. 重新运行 setup_trainlens.bat

═══════════════════════════════════════════════
七、技术支持
═══════════════════════════════════════════════

文档：
  - README.md - 项目总览
  - docs/TRAIN_SCRIPT_PROTOCOL.md - 训练脚本协议
  - docs/DATASET_INSPECTOR.md - 数据集检查工具
  - V1.4_FEATURES.md - V1.4 版本特性

示例脚本：
  - scripts/mock_train.py - 轻量级模拟训练
  - examples/example_cv_train.py - 完整 PyTorch CV 训练

实验管理：
  - 每次训练自动保存到 runs/exp_001, exp_002...
  - 包含 config.json, metrics.jsonl, train.log, summary.json
  - 在 "Experiment History" Tab 查看和对比

═══════════════════════════════════════════════
八、快速参考
═══════════════════════════════════════════════

安装：
  双击 setup_trainlens.bat

启动：
  双击 start_trainlens.bat

手动启动：
  .venv\Scripts\activate.bat
  streamlit run trainlens_app\app.py

清理实验记录：
  删除 runs/exp_* 文件夹

重置配置：
  删除 trainlens_config.json

重装依赖：
  双击 setup_trainlens.bat，选择重装

═══════════════════════════════════════════════

祝使用愉快！
