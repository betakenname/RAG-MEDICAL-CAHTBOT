# Use the Jenkins image as the base image
FROM jenkins/jenkins:lts

# 1. 定义一个构建参数，并给它一个默认值
ARG APT_MIRROR=deb.debian.org

# Switch to root user to install dependencies
USER root

# 2. 直接创建一个新的 sources.list 文件，内容指向我们指定的镜像源
#    这会覆盖掉镜像所有默认的、可能无法访问的软件源设置
RUN echo "deb https://${APT_MIRROR}/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://${APT_MIRROR}/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://${APT_MIRROR}/debian-security/ bookworm-security main contrib non-free" >> /etc/apt/sources.list

# Install prerequisites and Docker
RUN apt-get update -y && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update -y && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    apt-get clean

# Add Jenkins user to the Docker group (create if it doesn't exist)
RUN groupadd -f docker && \
    usermod -aG docker jenkins

# Create the Docker directory and volume for DinD
RUN mkdir -p /var/lib/docker
VOLUME /var/lib/docker

# Switch back to the Jenkins user
USER jenkins