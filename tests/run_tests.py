#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 測試執行腳本

這個腳本提供便捷的測試執行命令，支援不同類型的測試執行、覆蓋率報告生成和測試結果分析。
支援所有9個求職網站的測試：LinkedIn, Indeed, ZipRecruiter, Glassdoor, Google, Bayt, Naukri, BDJobs, Seek

使用方法:
    python run_tests.py --help                    # 顯示幫助
    python run_tests.py --all                     # 執行所有測試
    python run_tests.py --unit                    # 只執行單元測試
    python run_tests.py --integration             # 只執行整合測試
    python run_tests.py --performance             # 只執行效能測試
    python run_tests.py --coverage                # 執行測試並生成覆蓋率報告
    python run_tests.py --fast                    # 快速測試（跳過慢速測試）
    python run_tests.py --verbose                 # 詳細輸出
    python run_tests.py --parallel                # 並行執行測試
    python run_tests.py --report                  # 生成測試報告

作者: jobseeker Team
日期: 2024
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# 設定專案根目錄
project_root = Path(__file__).parent.parent  # 回到 jobseeker 根目錄
tests_dir = Path(__file__).parent  # tests 資料夾
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_dir))


class TestRunner:
    """測試執行器類別"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        self.coverage_dir = self.reports_dir / "coverage"
        
        # 確保報告目錄存在
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_command(self, command: List[str], capture_output: bool = False) -> Dict[str, Any]:
        """執行命令並返回結果"""
        print(f"執行命令: {' '.join(command)}")
        
        start_time = time.time()
        
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
            else:
                result = subprocess.run(
                    command,
                    cwd=self.project_root
                )
            
            end_time = time.time()
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "duration": end_time - start_time,
                "stdout": getattr(result, 'stdout', ''),
                "stderr": getattr(result, 'stderr', '')
            }
        
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "returncode": -1,
                "duration": end_time - start_time,
                "error": str(e),
                "stdout": '',
                "stderr": ''
            }
    
    def build_pytest_command(self, test_type: str = "all", 
                           options: Dict[str, Any] = None) -> List[str]:
        """構建 pytest 命令"""
        command = ["python", "-m", "pytest"]
        
        if options is None:
            options = {}
        
        # 根據測試類型添加路徑和標記
        if test_type == "unit":
            command.extend(["tests/unit"])
        elif test_type == "integration":
            command.extend(["tests/integration"])
            command.extend(["-m", "integration"])
        elif test_type == "performance":
            command.extend(["tests/performance"])
            command.extend(["-m", "performance"])
        elif test_type == "fast":
            command.extend(["tests"])
            command.extend(["-m", "not slow"])
        elif test_type == "slow":
            command.extend(["tests"])
            command.extend(["-m", "slow"])
        elif test_type == "network":
            command.extend(["tests"])
            command.extend(["-m", "requires_network"])
        else:  # all
            command.extend(["tests"])
        
        # 添加選項
        if options.get("verbose", False):
            command.extend(["-v"])
        
        if options.get("parallel", False):
            command.extend(["-n", "auto"])
        
        if options.get("coverage", False):
            command.extend([
                "--cov=jobseeker",
                "--cov-report=html:test_reports/coverage/html",
                "--cov-report=xml:test_reports/coverage/coverage.xml",
                "--cov-report=term-missing"
            ])
        
        if options.get("junit", False):
            command.extend([
                "--junit-xml=test_reports/junit.xml"
            ])
        
        if options.get("html_report", False):
            command.extend([
                "--html=test_reports/report.html",
                "--self-contained-html"
            ])
        
        # 添加其他 pytest 選項
        if options.get("maxfail"):
            command.extend(["--maxfail", str(options["maxfail"])])
        
        if options.get("timeout"):
            command.extend(["--timeout", str(options["timeout"])])
        
        if options.get("durations"):
            command.extend(["--durations", str(options["durations"])])
        
        return command
    
    def run_tests(self, test_type: str = "all", 
                  options: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行測試"""
        print(f"\n{'='*60}")
        print(f"執行 {test_type.upper()} 測試")
        print(f"{'='*60}")
        
        command = self.build_pytest_command(test_type, options)
        result = self.run_command(command)
        
        print(f"\n測試執行完成:")
        print(f"  成功: {'是' if result['success'] else '否'}")
        print(f"  執行時間: {result['duration']:.2f} 秒")
        print(f"  返回碼: {result['returncode']}")
        
        if not result['success'] and result.get('stderr'):
            print(f"  錯誤: {result['stderr']}")
        
        return result
    
    def run_linting(self) -> Dict[str, Any]:
        """執行程式碼檢查"""
        print(f"\n{'='*60}")
        print("執行程式碼檢查")
        print(f"{'='*60}")
        
        results = {}
        
        # Flake8 檢查
        print("\n執行 Flake8 檢查...")
        flake8_result = self.run_command([
            "python", "-m", "flake8", "jobseeker", "tests",
            "--max-line-length=88",
            "--extend-ignore=E203,W503",
            "--output-file=test_reports/flake8.txt"
        ], capture_output=True)
        results['flake8'] = flake8_result
        
        # Black 格式檢查
        print("執行 Black 格式檢查...")
        black_result = self.run_command([
            "python", "-m", "black", "--check", "--diff", "jobseeker", "tests"
        ], capture_output=True)
        results['black'] = black_result
        
        # isort 導入排序檢查
        print("執行 isort 導入排序檢查...")
        isort_result = self.run_command([
            "python", "-m", "isort", "--check-only", "--diff", "jobseeker", "tests"
        ], capture_output=True)
        results['isort'] = isort_result
        
        # mypy 類型檢查
        print("執行 mypy 類型檢查...")
        mypy_result = self.run_command([
            "python", "-m", "mypy", "jobseeker",
            "--ignore-missing-imports",
            "--no-strict-optional"
        ], capture_output=True)
        results['mypy'] = mypy_result
        
        # 總結結果
        all_passed = all(result['success'] for result in results.values())
        print(f"\n程式碼檢查完成:")
        for tool, result in results.items():
            status = "通過" if result['success'] else "失敗"
            print(f"  {tool}: {status}")
        
        print(f"\n總體結果: {'通過' if all_passed else '失敗'}")
        
        return {
            'success': all_passed,
            'results': results
        }
    
    def run_security_check(self) -> Dict[str, Any]:
        """執行安全檢查"""
        print(f"\n{'='*60}")
        print("執行安全檢查")
        print(f"{'='*60}")
        
        results = {}
        
        # Bandit 安全檢查
        print("\n執行 Bandit 安全檢查...")
        bandit_result = self.run_command([
            "python", "-m", "bandit", "-r", "jobseeker",
            "-f", "json",
            "-o", "test_reports/bandit.json"
        ], capture_output=True)
        results['bandit'] = bandit_result
        
        # Safety 依賴檢查
        print("執行 Safety 依賴安全檢查...")
        safety_result = self.run_command([
            "python", "-m", "safety", "check",
            "--json",
            "--output", "test_reports/safety.json"
        ], capture_output=True)
        results['safety'] = safety_result
        
        # 總結結果
        all_passed = all(result['success'] for result in results.values())
        print(f"\n安全檢查完成:")
        for tool, result in results.items():
            status = "通過" if result['success'] else "失敗"
            print(f"  {tool}: {status}")
        
        print(f"\n總體結果: {'通過' if all_passed else '失敗'}")
        
        return {
            'success': all_passed,
            'results': results
        }
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """生成測試報告"""
        report_file = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "results": results,
            "summary": {
                "total_duration": sum(r.get('duration', 0) for r in results.values() if isinstance(r, dict)),
                "all_passed": all(r.get('success', False) for r in results.values() if isinstance(r, dict))
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n測試報告已生成: {report_file}")
        return str(report_file)
    
    def install_test_dependencies(self) -> Dict[str, Any]:
        """安裝測試依賴"""
        print(f"\n{'='*60}")
        print("安裝測試依賴")
        print(f"{'='*60}")
        
        test_packages = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-html>=3.1.0",
            "pytest-xdist>=3.0.0",
            "pytest-timeout>=2.1.0",
            "pytest-mock>=3.10.0",
            "coverage>=7.0.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.3.0",
            "psutil>=5.9.0"
        ]
        
        command = ["python", "-m", "pip", "install"] + test_packages
        result = self.run_command(command)
        
        if result['success']:
            print("測試依賴安裝成功！")
        else:
            print("測試依賴安裝失敗！")
        
        return result
    
    def clean_test_artifacts(self) -> None:
        """清理測試產生的檔案"""
        print("\n清理測試產生的檔案...")
        
        # 清理 __pycache__ 目錄
        for pycache_dir in self.project_root.rglob("__pycache__"):
            if pycache_dir.is_dir():
                import shutil
                shutil.rmtree(pycache_dir)
                print(f"已刪除: {pycache_dir}")
        
        # 清理 .pyc 檔案
        for pyc_file in self.project_root.rglob("*.pyc"):
            pyc_file.unlink()
            print(f"已刪除: {pyc_file}")
        
        # 清理 pytest 快取
        pytest_cache = self.project_root / ".pytest_cache"
        if pytest_cache.exists():
            import shutil
            shutil.rmtree(pytest_cache)
            print(f"已刪除: {pytest_cache}")
        
        # 清理覆蓋率檔案
        coverage_file = self.project_root / ".coverage"
        if coverage_file.exists():
            coverage_file.unlink()
            print(f"已刪除: {coverage_file}")
        
        print("清理完成！")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="jobseeker 測試執行腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python run_tests.py --all --coverage          # 執行所有測試並生成覆蓋率報告
  python run_tests.py --unit --verbose          # 執行單元測試並顯示詳細輸出
  python run_tests.py --fast --parallel         # 快速並行執行測試
  python run_tests.py --performance             # 只執行效能測試
  python run_tests.py --lint --security         # 執行程式碼檢查和安全檢查
        """
    )
    
    # 測試類型選項
    test_group = parser.add_argument_group("測試類型")
    test_group.add_argument("--all", action="store_true", help="執行所有測試")
    test_group.add_argument("--unit", action="store_true", help="執行單元測試")
    test_group.add_argument("--integration", action="store_true", help="執行整合測試")
    test_group.add_argument("--performance", action="store_true", help="執行效能測試")
    test_group.add_argument("--fast", action="store_true", help="快速測試（跳過慢速測試）")
    test_group.add_argument("--slow", action="store_true", help="只執行慢速測試")
    test_group.add_argument("--network", action="store_true", help="執行需要網路的測試")
    
    # 測試選項
    options_group = parser.add_argument_group("測試選項")
    options_group.add_argument("--coverage", action="store_true", help="生成覆蓋率報告")
    options_group.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    options_group.add_argument("--parallel", "-p", action="store_true", help="並行執行測試")
    options_group.add_argument("--report", action="store_true", help="生成測試報告")
    options_group.add_argument("--maxfail", type=int, help="最大失敗次數後停止")
    options_group.add_argument("--timeout", type=int, help="測試超時時間（秒）")
    options_group.add_argument("--durations", type=int, default=10, help="顯示最慢的 N 個測試")
    
    # 其他選項
    other_group = parser.add_argument_group("其他選項")
    other_group.add_argument("--lint", action="store_true", help="執行程式碼檢查")
    other_group.add_argument("--security", action="store_true", help="執行安全檢查")
    other_group.add_argument("--install-deps", action="store_true", help="安裝測試依賴")
    other_group.add_argument("--clean", action="store_true", help="清理測試產生的檔案")
    other_group.add_argument("--project-root", help="專案根目錄路徑")
    
    args = parser.parse_args()
    
    # 如果沒有指定任何選項，顯示幫助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # 創建測試執行器
    runner = TestRunner(args.project_root)
    
    # 執行結果收集
    results = {}
    
    try:
        # 安裝依賴
        if args.install_deps:
            results['install_deps'] = runner.install_test_dependencies()
        
        # 清理檔案
        if args.clean:
            runner.clean_test_artifacts()
            return
        
        # 構建測試選項
        test_options = {
            "verbose": args.verbose,
            "parallel": args.parallel,
            "coverage": args.coverage,
            "junit": args.report,
            "html_report": args.report,
            "maxfail": args.maxfail,
            "timeout": args.timeout,
            "durations": args.durations
        }
        
        # 執行測試
        if args.all or not any([args.unit, args.integration, args.performance, 
                               args.fast, args.slow, args.network]):
            results['tests'] = runner.run_tests("all", test_options)
        else:
            if args.unit:
                results['unit_tests'] = runner.run_tests("unit", test_options)
            if args.integration:
                results['integration_tests'] = runner.run_tests("integration", test_options)
            if args.performance:
                results['performance_tests'] = runner.run_tests("performance", test_options)
            if args.fast:
                results['fast_tests'] = runner.run_tests("fast", test_options)
            if args.slow:
                results['slow_tests'] = runner.run_tests("slow", test_options)
            if args.network:
                results['network_tests'] = runner.run_tests("network", test_options)
        
        # 執行程式碼檢查
        if args.lint:
            results['linting'] = runner.run_linting()
        
        # 執行安全檢查
        if args.security:
            results['security'] = runner.run_security_check()
        
        # 生成報告
        if args.report and results:
            runner.generate_test_report(results)
        
        # 總結結果
        print(f"\n{'='*60}")
        print("測試執行總結")
        print(f"{'='*60}")
        
        all_passed = True
        for test_type, result in results.items():
            if isinstance(result, dict) and 'success' in result:
                status = "通過" if result['success'] else "失敗"
                duration = result.get('duration', 0)
                print(f"{test_type}: {status} ({duration:.2f}s)")
                if not result['success']:
                    all_passed = False
        
        print(f"\n總體結果: {'通過' if all_passed else '失敗'}")
        
        # 設置退出碼
        sys.exit(0 if all_passed else 1)
    
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n測試執行出錯: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
