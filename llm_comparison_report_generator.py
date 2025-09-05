#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM模型對比分析報告生成器
用於生成詳細的LLM模型測試結果分析報告，包含圖表、統計分析和建議

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import statistics
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
from pathlib import Path
import warnings
from jinja2 import Template
import base64
from io import BytesIO

# 設置中文字體和樣式
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")
warnings.filterwarnings('ignore')

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMProvider


@dataclass
class ComparisonMetrics:
    """對比指標"""
    provider: str
    total_tests: int
    success_rate: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    accuracy_score: float
    consistency_score: float
    robustness_score: float
    cost_efficiency: float
    overall_score: float
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CategoryAnalysis:
    """類別分析"""
    category: str
    provider_scores: Dict[str, float]
    best_provider: str
    worst_provider: str
    score_range: float
    insights: List[str] = field(default_factory=list)


@dataclass
class TrendAnalysis:
    """趨勢分析"""
    provider: str
    time_series: List[Tuple[float, float]]  # (timestamp, metric_value)
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0-1
    seasonal_patterns: Dict[str, float]
    anomalies: List[Tuple[float, float, str]]  # (timestamp, value, description)


class LLMComparisonReportGenerator:
    """LLM模型對比分析報告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        """初始化報告生成器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 創建子目錄
        (self.output_dir / "charts").mkdir(exist_ok=True)
        (self.output_dir / "data").mkdir(exist_ok=True)
        (self.output_dir / "html").mkdir(exist_ok=True)
        
        self.comparison_data: List[Dict[str, Any]] = []
        self.metrics: List[ComparisonMetrics] = []
        self.category_analyses: List[CategoryAnalysis] = []
        self.trend_analyses: List[TrendAnalysis] = []
        
        # 圖表配置
        self.chart_config = {
            'figsize': (12, 8),
            'dpi': 300,
            'style': 'whitegrid',
            'palette': 'husl',
            'font_size': 12
        }
    
    def load_test_results(self, result_files: List[str]) -> None:
        """載入測試結果文件"""
        print("📂 載入測試結果文件...")
        
        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.comparison_data.append({
                        'file': file_path,
                        'data': data
                    })
                print(f"   ✅ 已載入: {file_path}")
            except Exception as e:
                print(f"   ❌ 載入失敗 {file_path}: {str(e)}")
        
        print(f"📊 總共載入 {len(self.comparison_data)} 個結果文件")
    
    def analyze_comparison_metrics(self) -> None:
        """分析對比指標"""
        print("🔍 分析對比指標...")
        
        provider_data = defaultdict(list)
        
        # 收集各提供商的數據
        for file_data in self.comparison_data:
            results = file_data['data'].get('results', [])
            
            for result in results:
                provider = result.get('provider', 'unknown')
                provider_data[provider].append(result)
        
        # 計算每個提供商的指標
        for provider, results in provider_data.items():
            metrics = self._calculate_provider_metrics(provider, results)
            self.metrics.append(metrics)
        
        # 排序（按總分）
        self.metrics.sort(key=lambda x: x.overall_score, reverse=True)
        
        print(f"   📈 已分析 {len(self.metrics)} 個提供商的指標")
    
    def _calculate_provider_metrics(self, provider: str, results: List[Dict[str, Any]]) -> ComparisonMetrics:
        """計算提供商指標"""
        if not results:
            return ComparisonMetrics(
                provider=provider,
                total_tests=0,
                success_rate=0.0,
                avg_response_time=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                throughput=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                robustness_score=0.0,
                cost_efficiency=0.0,
                overall_score=0.0
            )
        
        # 基本統計
        total_tests = sum(r.get('total_requests', 0) for r in results)
        success_rates = [r.get('success_rate', 0.0) for r in results]
        response_times = [r.get('avg_response_time', 0.0) for r in results]
        throughputs = [r.get('throughput', 0.0) for r in results]
        
        # 計算平均值
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0.0
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        avg_throughput = statistics.mean(throughputs) if throughputs else 0.0
        
        # 計算百分位數
        all_response_times = []
        for result in results:
            rt_dist = result.get('response_time_distribution', [])
            all_response_times.extend(rt_dist)
        
        if all_response_times:
            median_response_time = np.percentile(all_response_times, 50)
            p95_response_time = np.percentile(all_response_times, 95)
            p99_response_time = np.percentile(all_response_times, 99)
        else:
            median_response_time = p95_response_time = p99_response_time = 0.0
        
        # 計算高級指標
        accuracy_score = self._calculate_accuracy_score(results)
        consistency_score = self._calculate_consistency_score(results)
        robustness_score = self._calculate_robustness_score(results)
        cost_efficiency = self._calculate_cost_efficiency(results)
        
        # 計算總分
        overall_score = self._calculate_overall_score(
            avg_success_rate, avg_response_time, avg_throughput,
            accuracy_score, consistency_score, robustness_score, cost_efficiency
        )
        
        # 生成優缺點和建議
        strengths, weaknesses, recommendations = self._generate_insights(
            provider, avg_success_rate, avg_response_time, avg_throughput,
            accuracy_score, consistency_score, robustness_score, cost_efficiency
        )
        
        return ComparisonMetrics(
            provider=provider,
            total_tests=total_tests,
            success_rate=avg_success_rate,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=avg_throughput,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            robustness_score=robustness_score,
            cost_efficiency=cost_efficiency,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _calculate_accuracy_score(self, results: List[Dict[str, Any]]) -> float:
        """計算準確性分數"""
        # 基於成功率和錯誤分佈計算
        success_rates = [r.get('success_rate', 0.0) for r in results]
        
        if not success_rates:
            return 0.0
        
        # 考慮成功率的穩定性
        avg_success_rate = statistics.mean(success_rates)
        success_rate_std = statistics.stdev(success_rates) if len(success_rates) > 1 else 0.0
        
        # 穩定性懲罰
        stability_penalty = min(success_rate_std * 2, 0.2)
        
        return max(0.0, avg_success_rate - stability_penalty)
    
    def _calculate_consistency_score(self, results: List[Dict[str, Any]]) -> float:
        """計算一致性分數"""
        # 基於響應時間變異性計算
        response_times = [r.get('avg_response_time', 0.0) for r in results]
        
        if len(response_times) < 2:
            return 1.0 if response_times else 0.0
        
        # 計算變異係數
        mean_rt = statistics.mean(response_times)
        std_rt = statistics.stdev(response_times)
        
        if mean_rt == 0:
            return 0.0
        
        cv = std_rt / mean_rt
        
        # 變異係數越小，一致性越高
        return max(0.0, 1.0 - cv)
    
    def _calculate_robustness_score(self, results: List[Dict[str, Any]]) -> float:
        """計算魯棒性分數"""
        # 基於錯誤處理和恢復能力計算
        error_rates = []
        timeout_rates = []
        
        for result in results:
            total_requests = result.get('total_requests', 0)
            if total_requests > 0:
                error_rate = result.get('error_requests', 0) / total_requests
                timeout_rate = result.get('timeout_requests', 0) / total_requests
                error_rates.append(error_rate)
                timeout_rates.append(timeout_rate)
        
        if not error_rates:
            return 0.0
        
        avg_error_rate = statistics.mean(error_rates)
        avg_timeout_rate = statistics.mean(timeout_rates)
        
        # 錯誤率和超時率越低，魯棒性越高
        robustness = 1.0 - (avg_error_rate + avg_timeout_rate)
        
        return max(0.0, robustness)
    
    def _calculate_cost_efficiency(self, results: List[Dict[str, Any]]) -> float:
        """計算成本效率"""
        # 基於吞吐量和資源使用計算
        throughputs = [r.get('throughput', 0.0) for r in results]
        memory_usages = [r.get('avg_memory_usage', 0.0) for r in results]
        
        if not throughputs or not memory_usages:
            return 0.0
        
        avg_throughput = statistics.mean(throughputs)
        avg_memory = statistics.mean(memory_usages)
        
        if avg_memory == 0:
            return 0.0
        
        # 吞吐量/記憶體使用量 = 效率
        efficiency = avg_throughput / avg_memory
        
        # 正規化到0-1範圍
        return min(1.0, efficiency / 10.0)  # 假設10是一個合理的上限
    
    def _calculate_overall_score(self, success_rate: float, response_time: float, 
                               throughput: float, accuracy: float, consistency: float, 
                               robustness: float, cost_efficiency: float) -> float:
        """計算總分"""
        # 權重配置
        weights = {
            'success_rate': 0.25,
            'response_time': 0.15,  # 響應時間越低越好
            'throughput': 0.15,
            'accuracy': 0.20,
            'consistency': 0.10,
            'robustness': 0.10,
            'cost_efficiency': 0.05
        }
        
        # 正規化響應時間（越低越好）
        normalized_response_time = max(0.0, 1.0 - min(response_time / 30.0, 1.0))
        
        # 正規化吞吐量
        normalized_throughput = min(throughput / 10.0, 1.0)
        
        # 計算加權總分
        total_score = (
            weights['success_rate'] * success_rate +
            weights['response_time'] * normalized_response_time +
            weights['throughput'] * normalized_throughput +
            weights['accuracy'] * accuracy +
            weights['consistency'] * consistency +
            weights['robustness'] * robustness +
            weights['cost_efficiency'] * cost_efficiency
        )
        
        return total_score
    
    def _generate_insights(self, provider: str, success_rate: float, response_time: float,
                         throughput: float, accuracy: float, consistency: float,
                         robustness: float, cost_efficiency: float) -> Tuple[List[str], List[str], List[str]]:
        """生成洞察、優缺點和建議"""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # 分析優勢
        if success_rate > 0.95:
            strengths.append("極高的成功率")
        elif success_rate > 0.90:
            strengths.append("高成功率")
        
        if response_time < 2.0:
            strengths.append("快速響應時間")
        elif response_time < 5.0:
            strengths.append("良好的響應時間")
        
        if throughput > 5.0:
            strengths.append("高吞吐量")
        elif throughput > 2.0:
            strengths.append("良好的吞吐量")
        
        if accuracy > 0.90:
            strengths.append("高準確性")
        
        if consistency > 0.85:
            strengths.append("良好的一致性")
        
        if robustness > 0.85:
            strengths.append("強魯棒性")
        
        if cost_efficiency > 0.7:
            strengths.append("高成本效率")
        
        # 分析弱點
        if success_rate < 0.80:
            weaknesses.append("成功率偏低")
            recommendations.append("檢查API配置和網路連接")
        
        if response_time > 10.0:
            weaknesses.append("響應時間過長")
            recommendations.append("優化請求參數或考慮使用更快的模型")
        
        if throughput < 1.0:
            weaknesses.append("吞吐量較低")
            recommendations.append("增加並發數或優化請求處理")
        
        if accuracy < 0.80:
            weaknesses.append("準確性有待提升")
            recommendations.append("調整模型參數或使用更適合的模型")
        
        if consistency < 0.70:
            weaknesses.append("一致性不穩定")
            recommendations.append("檢查模型配置的穩定性")
        
        if robustness < 0.70:
            weaknesses.append("錯誤處理能力不足")
            recommendations.append("增強錯誤處理和重試機制")
        
        if cost_efficiency < 0.5:
            weaknesses.append("成本效率較低")
            recommendations.append("優化資源使用或考慮更經濟的方案")
        
        # 通用建議
        if not recommendations:
            recommendations.append("繼續監控性能並定期評估")
        
        return strengths, weaknesses, recommendations
    
    def analyze_categories(self) -> None:
        """分析各類別表現"""
        print("📊 分析各類別表現...")
        
        categories = [
            ('成功率', 'success_rate'),
            ('響應時間', 'avg_response_time'),
            ('吞吐量', 'throughput'),
            ('準確性', 'accuracy_score'),
            ('一致性', 'consistency_score'),
            ('魯棒性', 'robustness_score'),
            ('成本效率', 'cost_efficiency')
        ]
        
        for category_name, metric_key in categories:
            provider_scores = {}
            
            for metric in self.metrics:
                score = getattr(metric, metric_key)
                # 響應時間需要反轉（越低越好）
                if metric_key == 'avg_response_time':
                    score = max(0.0, 1.0 - min(score / 30.0, 1.0))
                provider_scores[metric.provider] = score
            
            if provider_scores:
                best_provider = max(provider_scores.keys(), key=lambda k: provider_scores[k])
                worst_provider = min(provider_scores.keys(), key=lambda k: provider_scores[k])
                score_range = max(provider_scores.values()) - min(provider_scores.values())
                
                insights = self._generate_category_insights(category_name, provider_scores)
                
                analysis = CategoryAnalysis(
                    category=category_name,
                    provider_scores=provider_scores,
                    best_provider=best_provider,
                    worst_provider=worst_provider,
                    score_range=score_range,
                    insights=insights
                )
                
                self.category_analyses.append(analysis)
        
        print(f"   📈 已分析 {len(self.category_analyses)} 個類別")
    
    def _generate_category_insights(self, category: str, scores: Dict[str, float]) -> List[str]:
        """生成類別洞察"""
        insights = []
        
        if not scores:
            return insights
        
        values = list(scores.values())
        avg_score = statistics.mean(values)
        std_score = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 分析分數分佈
        if std_score < 0.1:
            insights.append(f"{category}方面各提供商表現相近")
        elif std_score > 0.3:
            insights.append(f"{category}方面提供商間差異顯著")
        
        # 分析整體水平
        if avg_score > 0.8:
            insights.append(f"整體{category}水平較高")
        elif avg_score < 0.5:
            insights.append(f"整體{category}水平有待提升")
        
        return insights
    
    def generate_charts(self) -> Dict[str, str]:
        """生成圖表"""
        print("📈 生成對比圖表...")
        
        chart_files = {}
        
        if not self.metrics:
            print("   ❌ 沒有數據可生成圖表")
            return chart_files
        
        # 1. 總分對比雷達圖
        chart_files['radar'] = self._create_radar_chart()
        
        # 2. 響應時間分佈圖
        chart_files['response_time'] = self._create_response_time_chart()
        
        # 3. 成功率對比柱狀圖
        chart_files['success_rate'] = self._create_success_rate_chart()
        
        # 4. 吞吐量對比圖
        chart_files['throughput'] = self._create_throughput_chart()
        
        # 5. 綜合性能熱力圖
        chart_files['heatmap'] = self._create_performance_heatmap()
        
        # 6. 成本效率散點圖
        chart_files['cost_efficiency'] = self._create_cost_efficiency_chart()
        
        print(f"   📊 已生成 {len(chart_files)} 個圖表")
        return chart_files
    
    def _create_radar_chart(self) -> str:
        """創建雷達圖"""
        fig, ax = plt.subplots(figsize=self.chart_config['figsize'], 
                              subplot_kw=dict(projection='polar'))
        
        # 準備數據
        categories = ['成功率', '響應時間', '吞吐量', '準確性', '一致性', '魯棒性', '成本效率']
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]  # 閉合圖形
        
        # 為每個提供商繪製雷達圖
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.metrics)))
        
        for i, metric in enumerate(self.metrics):
            values = [
                metric.success_rate,
                max(0.0, 1.0 - min(metric.avg_response_time / 30.0, 1.0)),  # 響應時間反轉
                min(metric.throughput / 10.0, 1.0),  # 正規化吞吐量
                metric.accuracy_score,
                metric.consistency_score,
                metric.robustness_score,
                metric.cost_efficiency
            ]
            values += values[:1]  # 閉合圖形
            
            ax.plot(angles, values, 'o-', linewidth=2, label=metric.provider, color=colors[i])
            ax.fill(angles, values, alpha=0.25, color=colors[i])
        
        # 設置標籤
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('LLM提供商綜合性能對比', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
        
        # 保存圖表
        filename = self.output_dir / "charts" / "radar_comparison.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        return str(filename)
    
    def _create_response_time_chart(self) -> str:
        """創建響應時間分佈圖"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 準備數據
        providers = [m.provider for m in self.metrics]
        avg_times = [m.avg_response_time for m in self.metrics]
        p95_times = [m.p95_response_time for m in self.metrics]
        p99_times = [m.p99_response_time for m in self.metrics]
        
        # 左圖：平均響應時間柱狀圖
        bars = ax1.bar(providers, avg_times, color='skyblue', alpha=0.7)
        ax1.set_title('平均響應時間對比', fontsize=14, fontweight='bold')
        ax1.set_ylabel('響應時間 (秒)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 添加數值標籤
        for bar, time in zip(bars, avg_times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{time:.2f}s', ha='center', va='bottom')
        
        # 右圖：百分位數對比
        x = np.arange(len(providers))
        width = 0.25
        
        ax2.bar(x - width, avg_times, width, label='平均', alpha=0.8)
        ax2.bar(x, p95_times, width, label='P95', alpha=0.8)
        ax2.bar(x + width, p99_times, width, label='P99', alpha=0.8)
        
        ax2.set_title('響應時間百分位數對比', fontsize=14, fontweight='bold')
        ax2.set_ylabel('響應時間 (秒)')
        ax2.set_xticks(x)
        ax2.set_xticklabels(providers, rotation=45)
        ax2.legend()
        
        # 保存圖表
        filename = self.output_dir / "charts" / "response_time_comparison.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        return str(filename)
    
    def _create_success_rate_chart(self) -> str:
        """創建成功率對比圖"""
        fig, ax = plt.subplots(figsize=self.chart_config['figsize'])
        
        # 準備數據
        providers = [m.provider for m in self.metrics]
        success_rates = [m.success_rate * 100 for m in self.metrics]  # 轉換為百分比
        
        # 創建柱狀圖
        colors = ['green' if sr >= 95 else 'orange' if sr >= 90 else 'red' for sr in success_rates]
        bars = ax.bar(providers, success_rates, color=colors, alpha=0.7)
        
        # 設置標籤和標題
        ax.set_title('成功率對比', fontsize=16, fontweight='bold')
        ax.set_ylabel('成功率 (%)')
        ax.set_ylim(0, 100)
        ax.tick_params(axis='x', rotation=45)
        
        # 添加數值標籤
        for bar, rate in zip(bars, success_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 添加參考線
        ax.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='優秀 (95%)')
        ax.axhline(y=90, color='orange', linestyle='--', alpha=0.5, label='良好 (90%)')
        ax.legend()
        
        # 保存圖表
        filename = self.output_dir / "charts" / "success_rate_comparison.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        return str(filename)
    
    def _create_throughput_chart(self) -> str:
        """創建吞吐量對比圖"""
        fig, ax = plt.subplots(figsize=self.chart_config['figsize'])
        
        # 準備數據
        providers = [m.provider for m in self.metrics]
        throughputs = [m.throughput for m in self.metrics]
        
        # 創建柱狀圖
        bars = ax.bar(providers, throughputs, color='lightcoral', alpha=0.7)
        
        # 設置標籤和標題
        ax.set_title('吞吐量對比', fontsize=16, fontweight='bold')
        ax.set_ylabel('吞吐量 (請求/秒)')
        ax.tick_params(axis='x', rotation=45)
        
        # 添加數值標籤
        for bar, throughput in zip(bars, throughputs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                   f'{throughput:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # 保存圖表
        filename = self.output_dir / "charts" / "throughput_comparison.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        return str(filename)
    
    def _create_performance_heatmap(self) -> str:
        """創建性能熱力圖"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 準備數據
        providers = [m.provider for m in self.metrics]
        metrics_data = []
        metric_names = ['成功率', '響應時間', '吞吐量', '準確性', '一致性', '魯棒性', '成本效率']
        
        for metric in self.metrics:
            row = [
                metric.success_rate,
                max(0.0, 1.0 - min(metric.avg_response_time / 30.0, 1.0)),  # 響應時間反轉
                min(metric.throughput / 10.0, 1.0),  # 正規化吞吐量
                metric.accuracy_score,
                metric.consistency_score,
                metric.robustness_score,
                metric.cost_efficiency
            ]
            metrics_data.append(row)
        
        # 創建熱力圖
        im = ax.imshow(metrics_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        # 設置標籤
        ax.set_xticks(range(len(metric_names)))
        ax.set_xticklabels(metric_names, rotation=45, ha='right')
        ax.set_yticks(range(len(providers)))
        ax.set_yticklabels(providers)
        
        # 添加數值標籤
        for i in range(len(providers)):
            for j in range(len(metric_names)):
                text = ax.text(j, i, f'{metrics_data[i][j]:.2f}',
                             ha="center", va="center", color="black", fontweight='bold')
        
        # 添加顏色條
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('性能分數', rotation=270, labelpad=20)
        
        ax.set_title('LLM提供商綜合性能熱力圖', fontsize=16, fontweight='bold', pad=20)
        
        # 保存圖表
        filename = self.output_dir / "charts" / "performance_heatmap.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        return str(filename)
    
    def _create_cost_efficiency_chart(self) -> str:
        """創建成本效率散點圖"""
        fig, ax = plt.subplots(figsize=self.chart_config['figsize'])
        
        # 準備數據
        throughputs = [m.throughput for m in self.metrics]
        cost_efficiencies = [m.cost_efficiency for m in self.metrics]
        providers = [m.provider for m in self.metrics]
        
        # 創建散點圖
        scatter = ax.scatter(throughputs, cost_efficiencies, s=100, alpha=0.7, c=range(len(providers)), cmap='viridis')
        
        # 添加提供商標籤
        for i, provider in enumerate(providers):
            ax.annotate(provider, (throughputs[i], cost_efficiencies[i]), 
                       xytext=(5, 5), textcoords='offset points', fontsize=10)
        
        # 設置標籤和標題
        ax.set_xlabel('吞吐量 (請求/秒)')
        ax.set_ylabel('成本效率')
        ax.set_title('吞吐量 vs 成本效率', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 保存圖表
        filename = self.output_dir / "charts" / "cost_efficiency_scatter.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        return str(filename)
    
    def generate_html_report(self, chart_files: Dict[str, str]) -> str:
        """生成HTML報告"""
        print("📄 生成HTML報告...")
        
        # HTML模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM模型對比分析報告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .chart-container {
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 10px;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .insights {
            background-color: #e8f5e8;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin: 15px 0;
            border-radius: 5px;
        }
        .strengths {
            color: #2e7d32;
        }
        .weaknesses {
            color: #d32f2f;
        }
        .recommendations {
            color: #1976d2;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .score-high { color: #2e7d32; font-weight: bold; }
        .score-medium { color: #f57c00; font-weight: bold; }
        .score-low { color: #d32f2f; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 LLM模型對比分析報告</h1>
        <p><strong>生成時間:</strong> {{ timestamp }}</p>
        <p><strong>測試提供商數量:</strong> {{ provider_count }}</p>
        <p><strong>總測試次數:</strong> {{ total_tests }}</p>
        
        <h2>📊 綜合排名</h2>
        <div class="metric-grid">
            {% for metric in metrics %}
            <div class="metric-card">
                <h3>{{ loop.index }}. {{ metric.provider }}</h3>
                <p><strong>總分:</strong> {{ "%.2f"|format(metric.overall_score) }}</p>
                <p><strong>成功率:</strong> {{ "%.1f%%"|format(metric.success_rate * 100) }}</p>
                <p><strong>平均響應時間:</strong> {{ "%.2f秒"|format(metric.avg_response_time) }}</p>
                <p><strong>吞吐量:</strong> {{ "%.2f 請求/秒"|format(metric.throughput) }}</p>
            </div>
            {% endfor %}
        </div>
        
        <h2>📈 性能圖表</h2>
        {% for chart_name, chart_file in charts.items() %}
        <div class="chart-container">
            <h3>{{ chart_titles[chart_name] }}</h3>
            <img src="{{ chart_file }}" alt="{{ chart_titles[chart_name] }}">
        </div>
        {% endfor %}
        
        <h2>📋 詳細指標對比</h2>
        <table>
            <thead>
                <tr>
                    <th>提供商</th>
                    <th>總分</th>
                    <th>成功率</th>
                    <th>響應時間</th>
                    <th>吞吐量</th>
                    <th>準確性</th>
                    <th>一致性</th>
                    <th>魯棒性</th>
                    <th>成本效率</th>
                </tr>
            </thead>
            <tbody>
                {% for metric in metrics %}
                <tr>
                    <td><strong>{{ metric.provider }}</strong></td>
                    <td class="{{ 'score-high' if metric.overall_score > 0.8 else 'score-medium' if metric.overall_score > 0.6 else 'score-low' }}">{{ "%.3f"|format(metric.overall_score) }}</td>
                    <td class="{{ 'score-high' if metric.success_rate > 0.95 else 'score-medium' if metric.success_rate > 0.9 else 'score-low' }}">{{ "%.1f%%"|format(metric.success_rate * 100) }}</td>
                    <td class="{{ 'score-high' if metric.avg_response_time < 2 else 'score-medium' if metric.avg_response_time < 5 else 'score-low' }}">{{ "%.2f秒"|format(metric.avg_response_time) }}</td>
                    <td class="{{ 'score-high' if metric.throughput > 5 else 'score-medium' if metric.throughput > 2 else 'score-low' }}">{{ "%.2f"|format(metric.throughput) }}</td>
                    <td class="{{ 'score-high' if metric.accuracy_score > 0.9 else 'score-medium' if metric.accuracy_score > 0.8 else 'score-low' }}">{{ "%.3f"|format(metric.accuracy_score) }}</td>
                    <td class="{{ 'score-high' if metric.consistency_score > 0.85 else 'score-medium' if metric.consistency_score > 0.7 else 'score-low' }}">{{ "%.3f"|format(metric.consistency_score) }}</td>
                    <td class="{{ 'score-high' if metric.robustness_score > 0.85 else 'score-medium' if metric.robustness_score > 0.7 else 'score-low' }}">{{ "%.3f"|format(metric.robustness_score) }}</td>
                    <td class="{{ 'score-high' if metric.cost_efficiency > 0.7 else 'score-medium' if metric.cost_efficiency > 0.5 else 'score-low' }}">{{ "%.3f"|format(metric.cost_efficiency) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <h2>💡 分析洞察</h2>
        {% for metric in metrics %}
        <div class="insights">
            <h3>{{ metric.provider }}</h3>
            {% if metric.strengths %}
            <div class="strengths">
                <strong>✅ 優勢:</strong>
                <ul>
                    {% for strength in metric.strengths %}
                    <li>{{ strength }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if metric.weaknesses %}
            <div class="weaknesses">
                <strong>❌ 弱點:</strong>
                <ul>
                    {% for weakness in metric.weaknesses %}
                    <li>{{ weakness }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if metric.recommendations %}
            <div class="recommendations">
                <strong>💡 建議:</strong>
                <ul>
                    {% for recommendation in metric.recommendations %}
                    <li>{{ recommendation }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endfor %}
        
        <h2>🎯 類別分析</h2>
        {% for analysis in category_analyses %}
        <div class="insights">
            <h3>{{ analysis.category }}</h3>
            <p><strong>最佳提供商:</strong> {{ analysis.best_provider }}</p>
            <p><strong>表現最差:</strong> {{ analysis.worst_provider }}</p>
            <p><strong>分數範圍:</strong> {{ "%.3f"|format(analysis.score_range) }}</p>
            {% if analysis.insights %}
            <ul>
                {% for insight in analysis.insights %}
                <li>{{ insight }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
        
        <h2>📝 總結建議</h2>
        <div class="insights">
            <h3>🏆 推薦選擇</h3>
            {% if metrics %}
            <p><strong>綜合表現最佳:</strong> {{ metrics[0].provider }} (總分: {{ "%.3f"|format(metrics[0].overall_score) }})</p>
            <p><strong>性價比最高:</strong> {{ best_cost_efficiency.provider }} (成本效率: {{ "%.3f"|format(best_cost_efficiency.cost_efficiency) }})</p>
            <p><strong>響應最快:</strong> {{ fastest_provider.provider }} (平均響應時間: {{ "%.2f秒"|format(fastest_provider.avg_response_time) }})</p>
            <p><strong>最穩定:</strong> {{ most_consistent.provider }} (一致性分數: {{ "%.3f"|format(most_consistent.consistency_score) }})</p>
            {% endif %}
            
            <h3>🎯 使用建議</h3>
            <ul>
                <li><strong>高性能需求:</strong> 選擇響應時間最快且吞吐量最高的提供商</li>
                <li><strong>穩定性優先:</strong> 選擇一致性和魯棒性分數最高的提供商</li>
                <li><strong>成本敏感:</strong> 選擇成本效率最高的提供商</li>
                <li><strong>準確性要求:</strong> 選擇準確性分數最高的提供商</li>
            </ul>
        </div>
        
        <footer style="margin-top: 50px; text-align: center; color: #666;">
            <p>報告由 LLM模型對比分析工具 自動生成</p>
            <p>生成時間: {{ timestamp }}</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # 準備模板數據
        template_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'provider_count': len(self.metrics),
            'total_tests': sum(m.total_tests for m in self.metrics),
            'metrics': self.metrics,
            'charts': chart_files,
            'chart_titles': {
                'radar': '綜合性能雷達圖',
                'response_time': '響應時間分析',
                'success_rate': '成功率對比',
                'throughput': '吞吐量對比',
                'heatmap': '性能熱力圖',
                'cost_efficiency': '成本效率分析'
            },
            'category_analyses': self.category_analyses,
            'best_cost_efficiency': max(self.metrics, key=lambda x: x.cost_efficiency) if self.metrics else None,
            'fastest_provider': min(self.metrics, key=lambda x: x.avg_response_time) if self.metrics else None,
            'most_consistent': max(self.metrics, key=lambda x: x.consistency_score) if self.metrics else None
        }
        
        # 渲染HTML
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # 保存HTML文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = self.output_dir / "html" / f"llm_comparison_report_{timestamp}.html"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   📄 HTML報告已生成: {html_filename}")
        return str(html_filename)
    
    def save_comparison_data(self) -> str:
        """保存對比數據"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / "data" / f"comparison_analysis_{timestamp}.json"
        
        # 準備保存的數據
        save_data = {
            'analysis_summary': {
                'timestamp': datetime.now().isoformat(),
                'provider_count': len(self.metrics),
                'total_tests': sum(m.total_tests for m in self.metrics)
            },
            'metrics': [asdict(metric) for metric in self.metrics],
            'category_analyses': [asdict(analysis) for analysis in self.category_analyses],
            'trend_analyses': [asdict(trend) for trend in self.trend_analyses]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 對比分析數據已保存: {filename}")
        return str(filename)
    
    def print_summary(self) -> None:
        """打印摘要"""
        if not self.metrics:
            print("❌ 沒有分析結果可顯示")
            return
        
        print("\n📊 LLM模型對比分析摘要")
        print("=" * 60)
        
        print(f"\n🏆 綜合排名 (共 {len(self.metrics)} 個提供商):")
        for i, metric in enumerate(self.metrics, 1):
            print(f"   {i}. {metric.provider:<15} 總分: {metric.overall_score:.3f}")
        
        if self.metrics:
            best = self.metrics[0]
            print(f"\n🥇 最佳提供商: {best.provider}")
            print(f"   總分: {best.overall_score:.3f}")
            print(f"   成功率: {best.success_rate:.1%}")
            print(f"   響應時間: {best.avg_response_time:.2f}秒")
            print(f"   吞吐量: {best.throughput:.2f} 請求/秒")
        
        print(f"\n📈 類別分析 (共 {len(self.category_analyses)} 個類別):")
        for analysis in self.category_analyses:
            print(f"   {analysis.category:<10} 最佳: {analysis.best_provider}")


def main():
    """主函數 - 報告生成器入口點"""
    print("📊 LLM模型對比分析報告生成器")
    print("=" * 60)
    
    # 創建報告生成器
    generator = LLMComparisonReportGenerator()
    
    # 查找測試結果文件
    result_files = []
    current_dir = Path(".")
    
    # 搜尋測試結果文件
    patterns = [
        "*test_results*.json",
        "*llm_test*.json",
        "*comparison*.json",
        "*benchmark*.json"
    ]
    
    for pattern in patterns:
        result_files.extend(current_dir.glob(pattern))
    
    if not result_files:
        print("❌ 未找到測試結果文件")
        print("請確保當前目錄下有以下格式的文件:")
        for pattern in patterns:
            print(f"   - {pattern}")
        return
    
    print(f"\n📂 找到 {len(result_files)} 個測試結果文件:")
    for file in result_files:
        print(f"   - {file}")
    
    try:
        # 載入測試結果
        generator.load_test_results([str(f) for f in result_files])
        
        # 分析對比指標
        generator.analyze_comparison_metrics()
        
        # 分析各類別表現
        generator.analyze_categories()
        
        # 生成圖表
        chart_files = generator.generate_charts()
        
        # 生成HTML報告
        html_report = generator.generate_html_report(chart_files)
        
        # 保存分析數據
        data_file = generator.save_comparison_data()
        
        # 顯示摘要
        generator.print_summary()
        
        print(f"\n✅ 報告生成完成！")
        print(f"   📄 HTML報告: {html_report}")
        print(f"   💾 分析數據: {data_file}")
        print(f"   📊 圖表目錄: {generator.output_dir / 'charts'}")
        
    except KeyboardInterrupt:
        print("\n❌ 報告生成被用戶中斷")
    except Exception as e:
        print(f"\n❌ 報告生成過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()