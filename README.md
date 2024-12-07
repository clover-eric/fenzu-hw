# 分组作业系统

这是一个基于Flask的Web应用程序，用于管理学生分组作业。教师可以发布作业任务，学生可以自由选择小组，并标记作业完成状态。

## 功能特点

- 教师可以发布、编辑和管理作业任务
- 支持12个学生小组，每组最多5名学生
- 学生可以自由选择和更换小组
- 实时显示作业完成状态
- 支持拖拽调整组员
- 响应式设计，支持移动端访问

## 部署方式

### 方式一：一键部署（最简单）

只需要运行以下命令：
bash
curl -fsSL https://raw.githubusercontent.com/clover-eric/fenzu-hw/main/install.sh | bash
```

### 方式二：Docker手动部署

1. 确保已安装 Docker 和 Docker Compose

2. 克隆仓库：
```bash
git clone https://github.com/clover-eric/fenzu-hw.git
cd fenzu-hw
```

3. 运行部署脚本：
```bash
chmod +x deploy.sh
./deploy.sh
```

4. 访问 http://localhost:5678

### 方式三：传统部署

1. 确保已安装Python 3.8或更高版本

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
python app.py
```

4. 访问 http://localhost:5678 

## 开发者指南

### 推送到GitHub

如果你想将修改后的代码推送到自己的GitHub仓库，我们提供了一个自动化推送脚本：

1. 确保已安装Git并配置好GitHub账号

2. 运行推送脚本：
```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

3. 根据提示输入你的GitHub仓库地址

脚本会自动：
- 检查必要的文件完整性
- 创建合适的.gitignore文件
- 排除不需要的文件（如数据库、缓存等）
- 初始化Git仓库
- 提交代码并推送到GitHub

### 文件说明

- `push_to_github.sh`: GitHub推送脚本
- `deploy.sh`: Docker部署脚本
- `install.sh`: 一键安装脚本
- `app.py`: 主应用程序
- `requirements.txt`: Python依赖列表
- `Dockerfile`: Docker镜像定义
- `docker-compose.yml`: Docker服务编排

## 默认账号

- 管理员账号：admin
- 管理员密码：admin

## 技术栈

- 后端：Flask + SQLAlchemy
- 前端：Bootstrap 5 + SortableJS
- 数据库：SQLite
- 容器化：Docker + Docker Compose

## 目录结构

```
.
├── app.py              # 主应用文件
├── requirements.txt    # 依赖包列表
├── Dockerfile         # Docker镜像定义
├── docker-compose.yml # Docker服务编排
├── deploy.sh         # 部署脚本
├── install.sh        # 一键部署脚本
├── push_to_github.sh # GitHub推送脚本
├── static/            # 静态文件
│   ├── css/          # CSS样式
│   └── js/           # JavaScript文件
├── templates/         # HTML模板
└── README.md         # 说明文档
```

## 开发说明

1. 数据库会在首次运行时自动创建
2. 默认端口为5678
3. 开发模式下启用了调试功能

## 注意事项

- 请确保在生产环境中修改默认管理员密码
- 建议定期备份数据库文件
- 如需修改端口，请在app.py和docker-compose.yml中更改
- Docker部署时，数据库和上传文件会持久化保存在主机的instance和static/uploads目录中

## 问题排查

如果遇到部署问题，请检查：

1. Docker和Docker Compose是否正确安装
2. 端口5678是否被占用
3. 目录权限是否正确
4. 容器日志是否有错误信息：
```bash
docker logs fenzu-hw
```

## 安全提示

- 一键部署脚本会从GitHub官方仓库拉取代码，确保安全性
- 建议在执行一键部署前检查脚本内容
- 所有脚本均为开源，可以在仓库中查看源码
- 推送到GitHub时会自动排除敏感文件和配置
```