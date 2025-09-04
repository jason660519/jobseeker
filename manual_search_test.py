#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動搜索測試指引
用於測試JobSeeker網頁應用的搜索欄功能
"""

import webbrowser
import time

class SearchTestGuide:
    """搜索測試指引類"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """初始化測試指引
        
        Args:
            base_url: 網頁應用的基礎URL
        """
        self.base_url = base_url
    
    def show_test_cases(self):
        """顯示測試案例"""
        print("🎯 JobSeeker 網頁搜索功能測試")
        print("=" * 60)
        print(f"🌐 測試網址: {self.base_url}")
        print("\n📋 建議測試案例:")
        print("-" * 60)
        
        test_cases = [
            # 基本職位搜索
            {"category": "基本職位搜索", "cases": [
                {"query": "軟體工程師", "location": "台北", "expected": "應該找到相關職位"},
                {"query": "Python開發者", "location": "新竹", "expected": "應該找到Python相關職位"},
                {"query": "前端工程師", "location": "台中", "expected": "應該找到前端開發職位"},
                {"query": "資料科學家", "location": "高雄", "expected": "應該找到數據分析職位"},
            ]},
            
            # 英文職位搜索
            {"category": "英文職位搜索", "cases": [
                {"query": "Software Engineer", "location": "Taipei", "expected": "應該支援英文搜索"},
                {"query": "Data Analyst", "location": "Taichung", "expected": "應該找到數據分析師職位"},
                {"query": "Product Manager", "location": "Kaohsiung", "expected": "應該找到產品經理職位"},
            ]},
            
            # 特殊字符測試
            {"category": "特殊字符測試", "cases": [
                {"query": "AI/ML工程師", "location": "台北", "expected": "應該正確處理特殊字符"},
                {"query": "C++開發者", "location": "新竹", "expected": "應該正確處理++符號"},
                {"query": "UI/UX設計師", "location": "台中", "expected": "應該正確處理斜線"},
            ]},
            
            # 邊界測試
            {"category": "邊界測試", "cases": [
                {"query": "", "location": "台北", "expected": "應該顯示錯誤或提示訊息"},
                {"query": "   ", "location": "台北", "expected": "應該處理空白字符"},
                {"query": "工程師", "location": "", "expected": "應該處理空地點"},
                {"query": "資深全端軟體開發工程師具備React和Node.js經驗", "location": "台北", "expected": "應該處理長查詢"},
            ]}
        ]
        
        for category_data in test_cases:
            print(f"\n📂 {category_data['category']}")
            print("-" * 40)
            
            for i, case in enumerate(category_data['cases'], 1):
                print(f"{i:2d}. 搜索: '{case['query']}' | 地點: '{case['location']}'")
                print(f"    預期: {case['expected']}")
                print()
    
    def show_test_instructions(self):
        """顯示測試說明"""
        print("\n🔍 測試步驟說明:")
        print("=" * 60)
        print("1. 📱 打開瀏覽器並訪問測試網址")
        print("2. 🔍 在搜索欄輸入職位關鍵字")
        print("3. 📍 在地點欄輸入地點")
        print("4. 🔘 點擊搜索按鈕")
        print("5. ⏱️ 觀察搜索結果和響應時間")
        print("6. ❗ 檢查是否有錯誤訊息")
        print("7. 📊 記錄測試結果")
        
        print("\n✅ 測試重點:")
        print("-" * 30)
        print("• 搜索功能是否正常運作")
        print("• 是否能正確處理中英文輸入")
        print("• 特殊字符是否被正確處理")
        print("• 空輸入是否有適當的錯誤處理")
        print("• 搜索結果是否合理")
        print("• 頁面響應速度是否正常")
        print("• 是否有JavaScript錯誤")
        
        print("\n🐛 常見問題檢查:")
        print("-" * 30)
        print("• 搜索按鈕無法點擊")
        print("• 搜索結果不顯示")
        print("• 頁面載入過慢")
        print("• 錯誤訊息不清楚")
        print("• 特殊字符導致錯誤")
        print("• 空輸入未被攔截")
    
    def show_browser_console_guide(self):
        """顯示瀏覽器控制台檢查指引"""
        print("\n🔧 瀏覽器開發者工具檢查:")
        print("=" * 60)
        print("1. 按 F12 打開開發者工具")
        print("2. 切換到 Console 標籤")
        print("3. 執行搜索並觀察是否有錯誤訊息")
        print("4. 切換到 Network 標籤")
        print("5. 執行搜索並檢查網絡請求")
        print("6. 查看 /search 請求的狀態碼和響應")
        
        print("\n📊 需要檢查的項目:")
        print("-" * 30)
        print("• JavaScript 錯誤 (紅色訊息)")
        print("• 網絡請求狀態 (200, 400, 500等)")
        print("• 請求響應時間")
        print("• 請求和響應的數據格式")
    
    def open_browser(self):
        """打開瀏覽器"""
        try:
            print(f"\n🌐 正在打開瀏覽器: {self.base_url}")
            webbrowser.open(self.base_url)
            print("✅ 瀏覽器已打開")
            return True
        except Exception as e:
            print(f"❌ 無法自動打開瀏覽器: {str(e)}")
            print(f"💡 請手動在瀏覽器中訪問: {self.base_url}")
            return False
    
    def run_interactive_guide(self):
        """運行互動式測試指引"""
        print("\n🎮 互動式測試模式")
        print("=" * 60)
        
        while True:
            print("\n選擇操作:")
            print("1. 📋 顯示測試案例")
            print("2. 🔍 顯示測試說明")
            print("3. 🔧 顯示開發者工具指引")
            print("4. 🌐 打開測試網頁")
            print("5. 🚪 退出")
            
            try:
                choice = input("\n請選擇 (1-5): ").strip()
                
                if choice == "1":
                    self.show_test_cases()
                elif choice == "2":
                    self.show_test_instructions()
                elif choice == "3":
                    self.show_browser_console_guide()
                elif choice == "4":
                    self.open_browser()
                elif choice == "5":
                    print("\n👋 測試指引結束，祝測試順利！")
                    break
                else:
                    print("❌ 無效選擇，請輸入 1-5")
                    
            except KeyboardInterrupt:
                print("\n\n👋 測試已取消")
                break
            except Exception as e:
                print(f"❌ 發生錯誤: {str(e)}")

def main():
    """主函數"""
    guide = SearchTestGuide()
    
    # 顯示歡迎訊息
    print("🎯 JobSeeker 搜索功能測試指引")
    print("=" * 60)
    print("這個工具將幫助您測試網頁應用的搜索功能")
    
    # 自動打開瀏覽器
    guide.open_browser()
    
    # 顯示基本測試案例
    guide.show_test_cases()
    
    # 顯示測試說明
    guide.show_test_instructions()
    
    # 詢問是否需要互動模式
    try:
        print("\n❓ 是否需要互動式測試指引？ (y/n, 預設為 n): ", end="")
        response = input().strip().lower()
        
        if response in ['y', 'yes', '是']:
            guide.run_interactive_guide()
        else:
            print("\n✅ 測試指引完成！")
            print("💡 您現在可以在瀏覽器中進行手動測試")
            
    except KeyboardInterrupt:
        print("\n\n👋 測試指引結束")

if __name__ == "__main__":
    main()