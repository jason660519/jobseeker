#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用戶提示測試執行器

這個腳本用於執行JobSpy的用戶提示測試套件。
支援執行所有測試、指定階段的測試或單一測試。

使用方法:
    python run_user_prompt_tests.py --all                    # 執行所有測試
    python run_user_prompt_tests.py --phase 1               # 執行第一階段測試
    python run_user_prompt_tests.py --test australia        # 執行澳洲測試
    python run_user_prompt_tests.py --list                  # 列出所有可用測試
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class UserPromptTestRunner:
    """用戶提示測試執行器類"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.test_config = self._load_test_config()
        
    def _load_test_config(self) -> Dict:
        """載入測試配置"""
        config_file = self.base_dir / "test_user_prompts.json"
        if not config_file.exists():
            print(f"❌ 測試配置檔案不存在: {config_file}")
            sys.exit(1)
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_tests(self):
        """列出所有可用的測試"""
        print("\n📋 可用的測試案例:")
        print("=" * 50)
        
        for test in self.test_config['test_prompts']:
            test_id = test['test_id']
            description = test['description']
            phase = self._get_test_phase(test_id)
            print(f"🔹 {test_id} (階段 {phase})")
            print(f"   描述: {description}")
            print()
    
    def _get_test_phase(self, test_id: str) -> int:
        """根據測試ID確定測試階段"""
        if test_id in ['australia', 'asia']:
            return 1
        elif test_id in ['singapore', 'europe']:
            return 2
        else:
            return 3
    
    def _get_test_script_path(self, test_id: str) -> Path:
        """獲取測試腳本路徑"""
        # 從配置檔案中查找測試的腳本路徑
        for test in self.test_config['test_prompts']:
            if test['test_id'] == test_id:
                script_path = test.get('script_path')
                if script_path:
                    return self.base_dir / script_path
                break
        
        return None
    
    def run_single_test(self, test_id: str) -> bool:
        """執行單一測試"""
        # 查找測試配置
        test_config = None
        for test in self.test_config['test_prompts']:
            if test['test_id'] == test_id:
                test_config = test
                break
        
        if not test_config:
            print(f"❌ 找不到測試ID: {test_id}")
            return False
        
        script_path = self._get_test_script_path(test_id)
        if not script_path or not script_path.exists():
            print(f"❌ 測試腳本不存在: {script_path}")
            return False
        
        print(f"\n🚀 執行測試: {test_config['description']}")
        print(f"📄 腳本: {script_path}")
        print("=" * 60)
        
        try:
            # 執行測試腳本
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.base_dir.parent.parent,  # JobSpy根目錄
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✅ 測試 {test_id} 執行成功")
                return True
            else:
                print(f"\n❌ 測試 {test_id} 執行失敗 (退出碼: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"\n❌ 執行測試時發生錯誤: {e}")
            return False
    
    def run_phase_tests(self, phase: int) -> Dict[str, bool]:
        """執行指定階段的所有測試"""
        results = {}
        
        print(f"\n🎯 執行階段 {phase} 的所有測試")
        print("=" * 50)
        
        for test in self.test_config['test_prompts']:
            test_id = test['test_id']
            if self._get_test_phase(test_id) == phase:
                print(f"\n📋 準備執行: {test['description']}")
                results[test_id] = self.run_single_test(test_id)
        
        return results
    
    def run_all_tests(self) -> Dict[str, bool]:
        """執行所有測試"""
        results = {}
        
        print("\n🎯 執行所有用戶提示測試")
        print("=" * 50)
        
        for test in self.test_config['test_prompts']:
            test_id = test['test_id']
            print(f"\n📋 準備執行: {test['description']}")
            results[test_id] = self.run_single_test(test_id)
        
        return results
    
    def generate_summary_report(self, results: Dict[str, bool]):
        """生成總結報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.base_dir / f"test_summary_{timestamp}.md"
        
        total_tests = len(results)
        passed_tests = sum(1 for success in results.values() if success)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 測試總結")
        print("=" * 30)
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 生成詳細報告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 用戶提示測試總結報告\n\n")
            f.write(f"**執行時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 測試統計\n\n")
            f.write(f"- 總測試數: {total_tests}\n")
            f.write(f"- 通過: {passed_tests}\n")
            f.write(f"- 失敗: {failed_tests}\n")
            f.write(f"- 成功率: {(passed_tests/total_tests)*100:.1f}%\n\n")
            
            f.write(f"## 詳細結果\n\n")
            for test_id, success in results.items():
                status = "✅ 通過" if success else "❌ 失敗"
                test_config = next((t for t in self.test_config['test_prompts'] if t['test_id'] == test_id), {})
                description = test_config.get('description', test_id)
                f.write(f"- **{test_id}**: {status}\n")
                f.write(f"  - 描述: {description}\n")
                f.write(f"  - 階段: {self._get_test_phase(test_id)}\n\n")
        
        print(f"\n📄 詳細報告已儲存至: {report_file}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='JobSpy 用戶提示測試執行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python run_user_prompt_tests.py --all                    # 執行所有測試
  python run_user_prompt_tests.py --phase 1               # 執行第一階段測試
  python run_user_prompt_tests.py --test australia        # 執行澳洲測試
  python run_user_prompt_tests.py --list                  # 列出所有可用測試
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='執行所有測試')
    group.add_argument('--phase', type=int, choices=[1, 2, 3], help='執行指定階段的測試')
    group.add_argument('--test', type=str, help='執行指定的單一測試')
    group.add_argument('--list', action='store_true', help='列出所有可用的測試')
    
    args = parser.parse_args()
    
    runner = UserPromptTestRunner()
    
    if args.list:
        runner.list_tests()
        return
    
    results = {}
    
    if args.all:
        results = runner.run_all_tests()
    elif args.phase:
        results = runner.run_phase_tests(args.phase)
    elif args.test:
        success = runner.run_single_test(args.test)
        results = {args.test: success}
    
    if results:
        runner.generate_summary_report(results)


if __name__ == "__main__":
    main()