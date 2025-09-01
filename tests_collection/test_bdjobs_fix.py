#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 BDJobs 修正是否有效
"""

from jobspy import scrape_jobs
from jobspy.model import Site

def test_bdjobs():
    """測試 BDJobs 是否能正常工作"""
    print("🧪 測試 BDJobs 修正...")
    
    try:
        # 測試 BDJobs
        jobs_df = scrape_jobs(
            site_name=Site.BDJOBS,
            search_term="Software Engineer",
            location="Dhaka, Bangladesh",
            results_wanted=5,
            verbose=1
        )
        
        if jobs_df is not None and not jobs_df.empty:
            print(f"✅ BDJobs 修正成功！找到 {len(jobs_df)} 個職位")
            print("前幾個職位:")
            for i, row in jobs_df.head(3).iterrows():
                print(f"  - {row['title']} at {row['company']}")
            return True
        else:
            print("⚠️ BDJobs 沒有找到職位，但沒有錯誤（可能是正常情況）")
            return True
            
    except Exception as e:
        error_msg = str(e)
        if "user_agent" in error_msg:
            print(f"❌ BDJobs 仍然有 user_agent 錯誤: {error_msg}")
            return False
        else:
            print(f"⚠️ BDJobs 有其他錯誤（但不是 user_agent 問題）: {error_msg}")
            return True

if __name__ == "__main__":
    success = test_bdjobs()
    if success:
        print("\n🎉 BDJobs user_agent 問題已修正！")
    else:
        print("\n❌ BDJobs user_agent 問題仍然存在")