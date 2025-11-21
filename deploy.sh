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

# 4. 准备应用目录
echo -e "${GREEN}[4/7] 准备应用目录...${NC}"
APP_DIR="/var/www/fate-roulette"
BACKUP_DIR="/var/www/fate-roulette_backups"

# 如果已存在，先备份
if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}检测到旧版本，正在备份...${NC}"
    mkdir -p $BACKUP_DIR
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    # 仅备份代码，排除 node_modules 以节省空间
    tar --exclude='node_modules' -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$APP_DIR" .
    echo -e "${GREEN}备份已保存至: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz${NC}"
fi

mkdir -p $APP_DIR

# 5. 复制文件（覆盖更新）
echo -e "${GREEN}[5/7] 复制应用文件...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 使用 rsync 进行增量更新，排除不必要的文件
if command -v rsync &> /dev/null; then
    rsync -av --exclude='node_modules' --exclude='.git' --exclude='deploy.sh' "$SCRIPT_DIR/" "$APP_DIR/"
else
    # 降级方案
    cp -r "$SCRIPT_DIR/"* "$APP_DIR/"
fi

cd $APP_DIR

# 6. 安装依赖
echo -e "${GREEN}[6/7] 安装/更新 NPM 依赖...${NC}"
# 清理缓存并重新安装，确保依赖一致性
npm install --production

# 7. 配置防火墙
echo -e "${GREEN}[7/7] 配置防火墙...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 3000/tcp
    ufw --force enable
fi

# 8. 启动/重启应用
echo -e "${GREEN}正在重启应用...${NC}"
# 使用 reload 实现零停机重启（如果支持），否则 restart
if pm2 list | grep -q "fate-roulette"; then
    pm2 reload fate-roulette
else
    pm2 start server.js --name "fate-roulette"
fi

pm2 startup
pm2 save

# 9. 显示状态
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}部署/更新完成！${NC}"
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
