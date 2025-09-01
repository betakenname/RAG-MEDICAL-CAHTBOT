// Jenkinsfile - 毕业最终版
pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo'
        IMAGE_TAG = "${BUILD_NUMBER}"
        LATEST_TAG = 'latest'
        JENKINS_CACHE = '/tmp/jenkins-cache'
    }

    stages {
        stage('📋 环境准备') {
            steps {
                script {
                    sh "mkdir -p ${env.JENKINS_CACHE}"
                    // 修正的缓存检查逻辑：检查核心模型文件是否存在
                    def modelCached = sh(script: "test -f ${env.JENKINS_CACHE}/Qwen3-Embedding-0.6B/model.safetensors", returnStatus: true) == 0
                    def ragDataCached = sh(script: "test -f ${env.JENKINS_CACHE}/rag_data.zip", returnStatus: true) == 0
                    
                    env.MODEL_CACHED = modelCached.toString()
                    env.RAG_CACHED = ragDataCached.toString()
                    
                    echo "模型文件缓存状态: ${env.MODEL_CACHED}"
                    echo "RAG数据缓存状态: ${env.RAG_CACHED}"
                }
            }
        }

        stage('🤖 下载嵌入模型 (仅在缓存不存在时)') {
            when { expression { env.MODEL_CACHED == 'false' } }
            steps {
                script {
                    echo "缓存不存在或不完整，正在从ModelScope下载完整模型..."
                    // 先clone，然后进入目录，再用 git lfs pull 下载大文件
                    sh """
                        cd ${env.JENKINS_CACHE}
                        rm -rf Qwen3-Embedding-0.6B
                        git clone https://www.modelscope.cn/Qwen/Qwen3-Embedding-0.6B.git
                        cd Qwen3-Embedding-0.6B
                        git lfs pull
                    """
                }
            }
        }

        stage('📦 下载RAG数据 (仅在缓存不存在时)') {
            when { expression { env.RAG_CACHED == 'false' } }
            steps {
                script {
                    echo "从 AWS S3 下载向量数据库到缓存..."
                    sh "cd ${env.JENKINS_CACHE} && curl -o rag_data.zip https://rag-medical-data-lzr-2025.s3.ap-southeast-2.amazonaws.com/rag_data.zip"
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

        stage('🏗️ 构建、扫描并推送Docker镜像') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'dotenv-file', variable: 'DOTENV_CONTENT')]) {
                        echo "从Jenkins凭据创建 .env 文件..."
                        sh 'echo "${DOTENV_CONTENT}" > .env'
                    }

                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                        def latestFullName = "${ecrUrl}/${env.ECR_REPO}:${env.LATEST_TAG}"

                        echo "登录到 Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"
                        
                        sh '''
                            cat > Dockerfile.jenkins << 'EOF'
FROM python:3.10-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true
WORKDIR /app
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*
COPY requirements.core.txt .
RUN pip install --no-cache-dir -r requirements.core.txt --timeout=600 --retries=3 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --extra-index-url https://download.pytorch.org/whl/cpu
COPY . .
EXPOSE 5000
CMD ["python", "-m", "app.application"]
EOF
                        '''

                        echo "构建 Docker 镜像..."
                        sh "docker build -f Dockerfile.jenkins -t ${imageFullName} ."
                        
                        echo "执行安全扫描..."
                        sh "trivy image --severity HIGH,CRITICAL ${imageFullName} || echo '安全扫描完成（可能有警告）'"
                        
                        echo "标记和推送镜像..."
                        sh "docker tag ${imageFullName} ${latestFullName}"
                        sh "docker push ${imageFullName}"
                        sh "docker push ${latestFullName}"
                    }
                }
            }
        }
        
         stage('🧪 基本测试') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
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
                                    docker stop $CONTAINER_ID
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
    }

    post {
        always {
            script {
                echo "清理工作区..."
                cleanWs()
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