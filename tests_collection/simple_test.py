#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的增強版爬蟲測試腳本
"""

import sys
import traceback
from jobseeker.model import ScraperInput, Site

def test_imports():
    """測試模組導入"""
    print("Testing imports...")
    try:
        from jobseeker.ziprecruiter.enhanced_ziprecruiter import EnhancedZipRecruiter
        from jobseeker.google.enhanced_google import EnhancedGoogle
        from jobseeker.bayt.enhanced_bayt import EnhancedBaytScraper
        from jobseeker.anti_detection import AntiDetectionScraper
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_anti_detection():
    """測試反檢測模組"""
    print("Testing anti-detection module...")
    try:
        from jobseeker.anti_detection import AntiDetectionScraper
        scraper = AntiDetectionScraper()
        headers = scraper.get_random_headers()
        if headers and 'User-Agent' in headers:
            print("✓ Anti-detection module working")
            return True
        else:
            print("✗ Anti-detection module failed")
            return False
    except Exception as e:
        print(f"✗ Anti-detection test failed: {e}")
        return False

def test_ziprecruiter():
    """測試 ZipRecruiter 爬蟲"""
    print("Testing ZipRecruiter scraper...")
    try:
        from jobseeker.ziprecruiter.enhanced_ziprecruiter import EnhancedZipRecruiter
        scraper = EnhancedZipRecruiter()
        scraper_input = ScraperInput(
            site_type=[Site.ZIP_RECRUITER],
            search_term="python developer",
            location="New York",
            results_wanted=5
        )
        
        result = scraper.scrape(scraper_input)
        
        if result and hasattr(result, 'jobs') and len(result.jobs) > 0:
            print(f"✓ ZipRecruiter test successful, got {len(result.jobs)} jobs")
            return True
        else:
            print("⚠ ZipRecruiter test completed but no jobs found")
            return False
            
    except Exception as e:
        print(f"✗ ZipRecruiter test failed: {e}")
        return False

def test_google():
    """測試 Google Jobs 爬蟲"""
    print("Testing Google Jobs scraper...")
    try:
        from jobseeker.google.enhanced_google import EnhancedGoogle
        scraper = EnhancedGoogle()
        scraper_input = ScraperInput(
            site_type=[Site.GOOGLE],
            search_term="software engineer",
            location="San Francisco",
            results_wanted=5
        )
        
        result = scraper.scrape(scraper_input)
        
        if result and hasattr(result, 'jobs') and len(result.jobs) > 0:
            print(f"✓ Google Jobs test successful, got {len(result.jobs)} jobs")
            return True
        else:
            print("⚠ Google Jobs test completed but no jobs found")
            return False
            
    except Exception as e:
        print(f"✗ Google Jobs test failed: {e}")
        return False

def test_bayt():
    """測試 Bayt 爬蟲"""
    print("Testing Bayt scraper...")
    try:
        from jobseeker.bayt.enhanced_bayt import EnhancedBaytScraper
        scraper = EnhancedBaytScraper()
        scraper_input = ScraperInput(
            site_type=[Site.BAYT],
            search_term="software engineer",
            location="Dubai",
            results_wanted=5
        )
        
        result = scraper.scrape(scraper_input)
        
        if result and hasattr(result, 'jobs') and len(result.jobs) > 0:
            print(f"✓ Bayt test successful, got {len(result.jobs)} jobs")
            return True
        else:
            print("⚠ Bayt test completed but no jobs found")
            return False
            
    except Exception as e:
        print(f"✗ Bayt test failed: {e}")
        return False

def main():
    """主測試函數"""
    print("=== Enhanced Scrapers Test ===")
    
    tests = [
        ("Import Test", test_imports),
        ("Anti-Detection Test", test_anti_detection),
        ("ZipRecruiter Test", test_ziprecruiter),
        ("Google Jobs Test", test_google),
        ("Bayt Test", test_bayt)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append(False)
    
    # 統計結果
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count) * 100
    
    print(f"\n=== Test Summary ===")
    print(f"Success Rate: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_count == total_count:
        print("All tests passed!")
        return 0
    elif success_count >= total_count * 0.6:
        print("Most tests passed.")
        return 0
    else:
        print("Many tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
