# 🚀 Railway 自動部署設置指南

## 📋 目前狀況

你的專案目前有：

- ✅ GitHub Actions CI/CD 管道
- ✅ GitHub Pages 自動部署
- ❌ **缺少 Railway 自動部署**

## 🎯 目標

設置 Railway 自動部署，讓每次 push 到 main 分支時自動部署到 Railway。

## 🛠️ 設置步驟

### 方法一：使用 Railway 的 GitHub 整合（推薦）

1. **前往 Railway 控制台**

   - 登入 [railway.app](https://railway.app)
   - 選擇你的 JobSpy 專案

2. **設置 GitHub 整合**

   - 在專案設定中找到 "GitHub" 選項
   - 點擊 "Connect GitHub Repository"
   - 選擇你的 `jason660519/jobseeker` 倉庫
   - 選擇 `main` 分支
   - 設置根目錄為 `web_app`

3. **配置自動部署**
   - 啟用 "Auto Deploy" 選項
   - Railway 會自動監聽 GitHub 的 push 事件
   - 每次 push 到 main 分支時自動觸發部署

### 方法二：使用 GitHub Actions（已創建）

我已經為你創建了 `.github/workflows/deploy-to-railway.yml` 文件，但需要設置以下 secrets：

1. **在 GitHub 倉庫中設置 Secrets**

   - 前往你的 GitHub 倉庫
   - 點擊 "Settings" → "Secrets and variables" → "Actions"
   - 添加以下 secrets：

   ```
   RAILWAY_TOKEN: 你的 Railway API Token
   RAILWAY_PROJECT_ID: 你的 Railway 專案 ID
   ```

2. **獲取 Railway Token**

   ```bash
   # 安裝 Railway CLI
   npm install -g @railway/cli

   # 登入並獲取 token
   railway login
   railway auth
   ```

3. **獲取專案 ID**
   - 在 Railway 專案頁面，URL 中的 ID 就是專案 ID
   - 例如：`https://railway.app/project/abc123` → 專案 ID 是 `abc123`

## 🔄 部署流程

設置完成後，部署流程會是：

1. **本地開發** → `git push origin main`
2. **GitHub 接收** → 觸發 GitHub Actions
3. **自動部署** → Railway 自動部署
4. **完成** → 應用更新上線

## ⚡ 推薦方案

**建議使用方法一（Railway GitHub 整合）**，因為：

- ✅ 設置簡單，無需管理 secrets
- ✅ Railway 原生支援，更穩定
- ✅ 自動處理環境變數
- ✅ 更好的錯誤處理和日誌

## 🔧 故障排除

### 如果自動部署失敗：

1. **檢查 Railway 日誌**

   - 前往 Railway 專案頁面
   - 查看 "Deployments" 標籤
   - 檢查構建和部署日誌

2. **檢查 GitHub Actions**

   - 前往 GitHub 倉庫的 "Actions" 標籤
   - 查看失敗的工作流程
   - 檢查錯誤訊息

3. **常見問題**
   - **權限問題**：確認 Railway 有權限訪問 GitHub 倉庫
   - **分支問題**：確認監聽的是正確的分支（main）
   - **目錄問題**：確認根目錄設置為 `web_app`

## 📊 監控部署

設置完成後，你可以：

1. **在 Railway 中監控**

   - 查看部署歷史
   - 監控應用狀態
   - 查看日誌

2. **在 GitHub 中監控**
   - 查看 Actions 執行狀態
   - 接收部署通知
   - 查看部署歷史

## 🎉 完成後的效果

設置完成後：

- ✅ 每次 `git push` 自動觸發部署
- ✅ 無需手動操作
- ✅ 部署狀態透明可見
- ✅ 自動回滾機制（如果部署失敗）

---

**選擇你喜歡的方法，我建議使用方法一（Railway GitHub 整合）！** 🚀
