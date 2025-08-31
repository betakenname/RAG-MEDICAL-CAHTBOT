pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo'
        IMAGE_TAG = 'latest'
        SERVICE_NAME = 'llmops-medical-service'
    }

    stages {
        // 下载嵌入模型
        stage('下载嵌入模型') {
            steps {
                script {
                    echo "从 ModelScope 克隆嵌入模型..."
                    sh 'rm -rf Qwen3-Embedding-0.6B'
                    sh 'git clone https://www.modelscope.cn/Qwen/Qwen3-Embedding-0.6B.git'
                }
            }
        }

        // 下载 RAG 数据
        stage('下载 RAG 数据') {
            steps {
                script {
                    echo "从 AWS S3 下载向量数据库..."
                    sh 'curl -o rag_data.zip https://rag-medical-data-lzr-2025.s3.ap-southeast-2.amazonaws.com/rag_data.zip'
                    echo "解压数据并整理目录..."
                    sh 'rm -rf vectorstore'
                    sh 'unzip -o rag_data.zip -d .'
                    sh 'mkdir -p vectorstore'
                    sh 'mv db_faiss vectorstore/'
                }
            }
        }

        // 构建、扫描并推送 Docker 镜像到 ECR
        stage('构建、扫描并推送 Docker 镜像到 ECR') {
            steps {
                script {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', 
                        credentialsId: 'aws-token',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        // 获取 AWS 账户 ID
                        def accountId = sh(
                            script: "aws sts get-caller-identity --query Account --output text", 
                            returnStdout: true
                        ).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"

                        echo "登录到 Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"

                        // 修复 Docker 权限问题
                        echo "修复 Docker 权限..."
                        sh 'sudo chmod 666 /var/run/docker.sock || true'

                        echo "构建 Docker 镜像: ${env.ECR_REPO}:${env.IMAGE_TAG}"
                        sh "docker build -t ${env.ECR_REPO}:${env.IMAGE_TAG} ."

                        echo "使用 Trivy 扫描镜像..."
                        sh "trivy image --severity HIGH,CRITICAL --format json -o trivy-report.json ${env.ECR_REPO}:${env.IMAGE_TAG} || true"
                        
                        echo "为 ECR 推送标记 Docker 镜像..."
                        sh "docker tag ${env.ECR_REPO}:${env.IMAGE_TAG} ${imageFullName}"
                        
                        echo "推送 Docker 镜像到 ECR: ${imageFullName}"
                        sh "docker push ${imageFullName}"

                        // 存档安全扫描报告
                        archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                    }
                }
            }
        }
    }
}