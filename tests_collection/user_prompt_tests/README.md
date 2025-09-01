# 用戶提示測試套件

## 📋 測試概述

本測試套件包含8個不同的用戶提示測試案例，涵蓋全球主要地區的AI相關職位搜尋需求。測試分為三個階段，逐步驗證JobSpy的功能完整性。

## 🗂️ 目錄結構

```
user_prompt_tests/
├── README.md                    # 本說明文件
├── phase1_basic_tests/          # 階段1：基礎功能測試
│   ├── user1_australia_test/    # 澳洲雙城市AI工程師搜尋
│   └── user2_asia_recent_test/  # 台北東京近期職位搜尋
├── phase2_advanced_tests/       # 階段2：進階篩選測試
│   ├── user3_singapore_salary/  # 新加坡香港高薪ML工程師
│   ├── user4_europe_remote/     # 歐洲遠程AI開發者
│   └── user5_usa_skills/        # 美國技能導向數據科學家
└── phase3_specialized_tests/    # 階段3：專業市場測試
    ├── user6_middle_east/       # 中東AI顧問資深職位
    ├── user7_india_fulltime/    # 印度深度學習工程師
    └── user8_canada_academic/   # 加拿大學術導向AI研究
```

## 🎯 測試案例詳情

### Phase 1: 基礎功能測試

#### User1: 澳洲雙城市AI工程師搜尋
- **提示**: "我要找澳洲 Sydney與Melbourne的AI Engineer 工作"
- **目標**: 驗證基本地區搜尋和澳洲本地網站支援
- **預期網站**: Seek, Indeed, LinkedIn
- **預期結果**: ≥10個職位

#### User2: 台北東京近期職位搜尋
- **提示**: "我要找台北與東京有效的AI Engineer 工作，近7日創建的新招募需求"
- **目標**: 測試日期篩選和亞太地區支援
- **預期網站**: LinkedIn, Indeed, Glassdoor
- **預期結果**: ≥5個近期職位

### Phase 2: 進階篩選測試

#### User3: 新加坡香港高薪ML工程師
- **提示**: "尋找新加坡和香港的Machine Learning Engineer職位，薪資範圍80k-150k USD"
- **目標**: 測試薪資篩選功能
- **預期網站**: LinkedIn, Glassdoor, Indeed
- **預期結果**: ≥8個含薪資資訊的職位

#### User4: 歐洲遠程AI開發者
- **提示**: "我想找倫敦和柏林的Senior AI Developer遠程工作機會"
- **目標**: 測試遠程工作篩選
- **預期網站**: LinkedIn, Indeed, Glassdoor
- **預期結果**: ≥6個遠程職位

#### User5: 美國技能導向數據科學家
- **提示**: "搜尋美國舊金山和西雅圖的Data Scientist職位，要求有Python和TensorFlow技能"
- **目標**: 測試技能關鍵字匹配
- **預期網站**: Indeed, LinkedIn, Glassdoor
- **預期結果**: ≥15個技能匹配職位

### Phase 3: 專業市場測試

#### User6: 中東AI顧問資深職位
- **提示**: "尋找杜拜和阿布達比的AI Consultant職位，需要5年以上經驗"
- **目標**: 測試中東地區網站和經驗篩選
- **預期網站**: Bayt, LinkedIn, Glassdoor
- **預期結果**: ≥4個資深職位

#### User7: 印度深度學習工程師
- **提示**: "我要找印度班加羅爾和海德拉巴的Deep Learning Engineer職位，全職工作"
- **目標**: 測試印度本地網站和工作類型篩選
- **預期網站**: Naukri, LinkedIn, Indeed
- **預期結果**: ≥12個全職職位

#### User8: 加拿大學術導向AI研究
- **提示**: "搜尋加拿大多倫多和溫哥華的AI Research Scientist職位，博士學位優先"
- **目標**: 測試學術要求和研究職位
- **預期網站**: Indeed, LinkedIn, Glassdoor
- **預期結果**: ≥6個研究導向職位

## 🚀 執行測試

### 自動執行所有測試
```bash
python run_user_prompt_tests.py --all
```

### 按階段執行測試
```bash
# 執行階段1測試
python run_user_prompt_tests.py --phase 1

# 執行階段2測試
python run_user_prompt_tests.py --phase 2

# 執行階段3測試
python run_user_prompt_tests.py --phase 3
```

### 執行單一測試
```bash
python run_user_prompt_tests.py --test user1
```

## 📊 測試結果分析

每個測試完成後會生成：

1. **原始資料檔案**: `[user_id]_raw_data.json`
2. **統一格式CSV**: `[user_id]_jobs.csv`
3. **測試報告**: `[user_id]_test_report.md`
4. **效能指標**: `[user_id]_performance.json`

## 🎯 成功標準

### 功能性測試
- ✅ 所有指定網站都有回應
- ✅ 達到最低職位數量要求
- ✅ CSV格式符合34欄位標準
- ✅ 資料品質檢查通過

### 效能測試
- ✅ 單次搜尋時間 < 5分鐘
- ✅ 記憶體使用 < 1GB
- ✅ 成功率 > 80%

### 資料品質
- ✅ 職位標題相關性 > 70%
- ✅ 地點匹配準確性 > 90%
- ✅ 重複職位比例 < 10%

## 🔧 故障排除

### 常見問題

1. **網站無回應**
   - 檢查網路連線
   - 確認反偵測機制正常運作
   - 檢查網站是否更新結構

2. **職位數量不足**
   - 調整搜尋關鍵字
   - 擴大地理範圍
   - 檢查日期篩選設定

3. **格式錯誤**
   - 驗證JobPost模型
   - 檢查欄位映射邏輯
   - 確認CSV輸出格式

## 📈 測試報告

完整的測試報告將包含：

- 📊 **執行摘要**: 整體成功率和關鍵指標
- 🌍 **地區覆蓋**: 各地區網站支援情況
- 🔍 **功能驗證**: 篩選和搜尋功能測試結果
- ⚡ **效能分析**: 執行時間和資源使用
- 🐛 **問題追蹤**: 發現的問題和建議改進

---

*此測試套件旨在全面驗證JobSpy在不同地區、不同需求下的職位搜尋能力，確保系統的穩定性和可靠性。*