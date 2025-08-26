pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-southeast-2'
        ECR_REPO = 'my-repo'
        IMAGE_TAG = 'latest'
        SERVICE_NAME = 'llmops-medical-service'
    }

    stages {
        stage('Clone GitHub Repo') {
            steps {
                script {
                    echo 'Cloning GitHub repo to Jenkins...'
                    // 清理工作区，确保每次都是全新的开始
                    cleanWs() 
                    // 检出代码
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/betakenname/RAG-MEDICAL-CAHTBOT.git']])
                }
            }
        }

        // ======================= 新增的关键阶段 =======================
        stage('Download RAG Data') {
            steps {
                script {
                    echo "Downloading vector database from AWS S3..."
                    sh 'curl -o rag_data.zip "https://rag-medical-data-lzr-2025.s3.ap-southeast-2.amazonaws.com/rag_data.zip"'
                    
                    echo "Unzipping data..."
                    sh 'unzip -o rag_data.zip -d .'
                    echo "Recreating 'vectorstore' directory to ensure it is clean..."      
                    sh 'rm -rf vectorstore'
                    echo "Creating 'vectorstore' directory and moving 'db_faiss' into it..."
                    // 1. 创建父目录 vectorstore (-p 确保如果目录已存在也不会报错)
                    sh 'mkdir -p vectorstore'
                    // 2. 将解压出的 db_faiss 目录，移动到 vectorstore 目录的内部
                    sh 'mv db_faiss vectorstore/'
                }
            }
        }
        // ==========================================================

        stage('Build, Scan, and Push Docker Image to ECR') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
                    script {
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

        // stage('Deploy to AWS App Runner') {
        //     steps {
        //         withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-token']]) {
        //             script {
        //                 def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
        //                 def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.ECR_REPO}"
        //                 def imageFullTag = "${ecrUrl}:${IMAGE_TAG}"

        //                 echo "Triggering deployment to AWS App Runner..."

        //                 sh """
        //                 SERVICE_ARN=\$(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].ServiceArn" --output text --region ${AWS_REGION})
        //                 echo "Found App Runner Service ARN: \$SERVICE_ARN"

        //                 aws apprunner start-deployment --service-arn \$SERVICE_ARN --region ${AWS_REGION}
        //                 """
        //             }
        //         }
        //     }
        // }
    }
}