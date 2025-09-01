#!/usr/bin/env pwsh
# jobseeker 測試腳本批次執行器
# 用於一次執行所有測試腳本並生成統合報告

Write-Host "=== jobseeker 測試腳本批次執行器 ===" -ForegroundColor Green
Write-Host "開始執行所有測試腳本..." -ForegroundColor Yellow

# 記錄開始時間
$startTime = Get-Date
$timestamp = $startTime.ToString("yyyyMMdd_HHmmss")

# 創建批次測試結果目錄
$batchResultDir = "batch_test_results_$timestamp"
New-Item -ItemType Directory -Path $batchResultDir -Force | Out-Null
Write-Host "批次測試結果將保存到: $batchResultDir" -ForegroundColor Cyan

# 定義測試腳本列表（按優先級排序）
$testScripts = @(
    @{Name="UI/UX 職位搜尋測試"; Script="ui_ux_test.py"; Priority="High"},
    @{Name="機器學習工程師職位測試（最終版）"; Script="ml_engineer_test_final.py"; Priority="High"},
    @{Name="增強版爬蟲測試（最終版）"; Script="test_enhanced_scrapers_final.py"; Priority="Medium"},
    @{Name="簡化版增強爬蟲測試"; Script="simple_test.py"; Priority="Medium"},
    @{Name="最終驗證測試"; Script="final_verification_test.py"; Priority="Low"},
    @{Name="BDJobs 修復測試"; Script="test_bdjobs_fix.py"; Priority="Low"}
)

# 測試結果統計
$testResults = @()
$totalTests = $testScripts.Count
$successfulTests = 0
$failedTests = 0

# 執行每個測試腳本
foreach ($test in $testScripts) {
    Write-Host "`n--- 執行: $($test.Name) ---" -ForegroundColor Magenta
    Write-Host "腳本: $($test.Script)" -ForegroundColor Gray
    Write-Host "優先級: $($test.Priority)" -ForegroundColor Gray
    
    $testStartTime = Get-Date
    
    try {
        # 執行測試腳本
        $output = python $test.Script 2>&1
        $exitCode = $LASTEXITCODE
        
        $testEndTime = Get-Date
        $duration = $testEndTime - $testStartTime
        
        if ($exitCode -eq 0) {
            Write-Host "✅ 測試成功完成" -ForegroundColor Green
            $status = "Success"
            $successfulTests++
        } else {
            Write-Host "❌ 測試執行失敗 (退出代碼: $exitCode)" -ForegroundColor Red
            $status = "Failed"
            $failedTests++
        }
        
        # 保存測試輸出
        $outputFile = Join-Path $batchResultDir "$($test.Script)_output.txt"
        $output | Out-File -FilePath $outputFile -Encoding UTF8
        
    } catch {
        Write-Host "❌ 測試執行異常: $($_.Exception.Message)" -ForegroundColor Red
        $status = "Error"
        $failedTests++
        $duration = New-TimeSpan
        
        # 保存錯誤信息
        $errorFile = Join-Path $batchResultDir "$($test.Script)_error.txt"
        $_.Exception.Message | Out-File -FilePath $errorFile -Encoding UTF8
    }
    
    # 記錄測試結果
    $testResults += [PSCustomObject]@{
        TestName = $test.Name
        Script = $test.Script
        Priority = $test.Priority
        Status = $status
        Duration = $duration.ToString("mm\:ss")
        StartTime = $testStartTime.ToString("HH:mm:ss")
        EndTime = $testEndTime.ToString("HH:mm:ss")
    }
    
    Write-Host "執行時間: $($duration.ToString('mm\:ss'))" -ForegroundColor Gray
}

# 計算總執行時間
$endTime = Get-Date
$totalDuration = $endTime - $startTime

# 生成統合報告
Write-Host "`n=== 批次測試完成 ===" -ForegroundColor Green
Write-Host "總執行時間: $($totalDuration.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
Write-Host "成功測試: $successfulTests/$totalTests" -ForegroundColor Green
Write-Host "失敗測試: $failedTests/$totalTests" -ForegroundColor Red
Write-Host "成功率: $([math]::Round(($successfulTests/$totalTests)*100, 1))%" -ForegroundColor Yellow

# 保存詳細報告
$reportFile = Join-Path $batchResultDir "batch_test_report.txt"
$report = @"
jobseeker 批次測試報告
==================================================
測試時間: $($startTime.ToString('yyyy-MM-dd HH:mm:ss')) - $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))
總執行時間: $($totalDuration.ToString('hh\:mm\:ss'))
測試腳本數量: $totalTests
成功測試: $successfulTests
失敗測試: $failedTests
成功率: $([math]::Round(($successfulTests/$totalTests)*100, 1))%

詳細結果:
==================================================
"@

foreach ($result in $testResults) {
    $report += "`n測試名稱: $($result.TestName)"
    $report += "`n腳本檔案: $($result.Script)"
    $report += "`n優先級: $($result.Priority)"
    $report += "`n狀態: $($result.Status)"
    $report += "`n開始時間: $($result.StartTime)"
    $report += "`n結束時間: $($result.EndTime)"
    $report += "`n執行時間: $($result.Duration)"
    $report += "`n" + "-" * 50
}

$report | Out-File -FilePath $reportFile -Encoding UTF8

# 顯示測試結果表格
Write-Host "`n測試結果摘要:" -ForegroundColor Cyan
$testResults | Format-Table -Property TestName, Status, Duration, Priority -AutoSize

Write-Host "詳細報告已保存到: $reportFile" -ForegroundColor Cyan
Write-Host "所有測試輸出已保存到: $batchResultDir" -ForegroundColor Cyan

# 如果有失敗的測試，顯示建議
if ($failedTests -gt 0) {
    Write-Host "`n⚠️  建議檢查失敗的測試:" -ForegroundColor Yellow
    $testResults | Where-Object { $_.Status -ne "Success" } | ForEach-Object {
        Write-Host "   - $($_.TestName) ($($_.Script))" -ForegroundColor Red
    }
}

Write-Host "`n批次測試執行完成！" -ForegroundColor Green
