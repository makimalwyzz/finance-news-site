---
description: 财经新闻网站维护与迭代指南 (Project Memory)
---

# 财经新闻网站项目状态与维护指南

该文档用于记录项目的核心设计决策、已知限制及未来迭代方向，确保 AI 助手在新的对话中能快速找回状态。

## 1. 核心架构设计
- **定时任务 (GitHub Actions)**: 负责每小时执行 `fetch_news.py`。
- **实时 API (Vercel)**: `/api/news.js` 提供实时刷新功能。
- **静态前端**: `index.html` 既能展示定时生成的静态 JSON，也能通过 API 获取动态数据。

## 2. 关键设计决策 (基于 2026-01-16 讨论)
- **超时控制**: Vercel 函数有 10s 限制。API 中每个源的超时强行限制在 **5s**，并使用 `Promise.allSettled` 确保部分源失败时整体依然可用。
- **数量限制**: 为了性能，每个新闻源在实时刷新时仅返回 **最新 10 条**。
- **时间解析**: 针对新浪财经 (Unix)、华尔街见闻 (ISO)、36氪、虎嗅等多种非标时间格式，前端实现了统一的 `parseDate` 函数以确保排序和显示正确（解决 "Invalid Date" 问题）。

## 3. 已知限制与问题
- **访问限制**: 目前默认的 `*.vercel.app` 域名在中国大陆需要 VPN。
- **API 覆盖**: 实时 API 支持 10 个源。部分中文源（新浪、华尔街）为 JSON API 格式，由 `api/news.js` 专用逻辑解析。
- **RSS 特性**: 路透社（Reuters）等国外源响应较慢，极易触发 5s 超时返回空结果。

## 4. 下一步迭代建议 (方案计划)
- **免 VPN 方案**: 
    1.  迁移至 **Cloudflare Pages** (需重写后端为 Functions 格式)。
    2.  或绑定**自定义域名**到 Vercel (推荐方案)。
- **完全静态化**: 如果不再需要实时刷新，可彻底关闭 API，仅依赖 GitHub Actions 定时推送静态数据。

## 运行维护指令
// turbo
1. 检查 API 连通性
`curl -s "https://finance-news-site-gold.vercel.app/api/news" | jq '.sources[].name'`

2. 检查抓取脚本状态
`python3 scripts/fetch_news.py .`
