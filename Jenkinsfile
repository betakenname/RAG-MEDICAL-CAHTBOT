pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo'
        IMAGE_TAG = "${BUILD_NUMBER}"
        LATEST_TAG = 'latest'
        JENKINS_CACHE = '/tmp/jenkins-cache'
        // 设置Docker构建超时时间
        DOCKER_BUILD_TIMEOUT = '60m'
    }

    stages {
        stage('📋 环境准备') {
            steps {
                script {
                    echo "准备构建环境..."
                    sh "mkdir -p ${env.JENKINS_CACHE}"
                    
                    def modelCached = sh(script: "test -d ${env.JENKINS_CACHE}/Qwen3-Embedding-0.6B", returnStatus: true) == 0
                    def ragDataCached = sh(script: "test -f ${env.JENKINS_CACHE}/rag_data.zip", returnStatus: true) == 0
                    
                    env.MODEL_CACHED = modelCached.toString()
                    env.RAG_CACHED = ragDataCached.toString()
                    
                    echo "模型缓存状态: ${env.MODEL_CACHED}"
                    echo "RAG数据缓存状态: ${env.RAG_CACHED}"
                }
            }
        }

        stage('🤖 下载嵌入模型 (仅在缓存不存在时)') {
            when {
                environment name: 'MODEL_CACHED', value: 'false'
            }
            steps {
                script {
                    echo "从 ModelScope 下载嵌入模型到缓存..."
                    sh """
                        cd ${env.JENKINS_CACHE}
                        rm -rf Qwen3-Embedding-0.6B
                        # 使用重试机制
                        for i in 1 2 3; do
                            git clone --depth=1 https://www.modelscope.cn/Qwen/Qwen3-Embedding-0.6B.git && break
                            echo "重试 \$i/3..."
                            sleep 10
                        done
                    """
                }
            }
        }

        stage('📦 下载RAG数据 (仅在缓存不存在时)') {
            when {
                environment name: 'RAG_CACHED', value: 'false'
            }
            steps {
                script {
                    echo "从 AWS S3 下载向量数据库到缓存..."
                    sh """
                        cd ${env.JENKINS_CACHE}
                        # 使用重试机制
                        for i in 1 2 3; do
                            curl -o rag_data.zip https://rag-medical-data-lzr-2025.s3.ap-southeast-2.amazonaws.com/rag_data.zip && break
                            echo "重试 \$i/3..."
                            sleep 10
                        done
                    """
                }
            }
        }

        stage('🔄 准备构建资源') {
            steps {
                script {
                    echo "从缓存复制构建资源到工作区..."
                    sh """
                        cp -r ${env.JENKINS_CACHE}/Qwen3-Embedding-0.6B .
                        cp ${env.JENKINS_CACHE}/rag_data.zip .
                        echo "解压数据并整理目录..."
                        rm -rf vectorstore
                        unzip -o rag_data.zip -d .
                        mkdir -p vectorstore && mv db_faiss vectorstore/
                        rm rag_data.zip
                        echo "构建资源准备完成"
                    """
                }
            }
        }

        stage('🏗️ 构建Docker镜像（优化版）') {
            steps {
                script {
                    // 创建.env文件
                    withCredentials([string(credentialsId: 'dotenv-file', variable: 'DOTENV_CONTENT')]) {
                        echo "从Jenkins凭据创建 .env 文件..."
                        sh 'echo "${DOTENV_CONTENT}" > .env'
                    }

                    // 创建优化的requirements文件（不带哈希）
                    sh '''
                        cat > requirements.core.txt << 'EOF'
Flask==3.1.2
flask-cors==6.0.1
torch==2.8.0
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
                    '''

                    // 创建优化的Dockerfile
                    sh '''
                        cat > Dockerfile.build << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \\
    apt-get install -y --no-install-recommends curl git && \\
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制requirements
COPY requirements.core.txt .

# 升级pip
RUN pip install --upgrade pip setuptools wheel

# 分批安装依赖，使用国内镜像源
RUN pip install --no-cache-dir \\
    Flask==3.1.2 \\
    flask-cors==6.0.1 \\
    numpy==2.2.6 \\
    python-dotenv==1.1.1 \\
    requests==2.32.5 \\
    -i https://pypi.tuna.tsinghua.edu.cn/simple \\
    --trusted-host pypi.tuna.tsinghua.edu.cn

# 安装PyTorch（使用CPU版本，体积更小）
RUN pip install --no-cache-dir \\
    torch==2.8.0+cpu \\
    -f https://download.pytorch.org/whl/torch_stable.html \\
    --default-timeout=1000 || \\
    pip install --no-cache-dir torch==2.8.0 \\
    -i https://pypi.tuna.tsinghua.edu.cn/simple \\
    --trusted-host pypi.tuna.tsinghua.edu.cn \\
    --default-timeout=1000

# 安装其他ML包
RUN pip install --no-cache-dir \\
    transformers==4.55.4 \\
    sentence-transformers==5.1.0 \\
    faiss-cpu==1.12.0 \\
    -i https://pypi.tuna.tsinghua.edu.cn/simple \\
    --trusted-host pypi.tuna.tsinghua.edu.cn \\
    --default-timeout=1000

# 安装langchain包
RUN pip install --no-cache-dir \\
    langchain==0.3.27 \\
    langchain-community==0.3.27 \\
    langchain-huggingface==0.3.1 \\
    langchain-openai==0.3.31 \\
    -i https://pypi.tuna.tsinghua.edu.cn/simple \\
    --trusted-host pypi.tuna.tsinghua.edu.cn \\
    --default-timeout=1000

# 复制应用文件
COPY . .

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
EOF
                    '''

                    // 使用AWS凭证进行登录和推送
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                        def latestFullName = "${ecrUrl}/${env.ECR_REPO}:${env.LATEST_TAG}"

                        echo "登录到 Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"

                        echo "构建Docker镜像（使用优化的Dockerfile）..."
                        sh """
                            # 设置超时时间构建
                            timeout ${env.DOCKER_BUILD_TIMEOUT} docker build \\
                                --network=host \\
                                -f Dockerfile.build \\
                                -t ${imageFullName} \\
                                .
                        """
                        
                        echo "为镜像打上 latest 标签..."
                        sh "docker tag ${imageFullName} ${latestFullName}"
                        
                        echo "推送 Docker 镜像到 ECR..."
                        sh "docker push ${imageFullName}"
                        sh "docker push ${latestFullName}"
                    }
                }
            }
        }
        
        stage('🧪 基本测试') {
            steps {
                script {
                    def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                    def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                    def imageToTest = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                    
                    echo "对镜像 ${imageToTest} 运行基本健康检查..."
                    sh '''
                        TEST_PORT=$(shuf -i 8080-8999 -n 1)
                        echo "使用测试端口: $TEST_PORT"
                        
                        CONTAINER_ID=$(docker run --rm -d --name test-medical-${BUILD_NUMBER} -p $TEST_PORT:5000 ''' + imageToTest + ''')
                        
                        echo "等待120秒让应用完全启动..."
                        sleep 120 
                        
                        for i in {1..5}; do
                            if curl -f -s -o /dev/null http://localhost:$TEST_PORT/health; then
                                echo "✅ 健康检查通过！"
                                docker stop $CONTAINER_ID || true
                                exit 0
                            fi
                            echo "等待服务启动... (尝试 $i/5)"
                            sleep 15
                        done
                        
                        echo "❌ 健康检查失败"
                        docker logs $CONTAINER_ID
                        docker stop $CONTAINER_ID
                        exit 1
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                echo "清理工作区..."
                sh "rm -rf Qwen3-Embedding-0.6B vectorstore rag_data.zip .env Dockerfile.build requirements.core.txt trivy-report.json || true"
            }
        }
        success {
            echo '🎉 Pipeline执行成功！应用已构建并推送到ECR'
        }
        failure {
            echo '❌ Pipeline执行失败，请检查日志'
        }
    }
}