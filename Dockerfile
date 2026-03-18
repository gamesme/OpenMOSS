FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码（排除数据和配置，通过 volume 挂载）
COPY app/ ./app/
COPY static/ ./static/
COPY skills/ ./skills/
COPY prompts/ ./prompts/
COPY rules/ ./rules/

# 运行时端口
EXPOSE 6565

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6565"]
