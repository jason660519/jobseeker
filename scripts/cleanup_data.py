#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據清理腳本
清理舊數據、壓縮歸檔、生成清理報告
"""

import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import argparse

class DataCleaner:
    """數據清理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cleanup_log = []
    
    def cleanup_old_data(self, retention_days: int = 30, dry_run: bool = False):
        """清理舊數據"""
        print(f"🧹 開始清理 {retention_days} 天前的數據...")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_str = cutoff_date.strftime("%Y%m%d")
        
        # 清理按日期分類的原始數據
        raw_date_dir = self.data_dir / "raw" / "by_date"
        archived_count = 0
        
        if raw_date_dir.exists():
            for date_dir in raw_date_dir.iterdir():
                if date_dir.is_dir() and date_dir.name < cutoff_str:
                    if dry_run:
                        print(f"  [DRY RUN] 將歸檔目錄: {date_dir.name}")
                    else:
                        self.archive_directory(date_dir)
                    archived_count += 1
        
        # 清理舊的導出文件
        exports_dir = self.data_dir / "exports"
        cleaned_exports = 0
        
        if exports_dir.exists():
            for format_dir in exports_dir.iterdir():
                if format_dir.is_dir():
                    cleaned_exports += self.cleanup_old_files(format_dir, cutoff_date, dry_run)
        
        # 清理舊的報告文件
        reports_dir = self.data_dir / "reports"
        cleaned_reports = 0
        
        if reports_dir.exists():
            for report_type_dir in reports_dir.iterdir():
                if report_type_dir.is_dir():
                    cleaned_reports += self.cleanup_old_files(report_type_dir, cutoff_date, dry_run)
        
        print(f"✅ 清理完成:")
        print(f"  - 歸檔了 {archived_count} 個日期目錄")
        print(f"  - 清理了 {cleaned_exports} 個導出文件")
        print(f"  - 清理了 {cleaned_reports} 個報告文件")
        
        return {
            "archived_directories": archived_count,
            "cleaned_exports": cleaned_exports,
            "cleaned_reports": cleaned_reports
        }
    
    def archive_directory(self, source_dir: Path):
        """歸檔目錄"""
        archive_dir = self.data_dir / "archive" / source_dir.name
        
        if archive_dir.exists():
            shutil.rmtree(archive_dir)
        
        shutil.move(str(source_dir), str(archive_dir))
        
        self.cleanup_log.append({
            "action": "archive_directory",
            "source": str(source_dir),
            "target": str(archive_dir),
            "timestamp": datetime.now().isoformat()
        })
    
    def cleanup_old_files(self, directory: Path, cutoff_date: datetime, dry_run: bool = False) -> int:
        """清理目錄中的舊文件"""
        cleaned_count = 0
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    if dry_run:
                        print(f"  [DRY RUN] 將刪除文件: {file_path.name}")
                    else:
                        file_path.unlink()
                        self.cleanup_log.append({
                            "action": "delete_file",
                            "file": str(file_path),
                            "timestamp": datetime.now().isoformat()
                        })
                    cleaned_count += 1
        
        return cleaned_count
    
    def compress_archive(self, compress_days: int = 7):
        """壓縮歸檔數據"""
        print(f"🗜️  開始壓縮 {compress_days} 天前的歸檔數據...")
        
        archive_dir = self.data_dir / "archive"
        if not archive_dir.exists():
            print("⚠️  歸檔目錄不存在，跳過壓縮")
            return 0
        
        compressed_count = 0
        cutoff_date = datetime.now() - timedelta(days=compress_days)
        
        for item in archive_dir.iterdir():
            if item.is_dir():
                item_time = datetime.fromtimestamp(item.stat().st_mtime)
                if item_time < cutoff_date:
                    # 壓縮目錄
                    compressed_file = item.with_suffix('.tar.gz')
                    if not compressed_file.exists():
                        self.compress_directory(item, compressed_file)
                        compressed_count += 1
        
        print(f"✅ 已壓縮 {compressed_count} 個歸檔目錄")
        return compressed_count
    
    def compress_directory(self, source_dir: Path, target_file: Path):
        """壓縮目錄"""
        import tarfile
        
        with tarfile.open(target_file, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)
        
        # 刪除原始目錄
        shutil.rmtree(source_dir)
        
        self.cleanup_log.append({
            "action": "compress_directory",
            "source": str(source_dir),
            "target": str(target_file),
            "timestamp": datetime.now().isoformat()
        })
    
    def optimize_storage(self):
        """優化存儲空間"""
        print("🔧 開始優化存儲空間...")
        
        # 1. 清理重複文件
        duplicates_removed = self.remove_duplicate_files()
        
        # 2. 壓縮大文件
        compressed_files = self.compress_large_files()
        
        # 3. 清理空目錄
        empty_dirs_removed = self.remove_empty_directories()
        
        print(f"✅ 存儲優化完成:")
        print(f"  - 移除了 {duplicates_removed} 個重複文件")
        print(f"  - 壓縮了 {compressed_files} 個大文件")
        print(f"  - 移除了 {empty_dirs_removed} 個空目錄")
        
        return {
            "duplicates_removed": duplicates_removed,
            "compressed_files": compressed_files,
            "empty_dirs_removed": empty_dirs_removed
        }
    
    def remove_duplicate_files(self) -> int:
        """移除重複文件"""
        # 這裡可以實現重複文件檢測邏輯
        # 暫時返回 0
        return 0
    
    def compress_large_files(self, size_mb: int = 10) -> int:
        """壓縮大文件"""
        compressed_count = 0
        size_bytes = size_mb * 1024 * 1024
        
        for file_path in self.data_dir.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size > size_bytes:
                if file_path.suffix not in ['.gz', '.zip', '.tar']:
                    compressed_file = file_path.with_suffix(file_path.suffix + '.gz')
                    if not compressed_file.exists():
                        self.compress_file(file_path, compressed_file)
                        compressed_count += 1
        
        return compressed_count
    
    def compress_file(self, source_file: Path, target_file: Path):
        """壓縮單個文件"""
        with open(source_file, 'rb') as f_in:
            with gzip.open(target_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 刪除原始文件
        source_file.unlink()
        
        self.cleanup_log.append({
            "action": "compress_file",
            "source": str(source_file),
            "target": str(target_file),
            "timestamp": datetime.now().isoformat()
        })
    
    def remove_empty_directories(self) -> int:
        """移除空目錄"""
        removed_count = 0
        
        # 從最深層開始檢查
        for dir_path in sorted(self.data_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and dir_path != self.data_dir:
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        removed_count += 1
                except OSError:
                    pass
        
        return removed_count
    
    def generate_cleanup_report(self):
        """生成清理報告"""
        report_data = {
            "cleanup_info": {
                "cleaned_at": datetime.now().isoformat(),
                "total_actions": len(self.cleanup_log),
                "data_directory": str(self.data_dir)
            },
            "cleanup_log": self.cleanup_log,
            "storage_info": self.get_storage_info()
        }
        
        report_path = self.data_dir / "cleanup_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📊 清理報告已生成: {report_path}")
    
    def get_storage_info(self) -> Dict:
        """獲取存儲信息"""
        total_size = 0
        file_count = 0
        
        for file_path in self.data_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "directory_structure": self.get_directory_structure()
        }
    
    def get_directory_structure(self) -> Dict:
        """獲取目錄結構"""
        structure = {}
        
        for item in self.data_dir.iterdir():
            if item.is_dir():
                structure[item.name] = self.count_directory_contents(item)
        
        return structure
    
    def count_directory_contents(self, directory: Path) -> Dict:
        """統計目錄內容"""
        files = 0
        dirs = 0
        size = 0
        
        for item in directory.rglob("*"):
            if item.is_file():
                files += 1
                size += item.stat().st_size
            elif item.is_dir():
                dirs += 1
        
        return {
            "files": files,
            "directories": dirs,
            "size_mb": round(size / (1024 * 1024), 2)
        }

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="JobSpy 數據清理工具")
    parser.add_argument("--data-dir", default="data", help="數據目錄路徑")
    parser.add_argument("--retention-days", type=int, default=30, help="數據保留天數")
    parser.add_argument("--compress-days", type=int, default=7, help="壓縮歸檔天數")
    parser.add_argument("--dry-run", action="store_true", help="試運行模式")
    parser.add_argument("--optimize", action="store_true", help="優化存儲空間")
    
    args = parser.parse_args()
    
    print("🧹 開始 JobSpy 數據清理...")
    
    cleaner = DataCleaner(args.data_dir)
    
    # 清理舊數據
    cleanup_result = cleaner.cleanup_old_data(args.retention_days, args.dry_run)
    
    # 壓縮歸檔
    compress_result = cleaner.compress_archive(args.compress_days)
    
    # 優化存儲
    if args.optimize:
        optimize_result = cleaner.optimize_storage()
    
    # 生成報告
    cleaner.generate_cleanup_report()
    
    print("✅ 數據清理完成！")

if __name__ == "__main__":
    main()
