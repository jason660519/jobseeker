#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據遷移腳本
將現有的混亂數據重新組織到新的目錄結構中
"""

import json
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

class DataMigrator:
    """數據遷移器"""
    
    def __init__(self, source_dir: str = ".", target_dir: str = "data"):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.migration_log = []
    
    def migrate_all_data(self):
        """遷移所有現有數據"""
        print("🚀 開始數據遷移...")
        
        # 1. 遷移測試結果數據
        self.migrate_test_results()
        
        # 2. 遷移 Web App 下載數據
        self.migrate_web_app_downloads()
        
        # 3. 遷移其他散落的數據文件
        self.migrate_scattered_files()
        
        # 4. 生成遷移報告
        self.generate_migration_report()
        
        print("✅ 數據遷移完成！")
    
    def migrate_test_results(self):
        """遷移測試結果數據"""
        print("📁 遷移測試結果數據...")
        
        test_results_dir = self.source_dir / "tests" / "results"
        if not test_results_dir.exists():
            print("⚠️  測試結果目錄不存在，跳過")
            return
        
        migrated_count = 0
        
        for item in test_results_dir.iterdir():
            if item.is_dir():
                # 處理按時間戳命名的目錄
                if self.is_timestamp_directory(item.name):
                    self.migrate_timestamp_directory(item)
                    migrated_count += 1
                else:
                    # 處理其他目錄
                    self.migrate_other_directory(item)
                    migrated_count += 1
            elif item.is_file() and item.suffix == '.json':
                # 處理單個 JSON 文件
                self.migrate_raw_json_file(item, "unknown", datetime.now().strftime("%Y%m%d_%H%M%S"))
                migrated_count += 1
        
        print(f"✅ 已遷移 {migrated_count} 個測試結果項目")
    
    def is_timestamp_directory(self, dirname: str) -> bool:
        """判斷是否為時間戳目錄"""
        # 匹配格式: search_term_location_YYYYMMDD_HHMMSS
        pattern = r'^[a-zA-Z0-9_]+_\d{8}_\d{6}$'
        return bool(re.match(pattern, dirname))
    
    def migrate_timestamp_directory(self, source_dir: Path):
        """遷移時間戳目錄"""
        print(f"  📂 遷移目錄: {source_dir.name}")
        
        # 解析目錄名
        parts = source_dir.name.split('_')
        if len(parts) >= 3:
            search_term = '_'.join(parts[:-2])
            timestamp = '_'.join(parts[-2:])
        else:
            search_term = source_dir.name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 處理 raw_data 目錄
        raw_data_dir = source_dir / "raw_data"
        if raw_data_dir.exists():
            for json_file in raw_data_dir.glob("*.json"):
                self.migrate_raw_json_file(json_file, search_term, timestamp)
        
        # 處理 csv_data 目錄
        csv_data_dir = source_dir / "csv_data"
        if csv_data_dir.exists():
            for csv_file in csv_data_dir.glob("*.csv"):
                self.migrate_csv_file(csv_file, search_term, timestamp)
        
        # 處理 summary 目錄
        summary_dir = source_dir / "summary"
        if summary_dir.exists():
            for json_file in summary_dir.glob("*.json"):
                self.migrate_raw_json_file(json_file, search_term, timestamp)
    
    def migrate_other_directory(self, source_dir: Path):
        """遷移其他目錄"""
        print(f"  📂 遷移其他目錄: {source_dir.name}")
        
        # 簡單地複製整個目錄到歸檔位置
        archive_dir = self.target_dir / "archive" / source_dir.name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        for item in source_dir.iterdir():
            if item.is_file():
                target_file = archive_dir / item.name
                shutil.copy2(item, target_file)
                
                self.migration_log.append({
                    "action": "migrate_other_file",
                    "source": str(item),
                    "target": str(target_file),
                    "timestamp": datetime.now().isoformat()
                })
    
    def migrate_raw_json_file(self, source_file: Path, search_term: str, timestamp: str):
        """遷移原始 JSON 文件"""
        try:
            # 讀取原始數據
            with open(source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取網站名稱
            site = self.extract_site_from_filename(source_file.name)
            
            # 創建目標目錄
            target_date_dir = self.target_dir / "raw" / "by_date" / timestamp[:8] / site
            target_date_dir.mkdir(parents=True, exist_ok=True)
            
            target_site_dir = self.target_dir / "raw" / "by_site" / site
            target_site_dir.mkdir(parents=True, exist_ok=True)
            
            # 標準化數據格式
            standardized_data = self.standardize_json_data(data, site, search_term, timestamp)
            
            # 保存到新位置
            filename = f"{site}_{search_term}_unknown_{timestamp}.json"
            
            # 保存到按日期分類的目錄
            target_date_file = target_date_dir / filename
            with open(target_date_file, 'w', encoding='utf-8') as f:
                json.dump(standardized_data, f, ensure_ascii=False, indent=2)
            
            # 保存到按網站分類的目錄
            target_site_file = target_site_dir / filename
            with open(target_site_file, 'w', encoding='utf-8') as f:
                json.dump(standardized_data, f, ensure_ascii=False, indent=2)
            
            self.migration_log.append({
                "action": "migrate_raw_json",
                "source": str(source_file),
                "target": str(target_date_file),
                "site": site,
                "search_term": search_term,
                "timestamp": timestamp
            })
            
        except Exception as e:
            print(f"❌ 遷移文件失敗 {source_file}: {e}")
    
    def migrate_csv_file(self, source_file: Path, search_term: str, timestamp: str):
        """遷移 CSV 文件"""
        try:
            # 讀取 CSV 數據
            df = pd.read_csv(source_file, encoding='utf-8')
            
            # 提取網站名稱
            site = self.extract_site_from_filename(source_file.name)
            
            # 創建目標目錄
            target_dir = self.target_dir / "processed" / "csv"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存到新位置
            filename = f"{site}_{search_term}_unknown_{timestamp}.csv"
            target_file = target_dir / filename
            
            df.to_csv(target_file, index=False, encoding='utf-8-sig')
            
            self.migration_log.append({
                "action": "migrate_csv",
                "source": str(source_file),
                "target": str(target_file),
                "site": site,
                "search_term": search_term,
                "timestamp": timestamp
            })
            
        except Exception as e:
            print(f"❌ 遷移 CSV 文件失敗 {source_file}: {e}")
    
    def migrate_web_app_downloads(self):
        """遷移 Web App 下載數據"""
        print("📁 遷移 Web App 下載數據...")
        
        downloads_dir = self.source_dir / "web_app" / "downloads"
        if not downloads_dir.exists():
            print("⚠️  Web App 下載目錄不存在，跳過")
            return
        
        migrated_count = 0
        
        for file_path in downloads_dir.iterdir():
            if file_path.is_file():
                self.migrate_download_file(file_path)
                migrated_count += 1
        
        print(f"✅ 已遷移 {migrated_count} 個下載文件")
    
    def migrate_download_file(self, source_file: Path):
        """遷移下載文件"""
        try:
            # 解析文件名
            filename_parts = source_file.stem.split('_')
            if len(filename_parts) >= 3:
                search_term = filename_parts[1]
                timestamp = filename_parts[2]
            else:
                search_term = "unknown"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 創建目標目錄
            format_type = source_file.suffix[1:]  # 移除點號
            target_dir = self.target_dir / "exports" / format_type
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 複製文件
            target_file = target_dir / source_file.name
            shutil.copy2(source_file, target_file)
            
            self.migration_log.append({
                "action": "migrate_download",
                "source": str(source_file),
                "target": str(target_file),
                "search_term": search_term,
                "timestamp": timestamp,
                "format": format_type
            })
            
        except Exception as e:
            print(f"❌ 遷移下載文件失敗 {source_file}: {e}")
    
    def migrate_scattered_files(self):
        """遷移散落的數據文件"""
        print("📁 遷移散落的數據文件...")
        
        # 查找所有可能的數據文件
        data_patterns = [
            "**/*_jobs_*.json",
            "**/*_results_*.json", 
            "**/*_data_*.json",
            "**/*_jobs_*.csv",
            "**/*_results_*.csv",
            "**/*_data_*.csv"
        ]
        
        migrated_count = 0
        
        for pattern in data_patterns:
            for file_path in self.source_dir.glob(pattern):
                # 跳過已經在目標目錄中的文件
                if str(file_path).startswith(str(self.target_dir)):
                    continue
                
                # 跳過已經處理過的目錄
                if file_path.parent.name in ["raw", "processed", "exports", "reports"]:
                    continue
                
                self.migrate_scattered_file(file_path)
                migrated_count += 1
        
        print(f"✅ 已遷移 {migrated_count} 個散落文件")
    
    def migrate_scattered_file(self, source_file: Path):
        """遷移散落文件"""
        try:
            # 根據文件類型決定目標目錄
            if source_file.suffix == '.json':
                target_dir = self.target_dir / "raw" / "by_site" / "unknown"
            elif source_file.suffix == '.csv':
                target_dir = self.target_dir / "processed" / "csv"
            else:
                return
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 複製文件
            target_file = target_dir / source_file.name
            shutil.copy2(source_file, target_file)
            
            self.migration_log.append({
                "action": "migrate_scattered",
                "source": str(source_file),
                "target": str(target_file),
                "file_type": source_file.suffix
            })
            
        except Exception as e:
            print(f"❌ 遷移散落文件失敗 {source_file}: {e}")
    
    def extract_site_from_filename(self, filename: str) -> str:
        """從文件名提取網站名稱"""
        # 常見的網站名稱映射
        site_mapping = {
            "linkedin": "linkedin",
            "indeed": "indeed", 
            "glassdoor": "glassdoor",
            "tw104": "tw104",
            "tw1111": "tw1111",
            "seek": "seek",
            "ziprecruiter": "ziprecruiter",
            "google": "google"
        }
        
        filename_lower = filename.lower()
        for site_key, site_name in site_mapping.items():
            if site_key in filename_lower:
                return site_name
        
        return "unknown"
    
    def standardize_json_data(self, data: Dict, site: str, search_term: str, timestamp: str) -> Dict:
        """標準化 JSON 數據格式"""
        # 檢查是否已經是標準格式
        if "metadata" in data and "jobs" in data:
            return data
        
        # 轉換為標準格式
        standardized = {
            "metadata": {
                "scrape_id": f"migrated_{timestamp}",
                "site": site,
                "search_term": search_term,
                "location": "unknown",
                "timestamp": timestamp,
                "total_records": len(data.get("data", [])),
                "scraper_version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "migrated": True
            },
            "jobs": data.get("data", [])
        }
        
        return standardized
    
    def generate_migration_report(self):
        """生成遷移報告"""
        report_data = {
            "migration_info": {
                "migrated_at": datetime.now().isoformat(),
                "total_migrations": len(self.migration_log),
                "source_directory": str(self.source_dir),
                "target_directory": str(self.target_dir)
            },
            "migration_log": self.migration_log,
            "summary": self.get_migration_summary()
        }
        
        report_path = self.target_dir / "migration_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📊 遷移報告已生成: {report_path}")
    
    def get_migration_summary(self) -> Dict:
        """獲取遷移摘要"""
        summary = {
            "by_action": {},
            "by_site": {},
            "by_format": {}
        }
        
        for log_entry in self.migration_log:
            action = log_entry.get("action", "unknown")
            site = log_entry.get("site", "unknown")
            format_type = log_entry.get("format", "unknown")
            
            summary["by_action"][action] = summary["by_action"].get(action, 0) + 1
            summary["by_site"][site] = summary["by_site"].get(site, 0) + 1
            summary["by_format"][format_type] = summary["by_format"].get(format_type, 0) + 1
        
        return summary

def main():
    """主函數"""
    print("🚀 開始 JobSpy 數據遷移...")
    
    migrator = DataMigrator()
    migrator.migrate_all_data()
    
    print("✅ 數據遷移完成！")
    print("📁 新的數據目錄結構已創建在 'data/' 目錄中")
    print("📊 詳細的遷移報告請查看 'data/migration_report.json'")

if __name__ == "__main__":
    main()
