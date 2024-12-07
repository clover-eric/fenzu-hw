#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}开始部署分组作业系统...${NC}"

# 检查是否安装了Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装Docker! 请先安装Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未安装Docker Compose! 请先安装Docker Compose."
    exit 1
fi

# 创建必要的目录
echo -e "${GREEN}创建必要的目录...${NC}"
mkdir -p instance
mkdir -p static/uploads

# 设置目录权限
echo -e "${GREEN}设置目录权限...${NC}"
chmod -R 755 instance
chmod -R 755 static/uploads

# 停止并删除旧容器（如果存在）
echo -e "${GREEN}清理旧容器...${NC}"
docker-compose down

# 构建新镜像并启动容器
echo -e "${GREEN}构建并启动容器...${NC}"
docker-compose up --build -d

# 检查容器是否成功启动
if [ $? -eq 0 ]; then
    echo -e "${GREEN}部署成功!${NC}"
    echo -e "${GREEN}应用程序已在 http://localhost:5678 上运行${NC}"
    echo -e "${YELLOW}默认管理员账号: admin${NC}"
    echo -e "${YELLOW}默认管理员密码: admin${NC}"
else
    echo -e "${RED}部署失败，请检查错误信息${NC}"
    exit 1
fi 