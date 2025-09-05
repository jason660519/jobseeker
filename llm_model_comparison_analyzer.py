#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM模型比較分析器
深入分析和比較不同LLM模型在各種測試場景下的表現差異

Author: JobSpy Team
Date: 2025-01-27
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict, Counter
import statistics
from scipy import stats
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class ComparisonDimension(Enum):
    """比較維度"""
    ACCURACY = "accuracy"  # 準確性
    SPEED = "speed"  # 速度
    CONSISTENCY = "consistency"  # 一致性
    ROBUSTNESS = "robustness"  # 魯棒性
    COST_EFFICIENCY = "cost_efficiency"  # 成本效率
    LANGUAGE_SUPPORT = "language_support"  # 語言支持
    COMPLEXITY_HANDLING = "complexity_handling"  # 複雜度處理
    ERROR_RATE = "error_rate"  # 錯誤率


class AnalysisType(Enum):
    """分析類型"""
    STATISTICAL = "statistical"  # 統計分析
    COMPARATIVE = "comparative"  # 比較分析
    TREND = "trend"  # 趨勢分析
    CORRELATION = "correlation"  # 相關性分析
    PERFORMANCE = "performance"  # 性能分析
    QUALITY = "quality"  # 質量分析


@dataclass
class ModelPerformance:
    """模型性能數據"""
    model_name: str
    provider: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    timeout_tests: int
    accuracy_score: float
    avg_response_time: float
    median_response_time: float
    consistency_score: float
    robustness_score: float
    cost_per_request: float
    error_rate: float
    confidence_scores: List[float] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    category_performance: Dict[str, float] = field(default_factory=dict)
    complexity_performance: Dict[str, float] = field(default_factory=dict)
    language_performance: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """比較結果"""
    dimension: ComparisonDimension
    models: List[str]
    scores: List[float]
    rankings: List[int]
    statistical_significance: Dict[str, float]
    effect_size: float
    confidence_interval: Tuple[float, float]
    p_value: float
    interpretation: str


@dataclass
class AnalysisInsight:
    """分析洞察"""
    insight_type: str
    title: str
    description: str
    evidence: Dict[str, Any]
    confidence: float
    recommendations: List[str]
    impact_level: str  # high, medium, low


class LLMModelComparisonAnalyzer:
    """LLM模型比較分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.model_performances = {}
        self.comparison_results = {}
        self.analysis_insights = []
        self.raw_data = []
        
    def load_test_results(self, results_files: List[str]) -> None:
        """載入測試結果"""
        print(f"📂 載入測試結果文件...")
        
        for file_path in results_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.raw_data.append(data)
                print(f"   ✅ 載入 {file_path}")
                
            except Exception as e:
                print(f"   ❌ 載入失敗 {file_path}: {str(e)}")
        
        print(f"   📊 總共載入 {len(self.raw_data)} 個結果文件")
    
    def extract_model_performances(self) -> None:
        """提取模型性能數據"""
        print("🔍 提取模型性能數據...")
        
        for data in self.raw_data:
            if "batches" not in data:
                continue
            
            # 按模型分組執行結果
            model_executions = defaultdict(list)
            
            for batch in data["batches"]:
                for execution in batch.get("executions", []):
                    provider = execution.get("provider", "unknown")
                    model_executions[provider].append(execution)
            
            # 計算每個模型的性能指標
            for provider, executions in model_executions.items():
                performance = self._calculate_model_performance(provider, executions)
                
                if provider in self.model_performances:
                    # 合併性能數據
                    self._merge_performance_data(self.model_performances[provider], performance)
                else:
                    self.model_performances[provider] = performance
        
        print(f"   ✅ 提取了 {len(self.model_performances)} 個模型的性能數據")
    
    def _calculate_model_performance(self, provider: str, executions: List[Dict[str, Any]]) -> ModelPerformance:
        """計算模型性能"""
        total_tests = len(executions)
        successful_tests = len([e for e in executions if e.get("status") == "completed"])
        failed_tests = len([e for e in executions if e.get("status") == "failed"])
        timeout_tests = len([e for e in executions if e.get("status") == "timeout"])
        
        # 響應時間統計
        response_times = [e.get("duration", 0) for e in executions if e.get("duration") is not None]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        median_response_time = statistics.median(response_times) if response_times else 0
        
        # 置信度分數
        confidence_scores = []
        for execution in executions:
            result = execution.get("result", {})
            if isinstance(result, dict) and "confidence" in result:
                confidence_scores.append(result["confidence"])
        
        # 準確性分析
        accuracy_score = self._calculate_accuracy(executions)
        
        # 一致性分析
        consistency_score = self._calculate_consistency(executions)
        
        # 魯棒性分析
        robustness_score = self._calculate_robustness(executions)
        
        # 類別性能
        category_performance = self._calculate_category_performance(executions)
        
        # 複雜度性能
        complexity_performance = self._calculate_complexity_performance(executions)
        
        # 語言性能
        language_performance = self._calculate_language_performance(executions)
        
        return ModelPerformance(
            model_name=provider,
            provider=provider,
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            timeout_tests=timeout_tests,
            accuracy_score=accuracy_score,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            consistency_score=consistency_score,
            robustness_score=robustness_score,
            cost_per_request=self._estimate_cost(provider),
            error_rate=failed_tests / total_tests if total_tests > 0 else 0,
            confidence_scores=confidence_scores,
            response_times=response_times,
            category_performance=category_performance,
            complexity_performance=complexity_performance,
            language_performance=language_performance
        )
    
    def _calculate_accuracy(self, executions: List[Dict[str, Any]]) -> float:
        """計算準確性"""
        correct_predictions = 0
        total_predictions = 0
        
        for execution in executions:
            if execution.get("status") != "completed":
                continue
            
            result = execution.get("result", {})
            metadata = execution.get("metadata", {})
            
            predicted_intent = result.get("intent", "unknown")
            expected_intent = metadata.get("expected_intent", "unknown")
            
            if expected_intent != "unknown":
                total_predictions += 1
                if predicted_intent == expected_intent:
                    correct_predictions += 1
        
        return correct_predictions / total_predictions if total_predictions > 0 else 0
    
    def _calculate_consistency(self, executions: List[Dict[str, Any]]) -> float:
        """計算一致性"""
        # 計算相同查詢的預測一致性
        query_predictions = defaultdict(list)
        
        for execution in executions:
            if execution.get("status") != "completed":
                continue
            
            test_case_id = execution.get("test_case_id", "")
            result = execution.get("result", {})
            intent = result.get("intent", "unknown")
            
            query_predictions[test_case_id].append(intent)
        
        consistency_scores = []
        for predictions in query_predictions.values():
            if len(predictions) > 1:
                # 計算最常見預測的比例
                most_common = Counter(predictions).most_common(1)[0][1]
                consistency = most_common / len(predictions)
                consistency_scores.append(consistency)
        
        return statistics.mean(consistency_scores) if consistency_scores else 1.0
    
    def _calculate_robustness(self, executions: List[Dict[str, Any]]) -> float:
        """計算魯棒性"""
        # 基於錯誤率和超時率計算魯棒性
        total_tests = len(executions)
        failed_tests = len([e for e in executions if e.get("status") == "failed"])
        timeout_tests = len([e for e in executions if e.get("status") == "timeout"])
        
        failure_rate = (failed_tests + timeout_tests) / total_tests if total_tests > 0 else 0
        robustness = 1.0 - failure_rate
        
        # 考慮響應時間的穩定性
        response_times = [e.get("duration", 0) for e in executions if e.get("duration") is not None]
        if len(response_times) > 1:
            cv = statistics.stdev(response_times) / statistics.mean(response_times)
            time_stability = max(0, 1 - cv)  # 變異係數越小，穩定性越高
            robustness = (robustness + time_stability) / 2
        
        return robustness
    
    def _calculate_category_performance(self, executions: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算類別性能"""
        category_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        
        for execution in executions:
            if execution.get("status") != "completed":
                continue
            
            metadata = execution.get("metadata", {})
            category = metadata.get("test_case_category", "unknown")
            
            result = execution.get("result", {})
            predicted_intent = result.get("intent", "unknown")
            expected_intent = metadata.get("expected_intent", "unknown")
            
            category_stats[category]["total"] += 1
            if predicted_intent == expected_intent and expected_intent != "unknown":
                category_stats[category]["correct"] += 1
        
        category_performance = {}
        for category, stats in category_stats.items():
            if stats["total"] > 0:
                category_performance[category] = stats["correct"] / stats["total"]
        
        return category_performance
    
    def _calculate_complexity_performance(self, executions: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算複雜度性能"""
        complexity_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        
        for execution in executions:
            if execution.get("status") != "completed":
                continue
            
            metadata = execution.get("metadata", {})
            complexity = metadata.get("test_case_complexity", "unknown")
            
            result = execution.get("result", {})
            predicted_intent = result.get("intent", "unknown")
            expected_intent = metadata.get("expected_intent", "unknown")
            
            complexity_stats[complexity]["total"] += 1
            if predicted_intent == expected_intent and expected_intent != "unknown":
                complexity_stats[complexity]["correct"] += 1
        
        complexity_performance = {}
        for complexity, stats in complexity_stats.items():
            if stats["total"] > 0:
                complexity_performance[complexity] = stats["correct"] / stats["total"]
        
        return complexity_performance
    
    def _calculate_language_performance(self, executions: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算語言性能"""
        language_stats = defaultdict(lambda: {"success": 0, "total": 0})
        
        for execution in executions:
            metadata = execution.get("metadata", {})
            # 這裡需要從測試案例中獲取語言信息
            # 暫時使用簡單的語言檢測
            language = "unknown"  # 實際應該從測試案例數據中獲取
            
            language_stats[language]["total"] += 1
            if execution.get("status") == "completed":
                language_stats[language]["success"] += 1
        
        language_performance = {}
        for language, stats in language_stats.items():
            if stats["total"] > 0:
                language_performance[language] = stats["success"] / stats["total"]
        
        return language_performance
    
    def _estimate_cost(self, provider: str) -> float:
        """估算成本"""
        # 簡化的成本估算
        cost_estimates = {
            "openai": 0.002,
            "anthropic": 0.003,
            "google": 0.001,
            "azure_openai": 0.002,
            "huggingface": 0.0001,
            "cohere": 0.0015,
            "ollama": 0.0
        }
        
        return cost_estimates.get(provider.lower(), 0.001)
    
    def _merge_performance_data(self, existing: ModelPerformance, new: ModelPerformance) -> None:
        """合併性能數據"""
        # 合併基本統計
        total_tests = existing.total_tests + new.total_tests
        existing.successful_tests += new.successful_tests
        existing.failed_tests += new.failed_tests
        existing.timeout_tests += new.timeout_tests
        
        # 重新計算平均值
        existing.accuracy_score = (existing.accuracy_score * existing.total_tests + 
                                 new.accuracy_score * new.total_tests) / total_tests
        
        existing.avg_response_time = (existing.avg_response_time * existing.total_tests + 
                                    new.avg_response_time * new.total_tests) / total_tests
        
        existing.total_tests = total_tests
        
        # 合併列表數據
        existing.confidence_scores.extend(new.confidence_scores)
        existing.response_times.extend(new.response_times)
        
        # 重新計算中位數
        if existing.response_times:
            existing.median_response_time = statistics.median(existing.response_times)
    
    def perform_comparative_analysis(self) -> None:
        """執行比較分析"""
        print("📊 執行比較分析...")
        
        if len(self.model_performances) < 2:
            print("   ⚠️ 需要至少2個模型進行比較")
            return
        
        models = list(self.model_performances.keys())
        
        # 各維度比較
        for dimension in ComparisonDimension:
            result = self._compare_dimension(dimension, models)
            self.comparison_results[dimension] = result
            print(f"   ✅ 完成 {dimension.value} 比較")
        
        print(f"   📈 完成 {len(self.comparison_results)} 個維度的比較分析")
    
    def _compare_dimension(self, dimension: ComparisonDimension, models: List[str]) -> ComparisonResult:
        """比較特定維度"""
        scores = []
        
        for model in models:
            performance = self.model_performances[model]
            
            if dimension == ComparisonDimension.ACCURACY:
                score = performance.accuracy_score
            elif dimension == ComparisonDimension.SPEED:
                # 速度分數：響應時間越短分數越高
                score = 1.0 / (1.0 + performance.avg_response_time)
            elif dimension == ComparisonDimension.CONSISTENCY:
                score = performance.consistency_score
            elif dimension == ComparisonDimension.ROBUSTNESS:
                score = performance.robustness_score
            elif dimension == ComparisonDimension.COST_EFFICIENCY:
                # 成本效率：準確性/成本
                score = performance.accuracy_score / (performance.cost_per_request + 0.0001)
            elif dimension == ComparisonDimension.ERROR_RATE:
                score = 1.0 - performance.error_rate  # 錯誤率越低分數越高
            else:
                score = 0.5  # 默認分數
            
            scores.append(score)
        
        # 計算排名
        rankings = self._calculate_rankings(scores)
        
        # 統計顯著性檢驗
        statistical_significance = self._test_statistical_significance(scores, models)
        
        # 效應大小
        effect_size = self._calculate_effect_size(scores)
        
        # 置信區間
        confidence_interval = self._calculate_confidence_interval(scores)
        
        # p值
        p_value = self._calculate_p_value(scores)
        
        # 解釋
        interpretation = self._interpret_comparison(dimension, scores, models, p_value)
        
        return ComparisonResult(
            dimension=dimension,
            models=models,
            scores=scores,
            rankings=rankings,
            statistical_significance=statistical_significance,
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            p_value=p_value,
            interpretation=interpretation
        )
    
    def _calculate_rankings(self, scores: List[float]) -> List[int]:
        """計算排名"""
        # 分數越高排名越靠前
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        rankings = [0] * len(scores)
        
        for rank, index in enumerate(sorted_indices):
            rankings[index] = rank + 1
        
        return rankings
    
    def _test_statistical_significance(self, scores: List[float], models: List[str]) -> Dict[str, float]:
        """統計顯著性檢驗"""
        significance = {}
        
        if len(scores) < 2:
            return significance
        
        # 進行成對t檢驗
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                model1, model2 = models[i], models[j]
                
                # 獲取原始數據進行t檢驗
                perf1 = self.model_performances[model1]
                perf2 = self.model_performances[model2]
                
                # 使用響應時間作為樣本數據
                data1 = perf1.response_times if perf1.response_times else [scores[i]]
                data2 = perf2.response_times if perf2.response_times else [scores[j]]
                
                if len(data1) > 1 and len(data2) > 1:
                    try:
                        t_stat, p_val = stats.ttest_ind(data1, data2)
                        significance[f"{model1}_vs_{model2}"] = p_val
                    except:
                        significance[f"{model1}_vs_{model2}"] = 1.0
                else:
                    significance[f"{model1}_vs_{model2}"] = 1.0
        
        return significance
    
    def _calculate_effect_size(self, scores: List[float]) -> float:
        """計算效應大小"""
        if len(scores) < 2:
            return 0.0
        
        # 使用Cohen's d計算效應大小
        max_score = max(scores)
        min_score = min(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 1.0
        
        return (max_score - min_score) / std_dev if std_dev > 0 else 0.0
    
    def _calculate_confidence_interval(self, scores: List[float]) -> Tuple[float, float]:
        """計算置信區間"""
        if len(scores) < 2:
            return (0.0, 1.0)
        
        mean_score = statistics.mean(scores)
        std_error = statistics.stdev(scores) / (len(scores) ** 0.5)
        
        # 95%置信區間
        margin = 1.96 * std_error
        return (mean_score - margin, mean_score + margin)
    
    def _calculate_p_value(self, scores: List[float]) -> float:
        """計算p值"""
        if len(scores) < 2:
            return 1.0
        
        # 使用單樣本t檢驗檢驗是否顯著不同於0.5（隨機水平）
        try:
            t_stat, p_val = stats.ttest_1samp(scores, 0.5)
            return p_val
        except:
            return 1.0
    
    def _interpret_comparison(self, dimension: ComparisonDimension, scores: List[float], 
                            models: List[str], p_value: float) -> str:
        """解釋比較結果"""
        best_model_idx = scores.index(max(scores))
        best_model = models[best_model_idx]
        best_score = scores[best_model_idx]
        
        worst_model_idx = scores.index(min(scores))
        worst_model = models[worst_model_idx]
        worst_score = scores[worst_model_idx]
        
        improvement = ((best_score - worst_score) / worst_score * 100) if worst_score > 0 else 0
        
        significance = "顯著" if p_value < 0.05 else "不顯著"
        
        interpretation = f"在{dimension.value}維度上，{best_model}表現最佳（分數：{best_score:.3f}），" \
                        f"比{worst_model}高出{improvement:.1f}%。差異統計上{significance}（p={p_value:.3f}）。"
        
        return interpretation
    
    def generate_insights(self) -> None:
        """生成分析洞察"""
        print("💡 生成分析洞察...")
        
        self.analysis_insights = []
        
        # 整體性能洞察
        self._generate_overall_performance_insights()
        
        # 維度特定洞察
        self._generate_dimension_specific_insights()
        
        # 成本效益洞察
        self._generate_cost_benefit_insights()
        
        # 使用場景建議
        self._generate_use_case_recommendations()
        
        print(f"   ✅ 生成了 {len(self.analysis_insights)} 個洞察")
    
    def _generate_overall_performance_insights(self) -> None:
        """生成整體性能洞察"""
        if not self.model_performances:
            return
        
        # 找出整體最佳模型
        overall_scores = {}
        for model, perf in self.model_performances.items():
            # 綜合分數：準確性、速度、魯棒性的加權平均
            overall_score = (perf.accuracy_score * 0.4 + 
                           (1.0 / (1.0 + perf.avg_response_time)) * 0.3 + 
                           perf.robustness_score * 0.3)
            overall_scores[model] = overall_score
        
        best_model = max(overall_scores.keys(), key=lambda k: overall_scores[k])
        best_score = overall_scores[best_model]
        
        insight = AnalysisInsight(
            insight_type="overall_performance",
            title="整體性能最佳模型",
            description=f"{best_model}在綜合評估中表現最佳，綜合分數為{best_score:.3f}",
            evidence={
                "overall_scores": overall_scores,
                "best_model": best_model,
                "performance_details": {
                    "accuracy": self.model_performances[best_model].accuracy_score,
                    "avg_response_time": self.model_performances[best_model].avg_response_time,
                    "robustness": self.model_performances[best_model].robustness_score
                }
            },
            confidence=0.85,
            recommendations=[
                f"對於一般用途，推薦使用{best_model}",
                "考慮在生產環境中部署此模型",
                "定期監控性能以確保持續優異表現"
            ],
            impact_level="high"
        )
        
        self.analysis_insights.append(insight)
    
    def _generate_dimension_specific_insights(self) -> None:
        """生成維度特定洞察"""
        for dimension, result in self.comparison_results.items():
            best_model_idx = result.rankings.index(1)
            best_model = result.models[best_model_idx]
            best_score = result.scores[best_model_idx]
            
            # 判斷是否有顯著差異
            has_significant_difference = result.p_value < 0.05
            
            if has_significant_difference:
                insight = AnalysisInsight(
                    insight_type="dimension_specific",
                    title=f"{dimension.value}維度分析",
                    description=f"{best_model}在{dimension.value}方面顯著優於其他模型",
                    evidence={
                        "dimension": dimension.value,
                        "best_model": best_model,
                        "best_score": best_score,
                        "p_value": result.p_value,
                        "effect_size": result.effect_size,
                        "all_scores": dict(zip(result.models, result.scores))
                    },
                    confidence=0.9 if result.p_value < 0.01 else 0.75,
                    recommendations=[
                        f"對於{dimension.value}要求較高的場景，優先考慮{best_model}",
                        "監控此維度的性能變化",
                        "考慮針對此維度進行模型優化"
                    ],
                    impact_level="medium"
                )
                
                self.analysis_insights.append(insight)
    
    def _generate_cost_benefit_insights(self) -> None:
        """生成成本效益洞察"""
        cost_efficiency_scores = {}
        
        for model, perf in self.model_performances.items():
            # 成本效益 = 性能 / 成本
            cost_efficiency = perf.accuracy_score / (perf.cost_per_request + 0.0001)
            cost_efficiency_scores[model] = cost_efficiency
        
        best_cost_model = max(cost_efficiency_scores.keys(), key=lambda k: cost_efficiency_scores[k])
        
        insight = AnalysisInsight(
            insight_type="cost_benefit",
            title="成本效益分析",
            description=f"{best_cost_model}提供最佳的成本效益比",
            evidence={
                "cost_efficiency_scores": cost_efficiency_scores,
                "best_cost_model": best_cost_model,
                "cost_details": {
                    model: {
                        "accuracy": perf.accuracy_score,
                        "cost_per_request": perf.cost_per_request,
                        "cost_efficiency": cost_efficiency_scores[model]
                    }
                    for model, perf in self.model_performances.items()
                }
            },
            confidence=0.8,
            recommendations=[
                f"對於成本敏感的應用，推薦{best_cost_model}",
                "定期評估成本效益比的變化",
                "考慮根據使用量調整模型選擇策略"
            ],
            impact_level="high"
        )
        
        self.analysis_insights.append(insight)
    
    def _generate_use_case_recommendations(self) -> None:
        """生成使用場景建議"""
        recommendations = {
            "高準確性要求": None,
            "低延遲要求": None,
            "高可靠性要求": None,
            "成本敏感": None
        }
        
        # 找出各場景的最佳模型
        for model, perf in self.model_performances.items():
            # 高準確性
            if recommendations["高準確性要求"] is None or perf.accuracy_score > self.model_performances[recommendations["高準確性要求"]].accuracy_score:
                recommendations["高準確性要求"] = model
            
            # 低延遲
            if recommendations["低延遲要求"] is None or perf.avg_response_time < self.model_performances[recommendations["低延遲要求"]].avg_response_time:
                recommendations["低延遲要求"] = model
            
            # 高可靠性
            if recommendations["高可靠性要求"] is None or perf.robustness_score > self.model_performances[recommendations["高可靠性要求"]].robustness_score:
                recommendations["高可靠性要求"] = model
            
            # 成本敏感
            if recommendations["成本敏感"] is None or perf.cost_per_request < self.model_performances[recommendations["成本敏感"]].cost_per_request:
                recommendations["成本敏感"] = model
        
        insight = AnalysisInsight(
            insight_type="use_case_recommendations",
            title="使用場景建議",
            description="基於不同需求的模型選擇建議",
            evidence={
                "scenario_recommendations": recommendations,
                "detailed_analysis": {
                    scenario: {
                        "recommended_model": model,
                        "performance_details": {
                            "accuracy": self.model_performances[model].accuracy_score,
                            "response_time": self.model_performances[model].avg_response_time,
                            "robustness": self.model_performances[model].robustness_score,
                            "cost": self.model_performances[model].cost_per_request
                        }
                    }
                    for scenario, model in recommendations.items() if model
                }
            },
            confidence=0.85,
            recommendations=[
                f"高準確性場景：使用{recommendations['高準確性要求']}",
                f"低延遲場景：使用{recommendations['低延遲要求']}",
                f"高可靠性場景：使用{recommendations['高可靠性要求']}",
                f"成本敏感場景：使用{recommendations['成本敏感']}"
            ],
            impact_level="high"
        )
        
        self.analysis_insights.append(insight)
    
    def create_visualizations(self, output_dir: str = "analysis_charts") -> None:
        """創建可視化圖表"""
        print(f"📊 創建可視化圖表...")
        
        Path(output_dir).mkdir(exist_ok=True)
        
        # 1. 模型性能雷達圖
        self._create_performance_radar_chart(output_dir)
        
        # 2. 響應時間分佈圖
        self._create_response_time_distribution(output_dir)
        
        # 3. 準確性vs成本散點圖
        self._create_accuracy_cost_scatter(output_dir)
        
        # 4. 維度比較熱力圖
        self._create_dimension_heatmap(output_dir)
        
        # 5. 錯誤率比較柱狀圖
        self._create_error_rate_comparison(output_dir)
        
        # 6. 性能趨勢圖
        self._create_performance_trends(output_dir)
        
        print(f"   ✅ 圖表已保存到 {output_dir} 目錄")
    
    def _create_performance_radar_chart(self, output_dir: str) -> None:
        """創建性能雷達圖"""
        if not self.model_performances:
            return
        
        # 準備數據
        models = list(self.model_performances.keys())
        dimensions = ['準確性', '速度', '一致性', '魯棒性', '成本效益']
        
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]  # 閉合圖形
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(models)))
        
        for i, model in enumerate(models):
            perf = self.model_performances[model]
            
            values = [
                perf.accuracy_score,
                1.0 / (1.0 + perf.avg_response_time),  # 速度分數
                perf.consistency_score,
                perf.robustness_score,
                perf.accuracy_score / (perf.cost_per_request + 0.0001)  # 成本效益
            ]
            
            # 標準化到0-1範圍
            max_values = [1.0, 1.0, 1.0, 1.0, max([p.accuracy_score / (p.cost_per_request + 0.0001) for p in self.model_performances.values()])]
            normalized_values = [v / max_v for v, max_v in zip(values, max_values)]
            normalized_values += normalized_values[:1]  # 閉合圖形
            
            ax.plot(angles, normalized_values, 'o-', linewidth=2, label=model, color=colors[i])
            ax.fill(angles, normalized_values, alpha=0.25, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions)
        ax.set_ylim(0, 1)
        ax.set_title('模型性能雷達圖', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/performance_radar.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_response_time_distribution(self, output_dir: str) -> None:
        """創建響應時間分佈圖"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for model, perf in self.model_performances.items():
            if perf.response_times:
                ax.hist(perf.response_times, bins=30, alpha=0.7, label=model, density=True)
        
        ax.set_xlabel('響應時間 (秒)')
        ax.set_ylabel('密度')
        ax.set_title('響應時間分佈圖')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/response_time_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_accuracy_cost_scatter(self, output_dir: str) -> None:
        """創建準確性vs成本散點圖"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        models = []
        accuracies = []
        costs = []
        
        for model, perf in self.model_performances.items():
            models.append(model)
            accuracies.append(perf.accuracy_score)
            costs.append(perf.cost_per_request)
        
        scatter = ax.scatter(costs, accuracies, s=100, alpha=0.7, c=range(len(models)), cmap='viridis')
        
        # 添加模型標籤
        for i, model in enumerate(models):
            ax.annotate(model, (costs[i], accuracies[i]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=10)
        
        ax.set_xlabel('每次請求成本 ($)')
        ax.set_ylabel('準確性分數')
        ax.set_title('準確性 vs 成本分析')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/accuracy_cost_scatter.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_dimension_heatmap(self, output_dir: str) -> None:
        """創建維度比較熱力圖"""
        if not self.comparison_results:
            return
        
        # 準備數據
        models = list(self.model_performances.keys())
        dimensions = [d.value for d in self.comparison_results.keys()]
        
        data = []
        for dimension in self.comparison_results.keys():
            result = self.comparison_results[dimension]
            data.append(result.scores)
        
        # 創建熱力圖
        fig, ax = plt.subplots(figsize=(12, 8))
        
        im = ax.imshow(data, cmap='RdYlGn', aspect='auto')
        
        # 設置標籤
        ax.set_xticks(range(len(models)))
        ax.set_yticks(range(len(dimensions)))
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.set_yticklabels(dimensions)
        
        # 添加數值標籤
        for i in range(len(dimensions)):
            for j in range(len(models)):
                text = ax.text(j, i, f'{data[i][j]:.3f}', ha="center", va="center", color="black")
        
        ax.set_title('模型各維度性能熱力圖')
        
        # 添加顏色條
        cbar = plt.colorbar(im)
        cbar.set_label('性能分數')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/dimension_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_error_rate_comparison(self, output_dir: str) -> None:
        """創建錯誤率比較柱狀圖"""
        models = list(self.model_performances.keys())
        error_rates = [perf.error_rate for perf in self.model_performances.values()]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(models, error_rates, color='lightcoral', alpha=0.7)
        
        # 添加數值標籤
        for bar, rate in zip(bars, error_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                   f'{rate:.3f}', ha='center', va='bottom')
        
        ax.set_ylabel('錯誤率')
        ax.set_title('模型錯誤率比較')
        ax.set_ylim(0, max(error_rates) * 1.2 if error_rates else 1)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/error_rate_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_performance_trends(self, output_dir: str) -> None:
        """創建性能趨勢圖"""
        # 這裡需要時間序列數據，暫時創建示例圖
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 模擬趨勢數據
        time_points = range(1, 11)
        
        for model, perf in self.model_performances.items():
            # 模擬性能趨勢（實際應該從歷史數據中獲取）
            trend = [perf.accuracy_score + np.random.normal(0, 0.05) for _ in time_points]
            ax.plot(time_points, trend, marker='o', label=model, linewidth=2)
        
        ax.set_xlabel('時間點')
        ax.set_ylabel('準確性分數')
        ax.set_title('模型性能趨勢')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/performance_trends.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_comprehensive_report(self, output_file: str = None) -> str:
        """生成綜合報告"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"model_comparison_report_{timestamp}.json"
        
        print(f"📄 生成綜合報告...")
        
        report = {
            "report_info": {
                "generation_time": datetime.now().isoformat(),
                "models_analyzed": list(self.model_performances.keys()),
                "total_models": len(self.model_performances),
                "analysis_dimensions": len(self.comparison_results)
            },
            "model_performances": {
                model: {
                    "total_tests": perf.total_tests,
                    "successful_tests": perf.successful_tests,
                    "accuracy_score": perf.accuracy_score,
                    "avg_response_time": perf.avg_response_time,
                    "consistency_score": perf.consistency_score,
                    "robustness_score": perf.robustness_score,
                    "error_rate": perf.error_rate,
                    "cost_per_request": perf.cost_per_request,
                    "category_performance": perf.category_performance,
                    "complexity_performance": perf.complexity_performance
                }
                for model, perf in self.model_performances.items()
            },
            "comparison_results": {
                dimension.value: {
                    "models": result.models,
                    "scores": result.scores,
                    "rankings": result.rankings,
                    "p_value": result.p_value,
                    "effect_size": result.effect_size,
                    "interpretation": result.interpretation
                }
                for dimension, result in self.comparison_results.items()
            },
            "analysis_insights": [
                {
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "recommendations": insight.recommendations,
                    "impact_level": insight.impact_level,
                    "evidence": insight.evidence
                }
                for insight in self.analysis_insights
            ],
            "summary": self._generate_executive_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 報告已保存到 {output_file}")
        return output_file
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """生成執行摘要"""
        if not self.model_performances:
            return {}
        
        # 找出各維度的最佳模型
        best_accuracy = max(self.model_performances.keys(), 
                          key=lambda k: self.model_performances[k].accuracy_score)
        best_speed = min(self.model_performances.keys(), 
                        key=lambda k: self.model_performances[k].avg_response_time)
        best_robustness = max(self.model_performances.keys(), 
                            key=lambda k: self.model_performances[k].robustness_score)
        
        # 計算整體統計
        total_tests = sum(perf.total_tests for perf in self.model_performances.values())
        avg_accuracy = statistics.mean([perf.accuracy_score for perf in self.model_performances.values()])
        avg_response_time = statistics.mean([perf.avg_response_time for perf in self.model_performances.values()])
        
        return {
            "total_tests_conducted": total_tests,
            "models_compared": len(self.model_performances),
            "average_accuracy": avg_accuracy,
            "average_response_time": avg_response_time,
            "best_performers": {
                "accuracy": {
                    "model": best_accuracy,
                    "score": self.model_performances[best_accuracy].accuracy_score
                },
                "speed": {
                    "model": best_speed,
                    "response_time": self.model_performances[best_speed].avg_response_time
                },
                "robustness": {
                    "model": best_robustness,
                    "score": self.model_performances[best_robustness].robustness_score
                }
            },
            "key_findings": [
                f"共分析了{len(self.model_performances)}個模型，進行了{total_tests}次測試",
                f"{best_accuracy}在準確性方面表現最佳",
                f"{best_speed}在響應速度方面表現最佳",
                f"{best_robustness}在魯棒性方面表現最佳",
                f"平均準確率為{avg_accuracy:.1%}，平均響應時間為{avg_response_time:.3f}秒"
            ],
            "insights_generated": len(self.analysis_insights),
            "high_impact_insights": len([i for i in self.analysis_insights if i.impact_level == "high"])
        }
    
    def print_analysis_summary(self) -> None:
        """打印分析摘要"""
        print("\n" + "=" * 80)
        print("🔍 LLM模型比較分析摘要")
        print("=" * 80)
        
        if not self.model_performances:
            print("❌ 沒有模型性能數據")
            return
        
        # 基本統計
        print(f"\n📊 基本統計:")
        print(f"   分析模型數量: {len(self.model_performances)}")
        print(f"   比較維度數量: {len(self.comparison_results)}")
        print(f"   生成洞察數量: {len(self.analysis_insights)}")
        
        # 模型性能概覽
        print(f"\n🏆 模型性能概覽:")
        for model, perf in self.model_performances.items():
            print(f"   {model}:")
            print(f"     準確率: {perf.accuracy_score:.1%}")
            print(f"     平均響應時間: {perf.avg_response_time:.3f}秒")
            print(f"     錯誤率: {perf.error_rate:.1%}")
            print(f"     魯棒性: {perf.robustness_score:.3f}")
        
        # 維度比較結果
        if self.comparison_results:
            print(f"\n📈 維度比較結果:")
            for dimension, result in self.comparison_results.items():
                best_idx = result.rankings.index(1)
                best_model = result.models[best_idx]
                print(f"   {dimension.value}: {best_model} (分數: {result.scores[best_idx]:.3f})")
        
        # 關鍵洞察
        high_impact_insights = [i for i in self.analysis_insights if i.impact_level == "high"]
        if high_impact_insights:
            print(f"\n💡 關鍵洞察:")
            for insight in high_impact_insights[:3]:  # 顯示前3個
                print(f"   • {insight.title}: {insight.description}")
        
        print("\n" + "=" * 80)


def main():
    """主函數 - 模型比較分析器入口點"""
    print("🔍 LLM模型比較分析器")
    print("=" * 60)
    
    try:
        # 獲取測試結果文件
        print("\n📂 請提供測試結果文件路徑:")
        files_input = input("輸入文件路徑 (用逗號分隔多個文件): ").strip()
        
        if not files_input:
            print("❌ 未提供文件路徑")
            return
        
        result_files = [f.strip() for f in files_input.split(",")]
        
        # 創建分析器
        analyzer = LLMModelComparisonAnalyzer()
        
        # 載入數據
        analyzer.load_test_results(result_files)
        
        # 提取性能數據
        analyzer.extract_model_performances()
        
        # 執行比較分析
        analyzer.perform_comparative_analysis()
        
        # 生成洞察
        analyzer.generate_insights()
        
        # 顯示摘要
        analyzer.print_analysis_summary()
        
        # 創建可視化
        create_viz = input("\n是否創建可視化圖表？ (y/n): ").strip().lower()
        if create_viz == 'y':
            analyzer.create_visualizations()
        
        # 生成報告
        generate_report = input("是否生成綜合報告？ (y/n): ").strip().lower()
        if generate_report == 'y':
            report_file = analyzer.generate_comprehensive_report()
            print(f"   📄 報告文件: {report_file}")
        
        print("\n🎉 分析完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 分析過程被用戶中斷")
    except Exception as e:
        print(f"\n❌ 分析過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()