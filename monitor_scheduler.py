#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON調度器監控和管理工具
提供實時監控、性能分析和管理功能

Author: JobSpy Team
Date: 2025-01-27
"""

import os
import sys
import json
import time
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
from collections import defaultdict, deque

# 導入必要的模組
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("警告: requests未安裝，API監控功能將不可用")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil未安裝，系統監控功能將受限")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("警告: redis未安裝，Redis監控功能將不可用")

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("提示: 安裝rich庫可獲得更好的顯示效果: pip install rich")


class SchedulerMonitor:
    """
    調度器監控器
    提供實時監控、性能分析和管理功能
    """

    def __init__(self, config_file: str = "scheduler_config.json", api_base_url: str = None):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # API配置
        if api_base_url:
            self.api_base_url = api_base_url
        else:
            api_config = self.config.get("api", {})
            host = api_config.get("host", "localhost")
            port = api_config.get("port", 8080)
            self.api_base_url = f"http://{host}:{port}"
        
        # 監控數據
        self.metrics_history = deque(maxlen=100)  # 保留最近100個數據點
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "queue_size": 1000,
            "error_rate": 10.0,
            "response_time": 5.0
        }
        
        # Redis連接
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                redis_config = self.config.get("queue", {})
                redis_url = redis_config.get("redis_url", "redis://localhost:6379/0")
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                print(f"Redis連接失敗: {e}")
        
        # Rich控制台
        self.console = Console() if RICH_AVAILABLE else None
        
        # 監控狀態
        self.monitoring = False
        self.monitor_thread = None

    def _load_config(self) -> Dict:
        """載入配置檔案"""
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}

    def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """發送API請求"""
        
        if not REQUESTS_AVAILABLE:
            print("requests庫未安裝，無法發送API請求")
            return None
        
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API請求失敗 ({endpoint}): {e}")
            return None

    def get_scheduler_status(self) -> Optional[Dict]:
        """獲取調度器狀態"""
        return self._make_api_request("/status")

    def get_performance_metrics(self) -> Optional[Dict]:
        """獲取性能指標"""
        return self._make_api_request("/metrics")

    def get_task_list(self, status: str = None, limit: int = 50) -> Optional[List[Dict]]:
        """獲取任務列表"""
        endpoint = f"/tasks?limit={limit}"
        if status:
            endpoint += f"&status={status}"
        
        result = self._make_api_request(endpoint)
        return result.get("tasks", []) if result else None

    def get_system_metrics(self) -> Dict:
        """獲取系統指標"""
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_io": {"bytes_sent": 0, "bytes_recv": 0}
        }
        
        if PSUTIL_AVAILABLE:
            # CPU使用率
            metrics["cpu_usage"] = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            metrics["memory_usage"] = memory.percent
            
            # 磁碟使用率
            disk = psutil.disk_usage('.')
            metrics["disk_usage"] = (disk.used / disk.total) * 100
            
            # 網路IO
            net_io = psutil.net_io_counters()
            metrics["network_io"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            }
        
        return metrics

    def get_redis_metrics(self) -> Dict:
        """獲取Redis指標"""
        
        metrics = {
            "connected": False,
            "memory_usage": 0,
            "connected_clients": 0,
            "total_commands_processed": 0,
            "queue_sizes": {}
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                metrics.update({
                    "connected": True,
                    "memory_usage": info.get("used_memory", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                })
                
                # 獲取隊列大小
                queue_keys = self.redis_client.keys("scheduler:queue:*")
                for key in queue_keys:
                    queue_name = key.decode('utf-8').split(':')[-1]
                    size = self.redis_client.llen(key)
                    metrics["queue_sizes"][queue_name] = size
                    
            except Exception as e:
                print(f"獲取Redis指標失敗: {e}")
        
        return metrics

    def collect_metrics(self) -> Dict:
        """收集所有指標"""
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "scheduler": self.get_scheduler_status(),
            "performance": self.get_performance_metrics(),
            "system": self.get_system_metrics(),
            "redis": self.get_redis_metrics()
        }
        
        return metrics

    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """檢查警報條件"""
        
        alerts = []
        
        # 檢查系統指標
        system_metrics = metrics.get("system", {})
        
        if system_metrics.get("cpu_usage", 0) > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "type": "warning",
                "message": f"CPU使用率過高: {system_metrics['cpu_usage']:.1f}%",
                "timestamp": metrics["timestamp"]
            })
        
        if system_metrics.get("memory_usage", 0) > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "warning",
                "message": f"記憶體使用率過高: {system_metrics['memory_usage']:.1f}%",
                "timestamp": metrics["timestamp"]
            })
        
        # 檢查Redis隊列
        redis_metrics = metrics.get("redis", {})
        queue_sizes = redis_metrics.get("queue_sizes", {})
        
        for queue_name, size in queue_sizes.items():
            if size > self.alert_thresholds["queue_size"]:
                alerts.append({
                    "type": "warning",
                    "message": f"隊列 {queue_name} 積壓過多: {size} 個任務",
                    "timestamp": metrics["timestamp"]
                })
        
        # 檢查調度器狀態
        scheduler_metrics = metrics.get("scheduler", {})
        if scheduler_metrics and not scheduler_metrics.get("is_running", False):
            alerts.append({
                "type": "error",
                "message": "調度器未運行",
                "timestamp": metrics["timestamp"]
            })
        
        return alerts

    def display_metrics_table(self, metrics: Dict):
        """顯示指標表格"""
        
        if not RICH_AVAILABLE:
            self._display_metrics_simple(metrics)
            return
        
        # 創建佈局
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # 標題
        layout["header"].update(
            Panel(f"LLM JSON調度器監控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                  style="bold blue")
        )
        
        # 系統指標表格
        system_table = Table(title="系統指標", show_header=True, header_style="bold magenta")
        system_table.add_column("指標", style="cyan")
        system_table.add_column("數值", style="green")
        system_table.add_column("狀態", style="yellow")
        
        system_metrics = metrics.get("system", {})
        cpu_usage = system_metrics.get("cpu_usage", 0)
        memory_usage = system_metrics.get("memory_usage", 0)
        disk_usage = system_metrics.get("disk_usage", 0)
        
        system_table.add_row(
            "CPU使用率", 
            f"{cpu_usage:.1f}%", 
            "🔴 高" if cpu_usage > 80 else "🟡 中" if cpu_usage > 50 else "🟢 正常"
        )
        system_table.add_row(
            "記憶體使用率", 
            f"{memory_usage:.1f}%", 
            "🔴 高" if memory_usage > 85 else "🟡 中" if memory_usage > 70 else "🟢 正常"
        )
        system_table.add_row(
            "磁碟使用率", 
            f"{disk_usage:.1f}%", 
            "🔴 高" if disk_usage > 90 else "🟡 中" if disk_usage > 80 else "🟢 正常"
        )
        
        layout["left"].update(system_table)
        
        # 調度器狀態表格
        scheduler_table = Table(title="調度器狀態", show_header=True, header_style="bold magenta")
        scheduler_table.add_column("項目", style="cyan")
        scheduler_table.add_column("數值", style="green")
        
        scheduler_metrics = metrics.get("scheduler", {})
        if scheduler_metrics:
            scheduler_table.add_row("運行狀態", "🟢 運行中" if scheduler_metrics.get("is_running") else "🔴 已停止")
            
            stats = scheduler_metrics.get("scheduler_stats", {})
            scheduler_table.add_row("已處理檔案", str(stats.get("total_files_processed", 0)))
            scheduler_table.add_row("處理成功", str(stats.get("successful_tasks", 0)))
            scheduler_table.add_row("處理失敗", str(stats.get("failed_tasks", 0)))
            
            worker_stats = scheduler_metrics.get("worker_stats", {})
            scheduler_table.add_row("活躍工作線程", str(worker_stats.get("active_workers", 0)))
            scheduler_table.add_row("總工作線程", str(worker_stats.get("total_workers", 0)))
        else:
            scheduler_table.add_row("狀態", "🔴 無法連接")
        
        layout["right"].update(scheduler_table)
        
        # Redis和隊列狀態
        redis_info = []
        redis_metrics = metrics.get("redis", {})
        
        if redis_metrics.get("connected"):
            redis_info.append(f"🟢 Redis已連接 ({redis_metrics.get('connected_clients', 0)} 個客戶端)")
            
            queue_sizes = redis_metrics.get("queue_sizes", {})
            if queue_sizes:
                redis_info.append("隊列狀態:")
                for queue_name, size in queue_sizes.items():
                    status_icon = "🔴" if size > 1000 else "🟡" if size > 100 else "🟢"
                    redis_info.append(f"  {status_icon} {queue_name}: {size} 個任務")
        else:
            redis_info.append("🔴 Redis連接失敗")
        
        layout["footer"].update(
            Panel("\n".join(redis_info), title="Redis狀態", style="bold yellow")
        )
        
        self.console.clear()
        self.console.print(layout)

    def _display_metrics_simple(self, metrics: Dict):
        """簡單文本顯示指標"""
        
        print("\n" + "="*60)
        print(f"LLM JSON調度器監控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 系統指標
        print("\n系統指標:")
        print("-" * 20)
        system_metrics = metrics.get("system", {})
        print(f"CPU使用率: {system_metrics.get('cpu_usage', 0):.1f}%")
        print(f"記憶體使用率: {system_metrics.get('memory_usage', 0):.1f}%")
        print(f"磁碟使用率: {system_metrics.get('disk_usage', 0):.1f}%")
        
        # 調度器狀態
        print("\n調度器狀態:")
        print("-" * 20)
        scheduler_metrics = metrics.get("scheduler", {})
        if scheduler_metrics:
            print(f"運行狀態: {'運行中' if scheduler_metrics.get('is_running') else '已停止'}")
            
            stats = scheduler_metrics.get("scheduler_stats", {})
            print(f"已處理檔案: {stats.get('total_files_processed', 0)}")
            print(f"處理成功: {stats.get('successful_tasks', 0)}")
            print(f"處理失敗: {stats.get('failed_tasks', 0)}")
            
            worker_stats = scheduler_metrics.get("worker_stats", {})
            print(f"活躍工作線程: {worker_stats.get('active_workers', 0)}")
            print(f"總工作線程: {worker_stats.get('total_workers', 0)}")
        else:
            print("狀態: 無法連接")
        
        # Redis狀態
        print("\nRedis狀態:")
        print("-" * 20)
        redis_metrics = metrics.get("redis", {})
        if redis_metrics.get("connected"):
            print(f"連接狀態: 已連接 ({redis_metrics.get('connected_clients', 0)} 個客戶端)")
            
            queue_sizes = redis_metrics.get("queue_sizes", {})
            if queue_sizes:
                print("隊列狀態:")
                for queue_name, size in queue_sizes.items():
                    print(f"  {queue_name}: {size} 個任務")
        else:
            print("連接狀態: 連接失敗")

    def start_monitoring(self, interval: int = 5):
        """開始實時監控"""
        
        print(f"開始監控調度器 (刷新間隔: {interval}秒)")
        print("按 Ctrl+C 停止監控")
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # 檢查警報
                alerts = self.check_alerts(metrics)
                if alerts:
                    for alert in alerts:
                        print(f"\n⚠️  警報: {alert['message']}")
                
                # 顯示指標
                self.display_metrics_table(metrics)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n監控已停止")
            self.monitoring = False

    def generate_report(self, hours: int = 24) -> Dict:
        """生成性能報告"""
        
        print(f"正在生成過去 {hours} 小時的性能報告...")
        
        # 收集當前指標
        current_metrics = self.collect_metrics()
        
        # 獲取任務統計
        tasks = self.get_task_list(limit=1000)
        
        # 分析任務狀態
        task_stats = defaultdict(int)
        if tasks:
            for task in tasks:
                task_stats[task.get("status", "unknown")] += 1
        
        # 生成報告
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_hours": hours,
            "current_status": {
                "scheduler_running": current_metrics.get("scheduler", {}).get("is_running", False),
                "redis_connected": current_metrics.get("redis", {}).get("connected", False),
                "system_health": self._assess_system_health(current_metrics)
            },
            "task_statistics": dict(task_stats),
            "performance_summary": {
                "total_tasks": sum(task_stats.values()),
                "success_rate": (task_stats.get("completed", 0) / max(sum(task_stats.values()), 1)) * 100,
                "error_rate": (task_stats.get("failed", 0) / max(sum(task_stats.values()), 1)) * 100
            },
            "system_metrics": current_metrics.get("system", {}),
            "recommendations": self._generate_recommendations(current_metrics, task_stats)
        }
        
        return report

    def _assess_system_health(self, metrics: Dict) -> str:
        """評估系統健康狀況"""
        
        system_metrics = metrics.get("system", {})
        scheduler_metrics = metrics.get("scheduler", {})
        redis_metrics = metrics.get("redis", {})
        
        # 檢查關鍵指標
        issues = []
        
        if not scheduler_metrics.get("is_running", False):
            issues.append("調度器未運行")
        
        if not redis_metrics.get("connected", False):
            issues.append("Redis連接失敗")
        
        if system_metrics.get("cpu_usage", 0) > 80:
            issues.append("CPU使用率過高")
        
        if system_metrics.get("memory_usage", 0) > 85:
            issues.append("記憶體使用率過高")
        
        if issues:
            return f"不良 ({', '.join(issues)})"
        elif (system_metrics.get("cpu_usage", 0) > 50 or 
              system_metrics.get("memory_usage", 0) > 70):
            return "一般"
        else:
            return "良好"

    def _generate_recommendations(self, metrics: Dict, task_stats: Dict) -> List[str]:
        """生成優化建議"""
        
        recommendations = []
        
        system_metrics = metrics.get("system", {})
        scheduler_metrics = metrics.get("scheduler", {})
        redis_metrics = metrics.get("redis", {})
        
        # 系統資源建議
        if system_metrics.get("cpu_usage", 0) > 80:
            recommendations.append("考慮增加CPU資源或減少並發工作線程數量")
        
        if system_metrics.get("memory_usage", 0) > 85:
            recommendations.append("考慮增加記憶體或優化記憶體使用")
        
        # 任務處理建議
        total_tasks = sum(task_stats.values())
        if total_tasks > 0:
            error_rate = (task_stats.get("failed", 0) / total_tasks) * 100
            if error_rate > 10:
                recommendations.append("錯誤率較高，建議檢查任務處理邏輯和錯誤日誌")
        
        # 隊列建議
        queue_sizes = redis_metrics.get("queue_sizes", {})
        for queue_name, size in queue_sizes.items():
            if size > 1000:
                recommendations.append(f"隊列 {queue_name} 積壓嚴重，建議增加工作線程或優化處理速度")
        
        # 工作線程建議
        worker_stats = scheduler_metrics.get("worker_stats", {})
        active_workers = worker_stats.get("active_workers", 0)
        total_workers = worker_stats.get("total_workers", 0)
        
        if total_workers > 0 and (active_workers / total_workers) > 0.9:
            recommendations.append("工作線程使用率很高，考慮增加工作線程數量")
        
        if not recommendations:
            recommendations.append("系統運行良好，無需特別優化")
        
        return recommendations

    def save_report(self, report: Dict, filename: str = None):
        """保存報告到檔案"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scheduler_report_{timestamp}.json"
        
        report_path = Path(filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"報告已保存到: {report_path.absolute()}")

    def restart_scheduler(self) -> bool:
        """重啟調度器"""
        
        print("正在重啟調度器...")
        
        result = self._make_api_request("/restart", method="POST")
        
        if result and result.get("success"):
            print("調度器重啟成功")
            return True
        else:
            print("調度器重啟失敗")
            return False

    def update_config(self, config_updates: Dict) -> bool:
        """更新配置"""
        
        print("正在更新配置...")
        
        result = self._make_api_request("/config", method="PUT", data=config_updates)
        
        if result and result.get("success"):
            print("配置更新成功")
            return True
        else:
            print("配置更新失敗")
            return False


def main():
    """主程序入口"""
    
    parser = argparse.ArgumentParser(description="LLM JSON調度器監控工具")
    parser.add_argument("action", 
                       choices=["monitor", "status", "report", "restart", "tasks"],
                       help="要執行的操作")
    parser.add_argument("--config", default="scheduler_config.json",
                       help="配置檔案路徑")
    parser.add_argument("--api-url", 
                       help="API基礎URL (例如: http://localhost:8080)")
    parser.add_argument("--interval", type=int, default=5,
                       help="監控刷新間隔（秒）")
    parser.add_argument("--hours", type=int, default=24,
                       help="報告時間範圍（小時）")
    parser.add_argument("--output", 
                       help="報告輸出檔案名")
    parser.add_argument("--task-status", 
                       choices=["pending", "processing", "completed", "failed"],
                       help="過濾任務狀態")
    parser.add_argument("--limit", type=int, default=50,
                       help="任務列表限制數量")
    
    args = parser.parse_args()
    
    monitor = SchedulerMonitor(args.config, args.api_url)
    
    if args.action == "monitor":
        monitor.start_monitoring(args.interval)
    
    elif args.action == "status":
        metrics = monitor.collect_metrics()
        monitor.display_metrics_table(metrics)
    
    elif args.action == "report":
        report = monitor.generate_report(args.hours)
        
        # 顯示報告摘要
        print("\n" + "="*60)
        print("性能報告摘要")
        print("="*60)
        print(f"生成時間: {report['generated_at']}")
        print(f"時間範圍: 過去 {report['period_hours']} 小時")
        print(f"系統健康: {report['current_status']['system_health']}")
        print(f"總任務數: {report['performance_summary']['total_tasks']}")
        print(f"成功率: {report['performance_summary']['success_rate']:.1f}%")
        print(f"錯誤率: {report['performance_summary']['error_rate']:.1f}%")
        
        print("\n優化建議:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
        
        # 保存報告
        if args.output:
            monitor.save_report(report, args.output)
        else:
            monitor.save_report(report)
    
    elif args.action == "restart":
        monitor.restart_scheduler()
    
    elif args.action == "tasks":
        tasks = monitor.get_task_list(args.task_status, args.limit)
        
        if tasks:
            print(f"\n找到 {len(tasks)} 個任務:")
            print("-" * 80)
            
            for task in tasks:
                print(f"ID: {task.get('id', 'N/A')}")
                print(f"狀態: {task.get('status', 'N/A')}")
                print(f"類型: {task.get('task_type', 'N/A')}")
                print(f"創建時間: {task.get('created_at', 'N/A')}")
                if task.get('error_message'):
                    print(f"錯誤: {task['error_message']}")
                print("-" * 40)
        else:
            print("未找到任務或無法連接到API")


if __name__ == "__main__":
    main()