# 命运轮盘 (Fate Roulette)

一个基于 Web 的多人卡牌对战游戏，支持单机 AI 对战和在线多人对战。

## 🎮 游戏简介

命运轮盘是一款策略卡牌对战游戏，玩家通过使用灵物和命运卡牌来击败对手。游戏包含 17 种独特的灵物和 5 种命运卡牌，每局游戏的牌堆都是随机生成的，确保每次游戏体验都不同。

### 核心玩法

- **生命值系统**：初始 4 点生命，上限 5 点
- **灵物机制**：失去生命时获得灵物作为补偿（每点生命获得 2 个灵物）
- **回合制对战**：使用灵物增强自己或削弱对手，然后使用命运卡牌结束回合
- **策略深度**：护身符、镜子等隐藏灵物，契约书的最终回合机制

## 🚀 快速开始

### 本地运行

```bash
# 克隆项目
git clone https://github.com/bwwq/fate-roulette.git
cd fate-roulette

# 安装依赖
npm install

# 启动服务器
node server.js
```

访问 `http://localhost:3000` 开始游戏

### Windows 用户

双击 `启动游戏.bat` 即可

## 🌐 服务器部署

### 一键部署（推荐）

在 Ubuntu/Debian 服务器上执行：

```bash
curl -fsSL https://raw.githubusercontent.com/bwwq/fate-roulette/main/install.sh | sudo bash
```

部署完成后访问 `http://你的服务器IP:3000`

### 手动部署

详细部署指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 🎯 游戏特色

### 17 种灵物

- **护身符/镜子**：隐藏灵物，对手无法看到具体是哪个
- **遥控器**：强制对手对自己使用卡牌
- **契约书**：生命归零时获得最终回合
- **手套/无线电**：控制对手的灵物
- 更多灵物效果请在游戏内查看

### 5 种命运卡牌

- **天罚**：造成 1 点伤害
- **恩赐**：获得 1 个灵物
- **虚无**：对自己使用获得额外回合
- **轮回**：目标对自己使用下一张牌
- **反噬**：造成伤害后给予目标额外回合

### 智能 AI

- **困难**：基础 AI，适合新手
- **专家**：策略 AI，会根据局势调整打法
- **地狱**：高级 AI，具有记牌和预判能力

## 🛠️ 技术栈

- **前端**：HTML5 / CSS3 / JavaScript
- **后端**：Node.js + Express + WebSocket
- **部署**：PM2 / Docker / Nginx

## 📝 游戏规则

### 基本规则

1. 初始生命 4 点，上限 5 点
2. 每回合可使用任意数量灵物（除非被手铐束缚）
3. 使用命运卡牌结束回合
4. 将对手生命降至 0 即可获胜

### 特殊机制

- **受伤补偿**：失去 1 点生命获得 2 个灵物
- **灵物上限**：最多持有 5 个灵物
- **隐藏灵物**：护身符和镜子对对手显示为"神秘护符"
- **连续使用限制**：遥控器和手铐无法连续使用

完整规则请在游戏内查看"游戏规则"页面

## 📁 项目结构

```
fate-roulette/
├── public/          # 前端文件
│   ├── index.html   # 游戏界面
│   ├── styles.css   # 样式
│   └── game.js      # 前端逻辑
├── server.js        # 服务器主程序
├── ai_logic.js      # AI 决策逻辑
├── package.json     # 项目配置
└── install.sh       # 一键部署脚本
```

## 🔧 常用命令

```bash
# 查看日志
pm2 logs fate-roulette

# 重启应用
pm2 restart fate-roulette

# 停止应用
pm2 stop fate-roulette

# 查看状态
pm2 status
```

## 🐛 问题反馈

如果遇到问题，请在 [Issues](https://github.com/bwwq/fate-roulette/issues) 页面提交

## 📄 许可证

MIT License

## 🙏 致谢

本项目基于 Python 原版游戏改编，感谢原作者的游戏设计
