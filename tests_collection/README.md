# jobseeker 測試腳本集合

這個目錄包含了 jobseeker 專案的所有測試腳本，方便統一管理和執行。

## 📁 目錄結構

### 🔍 職位搜尋測試
- **`ml_engineer_test.py`** - 機器學習工程師職位搜尋測試（基礎版本）
- **`ml_engineer_test_final.py`** - 機器學習工程師職位搜尋測試（最終版本）
- **`ml_engineer_test_fixed.py`** - 機器學習工程師職位搜尋測試（修復版本）
- **`ui_ux_test.py`** - UI/UX 設計師職位搜尋測試

### 🛠️ 增強功能測試
- **`test_enhanced_scrapers.py`** - 增強版爬蟲功能測試
- **`test_enhanced_scrapers_final.py`** - 增強版爬蟲功能測試（最終版本）
- **`simple_test.py`** - 簡化版增強爬蟲測試

### 🔧 特定網站修復測試
- **`test_bdjobs_fix.py`** - BDJobs 網站修復測試

### ✅ 驗證測試
- **`final_verification_test.py`** - 最終驗證測試

## 🚀 使用方式

### 執行單個測試
```bash
# 執行 UI/UX 職位搜尋測試
python ui_ux_test.py

# 執行機器學習工程師職位搜尋測試
python ml_engineer_test_final.py

# 執行增強版爬蟲測試
python test_enhanced_scrapers_final.py
```

### 執行所有測試
```bash
# 在 tests_collection 目錄中執行所有 Python 測試腳本
Get-ChildItem *.py | ForEach-Object { python $_.Name }
```

## 📊 測試結果

每個測試腳本執行後會生成對應的結果目錄，包含：
- **CSV 檔案** - 職位資料表格
- **JSON 檔案** - 原始資料格式
- **報告檔案** - 測試結果摘要

### 結果目錄命名規則
- `{test_name}_{timestamp}/` - 例如：`ui_ux_test_20250902_002729/`

## 🎯 測試目標

### 職位搜尋測試
- **目標**：每個求職網站至少獲取 6 筆相關職位
- **涵蓋網站**：Indeed, LinkedIn, Glassdoor, Seek, Naukri
- **搜尋條件**：支援遠端工作、全球範圍

### 增強功能測試
- **反檢測機制**：User-Agent 輪換、代理管理
- **Playwright 整合**：動態內容處理
- **錯誤處理**：智能重試機制

## 📈 成功率指標

- **整體目標**：60% 以上的網站成功率
- **職位數量**：每個測試至少 50+ 職位
- **資料品質**：完整的職位資訊（標題、公司、地點等）

## 🔄 維護說明

1. **新增測試**：將新的測試腳本放入此目錄
2. **命名規範**：使用描述性名稱，如 `{功能}_{版本}_test.py`
3. **文檔更新**：新增測試後請更新此 README
4. **結果清理**：定期清理舊的測試結果目錄

## 📝 注意事項

- 執行測試前請確保已安裝所有依賴套件
- 某些測試可能需要較長時間執行（特別是 Playwright 相關測試）
- 網路連線狀況會影響測試結果
- 建議在穩定的網路環境下執行測試

---

**最後更新**：2025-09-02  
**維護者**：jobseeker 開發團隊
