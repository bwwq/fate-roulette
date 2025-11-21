#!/bin/bash
# 命运轮盘 - 一键部署脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/bwwq/fate-roulette/main/install.sh | sudo bash

set -e

echo "================================"
echo "命运轮盘 - 一键部署"
echo "================================"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 安装 Node.js
echo -e "${GREEN}[1/5] 安装 Node.js...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
fi

# 安装 PM2
echo -e "${GREEN}[2/5] 安装 PM2...${NC}"
npm install -g pm2

# 克隆项目
echo -e "${GREEN}[3/5] 下载项目...${NC}"
cd /var/www
rm -rf fate-roulette
git clone https://github.com/bwwq/fate-roulette.git
cd fate-roulette

# 安装依赖
echo -e "${GREEN}[4/5] 安装依赖...${NC}"
npm install --production

# 启动应用
echo -e "${GREEN}[5/5] 启动应用...${NC}"
pm2 stop fate-roulette 2>/dev/null || true
pm2 delete fate-roulette 2>/dev/null || true
pm2 start server.js --name "fate-roulette"
pm2 startup
pm2 save

# 配置防火墙
if command -v ufw &> /dev/null; then
    ufw allow 3000/tcp
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${YELLOW}访问地址: http://$(curl -s ifconfig.me):3000${NC}"
echo ""
echo "常用命令:"
echo "  pm2 logs fate-roulette  # 查看日志"
echo "  pm2 restart fate-roulette  # 重启"
echo "  pm2 stop fate-roulette  # 停止"
echo ""
