#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 測試目錄整合工具
用於整理和統一管理所有測試相關的目錄和文件
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

def analyze_test_directories():
    """
    分析當前的測試目錄結構
    
    Returns:
        dict: 目錄分析結果
    """
    base_dir = Path("..")
    analysis = {
        "test_script_directories": {
            "tests": {
                "type": "正式測試框架目錄",
                "description": "使用 pytest 的正式測試框架，包含單元測試、整合測試、性能測試",
                "files": [],
                "subdirs": []
            },
            "tests_collection": {
                "type": "自定義測試腳本集合",
                "description": "包含各種功能驗證和職位搜尋測試腳本",
                "files": [],
                "subdirs": []
            }
        },
        "test_result_directories": {
            "ui_ux_test_results": [],
            "ml_engineer_test_results": [],
            "other_test_results": []
        }
    }
    
    # 分析 tests 目錄
    tests_dir = base_dir / "tests"
    if tests_dir.exists():
        for item in tests_dir.iterdir():
            if item.is_file():
                analysis["test_script_directories"]["tests"]["files"].append(item.name)
            else:
                analysis["test_script_directories"]["tests"]["subdirs"].append(item.name)
    
    # 分析 tests_collection 目錄
    tests_collection_dir = Path(".")
    for item in tests_collection_dir.iterdir():
        if item.is_file() and item.name.endswith('.py'):
            analysis["test_script_directories"]["tests_collection"]["files"].append(item.name)
    
    # 分析測試結果目錄
    for item in base_dir.iterdir():
        if item.is_dir():
            if item.name.startswith("ui_ux_test_"):
                analysis["test_result_directories"]["ui_ux_test_results"].append(item.name)
            elif item.name.startswith("ml_engineer_test_"):
                analysis["test_result_directories"]["ml_engineer_test_results"].append(item.name)
            elif "test" in item.name.lower() and item.name not in ["tests", "tests_collection"]:
                analysis["test_result_directories"]["other_test_results"].append(item.name)
    
    return analysis

def create_unified_structure():
    """
    創建統一的測試目錄結構
    """
    print("🏗️  創建統一測試目錄結構...")
    
    # 創建主要目錄結構
    directories = {
        "test_results": "所有測試執行結果",
        "test_results/ui_ux_tests": "UI/UX 職位搜尋測試結果",
        "test_results/ml_engineer_tests": "機器學習工程師職位測試結果",
        "test_results/enhanced_scraper_tests": "增強版爬蟲測試結果",
        "test_results/verification_tests": "功能驗證測試結果",
        "test_results/archived": "歷史測試結果歸檔"
    }
    
    for dir_path, description in directories.items():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 創建目錄: {dir_path} - {description}")
    
    return directories

def organize_test_results():
    """
    整理測試結果目錄
    """
    print("\n📁 整理測試結果目錄...")
    
    base_dir = Path("..")
    moved_count = 0
    
    # 移動 UI/UX 測試結果
    for item in base_dir.glob("ui_ux_test_*"):
        if item.is_dir():
            target = Path("test_results/ui_ux_tests") / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
                print(f"📦 移動: {item.name} -> test_results/ui_ux_tests/")
                moved_count += 1
    
    # 移動機器學習工程師測試結果
    for item in base_dir.glob("ml_engineer_test_*"):
        if item.is_dir():
            target = Path("test_results/ml_engineer_tests") / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
                print(f"📦 移動: {item.name} -> test_results/ml_engineer_tests/")
                moved_count += 1
    
    # 移動其他測試結果
    test_result_patterns = ["enhanced_test_*", "final_verification_*"]
    for pattern in test_result_patterns:
        for item in base_dir.glob(pattern):
            if item.is_dir():
                if "enhanced" in item.name:
                    target = Path("test_results/enhanced_scraper_tests") / item.name
                else:
                    target = Path("test_results/verification_tests") / item.name
                
                if not target.exists():
                    shutil.move(str(item), str(target))
                    print(f"📦 移動: {item.name} -> {target.parent.name}/")
                    moved_count += 1
    
    print(f"\n✅ 總共移動了 {moved_count} 個測試結果目錄")
    return moved_count

def create_directory_guide():
    """
    創建目錄結構說明文件
    """
    guide_content = """
# jobseeker 測試目錄結構說明

## 📁 目錄結構概覽

### 1. 測試腳本目錄

#### `tests/` - 正式測試框架
- **用途**: 使用 pytest 的正式測試框架
- **內容**: 單元測試、整合測試、性能測試
- **特點**: 遵循標準測試框架規範，適合 CI/CD 整合
- **執行方式**: `pytest tests/`

#### `tests_collection/` - 自定義測試腳本集合
- **用途**: 功能驗證和職位搜尋測試腳本
- **內容**: 各種實用測試腳本和批次執行工具
- **特點**: 獨立執行，生成詳細報告
- **執行方式**: 單獨執行或使用批次腳本

### 2. 測試結果目錄

#### `tests_collection/test_results/` - 統一測試結果存放區

```
test_results/
├── ui_ux_tests/              # UI/UX 職位搜尋測試結果
│   ├── ui_ux_test_20250902_002729/
│   └── ...
├── ml_engineer_tests/        # 機器學習工程師職位測試結果
│   ├── ml_engineer_test_20250901_211743/
│   └── ...
├── enhanced_scraper_tests/   # 增強版爬蟲測試結果
│   ├── enhanced_test_20250901_215209/
│   └── ...
├── verification_tests/       # 功能驗證測試結果
│   ├── final_verification_20250901_213005/
│   └── ...
└── archived/                 # 歷史測試結果歸檔
```

## 🔄 目錄差異說明

### `tests/` vs `tests_collection/`

| 特性 | tests/ | tests_collection/ |
|------|--------|-------------------|
| **框架** | pytest 標準框架 | 自定義腳本 |
| **用途** | 單元/整合測試 | 功能驗證/職位搜尋 |
| **執行** | `pytest` 命令 | 直接執行 Python 腳本 |
| **報告** | pytest 報告格式 | 自定義詳細報告 |
| **CI/CD** | 適合自動化 | 適合手動驗證 |
| **維護** | 遵循測試規範 | 靈活自定義 |

### 測試結果目錄分類

- **按功能分類**: 不同類型的測試結果分別存放
- **按時間命名**: 保留時間戳，便於追蹤
- **統一管理**: 所有結果集中在 `test_results/` 下

## 🚀 使用建議

### 開發階段
1. 使用 `tests_collection/` 中的腳本進行功能驗證
2. 執行 `run_all_tests.py` 進行批次測試

### 正式測試
1. 使用 `tests/` 目錄進行標準化測試
2. 整合到 CI/CD 流程中

### 結果管理
1. 定期檢查 `test_results/` 目錄
2. 將舊結果移動到 `archived/` 目錄
3. 保持目錄結構清潔

## 📋 維護指南

### 定期清理
```bash
# 移動 30 天前的測試結果到歸檔目錄
python organize_test_directories.py --archive-old --days 30
```

### 目錄整理
```bash
# 重新整理所有測試結果目錄
python organize_test_directories.py --reorganize
```

### 統計報告
```bash
# 生成測試目錄統計報告
python organize_test_directories.py --report
```
"""
    
    with open("test_results/DIRECTORY_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("📖 創建目錄結構說明文件: test_results/DIRECTORY_GUIDE.md")

def generate_analysis_report(analysis):
    """
    生成目錄分析報告
    
    Args:
        analysis (dict): 目錄分析結果
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
jobseeker 測試目錄分析報告
生成時間: {timestamp}
{'=' * 50}

## 測試腳本目錄分析

### tests/ 目錄 (正式測試框架)
- 類型: {analysis['test_script_directories']['tests']['type']}
- 說明: {analysis['test_script_directories']['tests']['description']}
- 文件數量: {len(analysis['test_script_directories']['tests']['files'])}
- 子目錄數量: {len(analysis['test_script_directories']['tests']['subdirs'])}

文件列表:
{chr(10).join(f'  - {f}' for f in analysis['test_script_directories']['tests']['files'])}

子目錄:
{chr(10).join(f'  - {d}/' for d in analysis['test_script_directories']['tests']['subdirs'])}

### tests_collection/ 目錄 (自定義測試腳本)
- 類型: {analysis['test_script_directories']['tests_collection']['type']}
- 說明: {analysis['test_script_directories']['tests_collection']['description']}
- 腳本數量: {len(analysis['test_script_directories']['tests_collection']['files'])}

腳本列表:
{chr(10).join(f'  - {f}' for f in analysis['test_script_directories']['tests_collection']['files'])}

## 測試結果目錄分析

### UI/UX 測試結果目錄
數量: {len(analysis['test_result_directories']['ui_ux_test_results'])}
{chr(10).join(f'  - {d}' for d in analysis['test_result_directories']['ui_ux_test_results'])}

### 機器學習工程師測試結果目錄
數量: {len(analysis['test_result_directories']['ml_engineer_test_results'])}
{chr(10).join(f'  - {d}' for d in analysis['test_result_directories']['ml_engineer_test_results'])}

### 其他測試結果目錄
數量: {len(analysis['test_result_directories']['other_test_results'])}
{chr(10).join(f'  - {d}' for d in analysis['test_result_directories']['other_test_results'])}

## 整合建議

1. **保持現有結構**: tests/ 和 tests_collection/ 各有不同用途，建議保持分離
2. **統一結果管理**: 將所有測試結果目錄整理到 tests_collection/test_results/ 下
3. **分類存放**: 按測試類型分別存放結果，便於管理和查找
4. **定期清理**: 建立歸檔機制，避免目錄過於雜亂

## 目錄用途對比

| 目錄 | 用途 | 特點 | 建議 |
|------|------|------|------|
| tests/ | 正式測試框架 | pytest 標準、CI/CD 友好 | 保持現狀，用於正式測試 |
| tests_collection/ | 功能驗證腳本 | 靈活自定義、詳細報告 | 繼續用於開發驗證 |
| 各種 *_test_* 目錄 | 測試結果存放 | 分散管理、不易維護 | 整合到統一結構中 |
"""
    
    with open("test_results/directory_analysis_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    # 同時保存 JSON 格式
    with open("test_results/directory_analysis.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "analysis": analysis
        }, f, indent=2, ensure_ascii=False)
    
    print("📊 生成目錄分析報告: test_results/directory_analysis_report.txt")
    print("📊 生成 JSON 分析數據: test_results/directory_analysis.json")

def main():
    """
    主函數 - 執行測試目錄整合
    """
    print("🔍 jobseeker 測試目錄整合工具")
    print("=" * 40)
    
    # 分析現有目錄結構
    print("\n📋 分析現有目錄結構...")
    analysis = analyze_test_directories()
    
    # 創建統一目錄結構
    unified_dirs = create_unified_structure()
    
    # 整理測試結果
    moved_count = organize_test_results()
    
    # 創建說明文件
    create_directory_guide()
    
    # 生成分析報告
    generate_analysis_report(analysis)
    
    # 顯示總結
    print("\n" + "=" * 50)
    print("🎉 測試目錄整合完成")
    print("=" * 50)
    
    print(f"\n📁 創建統一目錄: {len(unified_dirs)} 個")
    print(f"📦 移動測試結果: {moved_count} 個目錄")
    print(f"📖 生成說明文件: test_results/DIRECTORY_GUIDE.md")
    print(f"📊 生成分析報告: test_results/directory_analysis_report.txt")
    
    print("\n💡 建議:")
    print("   - tests/ 目錄保持用於正式測試框架")
    print("   - tests_collection/ 目錄用於功能驗證腳本")
    print("   - 所有測試結果統一存放在 tests_collection/test_results/")
    print("   - 定期將舊結果移動到 archived/ 目錄")
    
    print("\n🚀 整合完成！現在您可以更好地管理測試目錄了。")

if __name__ == "__main__":
    main()
