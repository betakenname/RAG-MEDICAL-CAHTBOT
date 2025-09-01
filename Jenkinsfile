pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo'
        IMAGE_TAG = "${BUILD_NUMBER}"
        LATEST_TAG = 'latest'
        SERVICE_NAME = 'llmops-medical-service'
        
        // 缓存目录
        JENKINS_CACHE = '/tmp/jenkins-cache'
    }

    stages {
        stage('📋 环境准备') {
            steps {
                script {
                    echo "准备构建环境..."
                    sh "mkdir -p ${env.JENKINS_CACHE}"
                    
                    // 检查缓存状态
                    def modelCached = sh(
                        script: "test -d ${env.JENKINS_CACHE}/Qwen3-Embedding-0.6B",
                        returnStatus: true
                    ) == 0
                    
                    def ragDataCached = sh(
                        script: "test -f ${env.JENKINS_CACHE}/rag_data.zip",
                        returnStatus: true
                    ) == 0
                    
                    env.MODEL_CACHED = modelCached.toString()
                    env.RAG_CACHED = ragDataCached.toString()
                    
                    echo "模型缓存状态: ${env.MODEL_CACHED}"
                    echo "RAG数据缓存状态: ${env.RAG_CACHED}"
                }
            }
        }

        stage('🤖 下载嵌入模型') {
            when {
                environment name: 'MODEL_CACHED', value: 'false'
            }
            steps {
                script {
                    echo "从 ModelScope 下载嵌入模型到缓存..."
                    sh """
                        cd ${env.JENKINS_CACHE}
                        rm -rf Qwen3-Embedding-0.6B
                        git clone https://www.modelscope.cn/Qwen/Qwen3-Embedding-0.6B.git || \\
                        git clone https://gitee.com/qwen/Qwen3-Embedding-0.6B.git
                    """
                }
            }
        }

        stage('📦 下载RAG数据') {
            when {
                environment name: 'RAG_CACHED', value: 'false'
            }
            steps {
                script {
                    echo "从 AWS S3 下载向量数据库到缓存..."
                    sh """
                        cd ${env.JENKINS_CACHE}
                        curl -o rag_data.zip https://rag-medical-data-lzr-2025.s3.ap-southeast-2.amazonaws.com/rag_data.zip
                        echo "RAG数据下载完成"
                    """
                }
            }
        }

        stage('🔄 准备构建资源') {
            steps {
                script {
                    echo "从缓存复制构建资源..."
                    sh """
                        # 复制模型
                        cp -r ${env.JENKINS_CACHE}/Qwen3-Embedding-0.6B .
                        
                        # 复制并解压RAG数据
                        cp ${env.JENKINS_CACHE}/rag_data.zip .
                        echo "解压数据并整理目录..."
                        rm -rf vectorstore
                        unzip -o rag_data.zip -d .
                        mkdir -p vectorstore
                        mv db_faiss vectorstore/
                        rm rag_data.zip
                        
                        echo "构建资源准备完成"
                    """
                }
            }
        }

        stage('🏗️ 构建Docker镜像') {
            steps {
                script {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', 
                        credentialsId: 'aws-token',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        def accountId = sh(
                            script: "aws sts get-caller-identity --query Account --output text", 
                            returnStdout: true
                        ).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                        def latestFullName = "${ecrUrl}/${env.ECR_REPO}:${env.LATEST_TAG}"

                        echo "登录到 Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"

                        // 创建优化的Dockerfile（针对Jenkins环境）
                        sh '''
                            cat > Dockerfile.jenkins << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# 安装必要工具
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# 复制requirements并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ \\
    --extra-index-url https://pypi.org/simple/ --timeout 600

# 复制所有构建好的资源
COPY Qwen3-Embedding-0.6B/ ./Qwen3-Embedding-0.6B/
COPY vectorstore/ ./vectorstore/
COPY app/ ./app/
COPY .env ./

# 预热模型
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('./Qwen3-Embedding-0.6B')" || echo "Model warmup skipped"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
CMD ["python", "-m", "app.application"]
EOF
                        '''

                        echo "构建 Docker 镜像: ${env.ECR_REPO}:${env.IMAGE_TAG}"
                        sh "docker build -f Dockerfile.jenkins -t ${env.ECR_REPO}:${env.IMAGE_TAG} ."

                        echo "安全扫描..."
                        sh "trivy image --severity HIGH,CRITICAL --format json -o trivy-report.json ${env.ECR_REPO}:${env.IMAGE_TAG} || true"
                        
                        echo "标记镜像..."
                        sh "docker tag ${env.ECR_REPO}:${env.IMAGE_TAG} ${imageFullName}"
                        sh "docker tag ${env.ECR_REPO}:${env.IMAGE_TAG} ${latestFullName}"
                        
                        echo "推送 Docker 镜像到 ECR..."
                        sh "docker push ${imageFullName}"
                        sh "docker push ${latestFullName}"

                        // 存档安全扫描报告
                        archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                    }
                }
            }
        }

        stage('🧪 基本测试') {
            steps {
                script {
                    echo "运行基本健康检查..."
                    sh """
                        docker run --rm -d --name test-medical-${env.BUILD_NUMBER} -p 808${env.BUILD_NUMBER % 10}:5000 ${env.ECR_REPO}:${env.IMAGE_TAG}
                        sleep 90
                        curl -f http://localhost:808${env.BUILD_NUMBER % 10}/health || exit 1
                        docker stop test-medical-${env.BUILD_NUMBER} || true
                    """
                    echo "健康检查通过！"
                }
            }
        }
    }

    post {
        always {
            script {
                // 清理构建镜像，但保留缓存
                sh "docker rmi ${env.ECR_REPO}:${env.IMAGE_TAG} || true"
                sh "docker system prune -f || true"
                
                // 清理工作目录，但保留Jenkins缓存
                sh "rm -rf Qwen3-Embedding-0.6B vectorstore rag_data.zip Dockerfile.jenkins || true"
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