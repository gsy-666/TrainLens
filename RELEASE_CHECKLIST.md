# TrainLens 发布检查清单

## 发布前检查

### 1. 代码检查

- [ ] 所有路径使用相对路径或 `%~dp0`，无硬编码绝对路径
- [ ] app.py 中无本机路径（如 `C:\Users\gsy_666\...`）
- [ ] 训练脚本示例可独立运行
- [ ] Dataset Inspector 功能正常
- [ ] Start/Stop 按钮工作正常
- [ ] 实验归档功能正常

### 2. 依赖检查

- [ ] requirements.txt 版本锁定正确
- [ ] 包含 pillow（Dataset Inspector 需要）
- [ ] numpy < 2.0.0（避免兼容性问题）
- [ ] 所有依赖可从 PyPI 安装

### 3. 脚本检查

- [ ] setup_trainlens.bat 使用 `%~dp0`
- [ ] start_trainlens.bat 使用 `%~dp0`
- [ ] 检查 Python 可用性
- [ ] 虚拟环境路径为 `.venv`（不是 `venv`）
- [ ] 错误提示友好且有解决方案

### 4. 文档检查

- [ ] README_使用说明.txt 完整
- [ ] 包含第一次安装步骤
- [ ] 包含常见问题解答
- [ ] dataset/README_dataset_format.txt 存在
- [ ] 所有示例路径正确

### 5. 功能测试

#### 训练功能
- [ ] 可启动 mock_train.py
- [ ] 可启动 example_cv_train.py
- [ ] 实时数据更新正常
- [ ] 进度轮盘显示正确
- [ ] 曲线绘制正常
- [ ] Stop 按钮可停止训练
- [ ] 训练完成后自动归档

#### 实验管理
- [ ] 自动创建 exp_001, exp_002...
- [ ] config.json 保存正确
- [ ] metrics.jsonl 复制正确
- [ ] train.log 记录完整
- [ ] summary.json 生成正确
- [ ] Experiment History Tab 显示所有实验

#### Dataset Inspector
- [ ] 自动读取侧边栏路径
- [ ] 统计数据正确
- [ ] 类别分布表格正确
- [ ] 分组柱状图渲染
- [ ] 随机图片预览正常
- [ ] Refresh 按钮工作
- [ ] 错误路径有友好提示

## 清理步骤

### 1. 清理运行记录

```batch
# 保留目录结构，删除实验数据
rmdir /s /q runs\exp_*
del runs\current\metrics.jsonl
del runs\current\train.log
del trainlens_config.json
```

保留：
- runs\current\ (空目录)

### 2. 清理测试数据集（可选）

如果要提供示例数据集，保留 dataset/
如果让用户自己创建，删除：

```batch
rmdir /s /q dataset
```

然后在 README 中说明如何创建。

### 3. 清理虚拟环境

用户需要在自己机器上创建，所以删除：

```batch
rmdir /s /q .venv
rmdir /s /q venv
```

### 4. 清理 Python 缓存

```batch
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc
```

### 5. 保留示例数据集（推荐）

如果保留测试用的 cat/dog 数据集：
- 让用户可以立即测试 Dataset Inspector
- 让用户看到正确的目录结构

保留：
```
dataset/
  train/
    cat/  (10 张图片)
    dog/  (15 张图片)
  val/
    cat/  (3 张图片)
    dog/  (5 张图片)
  README_dataset_format.txt
```

## 打包步骤

### 1. 最终目录结构

```
TrainLens/
├── .venv/                           # 删除（让用户自己创建）
├── dataset/                          # 保留示例
│   ├── train/
│   │   ├── cat/ (10 张图片)
│   │   └── dog/ (15 张图片)
│   ├── val/
│   │   ├── cat/ (3 张图片)
│   │   └── dog/ (5 张图片)
│   └── README_dataset_format.txt
├── docs/
│   ├── TRAIN_SCRIPT_PROTOCOL.md
│   ├── DATASET_INSPECTOR.md
│   └── ...
├── examples/
│   └── example_cv_train.py
├── runs/
│   └── current/                      # 保留空目录
├── scripts/
│   └── mock_train.py
├── trainlens_app/
│   ├── app.py
│   └── requirements.txt
├── setup_trainlens.bat               # 安装脚本
├── start_trainlens.bat               # 启动脚本
├── README.md                         # 英文文档
├── README_使用说明.txt                # 中文说明
└── RELEASE_CHECKLIST.md              # 本文件（发布后可删除）
```

### 2. 创建 ZIP 包

#### 方法 1：Windows 资源管理器

1. 进入 TrainLens 父目录
2. 右键点击 TrainLens 文件夹
3. 发送到 → 压缩(zipped)文件夹
4. 重命名为 `TrainLens_V1.4.zip`

#### 方法 2：命令行

```batch
cd C:\Users\gsy_666\Desktop
powershell Compress-Archive -Path TrainLens -DestinationPath TrainLens_V1.4.zip
```

### 3. 文件大小预估

- 代码和文档：< 1 MB
- 示例数据集（cat/dog 图片）：< 500 KB
- 总大小：约 1-2 MB（不含虚拟环境）

## 在另一台电脑测试

### 测试环境要求

- 全新的 Windows 10/11
- 未安装 Python（或已安装 Python 3.10/3.11）
- 无 Anaconda/Miniconda
- 无现有虚拟环境

### 测试步骤

1. **解压文件**
   ```
   解压 TrainLens_V1.4.zip 到 D:\TrainLens
   ```

2. **首次安装**
   ```
   双击 setup_trainlens.bat
   等待安装完成（2-5 分钟）
   ```

3. **启动 Dashboard**
   ```
   双击 start_trainlens.bat
   浏览器自动打开 http://localhost:8501
   ```

4. **测试基础功能**
   - 侧边栏配置：
     - Script: scripts/mock_train.py
     - Train: ./dataset/train
     - Val: ./dataset/val
     - Epochs: 5
   - 点击 Start Training
   - 观察进度轮盘和曲线更新
   - 点击 Stop Training

5. **测试 Dataset Inspector**
   - 切换到 Dataset Inspector Tab
   - 验证显示：
     - Train Images: 25
     - Val Images: 8
     - Classes: 2
     - 类别分布图表
     - 随机图片预览
   - 点击 Refresh 按钮

6. **测试 Example 脚本**
   - 侧边栏修改 Script: examples/example_cv_train.py
   - 点击 Start Training
   - 验证可以正常运行（fake mode 或真实训练）

7. **测试实验管理**
   - 运行完整训练（5-10 epochs）
   - 切换到 Experiment History Tab
   - 验证 exp_001 显示
   - 查看 Config 和 Training Log

### 测试通过标准

- [ ] setup_trainlens.bat 成功安装
- [ ] start_trainlens.bat 成功启动
- [ ] Dashboard 在浏览器打开
- [ ] mock_train.py 可以运行
- [ ] example_cv_train.py 可以运行
- [ ] 实时曲线正常更新
- [ ] Stop 按钮可以停止训练
- [ ] 实验自动归档到 exp_001
- [ ] Dataset Inspector 正常显示
- [ ] 所有功能无报错

### 常见安装问题

#### 问题 1：Python 未安装

**症状：** setup_trainlens.bat 提示 "未找到 Python"

**解决：**
1. 下载 Python 3.10 或 3.11
2. 安装时勾选 "Add Python to PATH"
3. 重启测试机
4. 重新运行 setup_trainlens.bat

#### 问题 2：网络问题导致依赖安装失败

**解决：** 使用国内镜像
```batch
.venv\Scripts\activate.bat
pip install -r trainlens_app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 问题 3：防火墙拦截

**解决：**
1. 允许 Python 通过防火墙
2. 或临时关闭防火墙测试

## 发布渠道

### 1. GitHub Release

创建 Release：
- Tag: v1.4
- Title: TrainLens V1.4 - 可分发版本
- Description: 主要更新内容
- Attach: TrainLens_V1.4.zip

### 2. 网盘分享

- 百度网盘
- 阿里云盘
- OneDrive
- Google Drive

分享时附上：
- README_使用说明.txt 中的内容
- 第一次使用步骤
- 常见问题解答

### 3. 文档网站（可选）

如果需要在线文档：
- GitHub Pages
- Read the Docs
- 飞书文档

## 版本号管理

当前版本：V1.4

版本命名规则：
- V1.x: 主要功能版本
- V1.x.y: Bug 修复版本

下一版本计划：
- V1.5: （未定）
- V2.0: 重大架构更新

## 更新日志（写在 CHANGELOG.md 或 Release Notes）

### V1.4 - 可分发版本

**新增：**
- setup_trainlens.bat: 一键安装脚本
- start_trainlens.bat: 一键启动脚本
- README_使用说明.txt: 中文使用文档
- RELEASE_CHECKLIST.md: 发布检查清单
- dataset/README_dataset_format.txt: 数据集格式说明
- 示例数据集（cat/dog）

**改进：**
- 所有路径使用相对路径
- requirements.txt 添加 pillow
- 更友好的错误提示
- 更完善的文档

**修复：**
- 虚拟环境路径统一为 .venv
- Windows 路径兼容性
- 依赖版本锁定

## 发布后检查

- [ ] 在至少 2 台不同电脑测试成功
- [ ] 文档链接无失效
- [ ] 示例脚本可运行
- [ ] 用户反馈的问题已记录
- [ ] 已创建 GitHub Release（如果适用）

## 技术支持准备

提前准备常见问题答案：
1. Python 版本不对怎么办？
2. 虚拟环境创建失败？
3. 依赖安装失败？
4. 端口被占用？
5. 训练脚本报错？
6. 曲线不更新？
7. GPU 不可用？
8. 如何接入自己的脚本？

所有答案已在 README_使用说明.txt 中。

## 总结

发布 TrainLens V1.4 前：
1. 运行本清单所有检查项
2. 清理不必要的文件
3. 保留示例数据集
4. 打包 ZIP
5. 在新电脑测试
6. 发布并提供文档链接

TrainLens V1.4 是一个完全可分发的版本，用户只需：
1. 解压
2. 双击 setup_trainlens.bat
3. 双击 start_trainlens.bat
