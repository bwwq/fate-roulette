# 命运轮盘 (Fate Roulette)

一个基于 Web 的多人卡牌对战游戏，支持单机 AI 对战和在线多人对战。

![游戏截图](screenshot.png)

## 🎮 游戏特色

- **17种独特灵物** - 每个灵物都有独特的战术价值
- **5种命运卡牌** - 随机生成的牌堆，每局都不同
- **智能AI对手** - 三种难度（困难、专家、地狱）
- **多人在线对战** - 支持房间创建、快速匹配
- **简洁护眼UI** - 现代化的深色主题设计
- **完整游戏机制** - 契约书、镜子反弹、遥控器等复杂交互

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/fate-roulette.git
cd fate-roulette

# 2. 安装依赖
npm install

# 3. 启动服务器
node server.js

# 4. 打开浏览器访问
http://localhost:3000
```

### Windows 用户

双击 `启动游戏.bat` 即可自动安装依赖并启动游戏。

## 📦 服务器部署

详细部署指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

### 快速部署（使用 PM2）

```bash
# 上传文件到服务器后
chmod +x deploy.sh
sudo ./deploy.sh
```

### Docker 部署

```bash
docker-compose up -d
```

## 🎯 游戏规则

### 核心规则
- **获胜条件**：将对手生命值降至 0 或以下
- **初始生命**：4 点（上限 5 点）
- **受伤补偿**：每失去 1 点生命，获得 2 个灵物
- **灵物上限**：最多持有 5 个灵物

### 回合流程
1. 使用任意数量的灵物（除非被手铐束缚）
2. 点击"使用命运卡牌"结束回合
3. 选择目标（自己或对手）
4. 结算效果，切换回合

### 特殊机制
- **隐藏灵物**：护身符和镜子对对手显示为"神秘护符"
- **契约书**：生命归零时以 1 血存活，获得最终回合
- **镜子反弹**：反弹命运卡牌效果，且伤害 +1
- **遥控器**：回合结束后，对手被迫对自己使用卡牌

完整规则请在游戏内查看"游戏规则"。

## 🛠️ 技术栈

### 前端
- HTML5 / CSS3 / JavaScript (ES6+)
- WebSocket (实时通信)
- Google Fonts (Noto Sans SC)

### 后端
- Node.js
- Express.js
- WebSocket (ws)

### 部署
- PM2 (进程管理)
- Nginx (反向代理)
- Docker (容器化)

## 📁 项目结构

```
fate-roulette/
├── public/              # 前端资源
│   ├── index.html      # 主页面
│   ├── styles.css      # 样式文件
│   └── game.js         # 游戏逻辑
├── server.js           # 服务器主文件
├── ai_logic.js         # AI 决策逻辑
├── main.py             # Python 原版参考
├── package.json        # 项目配置
├── DEPLOYMENT.md       # 部署指南
├── Dockerfile          # Docker 配置
├── docker-compose.yml  # Docker Compose
├── nginx.conf          # Nginx 配置
└── deploy.sh           # 一键部署脚本
```

## 🎨 UI 设计

- **配色方案**：Nord/Slate 深色主题
- **字体**：Noto Sans SC（思源黑体）
- **设计理念**：简洁、美观、大方、舒适、护眼

## 🤖 AI 实现

### 三种难度

1. **困难 (Hard)**
   - 基础决策逻辑
   - 40% 概率使用灵物

2. **专家 (Expert)**
   - 策略倾向系统（防御/进攻/稳定）
   - 灵物评分算法
   - 记牌功能（放大镜）
   - 智能目标选择

3. **地狱 (Hell)**
   - 继承专家 AI 所有功能
   - 牌堆组成追踪
   - 动态策略调整

AI 逻辑完全移植自 Python 原版的 `ExpertAIPlayer`。

## 🔧 开发

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
node server.js
```

### 代码规范

- 使用 ES6+ 语法
- 遵循 JavaScript Standard Style
- 注释使用中文

## 🐛 已知问题

- [ ] 移动端适配优化
- [ ] 添加音效
- [ ] 添加动画效果
- [ ] 持久化数据存储

## 📝 更新日志

### v1.0.0 (2025-01-21)
- ✅ 完整实现 17 种灵物效果
- ✅ 完整实现 5 种命运卡牌
- ✅ 三种难度 AI 对手
- ✅ 多人在线对战
- ✅ 房间系统和快速匹配
- ✅ 简洁护眼 UI
- ✅ 修复所有已知 Bug

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

- **原版 Python 实现**：[原作者]
- **Web 版本移植**：[您的名字]

## 🙏 致谢

- 感谢原版 Python 实现提供的游戏设计
- 感谢所有测试玩家的反馈

## 📞 联系方式

- GitHub Issues: [项目 Issues 页面]
- Email: your.email@example.com

---

⭐ 如果这个项目对您有帮助，请给个 Star！
