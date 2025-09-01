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
                    
                    // 检查缓存状态
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
                    withCredentials([string(credentialsId: 'dotenv-file', variable: 'DOTENV_CONTENT')]) {
                        echo "从Jenkins凭据创建 .env 文件..."
                        sh 'echo "${DOTENV_CONTENT}" > .env'
                        echo ".env 文件创建成功。"
                    }

                    // 使用AWS凭证进行登录和推送
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"
                        def latestFullName = "${ecrUrl}/${env.ECR_REPO}:${env.LATEST_TAG}"

                        echo "登录到 Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"

                        echo "使用项目根目录的 Dockerfile 构建镜像..."
                        // 直接使用我们已经优化并验证过的项目根目录下的 Dockerfile
                        sh "docker build -t ${imageFullName} ."
                        
                        echo "执行安全扫描..."
                        sh "trivy image --severity HIGH,CRITICAL --format json -o trivy-report.json ${imageFullName} || echo '安全扫描完成（可能有警告或失败）'"
                        
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
                        # 使用随机端口避免冲突
                        TEST_PORT=$(shuf -i 8080-8999 -n 1)
                        echo "使用测试端口: $TEST_PORT"
                        
                        CONTAINER_ID=$(docker run --rm -d --name test-medical-${BUILD_NUMBER} -p $TEST_PORT:5000 ''' + imageToTest + ''')
                        
                        # 增加等待时间确保模型加载
                        echo "等待120秒让应用完全启动..."
                        sleep 120 
                        
                        # 循环检查健康状态
                        for i in {1..5}; do
                            # 使用 -s -o /dev/null 来静默输出，只关心返回码
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
                // cleanWs() 会删除所有文件，包括缓存的模型和数据
                // 我们手动清理，保留缓存以备下次使用
                sh "rm -rf Qwen3-Embedding-0.6B vectorstore rag_data.zip .env Dockerfile.jenkins trivy-report.json || true"
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