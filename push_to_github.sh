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

# 检查git配置
check_git_config() {
    if [ -z "$(git config --global user.name)" ] || [ -z "$(git config --global user.email)" ]; then
        print_message "错误: Git用户名或邮箱未配置!" "${RED}"
        print_message "请运行以下命令配置:" "${YELLOW}"
        print_message "git config --global user.name \"你的用户名\"" "${YELLOW}"
        print_message "git config --global user.email \"你的邮箱\"" "${YELLOW}"
        exit 1
    fi
}

# 检查必要文件
check_required_files() {
    local required_files=("app.py" "requirements.txt" "Dockerfile" "docker-compose.yml" "deploy.sh" "install.sh")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_message "错误: 缺少必要文件 $file" "${RED}"
            exit 1
        fi
    done
}

# 创建.gitignore文件
create_gitignore() {
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# 数据库
*.db
*.sqlite3
instance/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db

# 上传文件
static/uploads/*
!static/uploads/.gitkeep

# 日志文件
*.log

# 临时文件
*.tmp
*.temp
.coverage
htmlcov/
EOL
}

# 主函数
main() {
    # 检查git是否安装
    print_message "检查环境..." "${YELLOW}"
    check_command "git"
    check_git_config

    # 检查必要文件
    print_message "检查必要文件..." "${YELLOW}"
    check_required_files

    # 确认远程仓库地址
    print_message "请输入GitHub仓库地址 (例如: https://github.com/username/repo.git):" "${YELLOW}"
    read -r repo_url

    if [ -z "$repo_url" ]; then
        print_message "错误: 仓库地址不能为空!" "${RED}"
        exit 1
    fi

    # 创建.gitignore
    print_message "创建.gitignore文件..." "${GREEN}"
    create_gitignore

    # 创建static/uploads目录和.gitkeep文件
    mkdir -p static/uploads
    touch static/uploads/.gitkeep

    # 初始化git仓库
    print_message "初始化Git仓库..." "${GREEN}"
    git init -b main  # 使用main作为默认分支

    # 添加文件
    print_message "添加文件到Git..." "${GREEN}"
    git add .

    # 提交更改
    print_message "提交更改..." "${GREEN}"
    git commit -m "Initial commit: 添加分组作业系统基础代码"

    # 添加远程仓库
    print_message "添加远程仓库..." "${GREEN}"
    if git remote | grep -q "^origin$"; then
        git remote remove origin
    fi
    git remote add origin "$repo_url"

    # 推送到GitHub
    print_message "推送到GitHub..." "${GREEN}"
    if git push -u origin main --force; then
        print_message "\n✨ 推送成功!" "${GREEN}"
        print_message "仓库地址: $repo_url" "${GREEN}"
        print_message "\n后续更新步骤:" "${YELLOW}"
        print_message "1. 修改代码后: git add ." "${YELLOW}"
        print_message "2. 提交更改: git commit -m \"更新说明\"" "${YELLOW}"
        print_message "3. 推送到GitHub: git push" "${YELLOW}"
    else
        print_message "\n❌ 推送失败!" "${RED}"
        print_message "可能的原因:" "${YELLOW}"
        print_message "1. 远程仓库地址错误" "${YELLOW}"
        print_message "2. 没有仓库的写入权限" "${YELLOW}"
        print_message "3. 需要先在GitHub上创建仓库" "${YELLOW}"
        print_message "\n解决方法:" "${GREEN}"
        print_message "1. 检查仓库地址是否正确" "${GREEN}"
        print_message "2. 确保已在GitHub上创建了空仓库" "${GREEN}"
        print_message "3. 检查是否有仓库的写入权限" "${GREEN}"
        print_message "4. 如果是私有仓库，确保已登录GitHub" "${GREEN}"
        exit 1
    fi
}

# 运行主函数
main 