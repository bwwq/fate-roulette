#!/bin/bash

# 命运轮盘 - 一键部署脚本
# 适用于 Ubuntu/Debian 系统

set -e

echo "================================"
echo "命运轮盘 - 服务器部署脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 1. 更新系统
echo -e "${GREEN}[1/7] 更新系统...${NC}"
apt update && apt upgrade -y

# 2. 安装 Node.js
echo -e "${GREEN}[2/7] 安装 Node.js...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
fi
echo "Node.js 版本: $(node -v)"
echo "NPM 版本: $(npm -v)"

# 3. 安装 PM2
echo -e "${GREEN}[3/7] 安装 PM2...${NC}"
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
fi

# 4. 创建应用目录
echo -e "${GREEN}[4/7] 创建应用目录...${NC}"
APP_DIR="/var/www/fate-roulette"
mkdir -p $APP_DIR

# 5. 复制文件（假设脚本在项目目录中运行）
echo -e "${GREEN}[5/7] 复制应用文件...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -r $SCRIPT_DIR/* $APP_DIR/
cd $APP_DIR

# 6. 安装依赖
echo -e "${GREEN}[6/7] 安装 NPM 依赖...${NC}"
npm install --production

# 7. 配置防火墙
echo -e "${GREEN}[7/7] 配置防火墙...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 3000/tcp
    ufw --force enable
fi

# 8. 启动应用
echo -e "${GREEN}启动应用...${NC}"
pm2 stop fate-roulette 2>/dev/null || true
pm2 delete fate-roulette 2>/dev/null || true
pm2 start server.js --name "fate-roulette"
pm2 startup
pm2 save

# 9. 显示状态
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
pm2 status
echo ""
echo -e "${YELLOW}访问地址: http://$(curl -s ifconfig.me):3000${NC}"
echo ""
echo "常用命令:"
echo "  查看日志: pm2 logs fate-roulette"
echo "  重启应用: pm2 restart fate-roulette"
echo "  停止应用: pm2 stop fate-roulette"
echo "  查看状态: pm2 status"
echo ""
