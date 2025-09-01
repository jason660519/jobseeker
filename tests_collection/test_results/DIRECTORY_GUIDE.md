
# jobseeker 測試目錄結構說明

## 📁 目錄結構概覽

### 1. 測試腳本目錄

#### `tests/` - 正式測試框架
- **用途**: 使用 pytest 的正式測試框架
- **內容**: 單元測試、整合測試、性能測試
- **特點**: 遵循標準測試框架規範，適合 CI/CD 整合
- **執行方式**: `pytest tests/`

#### `tests_collection/` - 自定義測試腳本集合
- **用途**: 功能驗證和職位搜尋測試腳本
- **內容**: 各種實用測試腳本和批次執行工具
- **特點**: 獨立執行，生成詳細報告
- **執行方式**: 單獨執行或使用批次腳本

### 2. 測試結果目錄

#### `tests_collection/test_results/` - 統一測試結果存放區

```
test_results/
├── ui_ux_tests/              # UI/UX 職位搜尋測試結果
│   ├── ui_ux_test_20250902_002729/
│   └── ...
├── ml_engineer_tests/        # 機器學習工程師職位測試結果
│   ├── ml_engineer_test_20250901_211743/
│   └── ...
├── enhanced_scraper_tests/   # 增強版爬蟲測試結果
│   ├── enhanced_test_20250901_215209/
│   └── ...
├── verification_tests/       # 功能驗證測試結果
│   ├── final_verification_20250901_213005/
│   └── ...
└── archived/                 # 歷史測試結果歸檔
```

## 🔄 目錄差異說明

### `tests/` vs `tests_collection/`

| 特性 | tests/ | tests_collection/ |
|------|--------|-------------------|
| **框架** | pytest 標準框架 | 自定義腳本 |
| **用途** | 單元/整合測試 | 功能驗證/職位搜尋 |
| **執行** | `pytest` 命令 | 直接執行 Python 腳本 |
| **報告** | pytest 報告格式 | 自定義詳細報告 |
| **CI/CD** | 適合自動化 | 適合手動驗證 |
| **維護** | 遵循測試規範 | 靈活自定義 |

### 測試結果目錄分類

- **按功能分類**: 不同類型的測試結果分別存放
- **按時間命名**: 保留時間戳，便於追蹤
- **統一管理**: 所有結果集中在 `test_results/` 下

## 🚀 使用建議

### 開發階段
1. 使用 `tests_collection/` 中的腳本進行功能驗證
2. 執行 `run_all_tests.py` 進行批次測試

### 正式測試
1. 使用 `tests/` 目錄進行標準化測試
2. 整合到 CI/CD 流程中

### 結果管理
1. 定期檢查 `test_results/` 目錄
2. 將舊結果移動到 `archived/` 目錄
3. 保持目錄結構清潔

## 📋 維護指南

### 定期清理
```bash
# 移動 30 天前的測試結果到歸檔目錄
python organize_test_directories.py --archive-old --days 30
```

### 目錄整理
```bash
# 重新整理所有測試結果目錄
python organize_test_directories.py --reorganize
```

### 統計報告
```bash
# 生成測試目錄統計報告
python organize_test_directories.py --report
```

