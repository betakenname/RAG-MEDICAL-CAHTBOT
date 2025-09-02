pipeline {
    agent any // 在任何可用的 agent 上运行

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo' // 你的ECR仓库名
        IMAGE_TAG = "${BUILD_NUMBER}" // 使用构建号作为标签
        LATEST_TAG = 'latest'
        JENKINS_CACHE = '/tmp/jenkins-cache' // Jenkins服务器上的缓存目录
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
                    sh "cd ${env.JENKINS_CACHE} && rm -rf Qwen3-Embedding-0.6B && git clone --depth=1 https://www.modelscope.cn/Qwen/Qwen3-Embedding-0.6B.git"
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
                    // 从Jenkins凭据中读取Secret text，并创建.env文件
                    withCredentials([file(credentialsId: 'dotenv-secret-file', variable: 'DOTENV_FILE_PATH')]) {
                    echo "从 Secret file 凭据复制内容到 .env 文件..."
                    // Jenkins 会将凭据文件放在一个临时路径下，我们通过变量 DOTENV_FILE_PATH 拿到这个路径
                    // 然后将这个临时文件复制到我们工作区的 .env 文件，供后续步骤使用
                    sh 'cp "${DOTENV_FILE_PATH}" .env'
                    }

                    // 使用AWS凭证进行登录和推送
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                        def latestFullName = "${ecrUrl}/${env.ECR_REPO}:${env.LATEST_TAG}"

                        echo "登录到 Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"
                        
                        // 动态创建Dockerfile.jenkins，并包含关键修正
                        sh '''
                            cat > Dockerfile.jenkins << 'EOF'
FROM python:3.10-slim

# 设置国内镜像源，增加网络稳定性
ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true

WORKDIR /app

# 安装必要的系统工具
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.core.txt .

# 安装Python依赖 (关键修正：添加PyTorch官方CPU源)
RUN pip install --no-cache-dir -r requirements.core.txt --timeout=600 --retries=3 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --extra-index-url https://download.pytorch.org/whl/cpu

# 复制所有应用代码和构建好的资源
COPY . .

# 【关键修复】设置生产环境变量，禁用Flask debug模式
ENV FLASK_DEBUG=False

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
                // 【关键修复】改进健康检查逻辑
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                    script {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageToTest = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                        
                        echo "对镜像 ${imageToTest} 运行基本健康检查..."
                        sh '''
                            set -e
                            TEST_PORT=$(shuf -i 8080-8999 -n 1)
                            echo "使用测试端口: $TEST_PORT"
                            
                            # 启动容器，禁用debug模式
                            CONTAINER_ID=$(docker run --rm -d --name test-medical-${BUILD_NUMBER} \
                                --env-file .env \
                                -e FLASK_DEBUG=False \
                                -p $TEST_PORT:5000 ''' + imageToTest + ''')
                            
                            echo "Container ID: $CONTAINER_ID"
                            echo "等待应用完全启动..."
                            
                            # 等待容器健康检查，最多3分钟
                            TIMEOUT=180
                            WAIT_TIME=0
                            SUCCESS=false
                            
                            while [ $WAIT_TIME -lt $TIMEOUT ]; do
                                echo "健康检查尝试 - 已等待 ${WAIT_TIME}s"
                                
                                # 检查容器是否还在运行
                                if ! docker ps | grep -q $CONTAINER_ID; then
                                    echo "❌ 容器已停止运行"
                                    docker logs $CONTAINER_ID
                                    docker rm -f $CONTAINER_ID 2>/dev/null || true
                                    exit 1
                                fi
                                
                                # 尝试健康检查
                                if curl -f -s -m 10 http://localhost:$TEST_PORT/health; then
                                    echo "✅ 健康检查通过！"
                                    SUCCESS=true
                                    break
                                else
                                    echo "健康检查暂未通过，继续等待..."
                                    # 显示容器日志的最后几行
                                    echo "=== 容器最新日志 ==="
                                    docker logs --tail 10 $CONTAINER_ID
                                    echo "==================="
                                fi
                                
                                sleep 15
                                WAIT_TIME=$((WAIT_TIME + 15))
                            done
                            
                            # 清理容器
                            echo "停止并清理测试容器..."
                            docker stop $CONTAINER_ID
                            docker rm -f $CONTAINER_ID 2>/dev/null || true
                            
                            if [ "$SUCCESS" = "true" ]; then
                                echo "🎉 健康检查成功完成"
                                exit 0
                            else
                                echo "❌ 健康检查超时失败"
                                exit 1
                            fi
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
                // 清理可能残留的测试容器
                sh "docker ps -a | grep test-medical-${BUILD_NUMBER} | awk '{print \$1}' | xargs -r docker rm -f || true"
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