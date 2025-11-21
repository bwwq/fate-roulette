# GitHub 上传指南

## 方法一：使用 GitHub Desktop（推荐新手）

### 1. 下载并安装 GitHub Desktop
- 访问：https://desktop.github.com/
- 下载并安装

### 2. 登录 GitHub 账号
- 打开 GitHub Desktop
- 点击 "Sign in to GitHub.com"
- 输入您的 GitHub 账号和密码

### 3. 创建新仓库
- 点击 "File" → "New repository"
- 填写信息：
  - Name: `fate-roulette`
  - Description: `命运轮盘 - Web 卡牌对战游戏`
  - Local path: `d:\文档\html\lp`
  - ✅ Initialize this repository with a README
  - License: MIT License
- 点击 "Create repository"

### 4. 发布到 GitHub
- 点击 "Publish repository"
- ✅ 勾选 "Keep this code private"（如果想私有）
- 点击 "Publish repository"

### 5. 完成！
访问：`https://github.com/你的用户名/fate-roulette`

---

## 方法二：使用命令行（推荐有经验的用户）

### 1. 初始化 Git 仓库

```bash
cd d:\文档\html\lp
git init
```

### 2. 添加所有文件

```bash
git add .
```

### 3. 提交更改

```bash
git commit -m "Initial commit: 命运轮盘游戏完整版"
```

### 4. 在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 填写仓库名称：`fate-roulette`
3. 描述：`命运轮盘 - Web 卡牌对战游戏`
4. 选择 Public 或 Private
5. **不要**勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

### 5. 关联远程仓库

```bash
git remote add origin https://github.com/你的用户名/fate-roulette.git
```

### 6. 推送代码

```bash
git branch -M main
git push -u origin main
```

### 7. 完成！

访问：`https://github.com/你的用户名/fate-roulette`

---

## 方法三：使用 VS Code（如果您使用 VS Code）

### 1. 打开项目文件夹
- 在 VS Code 中打开 `d:\文档\html\lp`

### 2. 初始化 Git
- 点击左侧 "Source Control" 图标
- 点击 "Initialize Repository"

### 3. 暂存所有文件
- 点击 "+" 号暂存所有更改

### 4. 提交
- 输入提交信息：`Initial commit: 命运轮盘游戏完整版`
- 点击 "✓" 提交

### 5. 发布到 GitHub
- 点击 "Publish to GitHub"
- 选择仓库名称和可见性
- 点击 "Publish"

---

## 后续更新代码

### 使用 GitHub Desktop
1. 在 GitHub Desktop 中查看更改
2. 填写提交信息
3. 点击 "Commit to main"
4. 点击 "Push origin"

### 使用命令行
```bash
git add .
git commit -m "更新说明"
git push
```

### 使用 VS Code
1. 暂存更改
2. 填写提交信息
3. 点击 "✓" 提交
4. 点击 "..." → "Push"

---

## 常见问题

### Q: 如何修改仓库描述？
A: 在 GitHub 仓库页面，点击右上角的 "Settings" → 修改 Description

### Q: 如何添加主题标签？
A: 在仓库页面，点击 "About" 右侧的齿轮图标 → 添加 Topics：
- `game`
- `card-game`
- `multiplayer`
- `websocket`
- `nodejs`
- `javascript`

### Q: 如何让 README 显示中文？
A: GitHub 会自动识别 UTF-8 编码的中文，无需额外设置

### Q: 如何删除敏感信息？
A: 如果不小心上传了密码等敏感信息：
1. 立即修改密码
2. 从代码中删除敏感信息
3. 提交并推送
4. 如需彻底删除历史记录，使用 `git filter-branch` 或 BFG Repo-Cleaner

---

## 推荐的 GitHub 仓库设置

### 1. 添加 Topics（标签）
- game
- card-game
- multiplayer
- websocket
- nodejs
- javascript
- ai

### 2. 添加 Description
```
🎮 命运轮盘 - 一个基于 Web 的多人卡牌对战游戏，支持智能 AI 对手和在线多人对战
```

### 3. 设置 Website
如果您部署了在线版本，可以添加网站链接

### 4. 启用 Issues
允许用户报告 Bug 和提出建议

### 5. 添加 README 徽章（可选）
```markdown
![Node.js](https://img.shields.io/badge/node-%3E%3D14.0.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
```

---

## 需要帮助？

如果遇到问题，可以：
1. 查看 GitHub 官方文档：https://docs.github.com/
2. 在项目中提 Issue
3. 联系我获取帮助
