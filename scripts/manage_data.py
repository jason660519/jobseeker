#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據管理腳本
提供統一的數據管理命令行界面
"""

import argparse
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from jobseeker.data_manager import data_manager

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="JobSpy 數據管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 數據摘要命令
    summary_parser = subparsers.add_parser('summary', help='顯示數據摘要')
    
    # 清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理舊數據')
    cleanup_parser.add_argument('--days', type=int, default=30, help='保留天數')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='試運行模式')
    
    # 遷移命令
    migrate_parser = subparsers.add_parser('migrate', help='遷移現有數據')
    
    # 查詢命令
    query_parser = subparsers.add_parser('query', help='查詢數據')
    query_parser.add_argument('--site', help='按網站篩選')
    query_parser.add_argument('--date', help='按日期篩選')
    query_parser.add_argument('--search-term', help='按搜尋詞篩選')
    
    args = parser.parse_args()
    
    if args.command == 'summary':
        show_summary()
    elif args.command == 'cleanup':
        cleanup_data(args.days, args.dry_run)
    elif args.command == 'migrate':
        migrate_data()
    elif args.command == 'query':
        query_data(args.site, args.date, args.search_term)
    else:
        parser.print_help()

def show_summary():
    """顯示數據摘要"""
    summary = data_manager.get_data_summary()
    
    print("📊 JobSpy 數據摘要")
    print("=" * 50)
    print(f"總文件數: {summary['total_files']}")
    print(f"總職位數: {summary['total_records']}")
    print(f"網站數: {len(summary.get('sites', []))}")
    date_range = summary.get('date_range', {})
    print(f"日期範圍: {date_range.get('earliest', 'N/A')} ~ {date_range.get('latest', 'N/A')}")
    
    if summary.get('sites'):
        print("\n📈 網站統計:")
        site_stats = data_manager.get_site_statistics()
        for site, stats in site_stats.items():
            print(f"  {site}: {stats['file_count']} 個文件, {stats['total_records']} 個職位")
    
    storage_info = data_manager.get_storage_info()
    print(f"\n💾 存儲信息:")
    print(f"  總大小: {storage_info['total_size_mb']} MB")
    print(f"  文件數: {storage_info['file_count']}")

def cleanup_data(days: int, dry_run: bool):
    """清理數據"""
    if dry_run:
        print(f"🧹 [試運行] 將清理 {days} 天前的數據")
    else:
        print(f"🧹 開始清理 {days} 天前的數據")
        archived_count = data_manager.cleanup_old_data(days)
        print(f"✅ 已歸檔 {archived_count} 個目錄")

def migrate_data():
    """遷移數據"""
    print("🚀 開始數據遷移...")
    
    # 這裡可以調用遷移腳本
    from scripts.migrate_existing_data import DataMigrator
    
    migrator = DataMigrator()
    migrator.migrate_all_data()
    
    print("✅ 數據遷移完成")

def query_data(site: str, date: str, search_term: str):
    """查詢數據"""
    from scripts.query_data import DataQuery
    
    query = DataQuery()
    
    if site:
        results = query.get_data_by_site(site)
        print(f"🔍 網站 '{site}' 的數據: {len(results)} 個文件")
    
    if date:
        results = query.get_data_by_date(date)
        print(f"📅 日期 '{date}' 的數據: {len(results)} 個文件")
    
    if search_term:
        results = query.get_data_by_search_term(search_term)
        print(f"🔍 搜尋詞 '{search_term}' 的數據: {len(results)} 個文件")
    
    if not any([site, date, search_term]):
        # 顯示所有可用選項
        print("📊 可用數據:")
        print(f"  網站: {query.list_sites()}")
        print(f"  日期: {query.list_dates()}")
        print(f"  搜尋詞: {query.list_search_terms()}")

if __name__ == "__main__":
    main()
