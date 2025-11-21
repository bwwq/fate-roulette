# 命运轮盘 - 服务器部署指南

## 部署方式选择

### 方案一：使用 PM2 (推荐)
适合：VPS、云服务器（阿里云、腾讯云等）

### 方案二：使用 Docker
适合：需要容器化部署的场景

### 方案三：使用 Nginx 反向代理
适合：需要 HTTPS 或多个应用共存

---

## 方案一：PM2 部署（最简单）

### 1. 准备服务器
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
sudo yum update -y  # CentOS

# 安装 Node.js (推荐 18.x 或更高)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node -v
npm -v
```

### 2. 上传项目文件
```bash
# 方法1: 使用 Git
cd /var/www
sudo git clone <你的仓库地址> fate-roulette
cd fate-roulette

# 方法2: 使用 SCP/SFTP
# 在本地执行
scp -r d:\文档\html\lp/* user@your-server-ip:/var/www/fate-roulette/
```

### 3. 安装依赖
```bash
cd /var/www/fate-roulette
npm install
```

### 4. 安装 PM2
```bash
sudo npm install -g pm2
```

### 5. 启动应用
```bash
# 启动应用
pm2 start server.js --name "fate-roulette"

# 设置开机自启
pm2 startup
pm2 save

# 查看状态
pm2 status
pm2 logs fate-roulette
```

### 6. 配置防火墙
```bash
# 开放 3000 端口
sudo ufw allow 3000/tcp
sudo ufw enable
```

### 7. 访问游戏
打开浏览器访问：`http://你的服务器IP:3000`

---

## 方案二：Docker 部署

### 1. 创建 Dockerfile
已为您创建 `Dockerfile`

### 2. 创建 docker-compose.yml
已为您创建 `docker-compose.yml`

### 3. 构建并运行
```bash
# 构建镜像
docker-compose build

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止容器
docker-compose down
```

### 4. 访问游戏
打开浏览器访问：`http://你的服务器IP:3000`

---

## 方案三：Nginx 反向代理 + HTTPS

### 1. 安装 Nginx
```bash
sudo apt install nginx -y
```

### 2. 配置 Nginx
已为您创建 `nginx.conf`

将配置复制到 Nginx：
```bash
sudo cp nginx.conf /etc/nginx/sites-available/fate-roulette
sudo ln -s /etc/nginx/sites-available/fate-roulette /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 配置 SSL (可选但推荐)
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取 SSL 证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 4. 使用 PM2 启动应用
```bash
pm2 start server.js --name "fate-roulette"
pm2 startup
pm2 save
```

### 5. 访问游戏
- HTTP: `http://yourdomain.com`
- HTTPS: `https://yourdomain.com`

---

## 环境变量配置

创建 `.env` 文件：
```env
PORT=3000
NODE_ENV=production
```

修改 `server.js` 使用环境变量：
```javascript
const PORT = process.env.PORT || 3000;
```

---

## 性能优化建议

### 1. 启用 Gzip 压缩
在 `server.js` 中添加：
```javascript
const compression = require('compression');
app.use(compression());
```

安装依赖：
```bash
npm install compression
```

### 2. 设置静态文件缓存
```javascript
app.use(express.static(path.join(__dirname, 'public'), {
    maxAge: '1d'
}));
```

### 3. PM2 集群模式
```bash
pm2 start server.js -i max --name "fate-roulette"
```

---

## 监控和维护

### PM2 监控
```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs fate-roulette

# 重启应用
pm2 restart fate-roulette

# 查看资源使用
pm2 monit
```

### 日志管理
```bash
# 安装日志轮转
pm2 install pm2-logrotate

# 配置日志大小
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

---

## 安全建议

### 1. 使用防火墙
```bash
# 只开放必要端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. 配置速率限制
在 `server.js` 中添加：
```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100 // 限制100个请求
});

app.use(limiter);
```

### 3. 使用 HTTPS
强烈建议使用 SSL/TLS 加密连接

---

## 故障排查

### 问题1: 端口被占用
```bash
# 查找占用端口的进程
sudo lsof -i :3000
# 或
sudo netstat -tulpn | grep 3000

# 杀死进程
sudo kill -9 <PID>
```

### 问题2: WebSocket 连接失败
- 检查防火墙是否开放端口
- 检查 Nginx 配置是否支持 WebSocket
- 确认服务器 IP/域名正确

### 问题3: 应用崩溃
```bash
# 查看 PM2 日志
pm2 logs fate-roulette --lines 100

# 查看错误日志
pm2 logs fate-roulette --err
```

---

## 快速部署脚本

已为您创建 `deploy.sh`，使用方法：
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 更新应用

### 使用 Git
```bash
cd /var/www/fate-roulette
git pull
npm install
pm2 restart fate-roulette
```

### 手动上传
```bash
# 上传新文件后
cd /var/www/fate-roulette
npm install
pm2 restart fate-roulette
```

---

## 备份建议

### 定期备份
```bash
# 创建备份脚本
sudo nano /usr/local/bin/backup-fate-roulette.sh
```

内容：
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/fate-roulette-$DATE.tar.gz /var/www/fate-roulette
find /backup -name "fate-roulette-*.tar.gz" -mtime +7 -delete
```

设置定时任务：
```bash
sudo chmod +x /usr/local/bin/backup-fate-roulette.sh
sudo crontab -e
# 添加：每天凌晨2点备份
0 2 * * * /usr/local/bin/backup-fate-roulette.sh
```

---

## 推荐的服务器配置

### 最低配置
- CPU: 1核
- 内存: 512MB
- 硬盘: 10GB
- 带宽: 1Mbps

### 推荐配置（支持100+在线用户）
- CPU: 2核
- 内存: 2GB
- 硬盘: 20GB
- 带宽: 5Mbps

---

## 常用云服务商

1. **阿里云** - https://www.aliyun.com
2. **腾讯云** - https://cloud.tencent.com
3. **华为云** - https://www.huaweicloud.com
4. **DigitalOcean** - https://www.digitalocean.com
5. **Vultr** - https://www.vultr.com

---

## 需要帮助？

如果遇到问题，请检查：
1. Node.js 版本是否 >= 14
2. 端口是否被占用
3. 防火墙是否正确配置
4. WebSocket 连接是否正常
5. PM2 日志中的错误信息
