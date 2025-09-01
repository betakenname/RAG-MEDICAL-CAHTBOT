#!/bin/bash
# Jenkins构建脚本 - 用于解决依赖安装问题

set -e  # 遇到错误立即停止

echo "=== 开始构建 ==="

# 1. 清理旧的构建缓存
echo "清理Docker构建缓存..."
docker system prune -f

# 2. 创建临时的requirements文件（不带哈希）
echo "创建临时的requirements文件..."
cat > requirements.temp.txt << 'EOF'
Flask==3.1.2
flask-cors==6.0.1
torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
transformers==4.55.4
sentence-transformers==5.1.0
faiss-cpu==1.12.0
langchain==0.3.27
langchain-community==0.3.27
langchain-huggingface==0.3.1
langchain-openai==0.3.31
numpy==2.2.6
python-dotenv==1.1.1
requests==2.32.5
EOF

# 3. 创建优化的Dockerfile
echo "创建优化的Dockerfile..."
cat > Dockerfile.optimized << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制requirements
COPY requirements.temp.txt .

# 分步安装依赖（避免一次性下载太多）
RUN pip install --upgrade pip setuptools wheel

# 先安装基础包
RUN pip install --no-cache-dir \
    Flask==3.1.2 \
    flask-cors==6.0.1 \
    numpy==2.2.6 \
    python-dotenv==1.1.1 \
    requests==2.32.5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装PyTorch CPU版本（体积更小）
RUN pip install --no-cache-dir \
    torch==2.8.0 \
    --index-url https://download.pytorch.org/whl/cpu \
    --default-timeout=1000

# 安装其他ML相关包
RUN pip install --no-cache-dir \
    transformers==4.55.4 \
    sentence-transformers==5.1.0 \
    faiss-cpu==1.12.0 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --default-timeout=1000

# 安装langchain相关包
RUN pip install --no-cache-dir \
    langchain==0.3.27 \
    langchain-community==0.3.27 \
    langchain-huggingface==0.3.1 \
    langchain-openai==0.3.31 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --default-timeout=1000

# 复制应用文件
COPY . .

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
EOF

# 4. 使用新的Dockerfile构建
echo "开始Docker构建..."
docker build -f Dockerfile.optimized -t test-build:latest .

echo "=== 构建完成 ==="