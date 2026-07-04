# 快速修复 NumPy 兼容性问题

如果遇到 `ImportError: numpy.core.multiarray failed to import` 错误，请运行：

```bash
pip uninstall numpy -y
pip install "numpy<2.0.0"
```

或者使用提供的修复脚本：

```bash
python -m pip install "numpy<2.0.0" --force-reinstall
```

然后重新启动 Dashboard：

```bash
streamlit run trainlens_app\app.py
```
