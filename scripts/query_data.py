#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據查詢工具
提供命令行界面來查詢和分析爬蟲數據
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class DataQuery:
    """數據查詢器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.index_file = self.data_dir / "index" / "data_index.json"
        self.load_index()
    
    def load_index(self):
        """加載數據索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {"files": {}, "by_site": {}, "by_date": {}, "by_search_term": {}}
    
    def list_sites(self) -> List[str]:
        """列出所有網站"""
        return list(self.index.get("by_site", {}).keys())
    
    def list_dates(self) -> List[str]:
        """列出所有日期"""
        return sorted(self.index.get("by_date", {}).keys())
    
    def list_search_terms(self) -> List[str]:
        """列出所有搜尋詞"""
        return list(self.index.get("by_search_term", {}).keys())
    
    def get_data_by_site(self, site: str) -> List[Dict]:
        """根據網站獲取數據"""
        return self.index.get("by_site", {}).get(site, [])
    
    def get_data_by_date(self, date: str) -> List[Dict]:
        """根據日期獲取數據"""
        return self.index.get("by_date", {}).get(date, [])
    
    def get_data_by_search_term(self, search_term: str) -> List[Dict]:
        """根據搜尋詞獲取數據"""
        return self.index.get("by_search_term", {}).get(search_term, [])
    
    def get_data_summary(self) -> Dict:
        """獲取數據摘要"""
        total_files = len(self.index.get("files", {}))
        total_records = sum(
            file_info.get("total_records", 0) 
            for file_info in self.index.get("files", {}).values()
        )
        
        sites = self.list_sites()
        dates = self.list_dates()
        search_terms = self.list_search_terms()
        
        return {
            "total_files": total_files,
            "total_records": total_records,
            "sites": sites,
            "date_range": {
                "earliest": dates[0] if dates else None,
                "latest": dates[-1] if dates else None
            },
            "unique_search_terms": len(search_terms),
            "unique_sites": len(sites)
        }
    
    def search_data(self, site: Optional[str] = None, date: Optional[str] = None, 
                   search_term: Optional[str] = None) -> List[Dict]:
        """搜尋數據"""
        results = []
        
        if site:
            results.extend(self.get_data_by_site(site))
        
        if date:
            results.extend(self.get_data_by_date(date))
        
        if search_term:
            results.extend(self.get_data_by_search_term(search_term))
        
        # 去重
        seen = set()
        unique_results = []
        for result in results:
            key = result.get("filepath", "")
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def load_job_data(self, filepath: str) -> List[Dict]:
        """加載職位數據"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "jobs" in data:
                return data["jobs"]
            elif "data" in data:
                return data["data"]
            else:
                return data
        except Exception as e:
            print(f"❌ 加載數據失敗 {filepath}: {e}")
            return []
    
    def analyze_jobs(self, jobs: List[Dict]) -> Dict:
        """分析職位數據"""
        if not jobs:
            return {}
        
        df = pd.DataFrame(jobs)
        
        analysis = {
            "total_jobs": len(jobs),
            "unique_companies": df['company'].nunique() if 'company' in df.columns else 0,
            "unique_locations": df['location'].nunique() if 'location' in df.columns else 0,
            "salary_info": self.analyze_salaries(df),
            "top_companies": self.get_top_companies(df),
            "top_locations": self.get_top_locations(df),
            "job_types": self.get_job_types(df)
        }
        
        return analysis
    
    def analyze_salaries(self, df: pd.DataFrame) -> Dict:
        """分析薪資信息"""
        if 'salary' not in df.columns:
            return {"available": False}
        
        salary_data = df[df['salary'].notna() & (df['salary'] != '')]
        
        if len(salary_data) == 0:
            return {"available": False, "count": 0}
        
        return {
            "available": True,
            "count": len(salary_data),
            "percentage": round(len(salary_data) / len(df) * 100, 2)
        }
    
    def get_top_companies(self, df: pd.DataFrame, top_n: int = 10) -> List[Dict]:
        """獲取熱門公司"""
        if 'company' not in df.columns:
            return []
        
        company_counts = df['company'].value_counts().head(top_n)
        
        return [
            {"company": company, "job_count": count}
            for company, count in company_counts.items()
        ]
    
    def get_top_locations(self, df: pd.DataFrame, top_n: int = 10) -> List[Dict]:
        """獲取熱門地點"""
        if 'location' not in df.columns:
            return []
        
        location_counts = df['location'].value_counts().head(top_n)
        
        return [
            {"location": location, "job_count": count}
            for location, count in location_counts.items()
        ]
    
    def get_job_types(self, df: pd.DataFrame) -> Dict:
        """獲取工作類型分布"""
        if 'job_type' not in df.columns:
            return {}
        
        job_type_counts = df['job_type'].value_counts()
        
        return {
            job_type: count
            for job_type, count in job_type_counts.items()
        }
    
    def export_analysis(self, analysis: Dict, output_file: str):
        """導出分析結果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 分析結果已導出: {output_file}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="JobSpy 數據查詢工具")
    parser.add_argument("--data-dir", default="data", help="數據目錄路徑")
    parser.add_argument("--site", help="按網站篩選")
    parser.add_argument("--date", help="按日期篩選 (YYYYMMDD)")
    parser.add_argument("--search-term", help="按搜尋詞篩選")
    parser.add_argument("--summary", action="store_true", help="顯示數據摘要")
    parser.add_argument("--list-sites", action="store_true", help="列出所有網站")
    parser.add_argument("--list-dates", action="store_true", help="列出所有日期")
    parser.add_argument("--analyze", action="store_true", help="分析職位數據")
    parser.add_argument("--export", help="導出分析結果到文件")
    
    args = parser.parse_args()
    
    query = DataQuery(args.data_dir)
    
    if args.list_sites:
        sites = query.list_sites()
        print("📊 可用網站:")
        for site in sites:
            print(f"  - {site}")
    
    elif args.list_dates:
        dates = query.list_dates()
        print("📅 可用日期:")
        for date in dates:
            print(f"  - {date}")
    
    elif args.summary:
        summary = query.get_data_summary()
        print("📊 數據摘要:")
        print(f"  總文件數: {summary['total_files']}")
        print(f"  總職位數: {summary['total_records']}")
        print(f"  網站數: {summary['unique_sites']}")
        print(f"  搜尋詞數: {summary['unique_search_terms']}")
        print(f"  日期範圍: {summary['date_range']['earliest']} ~ {summary['date_range']['latest']}")
    
    else:
        # 搜尋數據
        results = query.search_data(
            site=args.site,
            date=args.date,
            search_term=args.search_term
        )
        
        print(f"🔍 找到 {len(results)} 個匹配的數據文件")
        
        if args.analyze and results:
            # 分析第一個文件的數據
            first_result = results[0]
            jobs = query.load_job_data(first_result['filepath'])
            analysis = query.analyze_jobs(jobs)
            
            print("📊 職位分析:")
            print(f"  總職位數: {analysis.get('total_jobs', 0)}")
            print(f"  公司數: {analysis.get('unique_companies', 0)}")
            print(f"  地點數: {analysis.get('unique_locations', 0)}")
            
            if analysis.get('salary_info', {}).get('available'):
                salary_info = analysis['salary_info']
                print(f"  有薪資資訊: {salary_info['count']} ({salary_info['percentage']}%)")
            
            if analysis.get('top_companies'):
                print("  熱門公司:")
                for company in analysis['top_companies'][:5]:
                    print(f"    - {company['company']}: {company['job_count']} 個職位")
            
            if args.export:
                query.export_analysis(analysis, args.export)

if __name__ == "__main__":
    main()
