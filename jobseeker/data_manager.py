#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy 數據管理模組
統一管理所有爬蟲數據的存儲、組織和檢索
"""

import json
import csv
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import uuid
import pandas as pd
from collections import defaultdict

@dataclass
class DataMetadata:
    """數據元數據"""
    scrape_id: str
    site: str
    search_term: str
    location: str
    timestamp: str
    total_records: int
    scraper_version: str
    file_size: int
    created_at: str

@dataclass
class JobData:
    """標準化職位數據"""
    id: str
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    description: Optional[str] = None
    job_url: Optional[str] = None
    date_posted: Optional[str] = None
    source_site: str = ""
    job_type: Optional[str] = None
    is_remote: Optional[bool] = None
    experience_level: Optional[str] = None
    skills: Optional[List[str]] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None

class DataManager:
    """數據管理器"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.setup_directories()
        self.load_config()
    
    def setup_directories(self):
        """創建目錄結構"""
        directories = [
            "raw/by_date",
            "raw/by_site", 
            "processed/csv",
            "processed/json",
            "processed/combined",
            "exports/csv",
            "exports/json",
            "reports/daily",
            "reports/weekly", 
            "reports/monthly",
            "archive",
            "index"
        ]
        
        for dir_path in directories:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """加載配置"""
        self.config = {
            "naming_convention": "{site}_{term}_{location}_{timestamp}",
            "timestamp_format": "%Y%m%d_%H%M%S",
            "supported_formats": ["json", "csv", "xlsx"],
            "retention_days": 30,
            "compression": True,
            "max_file_size_mb": 100
        }
    
    def generate_scrape_id(self) -> str:
        """生成唯一的爬取ID"""
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        """獲取當前時間戳"""
        return datetime.now().strftime(self.config["timestamp_format"])
    
    def sanitize_filename(self, text: str) -> str:
        """清理文件名中的特殊字符"""
        import re
        # 替換特殊字符為下劃線
        text = re.sub(r'[<>:"/\\|?*]', '_', text)
        # 移除多餘的空格和連字符
        text = re.sub(r'\s+', '_', text.strip())
        text = re.sub(r'_+', '_', text)
        return text
    
    def save_raw_data(
        self, 
        site: str, 
        data: List[Dict], 
        search_term: str, 
        location: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """保存原始數據"""
        timestamp = self.get_timestamp()
        scrape_id = self.generate_scrape_id()
        
        # 清理文件名
        clean_term = self.sanitize_filename(search_term)
        clean_location = self.sanitize_filename(location)
        
        # 構建文件名
        filename = f"{site}_{clean_term}_{clean_location}_{timestamp}.json"
        
        # 按日期分類的目錄
        date_dir = self.base_dir / "raw" / "by_date" / timestamp[:8] / site
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # 按網站分類的目錄
        site_dir = self.base_dir / "raw" / "by_site" / site
        site_dir.mkdir(parents=True, exist_ok=True)
        
        # 準備數據
        file_data = {
            "metadata": {
                "scrape_id": scrape_id,
                "site": site,
                "search_term": search_term,
                "location": location,
                "timestamp": timestamp,
                "total_records": len(data),
                "scraper_version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "custom_metadata": metadata or {}
            },
            "jobs": data
        }
        
        # 保存到按日期分類的目錄
        date_filepath = date_dir / filename
        with open(date_filepath, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, ensure_ascii=False, indent=2)
        
        # 保存到按網站分類的目錄
        site_filepath = site_dir / filename
        with open(site_filepath, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        self.update_index(date_filepath, file_data["metadata"])
        
        print(f"✅ 原始數據已保存: {date_filepath}")
        return str(date_filepath)
    
    def save_processed_data(
        self, 
        data: List[Dict], 
        format: str = "csv",
        filename: Optional[str] = None
    ) -> str:
        """保存處理後的數據"""
        if not filename:
            timestamp = self.get_timestamp()
            filename = f"processed_data_{timestamp}.{format}"
        
        filepath = self.base_dir / "processed" / format / filename
        
        if format.lower() == "csv":
            # 轉換為 DataFrame 並保存
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        elif format.lower() == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 處理後數據已保存: {filepath}")
        return str(filepath)
    
    def save_export_data(
        self, 
        data: List[Dict], 
        format: str = "csv",
        search_term: str = "export",
        location: str = "unknown"
    ) -> str:
        """保存用戶導出數據"""
        timestamp = self.get_timestamp()
        clean_term = self.sanitize_filename(search_term)
        clean_location = self.sanitize_filename(location)
        
        filename = f"jobseeker_{clean_term}_{clean_location}_{timestamp}.{format}"
        filepath = self.base_dir / "exports" / format / filename
        
        if format.lower() == "csv":
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        elif format.lower() == "json":
            export_data = {
                "export_info": {
                    "search_term": search_term,
                    "location": location,
                    "timestamp": timestamp,
                    "total_records": len(data),
                    "exported_at": datetime.now().isoformat()
                },
                "jobs": data
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 導出數據已保存: {filepath}")
        return str(filepath)
    
    def update_index(self, filepath: Path, metadata: Dict):
        """更新數據索引"""
        index_file = self.base_dir / "index" / "data_index.json"
        
        # 加載現有索引
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {
                "total_files": 0,
                "by_site": defaultdict(list),
                "by_date": defaultdict(list),
                "by_search_term": defaultdict(list),
                "files": {}
            }
        
        # 更新索引
        file_info = {
            "filepath": str(filepath),
            "site": metadata["site"],
            "search_term": metadata["search_term"],
            "location": metadata["location"],
            "timestamp": metadata["timestamp"],
            "total_records": metadata["total_records"],
            "created_at": metadata["created_at"]
        }
        
        index["total_files"] += 1
        index["by_site"][metadata["site"]].append(file_info)
        index["by_date"][metadata["timestamp"][:8]].append(file_info)
        index["by_search_term"][metadata["search_term"]].append(file_info)
        index["files"][metadata["scrape_id"]] = file_info
        
        # 保存索引
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def get_data_by_site(self, site: str) -> List[Dict]:
        """根據網站獲取數據"""
        index_file = self.base_dir / "index" / "data_index.json"
        if not index_file.exists():
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        return index.get("by_site", {}).get(site, [])
    
    def get_data_by_date(self, date: str) -> List[Dict]:
        """根據日期獲取數據"""
        index_file = self.base_dir / "index" / "data_index.json"
        if not index_file.exists():
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        return index.get("by_date", {}).get(date, [])
    
    def cleanup_old_data(self, days: Optional[int] = None):
        """清理舊數據"""
        if days is None:
            days = self.config["retention_days"]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y%m%d")
        
        # 掃描所有數據文件
        raw_dir = self.base_dir / "raw" / "by_date"
        archived_count = 0
        
        for date_dir in raw_dir.iterdir():
            if date_dir.is_dir() and date_dir.name < cutoff_str:
                # 移動到歸檔目錄
                archive_dir = self.base_dir / "archive" / date_dir.name
                if archive_dir.exists():
                    shutil.rmtree(archive_dir)
                shutil.move(str(date_dir), str(archive_dir))
                archived_count += 1
        
        print(f"✅ 已歸檔 {archived_count} 個舊數據目錄")
        return archived_count
    
    def generate_report(self, report_type: str = "daily") -> str:
        """生成數據報告"""
        timestamp = self.get_timestamp()
        report_filename = f"{report_type}_report_{timestamp}.json"
        report_path = self.base_dir / "reports" / report_type / report_filename
        
        # 生成報告數據
        report_data = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "data_summary": self.get_data_summary(),
            "site_statistics": self.get_site_statistics(),
            "storage_info": self.get_storage_info()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {report_type} 報告已生成: {report_path}")
        return str(report_path)
    
    def get_data_summary(self) -> Dict:
        """獲取數據摘要"""
        index_file = self.base_dir / "index" / "data_index.json"
        if not index_file.exists():
            return {"total_files": 0, "total_records": 0}
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        total_records = sum(
            file_info.get("total_records", 0) 
            for file_info in index.get("files", {}).values()
        )
        
        return {
            "total_files": index.get("total_files", 0),
            "total_records": total_records,
            "sites": list(index.get("by_site", {}).keys()),
            "date_range": {
                "earliest": min(index.get("by_date", {}).keys()) if index.get("by_date") else None,
                "latest": max(index.get("by_date", {}).keys()) if index.get("by_date") else None
            }
        }
    
    def get_site_statistics(self) -> Dict:
        """獲取網站統計"""
        index_file = self.base_dir / "index" / "data_index.json"
        if not index_file.exists():
            return {}
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        stats = {}
        for site, files in index.get("by_site", {}).items():
            total_records = sum(file_info.get("total_records", 0) for file_info in files)
            stats[site] = {
                "file_count": len(files),
                "total_records": total_records,
                "avg_records_per_file": total_records / len(files) if files else 0
            }
        
        return stats
    
    def get_storage_info(self) -> Dict:
        """獲取存儲信息"""
        total_size = 0
        file_count = 0
        
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "base_directory": str(self.base_dir)
        }

# 全局數據管理器實例
data_manager = DataManager()
