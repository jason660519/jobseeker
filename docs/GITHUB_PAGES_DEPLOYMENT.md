# GitHub Pages 部署指南

## 概述

由於 GitHub Pages 只支援靜態網站，而 JobSpy 是一個 Flask 後端應用，我們需要採用混合部署策略：

- **前端**: 部署到 GitHub Pages（靜態 HTML/CSS/JS）
- **後端**: 部署到支援 Python 的平台（如 Railway、Heroku、Vercel）

## 部署架構

```
用戶瀏覽器 → GitHub Pages (前端) → 外部 API (後端) → 各求職網站
```

## 步驟 1: 準備靜態前端

### 1.1 創建靜態版本的前端文件

我們需要將 Flask 模板轉換為純靜態 HTML，並修改 JavaScript 以調用外部 API。

### 1.2 修改 API 端點

將所有 API 調用從相對路徑改為絕對路徑，指向部署的後端服務。

## 步驟 2: 後端部署選項

### 選項 A: Railway（推薦）
- 免費額度：每月 500 小時
- 支援 Python/Flask
- 自動部署
- 自定義域名

### 選項 B: Heroku
- 免費額度有限
- 需要信用卡驗證
- 支援 Python/Flask

### 選項 C: Vercel
- 免費額度充足
- 支援 Python 函數
- 需要調整為 serverless 架構

## 步驟 3: GitHub Pages 設置

### 3.1 創建 gh-pages 分支
```bash
git checkout -b gh-pages
```

### 3.2 設置 GitHub Pages
1. 進入 GitHub 倉庫設置
2. 選擇 "Pages" 選項
3. 選擇 "Deploy from a branch"
4. 選擇 "gh-pages" 分支
5. 選擇 "/ (root)" 作為源目錄

## 步驟 4: 自動化部署

使用 GitHub Actions 自動化部署流程：

1. 當主分支更新時，自動構建靜態前端
2. 自動部署到 gh-pages 分支
3. 自動更新 API 端點配置

## 配置示例

### 環境變數設置
```bash
# 後端 API 基礎 URL
VITE_API_BASE_URL=https://your-backend.railway.app

# 前端部署 URL
VITE_FRONTEND_URL=https://your-username.github.io/jobseeker
```

### API 端點映射
```javascript
// 原來的相對路徑
const response = await fetch('/api/search', {...});

// 改為絕對路徑
const response = await fetch(`${process.env.VITE_API_BASE_URL}/api/search`, {...});
```

## 優勢

1. **免費**: GitHub Pages 完全免費
2. **快速**: 全球 CDN 加速
3. **可靠**: GitHub 基礎設施
4. **自動化**: 通過 GitHub Actions 自動部署
5. **版本控制**: 完整的 Git 歷史記錄

## 注意事項

1. **CORS 設置**: 後端需要正確配置 CORS 允許前端域名
2. **API 限制**: 外部 API 可能有速率限制
3. **安全性**: 敏感配置需要通過環境變數管理
4. **監控**: 需要監控後端服務狀態

## 下一步

1. 選擇後端部署平台
2. 部署後端 API
3. 創建靜態前端版本
4. 設置 GitHub Pages
5. 配置自動化部署

## 支援

如果遇到問題，請參考：
- [GitHub Pages 文檔](https://docs.github.com/en/pages)
- [Railway 部署指南](https://docs.railway.app/)
- [CORS 配置指南](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
