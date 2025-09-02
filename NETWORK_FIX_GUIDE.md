# JobSpy 網路連接問題修復指南

## 問題描述

您遇到的問題是：
- ✅ `http://192.168.1.181:5000` 可以正常訪問
- ❌ `http://127.0.0.1:5000` 無法訪問

## 問題原因

原始的 `web_app/app.py` 文件中，Flask 應用被配置為只監聽 `127.0.0.1`：

```python
# 原始配置（有問題）
app.run(
    host='127.0.0.1',  # 只監聽本地回環地址
    port=int(os.environ.get('PORT', 5000)),
    debug=app.config['DEBUG']
)
```

這種配置導致應用只能通過實際的網路介面 IP (192.168.1.181) 訪問，而無法通過本地回環地址 (127.0.0.1) 訪問。

## 解決方案

### 1. 修改 Flask 應用配置

已將 `web_app/app.py` 中的主機配置修改為：

```python
# 修復後的配置
host = os.environ.get('HOST', '0.0.0.0')  # 監聽所有地址
port = int(os.environ.get('PORT', 5000))

app.run(
    host=host,
    port=port,
    debug=app.config['DEBUG']
)
```

### 2. 創建便捷啟動腳本

#### Windows 批次檔 (`start_server.bat`)
```batch
@echo off
chcp 65001 >nul
echo 🚀 啟動 JobSpy 網頁服務器
cd web_app
python app.py
```

#### PowerShell 腳本 (`start_server.ps1`)
```powershell
Write-Host "🚀 啟動 JobSpy 網頁服務器" -ForegroundColor Green
Set-Location web_app
python app.py
```

## 使用方法

### 方法 1：直接啟動
```powershell
cd web_app
python app.py
```

### 方法 2：使用批次檔
```cmd
start_server.bat
```

### 方法 3：使用 PowerShell 腳本
```powershell
.\start_server.ps1
```

### 方法 4：使用 run.py（推薦）
```powershell
python web_app/run.py --mode dev
```

## 驗證修復

啟動服務器後，您應該看到類似以下的輸出：

```
🚀 jobseeker 網頁應用啟動中...
📱 本地訪問: http://localhost:5000
📱 網路訪問: http://192.168.1.181:5000
📊 API 文檔: http://localhost:5000/api/sites
🔧 監聽地址: 0.0.0.0:5000
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.181:5000
```

現在以下地址都應該可以正常訪問：
- ✅ `http://127.0.0.1:5000`
- ✅ `http://localhost:5000`
- ✅ `http://192.168.1.181:5000`

## 技術說明

### 網路介面綁定

- `127.0.0.1`：本地回環地址，只能從本機訪問
- `192.168.1.181`：您的實際網路介面 IP，可以從網路中的其他設備訪問
- `0.0.0.0`：綁定所有可用的網路介面，包括回環地址和實際網路介面

### 安全考量

在生產環境中，建議：
1. 使用環境變數控制主機綁定
2. 配置防火牆規則
3. 使用 HTTPS
4. 實施適當的身份驗證

## 故障排除

### 如果仍然無法訪問

1. **檢查防火牆**：
   ```powershell
   netsh advfirewall show allprofiles
   ```

2. **檢查端口占用**：
   ```powershell
   netstat -an | findstr :5000
   ```

3. **檢查網路介面**：
   ```powershell
   ipconfig
   ```

4. **測試連接**：
   ```powershell
   ping 127.0.0.1
   ping 192.168.1.181
   ```

### 常見問題

**Q: 為什麼之前 192.168.1.181:5000 可以工作？**
A: 因為應用綁定到 127.0.0.1，但由於網路配置的特殊性，某些情況下仍可通過實際 IP 訪問。

**Q: 0.0.0.0 安全嗎？**
A: 在開發環境中是安全的。在生產環境中，應該根據需求綁定到特定的介面。

**Q: 如何只允許本地訪問？**
A: 設置環境變數 `HOST=127.0.0.1` 或直接修改代碼。

## 相關文件

- `web_app/app.py`：主要的 Flask 應用
- `web_app/run.py`：高級啟動腳本
- `start_server.bat`：Windows 批次啟動腳本
- `start_server.ps1`：PowerShell 啟動腳本
- `docker-compose.yml`：Docker 容器化配置

---

**修復完成時間**：2025-01-27  
**修復狀態**：✅ 已解決