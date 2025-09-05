#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進階LLM性能分析工具
提供深入的模型性能分析、比較和可視化功能

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import asyncio
import statistics
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer, LLMProvider
from jobseeker.llm_config import LLMConfigManager
from llm_test_scenarios_config import LLMTestScenariosConfig, TestScenario, TestComplexity, LanguageType


@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    response_time_mean: float
    response_time_std: float
    response_time_p95: float
    confidence_mean: float
    confidence_std: float
    error_rate: float
    consistency_score: float
    robustness_score: float


@dataclass
class ModelComparison:
    """模型比較結果"""
    model_a: str
    model_b: str
    accuracy_diff: float
    speed_ratio: float
    consistency_diff: float
    statistical_significance: bool
    p_value: float
    effect_size: float
    recommendation: str


@dataclass
class AnalysisInsight:
    """分析洞察"""
    category: str
    insight_type: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    recommendations: List[str]


class AdvancedLLMPerformanceAnalyzer:
    """進階LLM性能分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.config_manager = LLMConfigManager()
        self.scenario_config = LLMTestScenariosConfig()
        self.test_results: Dict[str, List[Dict[str, Any]]] = {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.model_comparisons: List[ModelComparison] = []
        self.insights: List[AnalysisInsight] = []
        
        # 設置matplotlib中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
    
    def run_comprehensive_analysis(self, providers: Optional[List[LLMProvider]] = None, 
                                 scenarios: Optional[List[TestScenario]] = None) -> Dict[str, Any]:
        """運行全面的性能分析"""
        print("🔬 開始進階LLM性能分析")
        print("=" * 60)
        
        # 確定要測試的提供商和場景
        if providers is None:
            providers = self.config_manager.get_available_providers()
        
        if scenarios is None:
            scenarios = list(self.scenario_config.get_all_scenarios().keys())
        
        print(f"📋 分析提供商: {[p.value for p in providers]}")
        print(f"🎯 分析場景: {[s.value for s in scenarios]}")
        
        # 收集測試數據
        self._collect_test_data(providers, scenarios)
        
        # 計算性能指標
        self._calculate_performance_metrics()
        
        # 進行模型比較
        self._perform_model_comparisons()
        
        # 生成分析洞察
        self._generate_insights()
        
        # 創建可視化報告
        self._create_visualizations()
        
        # 生成綜合報告
        comprehensive_report = self._generate_comprehensive_report()
        
        # 保存結果
        self._save_analysis_results(comprehensive_report)
        
        return comprehensive_report
    
    def _collect_test_data(self, providers: List[LLMProvider], scenarios: List[TestScenario]) -> None:
        """收集測試數據"""
        print("\n📊 收集測試數據...")
        
        for provider in providers:
            print(f"\n🔄 測試提供商: {provider.value}")
            
            try:
                analyzer = LLMIntentAnalyzer(provider=provider)
                provider_results = []
                
                for scenario in scenarios:
                    print(f"   📝 場景: {scenario.value}")
                    
                    # 獲取場景的測試查詢
                    queries = self.scenario_config.get_queries_by_scenario(scenario)
                    scenario_config = self.scenario_config.get_scenario_config(scenario)
                    
                    for query_data in queries:
                        # 執行多次測試以評估一致性
                        retry_count = scenario_config.retry_count if scenario_config else 3
                        
                        for attempt in range(retry_count):
                            result = self._execute_single_test(
                                analyzer, query_data, provider.value, scenario.value, attempt
                            )
                            provider_results.append(result)
                
                self.test_results[provider.value] = provider_results
                print(f"   ✅ 完成 {len(provider_results)} 個測試")
                
            except Exception as e:
                print(f"   ❌ 測試失敗: {str(e)}")
                continue
    
    def _execute_single_test(self, analyzer: LLMIntentAnalyzer, query_data: Dict[str, Any], 
                           provider: str, scenario: str, attempt: int) -> Dict[str, Any]:
        """執行單個測試"""
        start_time = time.time()
        
        try:
            # 執行意圖分析
            result = analyzer.analyze_intent(query_data["query"])
            
            response_time = time.time() - start_time
            
            # 構建測試結果
            test_result = {
                "provider": provider,
                "scenario": scenario,
                "query_id": query_data["id"],
                "query": query_data["query"],
                "attempt": attempt,
                "expected_job_related": query_data["expected_job_related"],
                "actual_job_related": result.is_job_related,
                "confidence": result.confidence,
                "response_time": response_time,
                "intent_type": result.intent_type.value if hasattr(result.intent_type, 'value') else str(result.intent_type),
                "reasoning": getattr(result, 'llm_reasoning', ''),
                "complexity": query_data.get("complexity", TestComplexity.SIMPLE).value,
                "language": query_data.get("language", LanguageType.CHINESE_TRADITIONAL).value,
                "tags": query_data.get("tags", []),
                "group": query_data.get("group", None),
                "timestamp": datetime.now().isoformat(),
                "error": None
            }
            
            # 提取結構化意圖
            if result.structured_intent and result.is_job_related:
                intent = result.structured_intent
                test_result["structured_intent"] = {
                    "job_titles": getattr(intent, 'job_titles', []),
                    "skills": getattr(intent, 'skills', []),
                    "locations": getattr(intent, 'locations', []),
                    "salary_range": getattr(intent, 'salary_range', None),
                    "work_type": getattr(intent, 'work_type', None)
                }
            else:
                test_result["structured_intent"] = {}
            
            return test_result
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "provider": provider,
                "scenario": scenario,
                "query_id": query_data["id"],
                "query": query_data["query"],
                "attempt": attempt,
                "expected_job_related": query_data["expected_job_related"],
                "actual_job_related": False,
                "confidence": 0.0,
                "response_time": response_time,
                "intent_type": "error",
                "reasoning": "",
                "complexity": query_data.get("complexity", TestComplexity.SIMPLE).value,
                "language": query_data.get("language", LanguageType.CHINESE_TRADITIONAL).value,
                "tags": query_data.get("tags", []),
                "group": query_data.get("group", None),
                "timestamp": datetime.now().isoformat(),
                "structured_intent": {},
                "error": str(e)
            }
    
    def _calculate_performance_metrics(self) -> None:
        """計算詳細的性能指標"""
        print("\n📈 計算性能指標...")
        
        for provider, results in self.test_results.items():
            if not results:
                continue
            
            # 過濾有效結果
            valid_results = [r for r in results if r["error"] is None]
            
            if not valid_results:
                continue
            
            # 計算基本指標
            y_true = [r["expected_job_related"] for r in valid_results]
            y_pred = [r["actual_job_related"] for r in valid_results]
            
            # 準確率
            accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
            
            # 精確率、召回率、F1分數
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # 響應時間統計
            response_times = [r["response_time"] for r in valid_results]
            response_time_mean = statistics.mean(response_times)
            response_time_std = statistics.stdev(response_times) if len(response_times) > 1 else 0
            response_time_p95 = np.percentile(response_times, 95)
            
            # 置信度統計
            confidences = [r["confidence"] for r in valid_results]
            confidence_mean = statistics.mean(confidences)
            confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0
            
            # 錯誤率
            error_count = len([r for r in results if r["error"] is not None])
            error_rate = error_count / len(results)
            
            # 一致性分數（同一查詢多次執行的一致性）
            consistency_score = self._calculate_consistency_score(valid_results)
            
            # 魯棒性分數（對噪音和異常輸入的處理能力）
            robustness_score = self._calculate_robustness_score(valid_results)
            
            self.performance_metrics[provider] = PerformanceMetrics(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                response_time_mean=response_time_mean,
                response_time_std=response_time_std,
                response_time_p95=response_time_p95,
                confidence_mean=confidence_mean,
                confidence_std=confidence_std,
                error_rate=error_rate,
                consistency_score=consistency_score,
                robustness_score=robustness_score
            )
            
            print(f"   ✅ {provider}: 準確率={accuracy:.3f}, F1={f1_score:.3f}, 響應時間={response_time_mean:.2f}s")
    
    def _calculate_consistency_score(self, results: List[Dict[str, Any]]) -> float:
        """計算一致性分數"""
        # 按查詢ID分組
        query_groups = defaultdict(list)
        for result in results:
            if result.get("group"):
                query_groups[result["group"]].append(result)
        
        if not query_groups:
            return 1.0  # 沒有重複查詢，假設完全一致
        
        consistency_scores = []
        
        for group, group_results in query_groups.items():
            if len(group_results) < 2:
                continue
            
            # 計算該組內的一致性
            predictions = [r["actual_job_related"] for r in group_results]
            confidences = [r["confidence"] for r in group_results]
            
            # 預測一致性
            prediction_consistency = len(set(predictions)) == 1
            
            # 置信度一致性（標準差越小越一致）
            confidence_consistency = 1.0 - (statistics.stdev(confidences) if len(confidences) > 1 else 0)
            
            group_consistency = (prediction_consistency * 0.7 + confidence_consistency * 0.3)
            consistency_scores.append(group_consistency)
        
        return statistics.mean(consistency_scores) if consistency_scores else 1.0
    
    def _calculate_robustness_score(self, results: List[Dict[str, Any]]) -> float:
        """計算魯棒性分數"""
        # 找出魯棒性測試的結果
        robustness_results = [r for r in results if "robustness" in r.get("scenario", "").lower()]
        
        if not robustness_results:
            return 0.5  # 沒有魯棒性測試，給予中等分數
        
        # 計算在噪音和異常輸入下的準確率
        correct_predictions = sum(1 for r in robustness_results 
                                if r["expected_job_related"] == r["actual_job_related"])
        
        return correct_predictions / len(robustness_results)
    
    def _perform_model_comparisons(self) -> None:
        """進行模型間的統計比較"""
        print("\n🔍 進行模型比較分析...")
        
        providers = list(self.performance_metrics.keys())
        
        for i in range(len(providers)):
            for j in range(i + 1, len(providers)):
                model_a, model_b = providers[i], providers[j]
                
                comparison = self._compare_two_models(model_a, model_b)
                self.model_comparisons.append(comparison)
                
                print(f"   📊 {model_a} vs {model_b}: 準確率差異={comparison.accuracy_diff:.3f}, 速度比={comparison.speed_ratio:.2f}")
    
    def _compare_two_models(self, model_a: str, model_b: str) -> ModelComparison:
        """比較兩個模型的性能"""
        metrics_a = self.performance_metrics[model_a]
        metrics_b = self.performance_metrics[model_b]
        
        results_a = [r for r in self.test_results[model_a] if r["error"] is None]
        results_b = [r for r in self.test_results[model_b] if r["error"] is None]
        
        # 準確率差異
        accuracy_diff = metrics_a.accuracy - metrics_b.accuracy
        
        # 速度比較（model_a相對於model_b的速度）
        speed_ratio = metrics_b.response_time_mean / metrics_a.response_time_mean
        
        # 一致性差異
        consistency_diff = metrics_a.consistency_score - metrics_b.consistency_score
        
        # 統計顯著性檢驗（使用準確率）
        accuracies_a = [1 if r["expected_job_related"] == r["actual_job_related"] else 0 for r in results_a]
        accuracies_b = [1 if r["expected_job_related"] == r["actual_job_related"] else 0 for r in results_b]
        
        if len(accuracies_a) > 1 and len(accuracies_b) > 1:
            t_stat, p_value = stats.ttest_ind(accuracies_a, accuracies_b)
            statistical_significance = p_value < 0.05
            
            # 效應大小（Cohen's d）
            pooled_std = np.sqrt(((len(accuracies_a) - 1) * np.var(accuracies_a, ddof=1) + 
                                 (len(accuracies_b) - 1) * np.var(accuracies_b, ddof=1)) / 
                                (len(accuracies_a) + len(accuracies_b) - 2))
            effect_size = (np.mean(accuracies_a) - np.mean(accuracies_b)) / pooled_std if pooled_std > 0 else 0
        else:
            p_value = 1.0
            statistical_significance = False
            effect_size = 0.0
        
        # 生成建議
        recommendation = self._generate_model_recommendation(model_a, model_b, metrics_a, metrics_b, 
                                                           accuracy_diff, speed_ratio, statistical_significance)
        
        return ModelComparison(
            model_a=model_a,
            model_b=model_b,
            accuracy_diff=accuracy_diff,
            speed_ratio=speed_ratio,
            consistency_diff=consistency_diff,
            statistical_significance=statistical_significance,
            p_value=p_value,
            effect_size=effect_size,
            recommendation=recommendation
        )
    
    def _generate_model_recommendation(self, model_a: str, model_b: str, 
                                     metrics_a: PerformanceMetrics, metrics_b: PerformanceMetrics,
                                     accuracy_diff: float, speed_ratio: float, 
                                     statistical_significance: bool) -> str:
        """生成模型選擇建議"""
        if not statistical_significance:
            if speed_ratio > 1.2:
                return f"{model_a}速度更快，準確率無顯著差異，推薦用於即時應用"
            elif speed_ratio < 0.8:
                return f"{model_b}速度更快，準確率無顯著差異，推薦用於即時應用"
            else:
                return "兩模型性能相近，可根據其他因素選擇"
        
        if accuracy_diff > 0.05:
            return f"{model_a}準確率顯著更高，推薦用於準確性要求高的場景"
        elif accuracy_diff < -0.05:
            return f"{model_b}準確率顯著更高，推薦用於準確性要求高的場景"
        else:
            if speed_ratio > 1.2:
                return f"準確率相近，{model_a}速度更快，推薦用於即時應用"
            elif speed_ratio < 0.8:
                return f"準確率相近，{model_b}速度更快，推薦用於即時應用"
            else:
                return "兩模型綜合性能相近"
    
    def _generate_insights(self) -> None:
        """生成分析洞察"""
        print("\n💡 生成分析洞察...")
        
        # 性能趨勢洞察
        self._analyze_performance_trends()
        
        # 場景特定洞察
        self._analyze_scenario_performance()
        
        # 語言和複雜度洞察
        self._analyze_language_complexity_impact()
        
        # 異常檢測洞察
        self._detect_performance_anomalies()
        
        print(f"   ✅ 生成了 {len(self.insights)} 個洞察")
    
    def _analyze_performance_trends(self) -> None:
        """分析性能趨勢"""
        if len(self.performance_metrics) < 2:
            return
        
        # 找出最佳和最差性能的模型
        best_accuracy = max(self.performance_metrics.items(), key=lambda x: x[1].accuracy)
        worst_accuracy = min(self.performance_metrics.items(), key=lambda x: x[1].accuracy)
        
        fastest_model = min(self.performance_metrics.items(), key=lambda x: x[1].response_time_mean)
        slowest_model = max(self.performance_metrics.items(), key=lambda x: x[1].response_time_mean)
        
        # 準確率洞察
        accuracy_gap = best_accuracy[1].accuracy - worst_accuracy[1].accuracy
        if accuracy_gap > 0.1:
            self.insights.append(AnalysisInsight(
                category="性能差異",
                insight_type="準確率差距",
                description=f"模型間準確率差距較大({accuracy_gap:.1%})，{best_accuracy[0]}表現最佳({best_accuracy[1].accuracy:.1%})，{worst_accuracy[0]}需要改進({worst_accuracy[1].accuracy:.1%})",
                confidence=0.9,
                supporting_data={
                    "best_model": best_accuracy[0],
                    "best_accuracy": best_accuracy[1].accuracy,
                    "worst_model": worst_accuracy[0],
                    "worst_accuracy": worst_accuracy[1].accuracy,
                    "gap": accuracy_gap
                },
                recommendations=[
                    f"優先使用{best_accuracy[0]}進行生產部署",
                    f"檢查{worst_accuracy[0]}的配置和提示詞設計",
                    "考慮對表現較差的模型進行微調或參數優化"
                ]
            ))
        
        # 速度洞察
        speed_ratio = slowest_model[1].response_time_mean / fastest_model[1].response_time_mean
        if speed_ratio > 2.0:
            self.insights.append(AnalysisInsight(
                category="性能差異",
                insight_type="響應速度差距",
                description=f"模型間響應速度差距顯著，{fastest_model[0]}比{slowest_model[0]}快{speed_ratio:.1f}倍",
                confidence=0.85,
                supporting_data={
                    "fastest_model": fastest_model[0],
                    "fastest_time": fastest_model[1].response_time_mean,
                    "slowest_model": slowest_model[0],
                    "slowest_time": slowest_model[1].response_time_mean,
                    "speed_ratio": speed_ratio
                },
                recommendations=[
                    f"即時應用場景優先選擇{fastest_model[0]}",
                    f"檢查{slowest_model[0]}的網路連接和API配置",
                    "考慮使用快取機制減少重複查詢的響應時間"
                ]
            ))
    
    def _analyze_scenario_performance(self) -> None:
        """分析場景特定性能"""
        scenario_performance = defaultdict(lambda: defaultdict(list))
        
        # 按場景和提供商分組統計
        for provider, results in self.test_results.items():
            for result in results:
                if result["error"] is None:
                    scenario = result["scenario"]
                    accuracy = 1 if result["expected_job_related"] == result["actual_job_related"] else 0
                    scenario_performance[scenario][provider].append(accuracy)
        
        # 分析每個場景的表現
        for scenario, provider_results in scenario_performance.items():
            if len(provider_results) < 2:
                continue
            
            # 計算各提供商在該場景的平均準確率
            scenario_accuracies = {}
            for provider, accuracies in provider_results.items():
                scenario_accuracies[provider] = statistics.mean(accuracies)
            
            # 找出該場景的最佳和最差表現
            best_provider = max(scenario_accuracies.items(), key=lambda x: x[1])
            worst_provider = min(scenario_accuracies.items(), key=lambda x: x[1])
            
            performance_gap = best_provider[1] - worst_provider[1]
            
            if performance_gap > 0.15:  # 15%以上的差距
                self.insights.append(AnalysisInsight(
                    category="場景特定性能",
                    insight_type=f"{scenario}場景分析",
                    description=f"在{scenario}場景中，{best_provider[0]}表現最佳({best_provider[1]:.1%})，{worst_provider[0]}表現較差({worst_provider[1]:.1%})",
                    confidence=0.8,
                    supporting_data={
                        "scenario": scenario,
                        "best_provider": best_provider[0],
                        "best_accuracy": best_provider[1],
                        "worst_provider": worst_provider[0],
                        "worst_accuracy": worst_provider[1],
                        "all_accuracies": scenario_accuracies
                    },
                    recommendations=[
                        f"在{scenario}場景中優先使用{best_provider[0]}",
                        f"分析{best_provider[0]}在該場景的成功因素",
                        f"針對{scenario}場景優化{worst_provider[0]}的表現"
                    ]
                ))
    
    def _analyze_language_complexity_impact(self) -> None:
        """分析語言和複雜度對性能的影響"""
        # 按語言分析
        language_performance = defaultdict(lambda: defaultdict(list))
        complexity_performance = defaultdict(lambda: defaultdict(list))
        
        for provider, results in self.test_results.items():
            for result in results:
                if result["error"] is None:
                    language = result["language"]
                    complexity = result["complexity"]
                    accuracy = 1 if result["expected_job_related"] == result["actual_job_related"] else 0
                    
                    language_performance[language][provider].append(accuracy)
                    complexity_performance[complexity][provider].append(accuracy)
        
        # 語言影響分析
        for language, provider_results in language_performance.items():
            if len(provider_results) < 2:
                continue
            
            language_accuracies = {}
            for provider, accuracies in provider_results.items():
                language_accuracies[provider] = statistics.mean(accuracies)
            
            # 檢查是否有顯著的語言偏好
            accuracy_values = list(language_accuracies.values())
            if len(accuracy_values) > 1:
                accuracy_std = statistics.stdev(accuracy_values)
                if accuracy_std > 0.1:  # 標準差大於10%
                    best_provider = max(language_accuracies.items(), key=lambda x: x[1])
                    
                    self.insights.append(AnalysisInsight(
                        category="語言特定性能",
                        insight_type=f"{language}語言分析",
                        description=f"在{language}語言測試中，模型表現差異較大，{best_provider[0]}表現最佳({best_provider[1]:.1%})",
                        confidence=0.75,
                        supporting_data={
                            "language": language,
                            "provider_accuracies": language_accuracies,
                            "std_dev": accuracy_std
                        },
                        recommendations=[
                            f"處理{language}語言查詢時優先使用{best_provider[0]}",
                            "考慮針對特定語言進行模型優化",
                            "分析語言特定的提示詞設計"
                        ]
                    ))
    
    def _detect_performance_anomalies(self) -> None:
        """檢測性能異常"""
        for provider, metrics in self.performance_metrics.items():
            anomalies = []
            
            # 檢測異常高的錯誤率
            if metrics.error_rate > 0.1:  # 10%以上錯誤率
                anomalies.append(f"錯誤率過高({metrics.error_rate:.1%})")
            
            # 檢測異常慢的響應時間
            if metrics.response_time_mean > 10.0:  # 超過10秒
                anomalies.append(f"響應時間過慢({metrics.response_time_mean:.1f}秒)")
            
            # 檢測異常低的一致性
            if metrics.consistency_score < 0.7:  # 一致性低於70%
                anomalies.append(f"一致性較低({metrics.consistency_score:.1%})")
            
            # 檢測置信度異常
            if metrics.confidence_std > 0.3:  # 置信度標準差過大
                anomalies.append(f"置信度不穩定(標準差={metrics.confidence_std:.2f})")
            
            if anomalies:
                self.insights.append(AnalysisInsight(
                    category="性能異常",
                    insight_type=f"{provider}異常檢測",
                    description=f"{provider}存在性能異常: {', '.join(anomalies)}",
                    confidence=0.9,
                    supporting_data={
                        "provider": provider,
                        "anomalies": anomalies,
                        "metrics": asdict(metrics)
                    },
                    recommendations=[
                        "檢查API配置和網路連接",
                        "驗證模型參數設置",
                        "考慮更換或優化該提供商的使用",
                        "增加重試機制和錯誤處理"
                    ]
                ))
    
    def _create_visualizations(self) -> None:
        """創建可視化圖表"""
        print("\n📊 創建可視化圖表...")
        
        if not self.performance_metrics:
            print("   ⚠️ 沒有性能數據，跳過可視化")
            return
        
        # 設置圖表樣式
        plt.style.use('seaborn-v0_8')
        
        # 創建性能比較圖
        self._create_performance_comparison_chart()
        
        # 創建響應時間分布圖
        self._create_response_time_distribution()
        
        # 創建場景性能熱力圖
        self._create_scenario_heatmap()
        
        # 創建置信度vs準確率散點圖
        self._create_confidence_accuracy_scatter()
        
        print("   ✅ 可視化圖表已生成")
    
    def _create_performance_comparison_chart(self) -> None:
        """創建性能比較圖表"""
        providers = list(self.performance_metrics.keys())
        metrics_names = ['準確率', 'F1分數', '一致性', '魯棒性']
        
        # 準備數據
        data = []
        for provider in providers:
            metrics = self.performance_metrics[provider]
            data.append([
                metrics.accuracy,
                metrics.f1_score,
                metrics.consistency_score,
                metrics.robustness_score
            ])
        
        # 創建雷達圖
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False).tolist()
        angles += angles[:1]  # 閉合圖形
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(providers)))
        
        for i, (provider, provider_data) in enumerate(zip(providers, data)):
            values = provider_data + provider_data[:1]  # 閉合數據
            ax.plot(angles, values, 'o-', linewidth=2, label=provider, color=colors[i])
            ax.fill(angles, values, alpha=0.25, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics_names)
        ax.set_ylim(0, 1)
        ax.set_title('LLM模型性能比較雷達圖', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig('llm_performance_radar.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_response_time_distribution(self) -> None:
        """創建響應時間分布圖"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for provider, results in self.test_results.items():
            response_times = [r["response_time"] for r in results if r["error"] is None]
            if response_times:
                ax.hist(response_times, bins=30, alpha=0.7, label=provider, density=True)
        
        ax.set_xlabel('響應時間 (秒)')
        ax.set_ylabel('密度')
        ax.set_title('LLM模型響應時間分布', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('llm_response_time_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_scenario_heatmap(self) -> None:
        """創建場景性能熱力圖"""
        # 準備數據
        scenario_data = defaultdict(lambda: defaultdict(list))
        
        for provider, results in self.test_results.items():
            for result in results:
                if result["error"] is None:
                    scenario = result["scenario"]
                    accuracy = 1 if result["expected_job_related"] == result["actual_job_related"] else 0
                    scenario_data[scenario][provider].append(accuracy)
        
        # 計算平均準確率
        scenarios = list(scenario_data.keys())
        providers = list(self.performance_metrics.keys())
        
        heatmap_data = np.zeros((len(scenarios), len(providers)))
        
        for i, scenario in enumerate(scenarios):
            for j, provider in enumerate(providers):
                if provider in scenario_data[scenario]:
                    heatmap_data[i, j] = statistics.mean(scenario_data[scenario][provider])
                else:
                    heatmap_data[i, j] = np.nan
        
        # 創建熱力圖
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        # 設置標籤
        ax.set_xticks(range(len(providers)))
        ax.set_xticklabels(providers, rotation=45, ha='right')
        ax.set_yticks(range(len(scenarios)))
        ax.set_yticklabels(scenarios)
        
        # 添加數值標註
        for i in range(len(scenarios)):
            for j in range(len(providers)):
                if not np.isnan(heatmap_data[i, j]):
                    text = ax.text(j, i, f'{heatmap_data[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontweight='bold')
        
        ax.set_title('各場景下的模型準確率熱力圖', fontsize=14, fontweight='bold')
        
        # 添加顏色條
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('準確率', rotation=270, labelpad=20)
        
        plt.tight_layout()
        plt.savefig('llm_scenario_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_confidence_accuracy_scatter(self) -> None:
        """創建置信度vs準確率散點圖"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.test_results)))
        
        for i, (provider, results) in enumerate(self.test_results.items()):
            confidences = []
            accuracies = []
            
            for result in results:
                if result["error"] is None:
                    confidences.append(result["confidence"])
                    accuracy = 1 if result["expected_job_related"] == result["actual_job_related"] else 0
                    accuracies.append(accuracy)
            
            if confidences and accuracies:
                ax.scatter(confidences, accuracies, alpha=0.6, label=provider, 
                          color=colors[i], s=50)
        
        ax.set_xlabel('置信度')
        ax.set_ylabel('準確率 (0=錯誤, 1=正確)')
        ax.set_title('置信度 vs 準確率散點圖', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.1, 1.1)
        
        plt.tight_layout()
        plt.savefig('llm_confidence_accuracy_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成綜合分析報告"""
        return {
            "analysis_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_providers": len(self.performance_metrics),
                "total_tests": sum(len(results) for results in self.test_results.values()),
                "total_insights": len(self.insights),
                "analysis_duration": "完整分析"
            },
            "performance_metrics": {
                provider: asdict(metrics) for provider, metrics in self.performance_metrics.items()
            },
            "model_comparisons": [asdict(comp) for comp in self.model_comparisons],
            "insights": [asdict(insight) for insight in self.insights],
            "recommendations": self._generate_final_recommendations(),
            "raw_test_data": self.test_results
        }
    
    def _generate_final_recommendations(self) -> Dict[str, Any]:
        """生成最終建議"""
        if not self.performance_metrics:
            return {}
        
        # 找出各方面的最佳模型
        best_accuracy = max(self.performance_metrics.items(), key=lambda x: x[1].accuracy)
        fastest_model = min(self.performance_metrics.items(), key=lambda x: x[1].response_time_mean)
        most_consistent = max(self.performance_metrics.items(), key=lambda x: x[1].consistency_score)
        most_robust = max(self.performance_metrics.items(), key=lambda x: x[1].robustness_score)
        
        # 計算綜合分數
        overall_scores = {}
        for provider, metrics in self.performance_metrics.items():
            # 綜合分數 = 準確率*0.3 + (1-標準化響應時間)*0.2 + 一致性*0.25 + 魯棒性*0.25
            normalized_time = 1 - min(metrics.response_time_mean / 10.0, 1.0)  # 假設10秒為最差
            overall_score = (
                metrics.accuracy * 0.3 +
                normalized_time * 0.2 +
                metrics.consistency_score * 0.25 +
                metrics.robustness_score * 0.25
            )
            overall_scores[provider] = overall_score
        
        best_overall = max(overall_scores.items(), key=lambda x: x[1])
        
        return {
            "best_overall": {
                "provider": best_overall[0],
                "score": best_overall[1],
                "description": f"{best_overall[0]}在綜合評估中表現最佳"
            },
            "best_accuracy": {
                "provider": best_accuracy[0],
                "accuracy": best_accuracy[1].accuracy,
                "description": f"{best_accuracy[0]}準確率最高({best_accuracy[1].accuracy:.1%})"
            },
            "fastest": {
                "provider": fastest_model[0],
                "response_time": fastest_model[1].response_time_mean,
                "description": f"{fastest_model[0]}響應速度最快({fastest_model[1].response_time_mean:.2f}秒)"
            },
            "most_consistent": {
                "provider": most_consistent[0],
                "consistency": most_consistent[1].consistency_score,
                "description": f"{most_consistent[0]}一致性最高({most_consistent[1].consistency_score:.1%})"
            },
            "most_robust": {
                "provider": most_robust[0],
                "robustness": most_robust[1].robustness_score,
                "description": f"{most_robust[0]}魯棒性最強({most_robust[1].robustness_score:.1%})"
            },
            "usage_scenarios": {
                "生產環境": best_overall[0],
                "即時應用": fastest_model[0],
                "高準確率需求": best_accuracy[0],
                "穩定性要求": most_consistent[0],
                "複雜環境": most_robust[0]
            },
            "key_insights": [insight.description for insight in self.insights[:5]]  # 前5個重要洞察
        }
    
    def _save_analysis_results(self, report: Dict[str, Any]) -> None:
        """保存分析結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存完整報告
        full_report_filename = f"advanced_llm_analysis_full_{timestamp}.json"
        with open(full_report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存摘要報告
        summary_report = {
            "analysis_summary": report["analysis_summary"],
            "performance_metrics": report["performance_metrics"],
            "recommendations": report["recommendations"],
            "key_insights": report["insights"][:10]  # 前10個洞察
        }
        
        summary_filename = f"advanced_llm_analysis_summary_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析結果已保存:")
        print(f"   完整報告: {full_report_filename}")
        print(f"   摘要報告: {summary_filename}")
        print(f"   可視化圖表: llm_*.png")
    
    def print_analysis_summary(self) -> None:
        """打印分析摘要"""
        if not self.performance_metrics:
            print("❌ 沒有分析結果可顯示")
            return
        
        print("\n📊 進階LLM性能分析摘要")
        print("=" * 60)
        
        # 基本統計
        total_tests = sum(len(results) for results in self.test_results.values())
        print(f"\n📋 分析概況:")
        print(f"   分析模型數量: {len(self.performance_metrics)}")
        print(f"   總測試次數: {total_tests}")
        print(f"   生成洞察數: {len(self.insights)}")
        print(f"   模型比較數: {len(self.model_comparisons)}")
        
        # 性能排名
        print(f"\n🏆 性能排名:")
        
        # 準確率排名
        accuracy_ranking = sorted(self.performance_metrics.items(), 
                                 key=lambda x: x[1].accuracy, reverse=True)
        print(f"\n   📈 準確率排名:")
        for i, (provider, metrics) in enumerate(accuracy_ranking, 1):
            print(f"      {i}. {provider}: {metrics.accuracy:.1%} (F1: {metrics.f1_score:.3f})")
        
        # 速度排名
        speed_ranking = sorted(self.performance_metrics.items(), 
                              key=lambda x: x[1].response_time_mean)
        print(f"\n   ⚡ 速度排名:")
        for i, (provider, metrics) in enumerate(speed_ranking, 1):
            print(f"      {i}. {provider}: {metrics.response_time_mean:.2f}s (P95: {metrics.response_time_p95:.2f}s)")
        
        # 一致性排名
        consistency_ranking = sorted(self.performance_metrics.items(), 
                                    key=lambda x: x[1].consistency_score, reverse=True)
        print(f"\n   🎯 一致性排名:")
        for i, (provider, metrics) in enumerate(consistency_ranking, 1):
            print(f"      {i}. {provider}: {metrics.consistency_score:.1%}")
        
        # 重要洞察
        print(f"\n💡 重要洞察:")
        for i, insight in enumerate(self.insights[:5], 1):
            print(f"   {i}. [{insight.category}] {insight.description}")
        
        # 模型比較
        if self.model_comparisons:
            print(f"\n🔍 關鍵比較:")
            for comp in self.model_comparisons[:3]:
                significance = "顯著" if comp.statistical_significance else "不顯著"
                print(f"   • {comp.model_a} vs {comp.model_b}: {comp.recommendation} (差異{significance})")
        
        print("\n" + "=" * 60)


def main():
    """主函數"""
    print("🔬 進階LLM性能分析工具")
    print("=" * 50)
    
    # 創建分析器
    analyzer = AdvancedLLMPerformanceAnalyzer()
    
    # 獲取可用的提供商
    available_providers = analyzer.config_manager.get_available_providers()
    
    if not available_providers:
        print("❌ 沒有可用的LLM提供商，請檢查配置")
        return
    
    print(f"📋 發現 {len(available_providers)} 個可用提供商: {[p.value for p in available_providers]}")
    
    # 獲取可用的測試場景
    available_scenarios = list(analyzer.scenario_config.get_all_scenarios().keys())
    print(f"🎯 可用測試場景: {[s.value for s in available_scenarios]}")
    
    # 詢問用戶選擇
    print("\n請選擇分析模式:")
    print("1. 快速分析 (基礎功能測試)")
    print("2. 標準分析 (多場景測試)")
    print("3. 全面分析 (所有場景)")
    print("4. 自定義分析")
    
    choice = input("\n請輸入選擇 (1-4): ").strip()
    
    if choice == "1":
        test_scenarios = [TestScenario.BASIC_FUNCTIONALITY]
    elif choice == "2":
        test_scenarios = [TestScenario.BASIC_FUNCTIONALITY, TestScenario.EDGE_CASES, TestScenario.MULTILINGUAL]
    elif choice == "3":
        test_scenarios = available_scenarios
    elif choice == "4":
        print("\n可用場景:")
        for i, scenario in enumerate(available_scenarios, 1):
            config = analyzer.scenario_config.get_scenario_config(scenario)
            print(f"  {i}. {config.name} - {config.description}")
        
        selected_indices = input("\n請輸入要測試的場景編號（用逗號分隔）: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
            test_scenarios = [available_scenarios[i] for i in indices if 0 <= i < len(available_scenarios)]
        except (ValueError, IndexError):
            print("❌ 輸入格式錯誤，使用標準分析")
            test_scenarios = [TestScenario.BASIC_FUNCTIONALITY, TestScenario.EDGE_CASES]
    else:
        print("❌ 無效選擇，使用快速分析")
        test_scenarios = [TestScenario.BASIC_FUNCTIONALITY]
    
    print(f"\n🎯 將執行以下場景測試: {[s.value for s in test_scenarios]}")
    
    # 運行分析
    try:
        print("\n🚀 開始分析...")
        comprehensive_report = analyzer.run_comprehensive_analysis(
            providers=available_providers,
            scenarios=test_scenarios
        )
        
        if comprehensive_report:
            # 顯示摘要報告
            analyzer.print_analysis_summary()
            
            print("\n✅ 分析完成！")
            print("📄 詳細報告和可視化圖表已保存")
        else:
            print("❌ 分析失敗，沒有生成報告")
            
    except KeyboardInterrupt:
        print("\n⚠️ 分析被用戶中斷")
    except Exception as e:
        print(f"\n❌ 分析過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()