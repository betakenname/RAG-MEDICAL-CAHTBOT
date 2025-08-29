pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo'
        IMAGE_TAG = 'latest'
        SERVICE_NAME = 'llmops-medical-service'
    }

    stages {
        // 【关键修改】删除子模块阶段，替换为直接下载
        stage('Download Embedding Model') {
            steps {
                script {
                    echo "Cloning the embedding model from ModelScope..."
                    // 先删除旧目录，确保每次都是新的
                    sh 'rm -rf Qwen3-Embedding-0.6B'
                    // 直接、简单地克隆模型仓库
                    sh 'git clone https://www.modelscope.cn/Qwen/Qwen3-Embedding-0.6B.git'
                }
            }
        }

        stage('Download RAG Data') {
            steps {
                script {
                    echo "Downloading vector database from AWS S3..."
                    sh 'curl -o rag_data.zip "https://rag-medical-data-lzr-2025.s3.ap-southeast-2.amazonaws.com/rag_data.zip"'
                    
                    echo "Unzipping data and arranging directory..."
                    sh 'rm -rf vectorstore'
                    sh 'unzip -o rag_data.zip -d .'
                    sh 'mkdir -p vectorstore'
                    sh 'mv db_faiss vectorstore/'
                }
            }
        }

        stage('Build, Scan, and Push Docker Image to ECR') {
            steps {
                script {
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                        def imageFullName = "${ecrUrl}/${env.ECR_REPO}:${env.IMAGE_TAG}"

                        echo "Logging into Amazon ECR..."
                        sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}"

                        echo "Building Docker image: ${env.ECR_REPO}:${env.IMAGE_TAG}"
                        sh "docker build -t ${env.ECR_REPO}:${env.IMAGE_TAG} ."

                        echo "Scanning image with Trivy..."
                        sh "trivy image --severity HIGH,CRITICAL --format json -o trivy-report.json ${env.ECR_REPO}:${env.IMAGE_TAG} || true"
                        
                        echo "Tagging Docker image for ECR push..."
                        sh "docker tag ${env.ECR_REPO}:${env.IMAGE_TAG} ${imageFullName}"
                        
                        echo "Pushing Docker image to ECR: ${imageFullName}"
                        sh "docker push ${imageFullName}"

                        archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                    }
                }
            }
        }
    }
}