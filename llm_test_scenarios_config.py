#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試場景配置文件
定義各種測試場景和參數設置，用於比較不同LLM模型的表現

Author: JobSpy Team
Date: 2025-01-27
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TestScenario(Enum):
    """測試場景枚舉"""
    BASIC_FUNCTIONALITY = "basic_functionality"  # 基礎功能測試
    STRESS_TEST = "stress_test"  # 壓力測試
    EDGE_CASES = "edge_cases"  # 邊界案例測試
    MULTILINGUAL = "multilingual"  # 多語言測試
    PERFORMANCE_BENCHMARK = "performance_benchmark"  # 性能基準測試
    CONSISTENCY_CHECK = "consistency_check"  # 一致性檢查
    ROBUSTNESS_TEST = "robustness_test"  # 魯棒性測試


class TestComplexity(Enum):
    """測試複雜度枚舉"""
    SIMPLE = "simple"  # 簡單
    MODERATE = "moderate"  # 中等
    COMPLEX = "complex"  # 複雜
    EXTREME = "extreme"  # 極端


class LanguageType(Enum):
    """語言類型枚舉"""
    CHINESE_TRADITIONAL = "zh-TW"  # 繁體中文
    CHINESE_SIMPLIFIED = "zh-CN"  # 簡體中文
    ENGLISH = "en"  # 英文
    MIXED_CHINESE_ENGLISH = "zh-en"  # 中英混合
    JAPANESE = "ja"  # 日文
    KOREAN = "ko"  # 韓文


@dataclass
class TestScenarioConfig:
    """測試場景配置"""
    scenario: TestScenario
    name: str
    description: str
    test_cases_count: int
    complexity_distribution: Dict[TestComplexity, float]  # 複雜度分布
    language_distribution: Dict[LanguageType, float]  # 語言分布
    expected_accuracy_threshold: float  # 期望準確率閾值
    max_response_time: float  # 最大響應時間（秒）
    retry_count: int  # 重試次數
    timeout: float  # 超時時間（秒）
    tags: List[str]


class LLMTestScenariosConfig:
    """LLM測試場景配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.scenarios = self._create_test_scenarios()
        self.stress_test_queries = self._create_stress_test_queries()
        self.multilingual_queries = self._create_multilingual_queries()
        self.edge_case_queries = self._create_edge_case_queries()
        self.consistency_test_queries = self._create_consistency_test_queries()
        self.robustness_test_queries = self._create_robustness_test_queries()
    
    def _create_test_scenarios(self) -> Dict[TestScenario, TestScenarioConfig]:
        """創建測試場景配置"""
        return {
            TestScenario.BASIC_FUNCTIONALITY: TestScenarioConfig(
                scenario=TestScenario.BASIC_FUNCTIONALITY,
                name="基礎功能測試",
                description="測試LLM在標準求職查詢上的基本表現",
                test_cases_count=50,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.6,
                    TestComplexity.MODERATE: 0.3,
                    TestComplexity.COMPLEX: 0.1,
                    TestComplexity.EXTREME: 0.0
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.7,
                    LanguageType.ENGLISH: 0.2,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.1
                },
                expected_accuracy_threshold=0.85,
                max_response_time=3.0,
                retry_count=2,
                timeout=10.0,
                tags=["基礎", "功能", "標準"]
            ),
            
            TestScenario.STRESS_TEST: TestScenarioConfig(
                scenario=TestScenario.STRESS_TEST,
                name="壓力測試",
                description="測試LLM在高負載和複雜查詢下的表現",
                test_cases_count=100,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.1,
                    TestComplexity.MODERATE: 0.3,
                    TestComplexity.COMPLEX: 0.4,
                    TestComplexity.EXTREME: 0.2
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.4,
                    LanguageType.ENGLISH: 0.3,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.2,
                    LanguageType.JAPANESE: 0.05,
                    LanguageType.KOREAN: 0.05
                },
                expected_accuracy_threshold=0.70,
                max_response_time=8.0,
                retry_count=3,
                timeout=20.0,
                tags=["壓力", "高負載", "複雜"]
            ),
            
            TestScenario.EDGE_CASES: TestScenarioConfig(
                scenario=TestScenario.EDGE_CASES,
                name="邊界案例測試",
                description="測試LLM處理邊界和異常情況的能力",
                test_cases_count=75,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.0,
                    TestComplexity.MODERATE: 0.2,
                    TestComplexity.COMPLEX: 0.5,
                    TestComplexity.EXTREME: 0.3
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.5,
                    LanguageType.ENGLISH: 0.3,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.2
                },
                expected_accuracy_threshold=0.60,
                max_response_time=5.0,
                retry_count=2,
                timeout=15.0,
                tags=["邊界", "異常", "困難"]
            ),
            
            TestScenario.MULTILINGUAL: TestScenarioConfig(
                scenario=TestScenario.MULTILINGUAL,
                name="多語言測試",
                description="測試LLM在不同語言環境下的表現",
                test_cases_count=60,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.4,
                    TestComplexity.MODERATE: 0.4,
                    TestComplexity.COMPLEX: 0.2,
                    TestComplexity.EXTREME: 0.0
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.25,
                    LanguageType.CHINESE_SIMPLIFIED: 0.15,
                    LanguageType.ENGLISH: 0.25,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.15,
                    LanguageType.JAPANESE: 0.1,
                    LanguageType.KOREAN: 0.1
                },
                expected_accuracy_threshold=0.75,
                max_response_time=4.0,
                retry_count=2,
                timeout=12.0,
                tags=["多語言", "國際化", "語言"]
            ),
            
            TestScenario.PERFORMANCE_BENCHMARK: TestScenarioConfig(
                scenario=TestScenario.PERFORMANCE_BENCHMARK,
                name="性能基準測試",
                description="測試LLM的響應速度和資源使用效率",
                test_cases_count=200,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.5,
                    TestComplexity.MODERATE: 0.3,
                    TestComplexity.COMPLEX: 0.15,
                    TestComplexity.EXTREME: 0.05
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.6,
                    LanguageType.ENGLISH: 0.3,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.1
                },
                expected_accuracy_threshold=0.80,
                max_response_time=2.0,
                retry_count=1,
                timeout=8.0,
                tags=["性能", "速度", "效率"]
            ),
            
            TestScenario.CONSISTENCY_CHECK: TestScenarioConfig(
                scenario=TestScenario.CONSISTENCY_CHECK,
                name="一致性檢查",
                description="測試LLM對相同或相似查詢的一致性表現",
                test_cases_count=80,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.3,
                    TestComplexity.MODERATE: 0.5,
                    TestComplexity.COMPLEX: 0.2,
                    TestComplexity.EXTREME: 0.0
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.7,
                    LanguageType.ENGLISH: 0.2,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.1
                },
                expected_accuracy_threshold=0.85,
                max_response_time=3.0,
                retry_count=5,  # 多次重試以測試一致性
                timeout=10.0,
                tags=["一致性", "穩定性", "重複"]
            ),
            
            TestScenario.ROBUSTNESS_TEST: TestScenarioConfig(
                scenario=TestScenario.ROBUSTNESS_TEST,
                name="魯棒性測試",
                description="測試LLM對噪音、錯誤輸入和異常情況的處理能力",
                test_cases_count=90,
                complexity_distribution={
                    TestComplexity.SIMPLE: 0.1,
                    TestComplexity.MODERATE: 0.2,
                    TestComplexity.COMPLEX: 0.4,
                    TestComplexity.EXTREME: 0.3
                },
                language_distribution={
                    LanguageType.CHINESE_TRADITIONAL: 0.4,
                    LanguageType.ENGLISH: 0.3,
                    LanguageType.MIXED_CHINESE_ENGLISH: 0.3
                },
                expected_accuracy_threshold=0.65,
                max_response_time=6.0,
                retry_count=2,
                timeout=15.0,
                tags=["魯棒性", "噪音", "異常"]
            )
        }
    
    def _create_stress_test_queries(self) -> List[Dict[str, Any]]:
        """創建壓力測試查詢"""
        return [
            {
                "id": "stress_001",
                "query": "我需要找一個在台北市信義區的全端工程師職位，要求熟悉React、Vue.js、Node.js、Python、Django、PostgreSQL、MongoDB、Redis、Docker、Kubernetes、AWS、GCP，薪資範圍80k-150k，可以遠程工作，公司規模100-500人，有股票選擇權，工作環境開放創新，有學習成長機會，團隊氛圍良好，加班不超過每週10小時，有彈性工時，提供健康保險和年終獎金",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["超長查詢", "多條件", "詳細需求"]
            },
            {
                "id": "stress_002",
                "query": "Looking for a senior software engineer position in Taipei with expertise in machine learning, deep learning, computer vision, natural language processing, TensorFlow, PyTorch, scikit-learn, pandas, numpy, matplotlib, seaborn, Jupyter, Git, Docker, Kubernetes, AWS, GCP, Azure, Python, R, SQL, NoSQL, big data, data pipeline, ETL, Apache Spark, Hadoop, Kafka, microservices architecture, RESTful APIs, GraphQL, CI/CD, DevOps, Agile, Scrum, remote work friendly, competitive salary, stock options, health insurance, flexible working hours",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.ENGLISH,
                "expected_job_related": True,
                "tags": ["英文長查詢", "AI/ML", "多技術棧"]
            },
            {
                "id": "stress_003",
                "query": "想轉職到科技業當product manager，目前在傳統製造業做了5年的專案管理，有PMP證照，熟悉Agile和Scrum，會一點Python和SQL，對AI和區塊鏈很有興趣，希望能找到有mentor制度的公司，薪資期望比現在高30%，地點不限但希望在台北或新竹，公司文化要開放包容，有diversity and inclusion的政策",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["轉職", "產品經理", "職涯發展"]
            },
            {
                "id": "stress_004",
                "query": "剛從美國回台灣的software engineer，在矽谷工作了3年，主要做backend development，熟悉Go、Java、Python、microservices、cloud native、Kubernetes、Docker，想找台灣的外商公司或有國際業務的本土公司，希望能用英文工作，薪資期望年薪200萬以上，有股票或期權，工作內容要有挑戰性，團隊要有國際化背景",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["海歸", "高薪", "國際化"]
            },
            {
                "id": "stress_005",
                "query": "我是一個自學轉職的前端工程師，沒有CS背景，之前是做平面設計的，自學了HTML、CSS、JavaScript、React、Vue.js，做了一些side project放在GitHub上，想找junior或entry level的前端職位，不介意薪資低一點，主要是想累積經驗，希望公司願意培養新人，有code review和技術分享的文化",
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["自學", "轉職", "新手"]
            }
        ]
    
    def _create_multilingual_queries(self) -> List[Dict[str, Any]]:
        """創建多語言測試查詢"""
        return [
            {
                "id": "multi_001",
                "query": "我想找software engineer的工作在台北",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.MIXED_CHINESE_ENGLISH,
                "expected_job_related": True,
                "tags": ["中英混合", "簡單"]
            },
            {
                "id": "multi_002",
                "query": "Looking for Python developer job in 台北市",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.MIXED_CHINESE_ENGLISH,
                "expected_job_related": True,
                "tags": ["英中混合", "程式語言"]
            },
            {
                "id": "multi_003",
                "query": "我需要一個full-stack engineer的position，要會React和Node.js",
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.MIXED_CHINESE_ENGLISH,
                "expected_job_related": True,
                "tags": ["混合語言", "全端"]
            },
            {
                "id": "multi_004",
                "query": "ソフトウェアエンジニアの仕事を探しています",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.JAPANESE,
                "expected_job_related": True,
                "tags": ["日文", "軟體工程師"]
            },
            {
                "id": "multi_005",
                "query": "소프트웨어 개발자 채용 정보를 찾고 있습니다",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.KOREAN,
                "expected_job_related": True,
                "tags": ["韓文", "開發者"]
            },
            {
                "id": "multi_006",
                "query": "我想找一个Python工程师的工作",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_SIMPLIFIED,
                "expected_job_related": True,
                "tags": ["簡體中文", "Python"]
            }
        ]
    
    def _create_edge_case_queries(self) -> List[Dict[str, Any]]:
        """創建邊界案例查詢"""
        return [
            {
                "id": "edge_001",
                "query": "",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": False,
                "tags": ["空字串", "邊界"]
            },
            {
                "id": "edge_002",
                "query": "   ",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": False,
                "tags": ["空白字元", "邊界"]
            },
            {
                "id": "edge_003",
                "query": "a",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.ENGLISH,
                "expected_job_related": False,
                "tags": ["單字元", "極短"]
            },
            {
                "id": "edge_004",
                "query": "工作" * 100,  # 重複"工作"100次
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["重複字詞", "超長"]
            },
            {
                "id": "edge_005",
                "query": "!@#$%^&*()_+-=[]{}|;':,.<>?",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.ENGLISH,
                "expected_job_related": False,
                "tags": ["特殊符號", "無意義"]
            },
            {
                "id": "edge_006",
                "query": "123456789",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.ENGLISH,
                "expected_job_related": False,
                "tags": ["純數字", "無意義"]
            },
            {
                "id": "edge_007",
                "query": "工作工作工作工作工作",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["重複關鍵字", "模糊"]
            },
            {
                "id": "edge_008",
                "query": "我不想找工作",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": False,
                "tags": ["否定", "反向"]
            },
            {
                "id": "edge_009",
                "query": "不是不想找工作，只是不知道找什麼工作",
                "complexity": TestComplexity.EXTREME,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["雙重否定", "複雜邏輯"]
            },
            {
                "id": "edge_010",
                "query": "工作？？？？？",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["問號", "不確定"]
            }
        ]
    
    def _create_consistency_test_queries(self) -> List[Dict[str, Any]]:
        """創建一致性測試查詢（相似查詢的不同表達方式）"""
        return [
            # 組1：Python工程師查詢的不同表達
            {
                "id": "consist_001_a",
                "query": "Python工程師 台北",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "group": "python_taipei",
                "tags": ["一致性", "Python", "台北"]
            },
            {
                "id": "consist_001_b",
                "query": "尋找台北的Python開發者職位",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "group": "python_taipei",
                "tags": ["一致性", "Python", "台北"]
            },
            {
                "id": "consist_001_c",
                "query": "我想在台北找Python程式設計師的工作",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "group": "python_taipei",
                "tags": ["一致性", "Python", "台北"]
            },
            
            # 組2：前端工程師查詢的不同表達
            {
                "id": "consist_002_a",
                "query": "前端工程師 React",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "group": "frontend_react",
                "tags": ["一致性", "前端", "React"]
            },
            {
                "id": "consist_002_b",
                "query": "Frontend Developer with React experience",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.ENGLISH,
                "expected_job_related": True,
                "group": "frontend_react",
                "tags": ["一致性", "前端", "React"]
            },
            {
                "id": "consist_002_c",
                "query": "我想找會React的前端開發者工作",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "group": "frontend_react",
                "tags": ["一致性", "前端", "React"]
            },
            
            # 組3：非求職查詢的不同表達
            {
                "id": "consist_003_a",
                "query": "今天天氣如何",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": False,
                "group": "weather",
                "tags": ["一致性", "天氣", "非求職"]
            },
            {
                "id": "consist_003_b",
                "query": "What's the weather like today",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.ENGLISH,
                "expected_job_related": False,
                "group": "weather",
                "tags": ["一致性", "天氣", "非求職"]
            },
            {
                "id": "consist_003_c",
                "query": "請問現在的天氣狀況",
                "complexity": TestComplexity.SIMPLE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": False,
                "group": "weather",
                "tags": ["一致性", "天氣", "非求職"]
            }
        ]
    
    def _create_robustness_test_queries(self) -> List[Dict[str, Any]]:
        """創建魯棒性測試查詢（包含噪音和錯誤）"""
        return [
            {
                "id": "robust_001",
                "query": "pythonn工程師 台北市",  # 拼寫錯誤
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["拼寫錯誤", "魯棒性"]
            },
            {
                "id": "robust_002",
                "query": "我想找工作，但是不知道找什麼，可能是程式設計師吧，或者其他的也可以",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["模糊意圖", "不確定"]
            },
            {
                "id": "robust_003",
                "query": "軟體工程師 台北 薪水 高 公司 好 環境 棒 同事 nice 老闆 不錯",
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["片段詞彙", "不完整句子"]
            },
            {
                "id": "robust_004",
                "query": "我想找工作😭😭😭 好難找啊🤔 有沒有推薦的💼",
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["表情符號", "情緒表達"]
            },
            {
                "id": "robust_005",
                "query": "PYTHON ENGINEER TAIPEI SALARY 100K REMOTE WORK",  # 全大寫
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.ENGLISH,
                "expected_job_related": True,
                "tags": ["全大寫", "格式異常"]
            },
            {
                "id": "robust_006",
                "query": "python engineer taipei salary 100k remote work",  # 全小寫
                "complexity": TestComplexity.MODERATE,
                "language": LanguageType.ENGLISH,
                "expected_job_related": True,
                "tags": ["全小寫", "格式異常"]
            },
            {
                "id": "robust_007",
                "query": "我想找工作，呃，就是那種，你知道的，寫程式的那種工作",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["口語化", "不正式"]
            },
            {
                "id": "robust_008",
                "query": "工作工作工作找工作找工作程式設計師程式設計師",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["重複詞彙", "無標點"]
            },
            {
                "id": "robust_009",
                "query": "我想找工作但是我不確定我想要什麼樣的工作也許是工程師也許不是",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["長句無標點", "猶豫不決"]
            },
            {
                "id": "robust_010",
                "query": "找工作 vs 不找工作 這是個問題",
                "complexity": TestComplexity.COMPLEX,
                "language": LanguageType.CHINESE_TRADITIONAL,
                "expected_job_related": True,
                "tags": ["哲學式", "對比"]
            }
        ]
    
    def get_scenario_config(self, scenario: TestScenario) -> Optional[TestScenarioConfig]:
        """獲取指定場景的配置"""
        return self.scenarios.get(scenario)
    
    def get_all_scenarios(self) -> Dict[TestScenario, TestScenarioConfig]:
        """獲取所有場景配置"""
        return self.scenarios
    
    def get_queries_by_scenario(self, scenario: TestScenario) -> List[Dict[str, Any]]:
        """根據場景獲取對應的測試查詢"""
        scenario_queries = {
            TestScenario.STRESS_TEST: self.stress_test_queries,
            TestScenario.MULTILINGUAL: self.multilingual_queries,
            TestScenario.EDGE_CASES: self.edge_case_queries,
            TestScenario.CONSISTENCY_CHECK: self.consistency_test_queries,
            TestScenario.ROBUSTNESS_TEST: self.robustness_test_queries
        }
        
        return scenario_queries.get(scenario, [])
    
    def get_scenario_summary(self) -> Dict[str, Any]:
        """獲取場景摘要信息"""
        summary = {
            "total_scenarios": len(self.scenarios),
            "scenarios": {},
            "total_queries": 0
        }
        
        for scenario, config in self.scenarios.items():
            queries = self.get_queries_by_scenario(scenario)
            query_count = len(queries)
            
            summary["scenarios"][scenario.value] = {
                "name": config.name,
                "description": config.description,
                "expected_test_cases": config.test_cases_count,
                "actual_queries": query_count,
                "complexity_distribution": {k.value: v for k, v in config.complexity_distribution.items()},
                "language_distribution": {k.value: v for k, v in config.language_distribution.items()},
                "expected_accuracy_threshold": config.expected_accuracy_threshold,
                "max_response_time": config.max_response_time,
                "tags": config.tags
            }
            
            summary["total_queries"] += query_count
        
        return summary


def main():
    """主函數 - 展示配置信息"""
    print("🔧 LLM測試場景配置")
    print("=" * 50)
    
    config_manager = LLMTestScenariosConfig()
    summary = config_manager.get_scenario_summary()
    
    print(f"📊 總場景數: {summary['total_scenarios']}")
    print(f"📝 總查詢數: {summary['total_queries']}")
    print()
    
    for scenario_key, scenario_info in summary["scenarios"].items():
        print(f"🎯 {scenario_info['name']} ({scenario_key})")
        print(f"   描述: {scenario_info['description']}")
        print(f"   預期測試案例: {scenario_info['expected_test_cases']}")
        print(f"   實際查詢數: {scenario_info['actual_queries']}")
        print(f"   準確率閾值: {scenario_info['expected_accuracy_threshold']:.1%}")
        print(f"   最大響應時間: {scenario_info['max_response_time']}s")
        print(f"   標籤: {', '.join(scenario_info['tags'])}")
        print()


if __name__ == "__main__":
    main()