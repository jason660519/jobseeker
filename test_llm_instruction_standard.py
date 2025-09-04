#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM指令標準規範測試腳本

此腳本用於測試修正後的LLM指令是否符合標準規範，
並能正確處理各種類型的用戶查詢。

Author: JobSpy Team
Date: 2025-01-05
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobseeker.llm_intent_analyzer import LLMIntentAnalyzer
from jobseeker.intent_analyzer import IntentType

class LLMInstructionStandardTester:
    """
    LLM指令標準規範測試器
    
    用於驗證LLM指令是否符合制定的標準規範，
    包括角色定義、輸出格式、JSON結構等方面。
    """
    
    def __init__(self):
        """初始化測試器"""
        self.analyzer = LLMIntentAnalyzer()
        self.test_cases = self._create_test_cases()
        self.results = []
        
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """
        創建測試案例
        
        Returns:
            List[Dict]: 測試案例列表
        """
        return [
            # 標準求職查詢測試
            {
                "category": "標準求職查詢",
                "cases": [
                    {
                        "query": "軟體工程師",
                        "location": "台北",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "基本職位查詢"
                    },
                    {
                        "query": "Python開發者",
                        "location": "新竹",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "技能導向查詢"
                    },
                    {
                        "query": "資深前端工程師",
                        "location": "台中",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "經驗級別查詢"
                    }
                ]
            },
            
            # JSON格式驗證測試
            {
                "category": "JSON格式驗證",
                "cases": [
                    {
                        "query": "數據分析師",
                        "location": "高雄",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "驗證JSON結構完整性",
                        "check_json_structure": True
                    },
                    {
                        "query": "UI/UX設計師",
                        "location": "台南",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "驗證特殊字符處理",
                        "check_json_structure": True
                    }
                ]
            },
            
            # 邊界案例測試
            {
                "category": "邊界案例",
                "cases": [
                    {
                        "query": "工作",
                        "location": "台北",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "模糊求職關鍵詞"
                    },
                    {
                        "query": "薪水",
                        "location": "台中",
                        "expected_job_related": False,
                        "expected_intent_type": "non_job_related",
                        "description": "薪資相關但非求職查詢"
                    },
                    {
                        "query": "台北",
                        "location": "",
                        "expected_job_related": False,
                        "expected_intent_type": "non_job_related",
                        "description": "僅地點名稱"
                    }
                ]
            },
            
            # 非求職相關測試
            {
                "category": "非求職相關",
                "cases": [
                    {
                        "query": "今天天氣如何",
                        "location": "",
                        "expected_job_related": False,
                        "expected_intent_type": "non_job_related",
                        "description": "天氣查詢"
                    },
                    {
                        "query": "推薦一部好電影",
                        "location": "",
                        "expected_job_related": False,
                        "expected_intent_type": "non_job_related",
                        "description": "娛樂推薦"
                    },
                    {
                        "query": "學習Python的最佳方法",
                        "location": "",
                        "expected_job_related": False,
                        "expected_intent_type": "non_job_related",
                        "description": "學習諮詢"
                    }
                ]
            },
            
            # 指令遵循測試
            {
                "category": "指令遵循驗證",
                "cases": [
                    {
                        "query": "機器學習工程師",
                        "location": "遠程",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "驗證職業分析師角色",
                        "check_role_compliance": True
                    },
                    {
                        "query": "全端開發者",
                        "location": "混合辦公",
                        "expected_job_related": True,
                        "expected_intent_type": "job_search",
                        "description": "驗證結構化輸出",
                        "check_structured_output": True
                    }
                ]
            }
        ]
    
    def _validate_json_structure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證JSON結構是否符合標準
        
        Args:
            result: LLM分析結果
            
        Returns:
            Dict: 驗證結果
        """
        validation_result = {
            "valid": True,
            "missing_fields": [],
            "invalid_types": [],
            "details": []
        }
        
        # 檢查必要字段
        required_fields = [
            "is_job_related", "intent_type", "confidence", 
            "reasoning", "structured_intent", "search_suggestions", 
            "response_message"
        ]
        
        for field in required_fields:
            if field not in result:
                validation_result["missing_fields"].append(field)
                validation_result["valid"] = False
        
        # 檢查數據類型
        type_checks = {
            "is_job_related": bool,
            "intent_type": str,
            "confidence": (int, float),
            "reasoning": str,
            "structured_intent": dict,
            "search_suggestions": list,
            "response_message": str
        }
        
        for field, expected_type in type_checks.items():
            if field in result and not isinstance(result[field], expected_type):
                validation_result["invalid_types"].append({
                    "field": field,
                    "expected": str(expected_type),
                    "actual": str(type(result[field]))
                })
                validation_result["valid"] = False
        
        # 檢查structured_intent結構
        if "structured_intent" in result and isinstance(result["structured_intent"], dict):
            structured_fields = [
                "job_titles", "skills", "locations", "salary_range",
                "work_mode", "company_size", "industry", "experience_level",
                "soft_preferences", "urgency"
            ]
            
            for field in structured_fields:
                if field not in result["structured_intent"]:
                    validation_result["missing_fields"].append(f"structured_intent.{field}")
                    validation_result["valid"] = False
        
        return validation_result
    
    def _check_role_compliance(self, reasoning: str) -> bool:
        """
        檢查是否遵循職業分析師角色
        
        Args:
            reasoning: 推理過程文本
            
        Returns:
            bool: 是否符合角色要求
        """
        # 檢查是否體現了職業分析師的專業性
        professional_indicators = [
            "分析", "評估", "判斷", "識別", "提取",
            "職業", "求職", "工作", "技能", "經驗"
        ]
        
        return any(indicator in reasoning for indicator in professional_indicators)
    
    def _check_structured_output(self, result: Dict[str, Any]) -> bool:
        """
        檢查是否提供了結構化輸出
        
        Args:
            result: 分析結果
            
        Returns:
            bool: 是否符合結構化輸出要求
        """
        if "structured_intent" not in result:
            return False
            
        structured_intent = result["structured_intent"]
        
        # 如果structured_intent為None，返回False
        if structured_intent is None:
            return False
        
        # 檢查是否提取了關鍵參數
        key_extractions = [
            "job_titles", "skills", "locations"
        ]
        
        return all(hasattr(structured_intent, field) for field in key_extractions)
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        運行單個測試案例
        
        Args:
            test_case: 測試案例
            
        Returns:
            Dict: 測試結果
        """
        query = test_case["query"]
        location = test_case.get("location", "")
        full_query = f"{query} {location}".strip()
        
        try:
            # 執行LLM意圖分析
            intent_result, decision_result = self.analyzer.analyze_intent_with_decision(full_query)
            
            # 基本結果檢查
            basic_passed = (
                intent_result.is_job_related == test_case["expected_job_related"] and
                intent_result.intent_type.value == test_case["expected_intent_type"]
            )
            
            result = {
                "test_case": test_case["description"],
                "query": query,
                "location": location,
                "full_query": full_query,
                "expected_job_related": test_case["expected_job_related"],
                "actual_job_related": intent_result.is_job_related,
                "expected_intent_type": test_case["expected_intent_type"],
                "actual_intent_type": intent_result.intent_type.value,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.llm_reasoning,
                "basic_passed": basic_passed,
                "timestamp": datetime.now().isoformat()
            }
            
            # 額外檢查
            if test_case.get("check_json_structure"):
                json_validation = self._validate_json_structure({
                    "is_job_related": intent_result.is_job_related,
                    "intent_type": intent_result.intent_type.value,
                    "confidence": intent_result.confidence,
                    "reasoning": intent_result.llm_reasoning,
                    "structured_intent": intent_result.structured_intent,
                    "search_suggestions": intent_result.search_query_suggestions,
                    "response_message": intent_result.response_message
                })
                result["json_validation"] = json_validation
                result["json_structure_valid"] = json_validation["valid"]
            
            if test_case.get("check_role_compliance"):
                role_compliance = self._check_role_compliance(intent_result.llm_reasoning)
                result["role_compliance"] = role_compliance
            
            if test_case.get("check_structured_output"):
                structured_output_valid = self._check_structured_output({
                    "structured_intent": intent_result.structured_intent
                })
                result["structured_output_valid"] = structured_output_valid
            
            # 綜合評估
            all_checks_passed = basic_passed
            if test_case.get("check_json_structure"):
                all_checks_passed = all_checks_passed and result.get("json_structure_valid", True)
            if test_case.get("check_role_compliance"):
                all_checks_passed = all_checks_passed and result.get("role_compliance", True)
            if test_case.get("check_structured_output"):
                all_checks_passed = all_checks_passed and result.get("structured_output_valid", True)
            
            result["overall_passed"] = all_checks_passed
            
        except Exception as e:
            result = {
                "test_case": test_case["description"],
                "query": query,
                "location": location,
                "full_query": full_query,
                "error": str(e),
                "basic_passed": False,
                "overall_passed": False,
                "timestamp": datetime.now().isoformat()
            }
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        運行所有測試案例
        
        Returns:
            Dict: 完整測試結果
        """
        print("🚀 開始LLM指令標準規範測試")
        print("=" * 50)
        
        all_results = []
        category_stats = {}
        
        for category_data in self.test_cases:
            category = category_data["category"]
            cases = category_data["cases"]
            
            print(f"\n📋 測試類別: {category}")
            print("-" * 30)
            
            category_results = []
            passed_count = 0
            
            for i, test_case in enumerate(cases, 1):
                result = self.run_single_test(test_case)
                category_results.append(result)
                all_results.append(result)
                
                status = "✅ PASS" if result["overall_passed"] else "❌ FAIL"
                print(f"  {i}. {test_case['description']} - {status}")
                
                if not result["overall_passed"]:
                    if "error" in result:
                        print(f"     錯誤: {result['error']}")
                    else:
                        print(f"     預期求職相關: {result['expected_job_related']}, 實際: {result['actual_job_related']}")
                        print(f"     預期意圖類型: {result['expected_intent_type']}, 實際: {result['actual_intent_type']}")
                        
                        # 顯示額外檢查結果
                        if "json_structure_valid" in result and not result["json_structure_valid"]:
                            print(f"     JSON結構驗證失敗: {result['json_validation']}")
                        if "role_compliance" in result and not result["role_compliance"]:
                            print(f"     角色遵循檢查失敗")
                        if "structured_output_valid" in result and not result["structured_output_valid"]:
                            print(f"     結構化輸出檢查失敗")
                else:
                    passed_count += 1
            
            category_pass_rate = (passed_count / len(cases)) * 100
            category_stats[category] = {
                "total": len(cases),
                "passed": passed_count,
                "failed": len(cases) - passed_count,
                "pass_rate": category_pass_rate
            }
            
            print(f"   類別通過率: {passed_count}/{len(cases)} ({category_pass_rate:.1f}%)")
        
        # 計算總體統計
        total_tests = len(all_results)
        total_passed = sum(1 for r in all_results if r["overall_passed"])
        total_failed = total_tests - total_passed
        overall_pass_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        # 生成測試報告
        test_summary = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "overall_pass_rate": overall_pass_rate,
                "category_stats": category_stats,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": all_results
        }
        
        # 顯示總結
        print("\n📊 測試總結")
        print("=" * 50)
        print(f"總測試案例: {total_tests}")
        print(f"通過案例: {total_passed}")
        print(f"失敗案例: {total_failed}")
        print(f"總通過率: {overall_pass_rate:.1f}%")
        
        # 評估標準規範遵循情況
        print("\n🎯 標準規範遵循評估")
        print("=" * 30)
        
        if overall_pass_rate >= 95:
            print("✅ 優秀！LLM指令完全符合標準規範")
        elif overall_pass_rate >= 85:
            print("✅ 良好！LLM指令基本符合標準規範")
        elif overall_pass_rate >= 70:
            print("⚠️ 一般！LLM指令部分符合標準規範，需要改進")
        else:
            print("❌ 不佳！LLM指令不符合標準規範，需要重大修正")
        
        print(f"最終通過率: {overall_pass_rate:.1f}%")
        
        # 保存測試結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"llm_instruction_standard_test_results_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 測試結果已保存至: {result_file}")
        
        return test_summary

def main():
    """
    主函數：運行LLM指令標準規範測試
    """
    tester = LLMInstructionStandardTester()
    results = tester.run_all_tests()
    
    return results

if __name__ == "__main__":
    main()