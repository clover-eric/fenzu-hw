#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 打印带颜色的信息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message "错误: 未安装 $1! 请先安装 $1." "${RED}"
        exit 1
    fi
}

# 检查必要的命令
print_message "检查环境依赖..." "${YELLOW}"
check_command "git"
check_command "docker"
check_command "docker-compose"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
print_message "创建临时目录: $TEMP_DIR" "${GREEN}"

# 清理函数
cleanup() {
    print_message "清理临时文件..." "${YELLOW}"
    rm -rf "$TEMP_DIR"
}

# 设置错误处理
trap cleanup EXIT
set -e

# 克隆仓库
print_message "克隆项目仓库..." "${YELLOW}"
git clone https://github.com/clover-eric/fenzu-hw.git "$TEMP_DIR/fenzu-hw"
cd "$TEMP_DIR/fenzu-hw"

# 创建必要的目录
print_message "创建必要的目录..." "${GREEN}"
mkdir -p instance
mkdir -p static/uploads

# 设置目录权限
print_message "设置目录权限..." "${GREEN}"
chmod -R 755 instance
chmod -R 755 static/uploads

# 停止并删除旧容器（如果存在）
print_message "清理旧容器..." "${GREEN}"
docker-compose down 2>/dev/null || true

# 构建新镜像并启动容器
print_message "构建并启动容器..." "${GREEN}"
docker-compose up --build -d

# 检查容器是否成功启动
if [ $? -eq 0 ]; then
    print_message "部署成功!" "${GREEN}"
    print_message "应用程序已在 http://localhost:5678 上运行" "${GREEN}"
    print_message "默认管理员账号: admin" "${YELLOW}"
    print_message "默认管理员密码: admin" "${YELLOW}"
    print_message "\n请注意：" "${YELLOW}"
    print_message "1. 请及时修改默认管理员密码" "${YELLOW}"
    print_message "2. 数据库文件位于 instance 目录" "${YELLOW}"
    print_message "3. 上传文件位于 static/uploads 目录" "${YELLOW}"
else
    print_message "部署失败，请检查错误信息" "${RED}"
    print_message "可以通过 'docker logs fenzu-hw' 查看详细日志" "${YELLOW}"
    exit 1
fi 