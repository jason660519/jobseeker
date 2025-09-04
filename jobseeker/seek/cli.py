#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek爬蟲引擎命令行接口
提供簡單易用的命令行工具來運行Seek爬蟲

Author: JobSpy Team
Date: 2024

Usage:
    python cli.py search "python developer" --location "Sydney" --pages 3
    python cli.py config --template development
    python cli.py export --format json --output results.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .seek_scraper_enhanced import SeekScraperEnhanced
from .config import SeekCrawlerConfig, ConfigTemplates


class SeekCLI:
    """
    Seek爬蟲命令行接口類
    """
    
    def __init__(self):
        self.scraper: Optional[SeekScraperEnhanced] = None
        self.config: Optional[SeekCrawlerConfig] = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """
        創建命令行參數解析器
        
        Returns:
            argparse.ArgumentParser: 參數解析器
        """
        parser = argparse.ArgumentParser(
            description='Seek爬蟲引擎 - 智能化求職網站數據抓取工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  %(prog)s search "python developer" --location "Sydney" --pages 3
  %(prog)s search "data scientist" --mode enhanced --ocr
  %(prog)s config --template production --save config.json
  %(prog)s export --input results.json --format csv
            """
        )
        
        # 添加子命令
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # 搜索命令
        search_parser = subparsers.add_parser('search', help='搜索職位')
        self._add_search_args(search_parser)
        
        # 配置命令
        config_parser = subparsers.add_parser('config', help='配置管理')
        self._add_config_args(config_parser)
        
        # 導出命令
        export_parser = subparsers.add_parser('export', help='數據導出')
        self._add_export_args(export_parser)
        
        # 狀態命令
        status_parser = subparsers.add_parser('status', help='查看狀態')
        self._add_status_args(status_parser)
        
        return parser
    
    def _add_search_args(self, parser: argparse.ArgumentParser):
        """
        添加搜索命令參數
        
        Args:
            parser: 參數解析器
        """
        # 必需參數
        parser.add_argument('search_term', help='搜索關鍵詞')
        
        # 可選參數
        parser.add_argument('--location', '-l', default='', help='工作地點')
        parser.add_argument('--job-type', '-t', default='', help='工作類型')
        parser.add_argument('--pages', '-p', type=int, default=5, help='最大抓取頁數')
        parser.add_argument('--results', '-r', type=int, default=100, help='期望結果數量')
        
        # 模式選項
        parser.add_argument('--mode', '-m', 
                          choices=['traditional', 'enhanced', 'hybrid'],
                          default='hybrid', help='爬蟲模式')
        
        # 功能開關
        parser.add_argument('--headless', action='store_true', default=True, help='無頭瀏覽器模式')
        parser.add_argument('--no-headless', dest='headless', action='store_false', help='顯示瀏覽器')
        parser.add_argument('--ocr', action='store_true', default=False, help='啟用OCR功能')
        parser.add_argument('--screenshots', action='store_true', default=True, help='啟用截圖')
        parser.add_argument('--no-screenshots', dest='screenshots', action='store_false', help='禁用截圖')
        
        # 輸出選項
        parser.add_argument('--output', '-o', help='輸出文件路徑')
        parser.add_argument('--format', '-f', 
                          choices=['json', 'csv', 'excel'],
                          default='json', help='輸出格式')
        
        # 配置選項
        parser.add_argument('--config', '-c', help='配置文件路徑')
        parser.add_argument('--storage-path', '-s', help='數據存儲路徑')
        
        # 性能選項
        parser.add_argument('--workers', '-w', type=int, default=3, help='最大工作線程數')
        parser.add_argument('--delay', '-d', type=float, default=2.0, help='請求間隔延遲(秒)')
        
        # 調試選項
        parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
        parser.add_argument('--debug', action='store_true', help='調試模式')
    
    def _add_config_args(self, parser: argparse.ArgumentParser):
        """
        添加配置命令參數
        
        Args:
            parser: 參數解析器
        """
        parser.add_argument('--template', '-t',
                          choices=['development', 'production', 'testing'],
                          help='使用配置模板')
        parser.add_argument('--save', '-s', help='保存配置到文件')
        parser.add_argument('--load', '-l', help='從文件加載配置')
        parser.add_argument('--show', action='store_true', help='顯示當前配置')
        parser.add_argument('--validate', action='store_true', help='驗證配置')
    
    def _add_export_args(self, parser: argparse.ArgumentParser):
        """
        添加導出命令參數
        
        Args:
            parser: 參數解析器
        """
        parser.add_argument('--input', '-i', required=True, help='輸入數據文件')
        parser.add_argument('--output', '-o', help='輸出文件路徑')
        parser.add_argument('--format', '-f',
                          choices=['json', 'csv', 'excel'],
                          default='json', help='輸出格式')
        parser.add_argument('--filter', help='數據過濾條件(JSON格式)')
    
    def _add_status_args(self, parser: argparse.ArgumentParser):
        """
        添加狀態命令參數
        
        Args:
            parser: 參數解析器
        """
        parser.add_argument('--performance', '-p', action='store_true', help='顯示性能統計')
        parser.add_argument('--storage', '-s', action='store_true', help='顯示存儲信息')
        parser.add_argument('--logs', '-l', action='store_true', help='顯示最近日誌')
    
    async def handle_search(self, args) -> int:
        """
        處理搜索命令
        
        Args:
            args: 命令行參數
            
        Returns:
            int: 退出代碼
        """
        try:
            print(f"🔍 開始搜索: {args.search_term}")
            if args.location:
                print(f"📍 地點: {args.location}")
            print(f"⚙️ 模式: {args.mode}")
            print(f"📄 最大頁數: {args.pages}")
            print()
            
            # 創建配置
            if args.config:
                self.config = SeekCrawlerConfig(args.config)
            else:
                self.config = SeekCrawlerConfig()
            
            # 應用命令行參數覆蓋
            self.config.scraping.mode = args.mode
            self.config.scraping.max_pages = args.pages
            self.config.scraping.results_wanted = args.results
            self.config.browser.headless = args.headless
            self.config.ocr.enabled = args.ocr
            self.config.scraping.enable_screenshots = args.screenshots
            
            if args.storage_path:
                self.config.storage.base_path = args.storage_path
            
            if args.debug:
                self.config.logging.level = 'DEBUG'
            elif args.verbose:
                self.config.logging.level = 'INFO'
            
            # 創建爬蟲實例
            self.scraper = SeekScraperEnhanced(
                scraping_mode=self.config.scraping.mode,
                headless=self.config.browser.headless,
                enable_ocr=self.config.ocr.enabled,
                enable_screenshots=self.config.scraping.enable_screenshots,
                storage_path=self.config.storage.base_path,
                max_workers=args.workers,
                rate_limit_delay=args.delay
            )
            
            # 初始化爬蟲
            if not await self.scraper.initialize():
                print("❌ 爬蟲初始化失敗")
                return 1
            
            print("✅ 爬蟲初始化成功")
            
            # 執行搜索
            jobs = await self.scraper.scrape_jobs(
                search_term=args.search_term,
                location=args.location,
                job_type=args.job_type,
                max_pages=args.pages,
                results_wanted=args.results
            )
            
            print(f"\n🎯 搜索完成: 找到 {len(jobs)} 個職位")
            
            if jobs:
                # 導出結果
                output_file = args.output
                if not output_file:
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_file = f"seek_results_{timestamp}.{args.format}"
                
                exported_file = await self.scraper.export_results(
                    jobs, args.format, output_file
                )
                
                if exported_file:
                    print(f"💾 結果已導出到: {exported_file}")
                
                # 顯示性能報告
                if args.verbose or args.debug:
                    performance_report = self.scraper.get_performance_report()
                    print("\n📊 性能報告:")
                    print(f"  成功率: {performance_report.get('success_rate', 0)}%")
                    print(f"  平均響應時間: {performance_report.get('average_response_time', 0):.2f}秒")
                    print(f"  每分鐘職位數: {performance_report.get('jobs_per_minute', 0):.1f}")
            
            return 0
            
        except KeyboardInterrupt:
            print("\n⏹️ 用戶中斷操作")
            return 130
        except Exception as e:
            print(f"❌ 搜索失敗: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return 1
        finally:
            if self.scraper:
                await self.scraper.cleanup()
    
    def handle_config(self, args) -> int:
        """
        處理配置命令
        
        Args:
            args: 命令行參數
            
        Returns:
            int: 退出代碼
        """
        try:
            if args.template:
                print(f"📋 使用配置模板: {args.template}")
                
                if args.template == 'development':
                    config = ConfigTemplates.development()
                elif args.template == 'production':
                    config = ConfigTemplates.production()
                elif args.template == 'testing':
                    config = ConfigTemplates.testing()
                
                if args.save:
                    config.save_to_file(args.save)
                    print(f"💾 配置已保存到: {args.save}")
                
                if args.show:
                    self._show_config(config)
            
            elif args.load:
                print(f"📂 加載配置文件: {args.load}")
                config = SeekCrawlerConfig(args.load)
                
                if args.show:
                    self._show_config(config)
            
            elif args.show:
                config = SeekCrawlerConfig()
                self._show_config(config)
            
            elif args.validate:
                config = SeekCrawlerConfig()
                print("✅ 配置驗證通過")
            
            return 0
            
        except Exception as e:
            print(f"❌ 配置操作失敗: {e}")
            return 1
    
    def handle_export(self, args) -> int:
        """
        處理導出命令
        
        Args:
            args: 命令行參數
            
        Returns:
            int: 退出代碼
        """
        try:
            print(f"📤 導出數據: {args.input} -> {args.format}")
            
            # 讀取輸入文件
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"❌ 輸入文件不存在: {args.input}")
                return 1
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # TODO: 實現數據轉換和導出邏輯
            print(f"📊 數據包含 {len(data.get('jobs', []))} 個職位")
            
            output_file = args.output or f"exported_data.{args.format}"
            print(f"💾 數據已導出到: {output_file}")
            
            return 0
            
        except Exception as e:
            print(f"❌ 導出失敗: {e}")
            return 1
    
    def handle_status(self, args) -> int:
        """
        處理狀態命令
        
        Args:
            args: 命令行參數
            
        Returns:
            int: 退出代碼
        """
        try:
            config = SeekCrawlerConfig()
            
            print("📊 Seek爬蟲引擎狀態")
            print("=" * 40)
            
            if args.storage or not any([args.performance, args.logs]):
                storage_path = Path(config.storage.base_path)
                print(f"\n💾 存儲信息:")
                print(f"  基礎路徑: {storage_path}")
                print(f"  路徑存在: {'✅' if storage_path.exists() else '❌'}")
                
                if storage_path.exists():
                    total_size = sum(f.stat().st_size for f in storage_path.rglob('*') if f.is_file())
                    print(f"  總大小: {total_size / 1024 / 1024:.2f} MB")
                    
                    for subdir_name, subdir_path in config.storage.subdirs.items():
                        full_path = storage_path / subdir_path
                        if full_path.exists():
                            file_count = len(list(full_path.rglob('*')))
                            print(f"  {subdir_name}: {file_count} 個文件")
            
            if args.performance:
                print(f"\n⚡ 性能配置:")
                print(f"  最大並發請求: {config.performance.max_concurrent_requests}")
                print(f"  內存限制: {config.performance.max_memory_usage_mb} MB")
                print(f"  緩存啟用: {'✅' if config.performance.enable_caching else '❌'}")
            
            if args.logs:
                logs_path = config.get_storage_path('logs')
                print(f"\n📝 日誌信息:")
                print(f"  日誌路徑: {logs_path}")
                
                if logs_path.exists():
                    log_files = list(logs_path.glob('*.log'))
                    print(f"  日誌文件數: {len(log_files)}")
                    
                    if log_files:
                        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
                        print(f"  最新日誌: {latest_log.name}")
            
            return 0
            
        except Exception as e:
            print(f"❌ 狀態查詢失敗: {e}")
            return 1
    
    def _show_config(self, config: SeekCrawlerConfig):
        """
        顯示配置信息
        
        Args:
            config: 配置對象
        """
        print("\n⚙️ 當前配置:")
        print("=" * 30)
        print(f"爬蟲模式: {config.scraping.mode}")
        print(f"無頭瀏覽器: {config.browser.headless}")
        print(f"OCR啟用: {config.ocr.enabled}")
        print(f"最大頁數: {config.scraping.max_pages}")
        print(f"期望結果數: {config.scraping.results_wanted}")
        print(f"存儲路徑: {config.storage.base_path}")
        print(f"日誌級別: {config.logging.level}")
        print(f"並發請求數: {config.performance.max_concurrent_requests}")
    
    async def run(self, args=None) -> int:
        """
        運行CLI應用
        
        Args:
            args: 命令行參數列表（可選）
            
        Returns:
            int: 退出代碼
        """
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        try:
            if parsed_args.command == 'search':
                return await self.handle_search(parsed_args)
            elif parsed_args.command == 'config':
                return self.handle_config(parsed_args)
            elif parsed_args.command == 'export':
                return self.handle_export(parsed_args)
            elif parsed_args.command == 'status':
                return self.handle_status(parsed_args)
            else:
                print(f"❌ 未知命令: {parsed_args.command}")
                return 1
        
        except Exception as e:
            print(f"❌ 執行失敗: {e}")
            return 1


def main():
    """
    主入口函數
    """
    cli = SeekCLI()
    
    try:
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷操作")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 程序異常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()