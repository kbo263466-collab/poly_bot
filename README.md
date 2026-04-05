# 🤖 PolyBot: 全球资讯双语自动化日报

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-green.svg)
![M4 Mac mini](https://img.shields.io/badge/Developed_on-M4_Mac_mini-orange.svg)

这是一个运行在 GitHub Actions 云端的私人助理脚本。它能定时抓取全球前沿新闻与 Polymarket 热门事件赔率，并通过 QQ 邮箱发送精美的双语简报。

## ✨ 核心功能
- **🌍 全球新闻汇总**：每日同步 NewsAPI 抓取 10 条前沿热点新闻。
- **💰 赔率双语监控**：实时追踪 Polymarket 热门事件，自动将赔率转换为百分比（%）并进行关键词汉化。
- **🛡️ 隐私安全架构**：所有敏感信息（邮箱账号、授权码、接收方）均通过 GitHub Secrets 加密存储，代码完全脱敏。
- **⏰ 定时精准推送**：每天北京时间 **08:00** 与 **12:30** 准时送达。

## 🛠️ 技术实现
- **开发环境**：Mac mini (M4, 2024) / VS Code
- **运行环境**：GitHub Actions (Ubuntu-latest)
- **数据源**：
  - Polymarket Gamma API
  - NewsAPI (Top Headlines)
- **通信协议**：SMTP over SSL (Port 465)

## 📦 部署与配置
项目使用 GitHub Actions 的环境变量进行驱动，需在仓库 `Settings -> Secrets -> Actions` 中配置以下变量：

| 变量名 | 说明 | 示例 |
| :--- | :--- | :--- |
| `MAIL_USER` | 发送方 QQ 邮箱 | 
| `MAIL_PASS` | SMTP 授权码 | 
| `MAIL_RECEIVER` | 接收方邮箱 | 

## 📅 工作流说明 (Workflow)
自动化脚本由 `.github/workflows/daily.yml` 控制：
- **手动触发**：支持在 Actions 页面点击 `Run workflow` 立即获取最新报表。
- **定时触发**：采用 Cron 表达式实现每日两次自动运行。

---
**Build with ❤️ by kbo263466-collab on M4 Mac mini**
