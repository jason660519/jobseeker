#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jobseeker 測試執行器

這個腳本提供了便捷的測試執行介面，支援不同類型的測試執行、
覆蓋率報告生成和測試結果分析。
支援所有9個求職網站的測試：LinkedIn, Indeed, ZipRecruiter, Glassdoor, Google, Bayt, Naukri, BDJobs, Seek

使用方式:
    python test_runner.py --help
    python test_runner.py --unit
    python test_runner.py --integration
    python test_runner.py --performance
    python test_runner.py --all --coverage

作者: jobseeker Team
日期: 2024
"""

import os
import sys
import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 設定專案根目錄
project_root = Path(__file__).parent.parent  # 回到 jobseeker 根目錄
tests_dir = Path(__file__).parent  # tests 資料夾
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_dir))

try:
    from tests.test_config import (
        TestConfig, TestEnvironment, get_test_config,
        check_test_environment, setup_test_environment,
        cleanup_test_environment
    )
except ImportError:
    print("警告: 無法導入測試配置，使用預設設定")
    TestConfig = None
    TestEnvironment = None


@dataclass
class TestResult:
    """測試結果類別"""
    test_type: str
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage: Optional[float] = None
    exit_code: int = 0
    output: str = ""
    
    @property
    def total(self) -> int:
        """總測試數量"""
        return self.passed + self.failed + self.skipped + self.errors
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'test_type': self.test_type,
            'passed': self.passed,
            'failed': self.failed,
            'skipped': self.skipped,
            'errors': self.errors,
            'total': self.total,
            'duration': self.duration,
            'success_rate': self.success_rate,
            'coverage': self.coverage,
            'exit_code': self.exit_code
        }


class TestRunner:
    """測試執行器類別"""
    
    def __init__(self, config: Optional[TestConfig] = None):
        """初始化測試執行器"""
        self.config = config or (get_test_config() if TestConfig else None)
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.results: List[TestResult] = []
        
        # 確保測試目錄存在
        if not self.test_dir.exists():
            raise FileNotFoundError(f"測試目錄不存在: {self.test_dir}")
    
    def check_dependencies(self) -> bool:
        """檢查測試依賴"""
        print("🔍 檢查測試環境...")
        
        # 檢查 pytest
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print("❌ pytest 未安裝或無法執行")
                return False
            print(f"✅ {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ pytest 未安裝")
            return False
        
        # 檢查測試環境
        if TestConfig:
            env_checks = check_test_environment()
            failed_checks = [k for k, v in env_checks.items() if not v]
            
            if failed_checks:
                print(f"⚠️  環境檢查失敗: {', '.join(failed_checks)}")
                return False
            
            print("✅ 測試環境檢查通過")
        
        return True
    
    def install_dependencies(self) -> bool:
        """安裝測試依賴"""
        print("📦 安裝測試依賴...")
        
        requirements_files = [
            self.project_root / "requirements-test.txt",
            self.project_root / "requirements.txt"
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ 已安裝 {req_file.name}")
                    else:
                        print(f"❌ 安裝 {req_file.name} 失敗: {result.stderr}")
                        return False
                        
                except subprocess.TimeoutExpired:
                    print(f"❌ 安裝 {req_file.name} 超時")
                    return False
        
        return True
    
    def run_pytest(self, args: List[str], test_type: str = "general") -> TestResult:
        """執行 pytest"""
        print(f"🧪 執行 {test_type} 測試...")
        
        # 構建完整命令
        cmd = [sys.executable, "-m", "pytest"] + args
        
        if self.config and self.config.verbose_logging:
            cmd.append("-v")
        
        print(f"執行命令: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.config.performance_timeout if self.config else 300
            )
            
            duration = time.time() - start_time
            
            # 解析測試結果
            test_result = self._parse_pytest_output(
                result.stdout + result.stderr,
                test_type,
                duration,
                result.returncode
            )
            
            test_result.output = result.stdout + result.stderr
            
            if result.returncode == 0:
                print(f"✅ {test_type} 測試完成 ({duration:.2f}s)")
            else:
                print(f"❌ {test_type} 測試失敗 ({duration:.2f}s)")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"⏰ {test_type} 測試超時 ({duration:.2f}s)")
            
            return TestResult(
                test_type=test_type,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=duration,
                exit_code=124,  # 超時退出碼
                output="測試執行超時"
            )
    
    def _parse_pytest_output(self, output: str, test_type: str, duration: float, exit_code: int) -> TestResult:
        """解析 pytest 輸出"""
        passed = failed = skipped = errors = 0
        coverage = None
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 解析測試結果統計
            if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                # 例如: "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            passed = int(parts[i-1])
                        except ValueError:
                            pass
                    elif part == "failed" and i > 0:
                        try:
                            failed = int(parts[i-1])
                        except ValueError:
                            pass
                    elif part == "skipped" and i > 0:
                        try:
                            skipped = int(parts[i-1])
                        except ValueError:
                            pass
                    elif part == "error" and i > 0:
                        try:
                            errors = int(parts[i-1])
                        except ValueError:
                            pass
            
            # 解析覆蓋率
            elif "TOTAL" in line and "%" in line:
                # 例如: "TOTAL    1000    200     80%"
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            coverage = float(part[:-1])
                        except ValueError:
                            pass
        
        return TestResult(
            test_type=test_type,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            coverage=coverage,
            exit_code=exit_code
        )
    
    def run_unit_tests(self, coverage: bool = False) -> TestResult:
        """執行單元測試"""
        args = ["tests/unit", "-m", "unit"]
        
        if coverage:
            args.extend([
                "--cov=jobseeker",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov"
            ])
        
        result = self.run_pytest(args, "單元測試")
        self.results.append(result)
        return result
    
    def run_integration_tests(self, coverage: bool = False) -> TestResult:
        """執行整合測試"""
        args = ["tests/integration", "-m", "integration"]
        
        if coverage:
            args.extend([
                "--cov=jobseeker",
                "--cov-append",
                "--cov-report=term-missing"
            ])
        
        result = self.run_pytest(args, "整合測試")
        self.results.append(result)
        return result
    
    def run_performance_tests(self) -> TestResult:
        """執行效能測試"""
        args = ["tests/performance", "-m", "performance", "--tb=short"]
        
        result = self.run_pytest(args, "效能測試")
        self.results.append(result)
        return result
    
    def run_network_tests(self) -> TestResult:
        """執行網路測試"""
        args = ["tests", "-m", "requires_network", "--tb=short"]
        
        result = self.run_pytest(args, "網路測試")
        self.results.append(result)
        return result
    
    def run_all_tests(self, coverage: bool = False, include_network: bool = False) -> List[TestResult]:
        """執行所有測試"""
        print("🚀 開始執行完整測試套件...")
        
        # 單元測試
        self.run_unit_tests(coverage=coverage)
        
        # 整合測試
        self.run_integration_tests(coverage=coverage)
        
        # 效能測試
        self.run_performance_tests()
        
        # 網路測試（可選）
        if include_network:
            self.run_network_tests()
        
        return self.results
    
    def run_smoke_tests(self) -> TestResult:
        """執行冒煙測試"""
        args = ["tests", "-m", "smoke", "--tb=line"]
        
        result = self.run_pytest(args, "冒煙測試")
        self.results.append(result)
        return result
    
    def run_quick_tests(self) -> TestResult:
        """執行快速測試"""
        args = ["tests", "-m", "fast", "--tb=line"]
        
        result = self.run_pytest(args, "快速測試")
        self.results.append(result)
        return result
    
    def run_code_quality_checks(self) -> Dict[str, bool]:
        """執行程式碼品質檢查"""
        print("🔍 執行程式碼品質檢查...")
        
        checks = {}
        
        # Black 格式檢查
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "."],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            checks['black'] = result.returncode == 0
            if checks['black']:
                print("✅ Black 格式檢查通過")
            else:
                print("❌ Black 格式檢查失敗")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            checks['black'] = False
            print("⚠️  Black 未安裝或執行失敗")
        
        # isort 導入排序檢查
        try:
            result = subprocess.run(
                [sys.executable, "-m", "isort", "--check-only", "."],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            checks['isort'] = result.returncode == 0
            if checks['isort']:
                print("✅ isort 導入排序檢查通過")
            else:
                print("❌ isort 導入排序檢查失敗")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            checks['isort'] = False
            print("⚠️  isort 未安裝或執行失敗")
        
        # Flake8 程式碼風格檢查
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "."],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            checks['flake8'] = result.returncode == 0
            if checks['flake8']:
                print("✅ Flake8 程式碼風格檢查通過")
            else:
                print("❌ Flake8 程式碼風格檢查失敗")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            checks['flake8'] = False
            print("⚠️  Flake8 未安裝或執行失敗")
        
        # MyPy 類型檢查
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy", "jobseeker"],
                cwd=self.project_root,
                capture_output=True,
                timeout=120
            )
            checks['mypy'] = result.returncode == 0
            if checks['mypy']:
                print("✅ MyPy 類型檢查通過")
            else:
                print("❌ MyPy 類型檢查失敗")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            checks['mypy'] = False
            print("⚠️  MyPy 未安裝或執行失敗")
        
        return checks
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """生成測試報告"""
        if not self.results:
            return "沒有測試結果可報告"
        
        report_lines = []
        report_lines.append("# jobseeker 測試報告")
        report_lines.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 總覽
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        report_lines.append("## 測試總覽")
        report_lines.append(f"- 總測試數: {total_passed + total_failed + total_skipped + total_errors}")
        report_lines.append(f"- 通過: {total_passed}")
        report_lines.append(f"- 失敗: {total_failed}")
        report_lines.append(f"- 跳過: {total_skipped}")
        report_lines.append(f"- 錯誤: {total_errors}")
        report_lines.append(f"- 總執行時間: {total_duration:.2f}s")
        
        if total_passed + total_failed + total_errors > 0:
            success_rate = (total_passed / (total_passed + total_failed + total_errors)) * 100
            report_lines.append(f"- 成功率: {success_rate:.1f}%")
        
        report_lines.append("")
        
        # 詳細結果
        report_lines.append("## 詳細結果")
        for result in self.results:
            report_lines.append(f"### {result.test_type}")
            report_lines.append(f"- 通過: {result.passed}")
            report_lines.append(f"- 失敗: {result.failed}")
            report_lines.append(f"- 跳過: {result.skipped}")
            report_lines.append(f"- 錯誤: {result.errors}")
            report_lines.append(f"- 執行時間: {result.duration:.2f}s")
            report_lines.append(f"- 成功率: {result.success_rate:.1f}%")
            
            if result.coverage is not None:
                report_lines.append(f"- 覆蓋率: {result.coverage:.1f}%")
            
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # 保存報告
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding='utf-8')
            print(f"📊 測試報告已保存到: {output_path}")
        
        return report_content
    
    def save_results_json(self, output_file: str) -> None:
        """保存測試結果為 JSON"""
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'results': [result.to_dict() for result in self.results],
            'summary': {
                'total_passed': sum(r.passed for r in self.results),
                'total_failed': sum(r.failed for r in self.results),
                'total_skipped': sum(r.skipped for r in self.results),
                'total_errors': sum(r.errors for r in self.results),
                'total_duration': sum(r.duration for r in self.results)
            }
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 測試結果已保存到: {output_path}")
    
    def cleanup(self) -> None:
        """清理測試環境"""
        if self.config:
            cleanup_test_environment(self.config)
        
        # 清理測試產生的檔案
        cleanup_patterns = [
            "**/.pytest_cache",
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            ".coverage",
            "htmlcov",
            "test-results.xml",
            "coverage.xml"
        ]
        
        for pattern in cleanup_patterns:
            for path in self.project_root.glob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="jobseeker 測試執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python test_runner.py --unit                    # 執行單元測試
  python test_runner.py --integration             # 執行整合測試
  python test_runner.py --performance             # 執行效能測試
  python test_runner.py --all --coverage          # 執行所有測試並生成覆蓋率報告
  python test_runner.py --smoke                   # 執行冒煙測試
  python test_runner.py --quick                   # 執行快速測試
  python test_runner.py --check                   # 執行程式碼品質檢查
  python test_runner.py --install                 # 安裝測試依賴
        """
    )
    
    # 測試類型選項
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="執行單元測試")
    test_group.add_argument("--integration", action="store_true", help="執行整合測試")
    test_group.add_argument("--performance", action="store_true", help="執行效能測試")
    test_group.add_argument("--network", action="store_true", help="執行網路測試")
    test_group.add_argument("--all", action="store_true", help="執行所有測試")
    test_group.add_argument("--smoke", action="store_true", help="執行冒煙測試")
    test_group.add_argument("--quick", action="store_true", help="執行快速測試")
    
    # 其他選項
    parser.add_argument("--coverage", action="store_true", help="生成覆蓋率報告")
    parser.add_argument("--include-network", action="store_true", help="包含網路測試（僅用於 --all）")
    parser.add_argument("--check", action="store_true", help="執行程式碼品質檢查")
    parser.add_argument("--install", action="store_true", help="安裝測試依賴")
    parser.add_argument("--report", type=str, help="生成測試報告到指定檔案")
    parser.add_argument("--json", type=str, help="保存測試結果為 JSON 格式")
    parser.add_argument("--cleanup", action="store_true", help="清理測試環境")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    # 如果沒有指定任何選項，顯示幫助
    if not any([
        args.unit, args.integration, args.performance, args.network,
        args.all, args.smoke, args.quick, args.check, args.install,
        args.cleanup
    ]):
        parser.print_help()
        return 1
    
    try:
        # 創建測試執行器
        config = None
        if TestConfig:
            config = get_test_config()
            if args.verbose:
                config.verbose_logging = True
        
        runner = TestRunner(config)
        
        # 安裝依賴
        if args.install:
            if not runner.install_dependencies():
                print("❌ 依賴安裝失敗")
                return 1
            print("✅ 依賴安裝完成")
            return 0
        
        # 檢查依賴
        if not runner.check_dependencies():
            print("❌ 依賴檢查失敗，請先執行: python test_runner.py --install")
            return 1
        
        # 程式碼品質檢查
        if args.check:
            checks = runner.run_code_quality_checks()
            failed_checks = [k for k, v in checks.items() if not v]
            
            if failed_checks:
                print(f"❌ 程式碼品質檢查失敗: {', '.join(failed_checks)}")
                return 1
            else:
                print("✅ 所有程式碼品質檢查通過")
                return 0
        
        # 執行測試
        exit_code = 0
        
        if args.unit:
            result = runner.run_unit_tests(coverage=args.coverage)
            exit_code = result.exit_code
        
        elif args.integration:
            result = runner.run_integration_tests(coverage=args.coverage)
            exit_code = result.exit_code
        
        elif args.performance:
            result = runner.run_performance_tests()
            exit_code = result.exit_code
        
        elif args.network:
            result = runner.run_network_tests()
            exit_code = result.exit_code
        
        elif args.smoke:
            result = runner.run_smoke_tests()
            exit_code = result.exit_code
        
        elif args.quick:
            result = runner.run_quick_tests()
            exit_code = result.exit_code
        
        elif args.all:
            results = runner.run_all_tests(
                coverage=args.coverage,
                include_network=args.include_network
            )
            exit_code = max(r.exit_code for r in results) if results else 0
        
        # 生成報告
        if args.report:
            runner.generate_report(args.report)
        
        # 保存 JSON 結果
        if args.json:
            runner.save_results_json(args.json)
        
        # 清理
        if args.cleanup:
            runner.cleanup()
            print("🧹 測試環境已清理")
        
        # 顯示總結
        if runner.results:
            print("\n" + "="*50)
            print("📊 測試總結")
            print("="*50)
            
            for result in runner.results:
                status = "✅" if result.exit_code == 0 else "❌"
                print(f"{status} {result.test_type}: {result.passed}通過, {result.failed}失敗, {result.skipped}跳過 ({result.duration:.2f}s)")
            
            total_failed = sum(r.failed + r.errors for r in runner.results)
            if total_failed == 0:
                print("\n🎉 所有測試通過！")
            else:
                print(f"\n⚠️  有 {total_failed} 個測試失敗")
        
        return exit_code
    
    except KeyboardInterrupt:
        print("\n⏹️  測試被用戶中斷")
        return 130
    
    except Exception as e:
        print(f"❌ 測試執行器錯誤: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
