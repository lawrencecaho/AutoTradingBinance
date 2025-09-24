```bash
# 在项目根目录下运行以下命令来启动API服务
# 首次运行前，确保已执行：pip install -e .

# 开发环境启动（带有自动重载）
uvicorn doapi.main:app --host 0.0.0.0 --port 8000 --reload

# 生产环境启动
uvicorn doapi.main:app --host 0.0.0.0 --port 8000 --workers 4

# 注意：确保在项目根目录（包含 setup.py 的目录）下运行命令
```

```bash
# 导出包名
pip freeze | grep -v '^//' | grep -v '^file:' | grep -v '^-e' | grep -v '#' | sort > requirements_temp.txt && mv requirements_temp.txt requirements.txt
```