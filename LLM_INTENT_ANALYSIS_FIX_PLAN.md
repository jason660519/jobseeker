# LLM意圖分析過度嚴格問題修復方案

## 📊 問題分析

### 當前問題
根據測試結果，LLM意圖分析系統存在**過度嚴格**的問題，導致明顯的求職相關查詢被錯誤拒絕：

**失敗案例:**
- "資料科學家" @ "高雄" → 被拒絕
- "Data Analyst" @ "Taichung" → 被拒絕  
- "UI/UX設計師" @ "台中" → 被拒絕

**錯誤訊息:**
```json
{
  "decision_analysis": {
    "confidence": 1.0,
    "reasoning": "查詢不是求職相關，拒絕處理",
    "strategy": "reject_query"
  },
  "error": "抱歉，我是AI助手，僅能協助您處理求職相關問題，無法進行一般聊天。"
}
```

### 根本原因分析

#### 1. 模擬LLM邏輯過於簡化
**位置:** `jobseeker/llm_intent_analyzer.py:440-550`

**問題:** `_mock_llm_call` 方法使用簡單的關鍵字匹配，缺乏語義理解：

```python
# 當前邏輯 - 過於嚴格
if any(keyword in query_lower for keyword in ['天氣', '電影', '音樂', '食譜', '烹飪']):
    return {
        "is_job_related": False,
        "intent_type": "non_job_related",
        "confidence": 0.9,
        "reasoning": "查詢內容與求職無關，涉及日常生活話題"
    }
```

**缺陷:**
- 只檢查明顯的非求職關鍵字
- 沒有檢查求職相關關鍵字
- 默認拒絕不在白名單中的查詢

#### 2. 求職關鍵字詞典不完整
**問題:** 缺少常見的職位名稱和技能關鍵字：
- "資料科學家" 未被識別
- "Data Analyst" 未被識別
- "UI/UX設計師" 未被識別

#### 3. 決策引擎過度依賴is_job_related標記
**位置:** `jobseeker/intelligent_decision_engine.py:150-155`

```python
if not intent_result.is_job_related:
    return self._create_rejection_decision(intent_result)
```

**問題:** 一旦標記為非求職相關，立即拒絕，沒有二次驗證機制。

## 🔧 修復方案

### 方案1: 增強模擬LLM的求職關鍵字識別 (立即修復)

#### 1.1 擴展求職關鍵字詞典

```python
# 新增完整的求職關鍵字詞典
JOB_KEYWORDS = {
    # 職位名稱 - 中文
    'job_titles_zh': [
        '工程師', '開發者', '程式設計師', '軟體工程師', '前端工程師', '後端工程師',
        '全端工程師', '資料科學家', '數據科學家', '資料分析師', '數據分析師',
        '產品經理', '專案經理', '設計師', 'UI設計師', 'UX設計師', 'UI/UX設計師',
        '測試工程師', '品質工程師', 'DevOps工程師', '系統管理員', '網路工程師',
        '資安工程師', '機器學習工程師', 'AI工程師', '人工智慧工程師',
        '業務', '銷售', '行銷', '客服', '人資', '會計', '財務', '法務'
    ],
    
    # 職位名稱 - 英文
    'job_titles_en': [
        'engineer', 'developer', 'programmer', 'software engineer', 'frontend engineer',
        'backend engineer', 'fullstack engineer', 'data scientist', 'data analyst',
        'product manager', 'project manager', 'designer', 'ui designer', 'ux designer',
        'qa engineer', 'test engineer', 'devops engineer', 'system administrator',
        'network engineer', 'security engineer', 'ml engineer', 'ai engineer',
        'sales', 'marketing', 'customer service', 'hr', 'accountant', 'finance', 'legal'
    ],
    
    # 技能關鍵字
    'skills': [
        'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
        'machine learning', 'deep learning', 'ai', 'ml', 'tensorflow', 'pytorch',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp', 'git', 'linux', 'windows', 'macos'
    ],
    
    # 求職相關動詞
    'job_verbs': [
        '找', '尋找', '搜尋', '應徵', '求職', '工作', '職位', '職缺',
        'find', 'search', 'looking for', 'apply', 'job', 'position', 'career'
    ],
    
    # 地點關鍵字
    'locations': [
        '台北', '新北', '桃園', '台中', '台南', '高雄', '新竹', '基隆',
        'taipei', 'taichung', 'kaohsiung', 'sydney', 'melbourne', 'singapore',
        '遠程', '遠端', 'remote', 'wfh', 'work from home'
    ]
}
```

#### 1.2 改進意圖判斷邏輯

```python
def _enhanced_job_intent_detection(self, query: str) -> Dict[str, Any]:
    """增強的求職意圖檢測"""
    query_lower = query.lower().strip()
    
    # 1. 明確的非求職查詢 (高置信度拒絕)
    non_job_keywords = [
        '天氣', '電影', '音樂', '食譜', '烹飪', '遊戲', '娛樂', '新聞',
        'weather', 'movie', 'music', 'recipe', 'cooking', 'game', 'entertainment'
    ]
    
    if any(keyword in query_lower for keyword in non_job_keywords):
        # 但要檢查是否同時包含求職關鍵字
        job_score = self._calculate_job_relevance_score(query_lower)
        if job_score < 0.3:  # 低於30%認為是非求職
            return {
                "is_job_related": False,
                "intent_type": "non_job_related",
                "confidence": 0.9,
                "reasoning": f"查詢包含非求職關鍵字且求職相關性得分僅{job_score:.2f}"
            }
    
    # 2. 計算求職相關性得分
    job_score = self._calculate_job_relevance_score(query_lower)
    
    # 3. 基於得分判斷
    if job_score >= 0.6:  # 高置信度求職查詢
        return self._create_job_related_response(query, job_score, "高")
    elif job_score >= 0.3:  # 中等置信度
        return self._create_job_related_response(query, job_score, "中")
    elif job_score >= 0.1:  # 低置信度，但仍可能是求職
        return self._create_job_related_response(query, job_score, "低")
    else:  # 極低置信度，拒絕
        return {
            "is_job_related": False,
            "intent_type": "unclear",
            "confidence": 0.8,
            "reasoning": f"查詢求職相關性得分過低({job_score:.2f})，建議明確說明求職需求"
        }

def _calculate_job_relevance_score(self, query_lower: str) -> float:
    """計算求職相關性得分"""
    score = 0.0
    
    # 職位名稱匹配 (權重: 0.4)
    for title in JOB_KEYWORDS['job_titles_zh'] + JOB_KEYWORDS['job_titles_en']:
        if title.lower() in query_lower:
            score += 0.4
            break
    
    # 技能關鍵字匹配 (權重: 0.3)
    skill_matches = sum(1 for skill in JOB_KEYWORDS['skills'] 
                       if skill.lower() in query_lower)
    if skill_matches > 0:
        score += min(0.3, skill_matches * 0.1)
    
    # 求職動詞匹配 (權重: 0.2)
    for verb in JOB_KEYWORDS['job_verbs']:
        if verb.lower() in query_lower:
            score += 0.2
            break
    
    # 地點關鍵字匹配 (權重: 0.1)
    for location in JOB_KEYWORDS['locations']:
        if location.lower() in query_lower:
            score += 0.1
            break
    
    return min(score, 1.0)
```

### 方案2: 添加二次驗證機制

#### 2.1 在決策引擎中添加覆蓋邏輯

```python
def make_decision_with_override(self, intent_result: Any, 
                               user_context: Optional[Dict[str, Any]] = None) -> DecisionResult:
    """帶有覆蓋機制的決策"""
    
    # 原始決策
    if not intent_result.is_job_related:
        # 二次驗證：檢查是否為誤判
        override_result = self._check_job_intent_override(intent_result)
        if override_result:
            self.logger.info(f"覆蓋原始決策：{override_result['reason']}")
            # 修改意圖結果
            intent_result.is_job_related = True
            intent_result.confidence = override_result['confidence']
            intent_result.llm_reasoning += f" [覆蓋: {override_result['reason']}]"
        else:
            return self._create_rejection_decision(intent_result)
    
    # 繼續正常決策流程...

def _check_job_intent_override(self, intent_result: Any) -> Optional[Dict[str, Any]]:
    """檢查是否需要覆蓋非求職判斷"""
    if hasattr(intent_result, 'structured_intent') and intent_result.structured_intent:
        intent = intent_result.structured_intent
        
        # 如果提取到了職位、技能或地點，很可能是求職查詢
        if (intent.job_titles or intent.skills or intent.locations):
            return {
                'reason': '檢測到職位/技能/地點信息，覆蓋為求職查詢',
                'confidence': 0.7
            }
    
    return None
```

### 方案3: 改進錯誤訊息

#### 3.1 提供更友善和具體的拒絕訊息

```python
def _create_rejection_decision(self, intent_result: Any) -> DecisionResult:
    """創建改進的拒絕決策"""
    
    # 分析拒絕原因
    if intent_result.confidence > 0.8:
        # 高置信度非求職查詢
        message = "抱歉，我專門協助求職相關問題。您可以嘗試搜索：\n" + \
                 "• '軟體工程師 台北'\n" + \
                 "• 'Python開發者 薪資'\n" + \
                 "• '前端工程師 遠程工作'"
    else:
        # 低置信度或不明確查詢
        message = "請提供更具體的求職需求，例如：\n" + \
                 "• 職位名稱 + 地點\n" + \
                 "• 技能關鍵字 + 工作類型\n" + \
                 "• 行業 + 經驗要求"
    
    return DecisionResult(
        strategy=ProcessingStrategy.REJECT_QUERY,
        platform_selection_mode=PlatformSelectionMode.FALLBACK,
        recommended_platforms=[],
        search_parameters={},
        priority_score=0.0,
        confidence=intent_result.confidence,
        reasoning=f"查詢非求職相關 (置信度: {intent_result.confidence:.2f})",
        fallback_options=[],
        estimated_results=0,
        processing_hints={'rejection_message': message}
    )
```

## 🚀 實施計劃

### 階段1: 立即修復 (優先級: 高)

1. **修復模擬LLM邏輯**
   - 擴展求職關鍵字詞典
   - 實施求職相關性評分算法
   - 測試失敗案例

2. **改進錯誤訊息**
   - 提供具體的搜索建議
   - 區分高/低置信度拒絕

### 階段2: 增強驗證 (優先級: 中)

1. **添加二次驗證機制**
   - 在決策引擎中實施覆蓋邏輯
   - 記錄覆蓋統計

2. **優化決策邏輯**
   - 調整置信度閾值
   - 增加邊界案例處理

### 階段3: 長期優化 (優先級: 低)

1. **集成真實LLM**
   - 配置OpenAI/Anthropic API
   - 優化提示詞模板

2. **機器學習優化**
   - 收集用戶反饋
   - 持續改進關鍵字詞典

## 📊 預期效果

### 修復後預期結果

**之前失敗的案例應該成功:**
- "資料科學家" @ "高雄" → ✅ 成功 (得分: 0.4 職位 + 0.1 地點 = 0.5)
- "Data Analyst" @ "Taichung" → ✅ 成功 (得分: 0.4 職位 + 0.1 地點 = 0.5)
- "UI/UX設計師" @ "台中" → ✅ 成功 (得分: 0.4 職位 + 0.1 地點 = 0.5)

**成功率提升:**
- 當前: 64.3% (9/14)
- 預期: 85%+ (12+/14)

**誤拒率降低:**
- 當前: 35.7% (5/14 失敗)
- 預期: <15% (2/14 失敗)

## 🔍 測試驗證

### 測試案例

```python
# 應該成功的案例
test_cases_should_pass = [
    "資料科學家 高雄",
    "Data Analyst Taichung", 
    "UI/UX設計師 台中",
    "Python工程師",
    "前端開發 台北",
    "機器學習 遠程"
]

# 應該拒絕的案例
test_cases_should_reject = [
    "今天天氣如何",
    "推薦一部電影",
    "晚餐吃什麼"
]

# 邊界案例
test_cases_boundary = [
    "工作",  # 太模糊，但可能是求職
    "台北",  # 只有地點
    "薪水",  # 可能與求職相關
]
```

### 驗證指標

1. **準確率**: 正確分類的比例
2. **召回率**: 求職查詢被正確識別的比例  
3. **精確率**: 被識別為求職的查詢中真正是求職的比例
4. **F1分數**: 精確率和召回率的調和平均

## 📝 實施檢查清單

- [ ] 擴展求職關鍵字詞典
- [ ] 實施求職相關性評分算法
- [ ] 修改`_mock_llm_call`方法
- [ ] 添加二次驗證機制
- [ ] 改進錯誤訊息
- [ ] 運行測試案例驗證
- [ ] 更新文檔
- [ ] 部署到生產環境

---

**修復完成後，LLM意圖分析系統將能夠:**
1. ✅ 正確識別常見職位名稱
2. ✅ 支援中英文求職查詢
3. ✅ 提供友善的錯誤訊息
4. ✅ 降低誤拒率至15%以下
5. ✅ 提升整體搜索成功率至85%以上