# -----------------------------------------------------------------------------
# 阶段 1: 基础环境和系统依赖
# -----------------------------------------------------------------------------
## 使用官方的 Python 3.11 slim 版本作为基础镜像
FROM python:3.11-slim

## 设置环境变量，防止生成 .pyc 文件并确保日志能直接输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

## 在容器内创建并切换到 /app 工作目录
WORKDIR /app

## 安装编译 Python 包（如 mysqlclient）所需的系统依赖
## 这一层很少变动，所以会被 Docker 牢牢缓存
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# 阶段 2: 安装 Python 依赖
# -----------------------------------------------------------------------------
## 【关键优化】先只复制依赖描述文件
## 只要 requirements.txt 文件没有变化，下面安装依赖的步骤就会使用缓存，
## 从而跳过耗时最长的下载和安装过程。
COPY requirements.txt .

## 安装所有 Python 依赖
# RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 300
# -----------------------------------------------------------------------------
    RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --timeout 1000
# 阶段 3: 复制应用代码并运行
# -----------------------------------------------------------------------------
## 【关键优化】最后再复制您经常变动的项目代码
## 这样，即使您只修改了一个代码文件，也只需要重新构建这一层，
## 而不是重新安装所有依赖。
COPY . .

## 暴露 Flask 应用运行的端口
EXPOSE 5000

## 容器启动时运行的命令
CMD ["python", "-m", "app.application"]