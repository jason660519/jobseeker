#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV格式驗證腳本
檢查JobSeeker下載的CSV檔案是否符合統一格式標準

Author: JobSeeker Team
Date: 2025-01-02
"""

import os
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

class CSVFormatValidator:
    """
    CSV格式驗證器
    """
    
    def __init__(self, downloads_dir="downloads"):
        """
        初始化驗證器
        
        Args:
            downloads_dir: 下載目錄路徑
        """
        self.downloads_dir = Path(downloads_dir)
        # 標準格式欄位 (按照用戶指定的格式)
        self.expected_columns = [
            'SITE', 'TITLE', 'COMPANY', 'CITY', 'STATE', 'JOB_TYPE', 
            'INTERVAL', 'MIN_AMOUNT', 'MAX_AMOUNT', 'JOB_URL', 'DESCRIPTION'
        ]
        self.validation_results = []
    
    def get_csv_files(self):
        """
        獲取所有CSV檔案
        
        Returns:
            list: CSV檔案路徑列表
        """
        if not self.downloads_dir.exists():
            print(f"下載目錄 {self.downloads_dir} 不存在")
            return []
        
        csv_files = list(self.downloads_dir.glob("*.csv"))
        return csv_files
    
    def validate_single_csv(self, csv_path):
        """
        驗證單個CSV檔案
        
        Args:
            csv_path: CSV檔案路徑
            
        Returns:
            dict: 驗證結果
        """
        result = {
            'file_name': csv_path.name,
            'file_path': str(csv_path),
            'file_size': csv_path.stat().st_size,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'row_count': 0,
            'column_count': 0,
            'missing_columns': [],
            'extra_columns': [],
            'encoding': 'unknown'
        }
        
        try:
            # 嘗試不同編碼讀取CSV
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'big5']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    result['encoding'] = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                result['is_valid'] = False
                result['errors'].append("無法讀取CSV檔案，編碼問題")
                return result
            
            # 基本統計
            result['row_count'] = len(df)
            result['column_count'] = len(df.columns)
            
            # 檢查欄位
            actual_columns = list(df.columns)
            expected_set = set(self.expected_columns)
            actual_set = set(actual_columns)
            
            # 缺少的欄位
            missing_columns = expected_set - actual_set
            if missing_columns:
                result['missing_columns'] = list(missing_columns)
                result['errors'].append(f"缺少欄位: {', '.join(missing_columns)}")
                result['is_valid'] = False
            
            # 額外的欄位
            extra_columns = actual_set - expected_set
            if extra_columns:
                result['extra_columns'] = list(extra_columns)
                result['warnings'].append(f"額外欄位: {', '.join(extra_columns)}")
            
            # 檢查欄位順序
            if actual_columns != self.expected_columns:
                result['warnings'].append("欄位順序與預期不符")
            
            # 檢查必要欄位是否有值
            required_fields = ['id', 'title', 'company', 'site']
            for field in required_fields:
                if field in df.columns:
                    null_count = df[field].isnull().sum()
                    if null_count > 0:
                        result['warnings'].append(f"必要欄位 '{field}' 有 {null_count} 個空值")
            
            # 檢查數據類型
            if 'is_remote' in df.columns:
                unique_values = df['is_remote'].unique()
                if not all(val in [True, False, 'True', 'False', 'true', 'false', None] for val in unique_values):
                    result['warnings'].append("is_remote欄位包含非布林值")
            
            # 檢查URL格式
            url_fields = ['job_url', 'company_url']
            for field in url_fields:
                if field in df.columns:
                    non_null_urls = df[field].dropna()
                    if len(non_null_urls) > 0:
                        invalid_urls = non_null_urls[~non_null_urls.str.startswith(('http://', 'https://'))]
                        if len(invalid_urls) > 0:
                            result['warnings'].append(f"{field}欄位有 {len(invalid_urls)} 個無效URL")
            
            # 檢查日期格式
            if 'date_posted' in df.columns:
                non_null_dates = df['date_posted'].dropna()
                if len(non_null_dates) > 0:
                    # 簡單檢查是否包含日期格式
                    date_pattern_count = non_null_dates.str.contains(r'\d{4}-\d{2}-\d{2}').sum()
                    if date_pattern_count < len(non_null_dates) * 0.8:  # 80%的日期應該符合格式
                        result['warnings'].append("date_posted欄位可能包含非標準日期格式")
            
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"讀取檔案時發生錯誤: {str(e)}")
        
        return result
    
    def validate_all_csv_files(self):
        """
        驗證所有CSV檔案
        
        Returns:
            dict: 完整驗證報告
        """
        csv_files = self.get_csv_files()
        
        if not csv_files:
            return {
                'summary': {
                    'total_files': 0,
                    'valid_files': 0,
                    'invalid_files': 0,
                    'validation_date': datetime.now().isoformat()
                },
                'files': []
            }
        
        print(f"開始驗證 {len(csv_files)} 個CSV檔案...")
        
        for csv_file in csv_files:
            print(f"驗證: {csv_file.name}")
            result = self.validate_single_csv(csv_file)
            self.validation_results.append(result)
        
        # 生成摘要
        total_files = len(self.validation_results)
        valid_files = sum(1 for r in self.validation_results if r['is_valid'])
        invalid_files = total_files - valid_files
        
        summary = {
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'success_rate': f"{(valid_files / total_files * 100):.1f}%" if total_files > 0 else "0%",
            'validation_date': datetime.now().isoformat()
        }
        
        return {
            'summary': summary,
            'files': self.validation_results
        }
    
    def generate_validation_report(self, output_file="csv_validation_report.json"):
        """
        生成驗證報告
        
        Args:
            output_file: 輸出檔案路徑
        """
        report = self.validate_all_csv_files()
        
        # 保存報告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        summary = report['summary']
        print(f"\n=== CSV格式驗證報告 ===")
        print(f"驗證時間: {summary['validation_date']}")
        print(f"總檔案數: {summary['total_files']}")
        print(f"有效檔案: {summary['valid_files']}")
        print(f"無效檔案: {summary['invalid_files']}")
        print(f"成功率: {summary['success_rate']}")
        
        # 顯示問題檔案
        invalid_files = [f for f in report['files'] if not f['is_valid']]
        if invalid_files:
            print(f"\n無效檔案詳情:")
            for file_info in invalid_files:
                print(f"  - {file_info['file_name']}: {', '.join(file_info['errors'])}")
        
        # 顯示警告
        files_with_warnings = [f for f in report['files'] if f['warnings']]
        if files_with_warnings:
            print(f"\n有警告的檔案:")
            for file_info in files_with_warnings:
                print(f"  - {file_info['file_name']}: {', '.join(file_info['warnings'])}")
        
        print(f"\n詳細報告已保存到: {output_file}")
        
        return report
    
    def create_format_sample(self, output_file="csv_format_sample.csv"):
        """
        創建標準格式範例CSV檔案
        
        Args:
            output_file: 輸出檔案路徑
        """
        # 創建標準格式範例數據 (按照用戶指定的格式)
        sample_data = {
            'SITE': ['linkedin', 'indeed', 'glassdoor'],
            'TITLE': ['軟體工程師', 'AI Engineer', 'UX Designer'],
            'COMPANY': ['科技公司A', 'AI公司B', '設計公司C'],
            'CITY': ['台北', '新竹', '台中'],
            'STATE': ['台灣', '台灣', '台灣'],
            'JOB_TYPE': ['全職', '全職', '遠端'],
            'INTERVAL': ['月薪', '年薪', '月薪'],
            'MIN_AMOUNT': ['50000', '800000', '45000'],
            'MAX_AMOUNT': ['80000', '1200000', '65000'],
            'JOB_URL': [
                'https://www.linkedin.com/jobs/view/1234567890',
                'https://www.indeed.com/viewjob?jk=1234567891',
                'https://www.glassdoor.com/job-listing/1234567892'
            ],
            'DESCRIPTION': [
                '負責軟體開發、系統設計與維護，需具備Python、Java等程式語言經驗',
                '開發AI模型，進行機器學習演算法研究，需熟悉TensorFlow、PyTorch',
                '負責使用者介面設計，提升使用者體驗，需熟悉Figma、Sketch等設計工具'
            ]
        }
        
        # 創建DataFrame並保存
        df = pd.DataFrame(sample_data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"標準格式範例已保存到: {output_file}")
        return output_file

def main():
    """
    主函數
    """
    validator = CSVFormatValidator()
    
    # 驗證所有CSV檔案
    report = validator.generate_validation_report()
    
    # 創建標準格式範例
    validator.create_format_sample()
    
    return report

if __name__ == "__main__":
    main()