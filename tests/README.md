# JobSpy 測試套件

這個資料夾包含了 JobSpy 專案的完整測試基礎設施，支援所有9個求職網站的測試。

## 📁 資料夾結構

```
tests/
├── README.md                    # 本檔案 - 測試說明
├── conftest.py                  # 全域測試配置和 fixtures
├── pytest.ini                  # pytest 配置檔案
├── requirements-test.txt        # 測試依賴套件
├── test_config.py              # 測試環境配置
├── test_runner.py              # 主要測試執行器
├── run_tests.py                # 簡化的測試執行腳本
├── test_examples.py            # 測試範例和模板
├── test_all_sites.py           # 所有網站的綜合測試
├── unit/                       # 單元測試
│   └── test_basic_functionality.py
├── integration/                # 整合測試
│   └── test_integration.py
├── performance/                # 效能測試
│   └── test_performance.py
└── fixtures/                   # 測試資料和工具
    ├── test_data.py
    └── test_utils.py
```

## 🌐 支援的網站

JobSpy 測試套件支援以下9個求職網站：

1. **LinkedIn** - 專業社交網路平台
2. **Indeed** - 全球最大求職網站
3. **ZipRecruiter** - 美國求職平台
4. **Glassdoor** - 公司評價和薪資資訊
5. **Google Jobs** - Google 求職搜尋
6. **Bayt** - 中東地區求職平台
7. **Naukri** - 印度求職網站
8. **BDJobs** - 孟加拉求職平台
9. **Seek** - 澳洲求職網站

## 🚀 快速開始

### 1. 安裝測試依賴

```bash
# 進入測試目錄
cd tests

# 安裝測試依賴
pip install -r requirements-test.txt
```

### 2. 執行基本測試

```bash
# 執行所有測試
python test_runner.py --all

# 執行快速測試（跳過慢速測試）
python test_runner.py --quick

# 執行特定類型的測試
python test_runner.py --unit
python test_runner.py --integration
python test_runner.py --performance
```

### 3. 測試特定網站

```bash
# 測試所有網站
pytest test_all_sites.py -v

# 測試特定網站（使用 Mock）
pytest test_all_sites.py::TestAllSitesIntegration::test_individual_site_scraping_mock -v

# 測試真實網路連接（較慢）
pytest test_all_sites.py -m "network" -v
```

## 🧪 測試類型

### 單元測試 (Unit Tests)
- **位置**: `unit/`
- **特點**: 快速執行，使用 Mock，高覆蓋率
- **執行**: `pytest unit/ -v`

### 整合測試 (Integration Tests)
- **位置**: `integration/`
- **特點**: 測試模組協作，可能需要網路
- **執行**: `pytest integration/ -v`

### 效能測試 (Performance Tests)
- **位置**: `performance/`
- **特點**: 測量執行時間和資源使用
- **執行**: `pytest performance/ -v`

### 全網站測試 (All Sites Tests)
- **位置**: `test_all_sites.py`
- **特點**: 測試所有9個網站的功能
- **執行**: `pytest test_all_sites.py -v`

## 🏷️ 測試標記

使用 pytest 標記來分類和選擇測試：

```bash
# 只執行單元測試
pytest -m "unit" -v

# 只執行整合測試
pytest -m "integration" -v

# 跳過慢速測試
pytest -m "not slow" -v

# 跳過需要網路的測試
pytest -m "not network" -v

# 只執行效能測試
pytest -m "performance" -v

# 只執行 Mock 測試
pytest -m "mock" -v
```

### 可用標記
- `unit` - 單元測試
- `integration` - 整合測試
- `performance` - 效能測試
- `slow` - 慢速測試
- `network` - 需要網路連接
- `mock` - 使用 Mock
- `asyncio` - 非同步測試

## 📊 測試報告

### 生成覆蓋率報告

```bash
# HTML 覆蓋率報告
python test_runner.py --coverage --html

# 查看報告
start htmlcov/index.html  # Windows
```

### 生成測試報告

```bash
# 生成詳細報告
python test_runner.py --report test-report.md

# JSON 格式報告
python test_runner.py --json test-results.json
```

## 🐳 Docker 測試

### 使用 Docker Compose

```bash
# 回到專案根目錄
cd ..

# 執行所有測試
docker-compose --profile test up jobspy-test

# 執行單元測試
docker-compose --profile test up jobspy-unit-test

# 執行整合測試
docker-compose --profile test up jobspy-integration-test

# 執行效能測試
docker-compose --profile performance up jobspy-performance-test
```

### 進入測試容器

```bash
# 啟動開發環境
docker-compose --profile dev up -d

# 進入容器
docker-compose exec jobspy-dev bash

# 在容器內執行測試
cd tests
python test_runner.py --quick
```

## ⚙️ 配置選項

### 環境變數

```bash
# 測試環境設定
export JOBSPY_TEST_ENV=local
export JOBSPY_MOCK_NETWORK=true
export JOBSPY_CACHE_ENABLED=false
export JOBSPY_VERBOSE=true
```

### pytest.ini 配置

測試配置已在 `pytest.ini` 中設定，包括：
- 測試發現規則
- 覆蓋率設定
- 標記定義
- 輸出格式

## 🔧 自訂測試

### 新增網站測試

1. 在 `test_all_sites.py` 中新增網站到 `ALL_SITES` 列表
2. 更新 `SITE_NAMES` 對應
3. 新增網站特定的測試方法

### 新增測試案例

```python
import pytest
from jobspy import scrape_jobs
from jobspy.model import Site

@pytest.mark.unit
def test_my_custom_feature():
    """自訂測試案例"""
    result = scrape_jobs(
        site_name=Site.INDEED,
        search_term="my test",
        results_wanted=1
    )
    assert isinstance(result, pd.DataFrame)
```

## 📈 效能基準

### 執行效能測試

```bash
# 效能基準測試
pytest performance/ -v --benchmark-only

# 比較效能
pytest test_all_sites.py::TestAsyncAllSites::test_async_scraping_performance_comparison -v
```

### 效能指標

- **單網站爬取**: < 30 秒
- **多網站並發**: < 60 秒
- **記憶體使用**: < 500MB
- **成功率**: > 80%

## 🛠️ 故障排除

### 常見問題

1. **測試執行緩慢**
   ```bash
   # 只執行快速測試
   pytest -m "not slow" -v
   
   # 並行執行
   pytest -n auto
   ```

2. **網路連接問題**
   ```bash
   # 使用 Mock 模式
   export JOBSPY_MOCK_NETWORK=true
   pytest -m "not network" -v
   ```

3. **記憶體不足**
   ```bash
   # 減少並發數
   export JOBSPY_TEST_CONCURRENCY=2
   ```

### 除錯技巧

```bash
# 詳細輸出
pytest -v -s

# 顯示本地變數
pytest --tb=long

# 進入除錯模式
pytest --pdb

# 執行特定測試
pytest test_all_sites.py::TestAllSitesIntegration::test_individual_site_scraping_mock[linkedin] -v
```

## 📚 參考資源

### 文檔
- [TESTING_STRATEGY.md](../TESTING_STRATEGY.md) - 測試策略
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - 詳細測試指南
- [pytest 官方文檔](https://docs.pytest.org/)

### 範例
- `test_examples.py` - 測試範例和模板
- `test_all_sites.py` - 全網站測試範例
- `fixtures/test_utils.py` - 測試工具範例

## 🤝 貢獻指南

### 新增測試

1. 選擇適當的測試類型和位置
2. 遵循命名慣例 (`test_*.py`)
3. 使用適當的測試標記
4. 包含文檔字串
5. 確保測試可重現

### 測試審查清單

- [ ] 測試名稱清楚描述目的
- [ ] 使用 AAA 模式（Arrange, Act, Assert）
- [ ] 包含適當的斷言
- [ ] 使用適當的測試標記
- [ ] 測試覆蓋邊界情況
- [ ] 包含錯誤處理測試
- [ ] 執行時間合理
- [ ] 清理測試資源

## 📞 支援

如果您在測試過程中遇到問題：

1. 查看本文檔的故障排除部分
2. 檢查測試日誌和錯誤訊息
3. 查看 [GitHub Issues](https://github.com/your-repo/jobspy/issues)
4. 聯繫維護團隊

---

**記住**: 這個測試套件是通用的，可以同時測試所有9個支援的求職網站！🚀