# JobSpy 數據管理指南

## 📋 概述

JobSpy 現在使用統一的數據管理系統來組織和存儲所有爬蟲數據。這個系統提供了：

- ✅ **統一的目錄結構**
- ✅ **標準化的文件命名**
- ✅ **完整的數據索引**
- ✅ **自動清理和歸檔**
- ✅ **多格式導出支持**

## 📁 目錄結構

```
data/
├── raw/                           # 原始數據
│   ├── by_date/                   # 按日期分類
│   │   ├── 20250127/
│   │   │   ├── linkedin/
│   │   │   ├── indeed/
│   │   │   └── glassdoor/
│   │   └── 20250128/
│   └── by_site/                   # 按網站分類
│       ├── linkedin/
│       ├── indeed/
│       └── glassdoor/
├── processed/                     # 處理後的數據
│   ├── csv/
│   ├── json/
│   └── combined/
├── exports/                       # 用戶導出
│   ├── csv/
│   └── json/
├── reports/                       # 報告和摘要
│   ├── daily/
│   ├── weekly/
│   └── monthly/
├── archive/                       # 歸檔數據
└── index/                         # 數據索引
    └── data_index.json
```

## 🚀 快速開始

### 1. 設置數據目錄

```bash
# 創建數據目錄結構
make setup

# 或者使用 Python
python -c "from jobseeker.data_manager import data_manager; print('✅ 設置完成')"
```

### 2. 遷移現有數據

```bash
# 遷移所有現有數據到新結構
make migrate

# 或者直接運行腳本
python scripts/migrate_existing_data.py
```

### 3. 查看數據摘要

```bash
# 顯示數據摘要
make summary

# 或者使用查詢工具
python scripts/query_data.py --summary
```

## 🔧 數據管理命令

### 基本命令

```bash
# 顯示數據摘要
python scripts/manage_data.py summary

# 查詢特定網站的數據
python scripts/manage_data.py query --site linkedin

# 查詢特定日期的數據
python scripts/manage_data.py query --date 20250127

# 查詢特定搜尋詞的數據
python scripts/manage_data.py query --search-term "python engineer"
```

### 清理命令

```bash
# 清理 30 天前的數據
make cleanup

# 試運行清理 (不實際刪除)
make cleanup-dry

# 自定義保留天數
python scripts/cleanup_data.py --retention-days 60
```

## 🔧 高級用法

### 1. 使用數據管理器 API

```python
from jobseeker.data_manager import data_manager

# 保存原始數據
filepath = data_manager.save_raw_data(
    site="linkedin",
    data=job_data,
    search_term="python engineer",
    location="taipei"
)

# 保存處理後的數據
processed_path = data_manager.save_processed_data(
    data=job_data,
    format="csv"
)

# 導出數據
export_path = data_manager.save_export_data(
    data=job_data,
    format="json",
    search_term="python engineer",
    location="taipei"
)
```

### 2. 查詢和分析數據

```python
from scripts.query_data import DataQuery

query = DataQuery()

# 獲取所有網站
sites = query.list_sites()

# 獲取特定網站的數據
linkedin_data = query.get_data_by_site("linkedin")

# 分析職位數據
jobs = query.load_job_data("path/to/file.json")
analysis = query.analyze_jobs(jobs)
```

## 📈 數據分析

### 1. 基本分析

```bash
# 分析職位數據
python scripts/query_data.py --analyze --export analysis_report.json

# 按網站分析
python scripts/query_data.py --site linkedin --analyze
```

### 2. 生成報告

```bash
# 生成日報
python -c "from jobseeker.data_manager import data_manager; data_manager.generate_report('daily')"

# 生成週報
python -c "from jobseeker.data_manager import data_manager; data_manager.generate_report('weekly')"
```

## 🔄 數據遷移

### 從舊系統遷移

1. **備份現有數據**
   ```bash
   make backup
   ```

2. **運行遷移腳本**
   ```bash
   make migrate
   ```

3. **驗證遷移結果**
   ```bash
   make summary
   ```

### 遷移報告

遷移完成後會生成 `data/migration_report.json`，包含：
- 遷移的文件數量
- 按網站分類的統計
- 按格式分類的統計
- 詳細的遷移日誌

## 🧹 數據清理

### 自動清理

系統會自動清理超過保留期的數據：

```python
# 清理 30 天前的數據
data_manager.cleanup_old_data(30)

# 壓縮歸檔數據
data_manager.compress_archive(7)
```

### 手動清理

```bash
# 清理並壓縮
python scripts/cleanup_data.py --retention-days 30 --compress-days 7

# 優化存儲空間
python scripts/cleanup_data.py --optimize
```

## 📋 最佳實踐

### 1. 定期維護

```bash
# 每週運行一次
make cleanup
make summary
```

### 2. 監控存儲

```bash
# 檢查存儲使用情況
python scripts/manage_data.py summary
```

### 3. 備份重要數據

```bash
# 定期備份
make backup
```

## 🆘 故障排除

### 常見問題

1. **數據目錄不存在**
   ```bash
   make setup
   ```

2. **索引文件損壞**
   ```bash
   python -c "from jobseeker.data_manager import data_manager; data_manager.update_index()"
   ```

### 恢復數據

```bash
# 從備份恢復
make restore BACKUP_FILE=backup_20250127_143022.tar.gz
```

## 📞 支持

如果遇到問題，請：

1. 檢查配置是否正確
2. 查看遷移報告
3. 運行數據驗證
4. 聯繫開發團隊

---

**注意**: 這個數據管理系統是向後兼容的，現有的爬蟲代碼無需修改即可使用新的數據管理功能。
