#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM測試結果可視化儀表板
用於生成互動式圖表和儀表板，展示LLM模型測試結果的詳細分析

Author: JobSpy Team
Date: 2025-01-27
"""

import sys
import os
import json
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import base64
from io import BytesIO
import warnings
from collections import defaultdict, Counter
import statistics

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMProvider

warnings.filterwarnings('ignore')


@dataclass
class VisualizationConfig:
    """可視化配置"""
    theme: str = "plotly_white"  # 主題
    color_palette: List[str] = field(default_factory=lambda: [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ])
    font_family: str = "Arial, sans-serif"
    font_size: int = 12
    chart_height: int = 500
    chart_width: int = 800
    show_grid: bool = True
    show_legend: bool = True


class LLMTestVisualizationDashboard:
    """LLM測試結果可視化儀表板"""
    
    def __init__(self, config: VisualizationConfig = None):
        """初始化儀表板"""
        self.config = config or VisualizationConfig()
        self.test_data: List[Dict[str, Any]] = []
        self.processed_data: Dict[str, pd.DataFrame] = {}
        self.charts: Dict[str, go.Figure] = {}
        
        # 設置Plotly默認配置
        self._setup_plotly_config()
    
    def _setup_plotly_config(self):
        """設置Plotly配置"""
        # 設置默認模板
        import plotly.io as pio
        pio.templates.default = self.config.theme
        
        # 設置字體
        self.font_config = dict(
            family=self.config.font_family,
            size=self.config.font_size,
            color="#2E2E2E"
        )
    
    def load_test_results(self, result_files: List[str]) -> None:
        """載入測試結果文件"""
        print("📂 載入測試結果文件...")
        
        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.test_data.append({
                        'file': file_path,
                        'data': data,
                        'timestamp': os.path.getmtime(file_path)
                    })
                print(f"   ✅ 已載入: {file_path}")
            except Exception as e:
                print(f"   ❌ 載入失敗 {file_path}: {str(e)}")
        
        print(f"📊 總共載入 {len(self.test_data)} 個結果文件")
        
        # 處理數據
        self._process_data()
    
    def _process_data(self) -> None:
        """處理測試數據"""
        print("🔄 處理測試數據...")
        
        # 提取性能指標
        performance_data = []
        comparison_data = []
        benchmark_data = []
        stress_data = []
        
        for file_info in self.test_data:
            data = file_info['data']
            file_name = Path(file_info['file']).name
            timestamp = datetime.fromtimestamp(file_info['timestamp'])
            
            # 根據文件類型處理數據
            if 'performance' in file_name.lower():
                performance_data.extend(self._extract_performance_data(data, timestamp))
            elif 'comparison' in file_name.lower():
                comparison_data.extend(self._extract_comparison_data(data, timestamp))
            elif 'benchmark' in file_name.lower():
                benchmark_data.extend(self._extract_benchmark_data(data, timestamp))
            elif 'stress' in file_name.lower():
                stress_data.extend(self._extract_stress_data(data, timestamp))
            else:
                # 通用數據處理
                performance_data.extend(self._extract_generic_data(data, timestamp))
        
        # 轉換為DataFrame
        if performance_data:
            self.processed_data['performance'] = pd.DataFrame(performance_data)
        if comparison_data:
            self.processed_data['comparison'] = pd.DataFrame(comparison_data)
        if benchmark_data:
            self.processed_data['benchmark'] = pd.DataFrame(benchmark_data)
        if stress_data:
            self.processed_data['stress'] = pd.DataFrame(stress_data)
        
        print(f"   📈 已處理 {len(self.processed_data)} 種類型的數據")
    
    def _extract_performance_data(self, data: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """提取性能數據"""
        results = []
        
        # 處理性能分析結果
        if 'analysis_results' in data:
            for provider, metrics in data['analysis_results'].items():
                if isinstance(metrics, dict):
                    result = {
                        'timestamp': timestamp,
                        'provider': provider,
                        'data_type': 'performance',
                        'success_rate': metrics.get('success_rate', 0.0),
                        'avg_response_time': metrics.get('avg_response_time', 0.0),
                        'throughput': metrics.get('throughput', 0.0),
                        'accuracy_score': metrics.get('accuracy_score', 0.0),
                        'consistency_score': metrics.get('consistency_score', 0.0),
                        'robustness_score': metrics.get('robustness_score', 0.0),
                        'cost_efficiency': metrics.get('cost_efficiency', 0.0),
                        'overall_score': metrics.get('overall_score', 0.0)
                    }
                    results.append(result)
        
        return results
    
    def _extract_comparison_data(self, data: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """提取對比數據"""
        results = []
        
        # 處理對比測試結果
        if 'comparison_results' in data:
            for result in data['comparison_results']:
                if isinstance(result, dict):
                    extracted = {
                        'timestamp': timestamp,
                        'provider': result.get('provider', 'unknown'),
                        'data_type': 'comparison',
                        'test_category': result.get('test_category', 'general'),
                        'success_rate': result.get('success_rate', 0.0),
                        'avg_response_time': result.get('avg_response_time', 0.0),
                        'throughput': result.get('throughput', 0.0),
                        'accuracy': result.get('accuracy', 0.0),
                        'total_tests': result.get('total_tests', 0)
                    }
                    results.append(extracted)
        
        return results
    
    def _extract_benchmark_data(self, data: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """提取基準測試數據"""
        results = []
        
        # 處理基準測試結果
        if 'benchmark_results' in data:
            for category, category_results in data['benchmark_results'].items():
                if isinstance(category_results, dict):
                    for provider, metrics in category_results.items():
                        if isinstance(metrics, dict):
                            result = {
                                'timestamp': timestamp,
                                'provider': provider,
                                'data_type': 'benchmark',
                                'category': category,
                                'score': metrics.get('score', 0.0),
                                'accuracy': metrics.get('accuracy', 0.0),
                                'response_time': metrics.get('response_time', 0.0),
                                'test_count': metrics.get('test_count', 0)
                            }
                            results.append(result)
        
        return results
    
    def _extract_stress_data(self, data: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """提取壓力測試數據"""
        results = []
        
        # 處理壓力測試結果
        if 'stress_results' in data:
            for test_type, test_results in data['stress_results'].items():
                if isinstance(test_results, dict):
                    for provider, metrics in test_results.items():
                        if isinstance(metrics, dict):
                            result = {
                                'timestamp': timestamp,
                                'provider': provider,
                                'data_type': 'stress',
                                'stress_type': test_type,
                                'success_rate': metrics.get('success_rate', 0.0),
                                'avg_response_time': metrics.get('avg_response_time', 0.0),
                                'max_response_time': metrics.get('max_response_time', 0.0),
                                'throughput': metrics.get('throughput', 0.0),
                                'error_rate': metrics.get('error_rate', 0.0),
                                'memory_usage': metrics.get('memory_usage', 0.0)
                            }
                            results.append(result)
        
        return results
    
    def _extract_generic_data(self, data: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """提取通用數據"""
        results = []
        
        # 嘗試從各種可能的結構中提取數據
        if 'results' in data:
            for result in data['results']:
                if isinstance(result, dict) and 'provider' in result:
                    extracted = {
                        'timestamp': timestamp,
                        'provider': result.get('provider', 'unknown'),
                        'data_type': 'generic',
                        'success_rate': result.get('success_rate', 0.0),
                        'avg_response_time': result.get('avg_response_time', 0.0),
                        'throughput': result.get('throughput', 0.0)
                    }
                    results.append(extracted)
        
        return results
    
    def create_performance_overview_chart(self) -> go.Figure:
        """創建性能概覽圖表"""
        if 'performance' not in self.processed_data:
            return self._create_empty_chart("沒有性能數據可顯示")
        
        df = self.processed_data['performance']
        
        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('成功率對比', '響應時間對比', '吞吐量對比', '綜合評分對比'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        providers = df['provider'].unique()
        colors = self.config.color_palette[:len(providers)]
        
        # 成功率柱狀圖
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            fig.add_trace(
                go.Bar(
                    x=[provider],
                    y=[provider_data['success_rate'].mean() * 100],
                    name=provider,
                    marker_color=colors[i],
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # 響應時間箱線圖
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            fig.add_trace(
                go.Box(
                    y=provider_data['avg_response_time'],
                    name=provider,
                    marker_color=colors[i],
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # 吞吐量散點圖
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            fig.add_trace(
                go.Scatter(
                    x=provider_data['avg_response_time'],
                    y=provider_data['throughput'],
                    mode='markers',
                    name=provider,
                    marker=dict(color=colors[i], size=10),
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # 綜合評分雷達圖（簡化版）
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            avg_score = provider_data['overall_score'].mean()
            fig.add_trace(
                go.Bar(
                    x=[provider],
                    y=[avg_score],
                    name=provider,
                    marker_color=colors[i],
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text="LLM性能概覽儀表板",
                font=dict(size=20, family=self.config.font_family)
            ),
            height=800,
            showlegend=True,
            font=self.font_config
        )
        
        # 更新軸標籤
        fig.update_xaxes(title_text="提供商", row=1, col=1)
        fig.update_yaxes(title_text="成功率 (%)", row=1, col=1)
        
        fig.update_xaxes(title_text="提供商", row=1, col=2)
        fig.update_yaxes(title_text="響應時間 (秒)", row=1, col=2)
        
        fig.update_xaxes(title_text="響應時間 (秒)", row=2, col=1)
        fig.update_yaxes(title_text="吞吐量 (請求/秒)", row=2, col=1)
        
        fig.update_xaxes(title_text="提供商", row=2, col=2)
        fig.update_yaxes(title_text="綜合評分", row=2, col=2)
        
        self.charts['performance_overview'] = fig
        return fig
    
    def create_comparison_radar_chart(self) -> go.Figure:
        """創建對比雷達圖"""
        if 'performance' not in self.processed_data:
            return self._create_empty_chart("沒有性能數據可顯示")
        
        df = self.processed_data['performance']
        
        # 準備雷達圖數據
        categories = ['成功率', '響應時間', '吞吐量', '準確性', '一致性', '魯棒性', '成本效率']
        
        fig = go.Figure()
        
        providers = df['provider'].unique()
        colors = self.config.color_palette[:len(providers)]
        
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            
            # 計算各項指標的平均值並正規化
            values = [
                provider_data['success_rate'].mean(),
                1.0 - min(provider_data['avg_response_time'].mean() / 30.0, 1.0),  # 響應時間反轉
                min(provider_data['throughput'].mean() / 10.0, 1.0),  # 正規化吞吐量
                provider_data['accuracy_score'].mean(),
                provider_data['consistency_score'].mean(),
                provider_data['robustness_score'].mean(),
                provider_data['cost_efficiency'].mean()
            ]
            
            # 閉合雷達圖
            values += values[:1]
            categories_closed = categories + categories[:1]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories_closed,
                fill='toself',
                name=provider,
                line_color=colors[i],
                fillcolor=colors[i],
                opacity=0.6
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title=dict(
                text="LLM提供商綜合性能雷達圖",
                font=dict(size=18, family=self.config.font_family)
            ),
            showlegend=True,
            font=self.font_config,
            height=600
        )
        
        self.charts['comparison_radar'] = fig
        return fig
    
    def create_time_series_chart(self) -> go.Figure:
        """創建時間序列圖表"""
        if not self.processed_data:
            return self._create_empty_chart("沒有時間序列數據可顯示")
        
        fig = go.Figure()
        
        # 合併所有數據
        all_data = []
        for data_type, df in self.processed_data.items():
            df_copy = df.copy()
            df_copy['data_source'] = data_type
            all_data.append(df_copy)
        
        if not all_data:
            return self._create_empty_chart("沒有數據可顯示")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 按提供商分組繪製時間序列
        providers = combined_df['provider'].unique()
        colors = self.config.color_palette[:len(providers)]
        
        for i, provider in enumerate(providers):
            provider_data = combined_df[combined_df['provider'] == provider]
            
            # 按時間排序
            provider_data = provider_data.sort_values('timestamp')
            
            # 繪製成功率趨勢
            if 'success_rate' in provider_data.columns:
                fig.add_trace(go.Scatter(
                    x=provider_data['timestamp'],
                    y=provider_data['success_rate'] * 100,
                    mode='lines+markers',
                    name=f'{provider} - 成功率',
                    line=dict(color=colors[i]),
                    yaxis='y1'
                ))
            
            # 繪製響應時間趨勢
            if 'avg_response_time' in provider_data.columns:
                fig.add_trace(go.Scatter(
                    x=provider_data['timestamp'],
                    y=provider_data['avg_response_time'],
                    mode='lines+markers',
                    name=f'{provider} - 響應時間',
                    line=dict(color=colors[i], dash='dash'),
                    yaxis='y2'
                ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text="LLM性能時間序列分析",
                font=dict(size=18, family=self.config.font_family)
            ),
            xaxis=dict(title="時間"),
            yaxis=dict(
                title="成功率 (%)",
                side="left"
            ),
            yaxis2=dict(
                title="響應時間 (秒)",
                side="right",
                overlaying="y"
            ),
            showlegend=True,
            font=self.font_config,
            height=500
        )
        
        self.charts['time_series'] = fig
        return fig
    
    def create_benchmark_heatmap(self) -> go.Figure:
        """創建基準測試熱力圖"""
        if 'benchmark' not in self.processed_data:
            return self._create_empty_chart("沒有基準測試數據可顯示")
        
        df = self.processed_data['benchmark']
        
        # 創建透視表
        pivot_table = df.pivot_table(
            values='score',
            index='provider',
            columns='category',
            aggfunc='mean'
        )
        
        # 創建熱力圖
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='RdYlGn',
            text=np.round(pivot_table.values, 3),
            texttemplate="%{text}",
            textfont={"size": 12},
            colorbar=dict(title="分數")
        ))
        
        fig.update_layout(
            title=dict(
                text="LLM基準測試性能熱力圖",
                font=dict(size=18, family=self.config.font_family)
            ),
            xaxis=dict(title="測試類別"),
            yaxis=dict(title="提供商"),
            font=self.font_config,
            height=500
        )
        
        self.charts['benchmark_heatmap'] = fig
        return fig
    
    def create_stress_test_chart(self) -> go.Figure:
        """創建壓力測試圖表"""
        if 'stress' not in self.processed_data:
            return self._create_empty_chart("沒有壓力測試數據可顯示")
        
        df = self.processed_data['stress']
        
        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('成功率 vs 壓力類型', '響應時間分佈', '吞吐量對比', '錯誤率分析'),
            specs=[[{"type": "bar"}, {"type": "box"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        providers = df['provider'].unique()
        stress_types = df['stress_type'].unique()
        colors = self.config.color_palette[:len(providers)]
        
        # 成功率 vs 壓力類型
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            success_rates = []
            for stress_type in stress_types:
                stress_data = provider_data[provider_data['stress_type'] == stress_type]
                avg_success = stress_data['success_rate'].mean() * 100 if not stress_data.empty else 0
                success_rates.append(avg_success)
            
            fig.add_trace(
                go.Bar(
                    x=stress_types,
                    y=success_rates,
                    name=provider,
                    marker_color=colors[i]
                ),
                row=1, col=1
            )
        
        # 響應時間分佈
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            fig.add_trace(
                go.Box(
                    y=provider_data['avg_response_time'],
                    name=provider,
                    marker_color=colors[i],
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # 吞吐量對比
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            avg_throughput = provider_data['throughput'].mean()
            fig.add_trace(
                go.Bar(
                    x=[provider],
                    y=[avg_throughput],
                    name=provider,
                    marker_color=colors[i],
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # 錯誤率分析
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            avg_error_rate = provider_data['error_rate'].mean() * 100
            fig.add_trace(
                go.Bar(
                    x=[provider],
                    y=[avg_error_rate],
                    name=provider,
                    marker_color=colors[i],
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text="LLM壓力測試分析儀表板",
                font=dict(size=18, family=self.config.font_family)
            ),
            height=800,
            showlegend=True,
            font=self.font_config
        )
        
        # 更新軸標籤
        fig.update_xaxes(title_text="壓力類型", row=1, col=1)
        fig.update_yaxes(title_text="成功率 (%)", row=1, col=1)
        
        fig.update_yaxes(title_text="響應時間 (秒)", row=1, col=2)
        
        fig.update_xaxes(title_text="提供商", row=2, col=1)
        fig.update_yaxes(title_text="吞吐量 (請求/秒)", row=2, col=1)
        
        fig.update_xaxes(title_text="提供商", row=2, col=2)
        fig.update_yaxes(title_text="錯誤率 (%)", row=2, col=2)
        
        self.charts['stress_test'] = fig
        return fig
    
    def create_cost_efficiency_chart(self) -> go.Figure:
        """創建成本效率分析圖表"""
        if 'performance' not in self.processed_data:
            return self._create_empty_chart("沒有性能數據可顯示")
        
        df = self.processed_data['performance']
        
        # 創建散點圖：吞吐量 vs 成本效率
        fig = go.Figure()
        
        providers = df['provider'].unique()
        colors = self.config.color_palette[:len(providers)]
        
        for i, provider in enumerate(providers):
            provider_data = df[df['provider'] == provider]
            
            fig.add_trace(go.Scatter(
                x=provider_data['throughput'],
                y=provider_data['cost_efficiency'],
                mode='markers',
                name=provider,
                marker=dict(
                    color=colors[i],
                    size=provider_data['overall_score'] * 20,  # 氣泡大小表示總分
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                text=provider_data['provider'],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "吞吐量: %{x:.2f} 請求/秒<br>"
                    "成本效率: %{y:.3f}<br>"
                    "總分: %{marker.size:.3f}<br>"
                    "<extra></extra>"
                )
            ))
        
        # 添加趨勢線
        if len(df) > 1:
            z = np.polyfit(df['throughput'], df['cost_efficiency'], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(df['throughput'].min(), df['throughput'].max(), 100)
            y_trend = p(x_trend)
            
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=y_trend,
                mode='lines',
                name='趨勢線',
                line=dict(color='red', dash='dash'),
                showlegend=True
            ))
        
        fig.update_layout(
            title=dict(
                text="LLM成本效率分析 (氣泡大小 = 總分)",
                font=dict(size=18, family=self.config.font_family)
            ),
            xaxis=dict(title="吞吐量 (請求/秒)"),
            yaxis=dict(title="成本效率"),
            showlegend=True,
            font=self.font_config,
            height=500
        )
        
        self.charts['cost_efficiency'] = fig
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """創建空圖表"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title=message,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig
    
    def generate_dashboard_html(self, output_file: str = None) -> str:
        """生成儀表板HTML文件"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"llm_dashboard_{timestamp}.html"
        
        print("📊 生成互動式儀表板...")
        
        # 創建所有圖表
        charts = {
            'performance_overview': self.create_performance_overview_chart(),
            'comparison_radar': self.create_comparison_radar_chart(),
            'time_series': self.create_time_series_chart(),
            'benchmark_heatmap': self.create_benchmark_heatmap(),
            'stress_test': self.create_stress_test_chart(),
            'cost_efficiency': self.create_cost_efficiency_chart()
        }
        
        # 生成HTML內容
        html_content = self._generate_html_template(charts)
        
        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   📄 儀表板已生成: {output_file}")
        return output_file
    
    def _generate_html_template(self, charts: Dict[str, go.Figure]) -> str:
        """生成HTML模板"""
        # 將圖表轉換為HTML
        chart_htmls = {}
        for name, fig in charts.items():
            chart_htmls[name] = pyo.plot(fig, output_type='div', include_plotlyjs=False)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM測試結果可視化儀表板</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: {self.config.font_family};
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #4CAF50;
        }}
        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin: 0;
        }}
        .header p {{
            color: #666;
            font-size: 1.2em;
            margin: 10px 0 0 0;
        }}
        .chart-section {{
            margin: 40px 0;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .chart-title {{
            font-size: 1.5em;
            color: #333;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        .chart-container {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .navigation {{
            position: sticky;
            top: 20px;
            background-color: #333;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .navigation a {{
            color: white;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background-color 0.3s;
        }}
        .navigation a:hover {{
            background-color: #555;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LLM測試結果可視化儀表板</h1>
            <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="navigation">
            <a href="#overview">性能概覽</a>
            <a href="#radar">綜合對比</a>
            <a href="#timeseries">時間趨勢</a>
            <a href="#benchmark">基準測試</a>
            <a href="#stress">壓力測試</a>
            <a href="#cost">成本效率</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(self.processed_data)}</div>
                <div class="stat-label">數據類型</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(self.test_data)}</div>
                <div class="stat-label">測試文件</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(charts)}</div>
                <div class="stat-label">可視化圖表</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(df) for df in self.processed_data.values())}</div>
                <div class="stat-label">數據點</div>
            </div>
        </div>
        
        <div id="overview" class="chart-section">
            <div class="chart-title">📊 性能概覽儀表板</div>
            <div class="chart-container">
                {chart_htmls.get('performance_overview', '<p>無數據可顯示</p>')}
            </div>
        </div>
        
        <div id="radar" class="chart-section">
            <div class="chart-title">🎯 綜合性能雷達圖</div>
            <div class="chart-container">
                {chart_htmls.get('comparison_radar', '<p>無數據可顯示</p>')}
            </div>
        </div>
        
        <div id="timeseries" class="chart-section">
            <div class="chart-title">📈 性能時間趨勢</div>
            <div class="chart-container">
                {chart_htmls.get('time_series', '<p>無數據可顯示</p>')}
            </div>
        </div>
        
        <div id="benchmark" class="chart-section">
            <div class="chart-title">🏆 基準測試熱力圖</div>
            <div class="chart-container">
                {chart_htmls.get('benchmark_heatmap', '<p>無數據可顯示</p>')}
            </div>
        </div>
        
        <div id="stress" class="chart-section">
            <div class="chart-title">⚡ 壓力測試分析</div>
            <div class="chart-container">
                {chart_htmls.get('stress_test', '<p>無數據可顯示</p>')}
            </div>
        </div>
        
        <div id="cost" class="chart-section">
            <div class="chart-title">💰 成本效率分析</div>
            <div class="chart-container">
                {chart_htmls.get('cost_efficiency', '<p>無數據可顯示</p>')}
            </div>
        </div>
        
        <div class="footer">
            <p>由 LLM測試結果可視化儀表板 自動生成</p>
            <p>數據更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def export_charts_as_images(self, output_dir: str = "charts") -> Dict[str, str]:
        """導出圖表為圖片文件"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = {}
        
        print("📸 導出圖表為圖片...")
        
        for name, fig in self.charts.items():
            try:
                filename = output_path / f"{name}.png"
                fig.write_image(str(filename), width=1200, height=800, scale=2)
                exported_files[name] = str(filename)
                print(f"   ✅ 已導出: {filename}")
            except Exception as e:
                print(f"   ❌ 導出失敗 {name}: {str(e)}")
        
        return exported_files
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """生成摘要報告"""
        summary = {
            'generation_time': datetime.now().isoformat(),
            'data_summary': {
                'total_files': len(self.test_data),
                'data_types': list(self.processed_data.keys()),
                'total_records': sum(len(df) for df in self.processed_data.values())
            },
            'charts_generated': list(self.charts.keys()),
            'insights': []
        }
        
        # 生成洞察
        if 'performance' in self.processed_data:
            df = self.processed_data['performance']
            
            # 最佳提供商
            if 'overall_score' in df.columns:
                best_provider = df.loc[df['overall_score'].idxmax(), 'provider']
                best_score = df['overall_score'].max()
                summary['insights'].append(f"綜合表現最佳: {best_provider} (分數: {best_score:.3f})")
            
            # 響應時間最快
            if 'avg_response_time' in df.columns:
                fastest_provider = df.loc[df['avg_response_time'].idxmin(), 'provider']
                fastest_time = df['avg_response_time'].min()
                summary['insights'].append(f"響應最快: {fastest_provider} ({fastest_time:.2f}秒)")
            
            # 成功率最高
            if 'success_rate' in df.columns:
                most_reliable = df.loc[df['success_rate'].idxmax(), 'provider']
                highest_success = df['success_rate'].max()
                summary['insights'].append(f"最可靠: {most_reliable} (成功率: {highest_success:.1%})")
        
        return summary


def create_streamlit_dashboard():
    """創建Streamlit儀表板"""
    st.set_page_config(
        page_title="LLM測試結果儀表板",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🤖 LLM測試結果可視化儀表板")
    st.markdown("---")
    
    # 側邊欄
    st.sidebar.header("📁 數據載入")
    
    # 文件上傳
    uploaded_files = st.sidebar.file_uploader(
        "選擇測試結果文件",
        type=['json'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # 創建儀表板實例
        dashboard = LLMTestVisualizationDashboard()
        
        # 保存上傳的文件並載入
        temp_files = []
        for uploaded_file in uploaded_files:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            temp_files.append(temp_path)
        
        try:
            dashboard.load_test_results(temp_files)
            
            # 顯示數據摘要
            st.sidebar.success(f"已載入 {len(temp_files)} 個文件")
            
            summary = dashboard.generate_summary_report()
            st.sidebar.write("**數據摘要:**")
            st.sidebar.write(f"- 總記錄數: {summary['data_summary']['total_records']}")
            st.sidebar.write(f"- 數據類型: {', '.join(summary['data_summary']['data_types'])}")
            
            # 主要內容區域
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📊 性能概覽", "🎯 綜合對比", "📈 時間趨勢", 
                "🏆 基準測試", "⚡ 壓力測試", "💰 成本效率"
            ])
            
            with tab1:
                st.subheader("性能概覽儀表板")
                fig = dashboard.create_performance_overview_chart()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.subheader("綜合性能雷達圖")
                fig = dashboard.create_comparison_radar_chart()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("性能時間趨勢")
                fig = dashboard.create_time_series_chart()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                st.subheader("基準測試熱力圖")
                fig = dashboard.create_benchmark_heatmap()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab5:
                st.subheader("壓力測試分析")
                fig = dashboard.create_stress_test_chart()
                st.plotly_chart(fig, use_container_width=True)
            
            with tab6:
                st.subheader("成本效率分析")
                fig = dashboard.create_cost_efficiency_chart()
                st.plotly_chart(fig, use_container_width=True)
            
            # 洞察摘要
            if summary['insights']:
                st.markdown("---")
                st.subheader("💡 關鍵洞察")
                for insight in summary['insights']:
                    st.write(f"• {insight}")
            
            # 導出選項
            st.markdown("---")
            st.subheader("📥 導出選項")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("生成HTML儀表板"):
                    html_file = dashboard.generate_dashboard_html()
                    st.success(f"HTML儀表板已生成: {html_file}")
            
            with col2:
                if st.button("導出圖表圖片"):
                    exported_files = dashboard.export_charts_as_images()
                    st.success(f"已導出 {len(exported_files)} 個圖表")
        
        finally:
            # 清理臨時文件
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    else:
        st.info("請在側邊欄上傳測試結果文件以開始分析")
        
        # 顯示示例
        st.subheader("📋 支援的文件格式")
        st.write("""
        支援以下類型的JSON測試結果文件:
        - 性能測試結果 (performance_*.json)
        - 對比測試結果 (comparison_*.json)
        - 基準測試結果 (benchmark_*.json)
        - 壓力測試結果 (stress_*.json)
        - 通用測試結果 (test_results_*.json)
        """)


def main():
    """主函數 - 可視化儀表板入口點"""
    print("📊 LLM測試結果可視化儀表板")
    print("=" * 60)
    
    # 檢查是否在Streamlit環境中運行
    try:
        import streamlit as st
        # 如果成功導入且在Streamlit環境中，運行Streamlit應用
        create_streamlit_dashboard()
        return
    except (ImportError, AttributeError):
        pass
    
    # 命令行模式
    dashboard = LLMTestVisualizationDashboard()
    
    # 查找測試結果文件
    result_files = []
    current_dir = Path(".")
    
    patterns = [
        "*test_results*.json",
        "*performance*.json",
        "*comparison*.json",
        "*benchmark*.json",
        "*stress*.json"
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
        dashboard.load_test_results([str(f) for f in result_files])
        
        # 生成HTML儀表板
        html_file = dashboard.generate_dashboard_html()
        
        # 導出圖表
        exported_files = dashboard.export_charts_as_images()
        
        # 生成摘要報告
        summary = dashboard.generate_summary_report()
        
        print(f"\n✅ 儀表板生成完成！")
        print(f"   📄 HTML儀表板: {html_file}")
        print(f"   📊 圖表文件: {len(exported_files)} 個")
        print(f"   💡 關鍵洞察: {len(summary['insights'])} 條")
        
        # 顯示洞察
        if summary['insights']:
            print("\n💡 關鍵洞察:")
            for insight in summary['insights']:
                print(f"   • {insight}")
        
        # 提示如何查看
        print(f"\n🌐 在瀏覽器中打開 {html_file} 查看互動式儀表板")
        
    except KeyboardInterrupt:
        print("\n❌ 儀表板生成被用戶中斷")
    except Exception as e:
        print(f"\n❌ 儀表板生成過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()