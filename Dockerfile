## Parent image
FROM python:3.11-slim

## Essential environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

## Work directory inside the docker container
WORKDIR /app

## Installing system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

## Copying all contents from local to container
COPY . .

## Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

## Expose only flask port
EXPOSE 5000

## Run the Flask app
## Run the Flask app using module path
CMD ["python", "-m", "app.application"]


