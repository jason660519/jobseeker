# Glassdoor 地區限制說明

## 問題描述

Glassdoor 求職網站對某些地區有使用限制，特別是對於全球範圍（WORLDWIDE）的查詢。當系統嘗試使用 Glassdoor 代理進行全球查詢時，會拋出 "Glassdoor is not available for WORLDWIDE" 錯誤。

## 根本原因

1. **模型限制**: 在 `jobseeker/model.py` 中，`Country.WORLDWIDE` 被定義為 `("worldwide", "www")`，但沒有對應的 Glassdoor 域名值
2. **智能路由**: 智能路由系統在沒有具體地理位置時會選擇包含 Glassdoor 的代理組合
3. **配置問題**: 地理區域和行業配置中包含 Glassdoor 作為偏好代理

## 解決方案

### 1. 智能路由器修改

在 `jobseeker/intelligent_router.py` 中實施以下修改：

- **全球代理選擇**: 當沒有地理匹配時，使用全球代理但排除 Glassdoor
- **地區限制檢查**: 添加 Glassdoor 地區限制檢查邏輯
- **後備代理**: 調整後備代理選擇，排除 Glassdoor

### 2. 地理區域配置更新

從以下地理區域的次要代理中移除 Glassdoor：
- 北美地區 (North_America)
- 東南亞地區 (Southeast_Asia) 
- 歐洲地區 (Europe)

### 3. 行業配置更新

從以下行業類別的偏好代理中移除 Glassdoor：
- 技術行業 (Technology)
- 金融行業 (Finance)

### 4. 錯誤處理改進

在 `jobseeker/route_manager.py` 中添加特殊的 Glassdoor 錯誤處理：
- 將地區限制錯誤標記為警告而非嚴重錯誤
- 提供更清晰的錯誤訊息

### 5. 測試案例更新

修改 `web_app/test_cases.json` 中的測試案例：
- 將全球範圍查詢改為具體地理位置
- 確保測試案例使用支援的地區

## 支援的 Glassdoor 地區

Glassdoor 目前支援以下地區：
- 美國 (United States)
- 加拿大 (Canada)
- 英國 (United Kingdom)
- 德國 (Germany)
- 法國 (France)
- 澳洲 (Australia)
- 印度 (India)
- 新加坡 (Singapore)

## 最佳實踐

1. **地理查詢**: 使用具體的國家或城市名稱而非全球範圍
2. **代理選擇**: 對於全球查詢，優先使用 Indeed、LinkedIn 和 Google
3. **錯誤處理**: 實施優雅的降級機制，當 Glassdoor 不可用時自動切換到其他代理
4. **測試**: 定期測試不同地區的查詢以確保系統穩定性

## 監控建議

- 監控 Glassdoor 相關錯誤的頻率
- 追蹤不同地區的成功率
- 定期檢查 Glassdoor 是否擴展到新地區
- 評估替代代理的效能

## 更新歷史

- **2025-01-02**: 初始版本，解決 WORLDWIDE 查詢問題
- 實施智能路由器修改
- 更新地理和行業配置
- 改進錯誤處理機制