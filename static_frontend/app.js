/**
 * JobSpy 靜態前端 JavaScript
 * 負責處理搜尋表單、API 調用、結果展示等功能
 */

// 配置
const CONFIG = {
    // API 基礎 URL - 本地開發環境
    API_BASE_URL: 'http://localhost:5000', // 本地後端地址
    
    // 分頁設置
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    
    // 搜尋設置
    DEFAULT_RESULTS_WANTED: 20,
    MAX_RESULTS_WANTED: 100,
    
    // 動畫設置
    ANIMATION_DURATION: 300,
    
    // 快取設置
    CACHE_DURATION: 5 * 60 * 1000, // 5 分鐘
};

// 全域變數
let currentSearchId = null;
let currentPage = 1;
let currentPerPage = CONFIG.DEFAULT_PAGE_SIZE;
let searchCache = new Map();

// DOM 元素
const elements = {
    searchForm: null,
    searchBtn: null,
    loadingSpinner: null,
    resultsSection: null,
    resultsList: null,
    searchStats: null,
    paginationNav: null,
    paginationList: null,
    downloadCsvBtn: null,
    downloadJsonBtn: null,
    totalJobs: null,
    executionTime: null,
    successfulPlatforms: null,
    failedPlatforms: null
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    bindEvents();
    loadSupportedSites();
    console.log('JobSpy 前端已初始化');
});

/**
 * 初始化 DOM 元素
 */
function initializeElements() {
    elements.searchForm = document.getElementById('searchForm');
    elements.searchBtn = document.getElementById('searchBtn');
    elements.loadingSpinner = document.getElementById('loadingSpinner');
    elements.resultsSection = document.getElementById('resultsSection');
    elements.resultsList = document.getElementById('resultsList');
    elements.searchStats = document.getElementById('searchStats');
    elements.paginationNav = document.getElementById('paginationNav');
    elements.paginationList = document.getElementById('paginationList');
    elements.downloadCsvBtn = document.getElementById('downloadCsvBtn');
    elements.downloadJsonBtn = document.getElementById('downloadJsonBtn');
    elements.totalJobs = document.getElementById('totalJobs');
    elements.executionTime = document.getElementById('executionTime');
    elements.successfulPlatforms = document.getElementById('successfulPlatforms');
    elements.failedPlatforms = document.getElementById('failedPlatforms');
}

/**
 * 綁定事件監聽器
 */
function bindEvents() {
    // 搜尋表單提交
    if (elements.searchForm) {
        elements.searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    // 下載按鈕
    if (elements.downloadCsvBtn) {
        elements.downloadCsvBtn.addEventListener('click', () => downloadResults('csv'));
    }
    
    if (elements.downloadJsonBtn) {
        elements.downloadJsonBtn.addEventListener('click', () => downloadResults('json'));
    }
    
    // 分頁點擊
    if (elements.paginationList) {
        elements.paginationList.addEventListener('click', handlePaginationClick);
    }
    
    // 鍵盤快捷鍵
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * 處理搜尋表單提交
 */
async function handleSearchSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(elements.searchForm);
    const searchParams = {
        query: formData.get('query') || document.getElementById('query').value,
        location: formData.get('location') || document.getElementById('location').value,
        results_wanted: parseInt(formData.get('results_wanted') || document.getElementById('results_wanted').value),
        hours_old: formData.get('hours_old') || document.getElementById('hours_old').value,
        selected_sites: formData.get('selected_sites') || document.getElementById('selected_sites').value,
        page: 1,
        per_page: CONFIG.DEFAULT_PAGE_SIZE
    };
    
    // 驗證輸入
    if (!searchParams.query.trim()) {
        showAlert('請輸入搜尋關鍵字', 'warning');
        return;
    }
    
    if (searchParams.results_wanted < 1 || searchParams.results_wanted > CONFIG.MAX_RESULTS_WANTED) {
        showAlert(`搜尋結果數量必須在 1-${CONFIG.MAX_RESULTS_WANTED} 之間`, 'warning');
        return;
    }
    
    // 執行搜尋
    await performSearch(searchParams);
}

/**
 * 執行搜尋
 */
async function performSearch(params) {
    try {
        // 顯示載入狀態
        showLoading(true);
        hideResults();
        
        // 檢查快取
        const cacheKey = generateCacheKey(params);
        const cachedResult = searchCache.get(cacheKey);
        
        if (cachedResult && Date.now() - cachedResult.timestamp < CONFIG.CACHE_DURATION) {
            console.log('使用快取結果');
            displayResults(cachedResult.data);
            return;
        }
        
        // 發送搜尋請求
        const response = await fetch(`${CONFIG.API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '搜尋失敗');
        }
        
        // 快取結果
        searchCache.set(cacheKey, {
            data: result,
            timestamp: Date.now()
        });
        
        // 顯示結果
        displayResults(result);
        
    } catch (error) {
        console.error('搜尋錯誤:', error);
        showAlert(`搜尋失敗: ${error.message}`, 'danger');
        hideResults();
    } finally {
        showLoading(false);
    }
}

/**
 * 顯示搜尋結果
 */
function displayResults(result) {
    currentSearchId = result.search_id;
    currentPage = result.pagination.page;
    currentPerPage = result.pagination.per_page;
    
    // 更新統計資訊
    updateSearchStats(result);
    
    // 顯示結果列表
    displayJobList(result.jobs);
    
    // 顯示分頁
    displayPagination(result.pagination);
    
    // 顯示結果區域
    showResults();
    
    // 滾動到結果區域
    elements.resultsSection.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
}

/**
 * 更新搜尋統計資訊
 */
function updateSearchStats(result) {
    if (elements.totalJobs) {
        elements.totalJobs.textContent = result.total_jobs || 0;
    }
    
    if (elements.executionTime) {
        elements.executionTime.textContent = (result.routing_info?.execution_time || 0).toFixed(2);
    }
    
    if (elements.successfulPlatforms) {
        elements.successfulPlatforms.textContent = result.routing_info?.successful_platforms?.length || 0;
    }
    
    if (elements.failedPlatforms) {
        elements.failedPlatforms.textContent = result.routing_info?.failed_platforms?.length || 0;
    }
    
    if (elements.searchStats) {
        elements.searchStats.style.display = 'block';
    }
}

/**
 * 顯示職位列表
 */
function displayJobList(jobs) {
    if (!elements.resultsList) return;
    
    if (!jobs || jobs.length === 0) {
        elements.resultsList.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">未找到符合條件的職位</h4>
                <p class="text-muted">請嘗試調整搜尋條件或關鍵字</p>
            </div>
        `;
        return;
    }
    
    const jobsHtml = jobs.map(job => createJobCard(job)).join('');
    elements.resultsList.innerHTML = jobsHtml;
    
    // 添加動畫效果
    const jobCards = elements.resultsList.querySelectorAll('.job-card');
    jobCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

/**
 * 創建職位卡片 HTML
 */
function createJobCard(job) {
    const salaryInfo = getSalaryInfo(job);
    const dateInfo = formatDate(job.date_posted);
    const isRemote = job.is_remote ? '<span class="badge bg-success me-2">遠端工作</span>' : '';
    
    return `
        <div class="job-card fade-in-up">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div class="flex-grow-1">
                    <a href="${job.job_url || '#'}" target="_blank" class="job-title">
                        ${escapeHtml(job.title || '無標題')}
                    </a>
                    <div class="job-company">${escapeHtml(job.company || '未知公司')}</div>
                    <div class="job-location">
                        <i class="fas fa-map-marker-alt me-1"></i>
                        ${escapeHtml(job.location || '地點未指定')}
                    </div>
                </div>
                <div class="text-end">
                    <span class="badge bg-primary">${escapeHtml(job.site || '未知網站')}</span>
                </div>
            </div>
            
            <div class="job-description">
                ${escapeHtml(truncateText(job.description || '', 200))}
            </div>
            
            <div class="job-meta">
                ${isRemote}
                ${salaryInfo}
                <span><i class="fas fa-calendar me-1"></i>${dateInfo}</span>
                ${job.job_type ? `<span class="badge bg-secondary">${escapeHtml(job.job_type)}</span>` : ''}
            </div>
            
            <div class="job-actions">
                <a href="${job.job_url || '#'}" target="_blank" class="btn btn-primary btn-sm">
                    <i class="fas fa-external-link-alt me-1"></i>查看職位
                </a>
                ${job.job_url_direct ? `
                    <a href="${job.job_url_direct}" target="_blank" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-link me-1"></i>直接連結
                    </a>
                ` : ''}
                <button class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard('${job.job_url || ''}')">
                    <i class="fas fa-copy me-1"></i>複製連結
                </button>
            </div>
        </div>
    `;
}

/**
 * 顯示分頁
 */
function displayPagination(pagination) {
    if (!elements.paginationNav || !elements.paginationList) return;
    
    if (pagination.total_pages <= 1) {
        elements.paginationNav.style.display = 'none';
        return;
    }
    
    elements.paginationNav.style.display = 'block';
    
    const currentPage = pagination.page;
    const totalPages = pagination.total_pages;
    const maxVisiblePages = 5;
    
    let paginationHtml = '';
    
    // 上一頁按鈕
    if (pagination.has_prev) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${currentPage - 1}">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    } else {
        paginationHtml += `
            <li class="page-item disabled">
                <span class="page-link">
                    <i class="fas fa-chevron-left"></i>
                </span>
            </li>
        `;
    }
    
    // 計算顯示的頁碼範圍
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // 第一頁和省略號
    if (startPage > 1) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="1">1</a>
            </li>
        `;
        if (startPage > 2) {
            paginationHtml += `
                <li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>
            `;
        }
    }
    
    // 頁碼
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHtml += `
                <li class="page-item active">
                    <span class="page-link">${i}</span>
                </li>
            `;
        } else {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
    }
    
    // 最後一頁和省略號
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += `
                <li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>
            `;
        }
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>
            </li>
        `;
    }
    
    // 下一頁按鈕
    if (pagination.has_next) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${currentPage + 1}">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    } else {
        paginationHtml += `
            <li class="page-item disabled">
                <span class="page-link">
                    <i class="fas fa-chevron-right"></i>
                </span>
            </li>
        `;
    }
    
    elements.paginationList.innerHTML = paginationHtml;
}

/**
 * 處理分頁點擊
 */
function handlePaginationClick(event) {
    event.preventDefault();
    
    const pageLink = event.target.closest('.page-link');
    if (!pageLink || pageLink.closest('.disabled')) return;
    
    const page = parseInt(pageLink.dataset.page);
    if (!page || page === currentPage) return;
    
    // 更新搜尋參數並重新搜尋
    const formData = new FormData(elements.searchForm);
    const searchParams = {
        query: formData.get('query') || document.getElementById('query').value,
        location: formData.get('location') || document.getElementById('location').value,
        results_wanted: parseInt(formData.get('results_wanted') || document.getElementById('results_wanted').value),
        hours_old: formData.get('hours_old') || document.getElementById('hours_old').value,
        selected_sites: formData.get('selected_sites') || document.getElementById('selected_sites').value,
        page: page,
        per_page: currentPerPage
    };
    
    performSearch(searchParams);
}

/**
 * 下載搜尋結果
 */
async function downloadResults(format) {
    if (!currentSearchId) {
        showAlert('沒有可下載的搜尋結果', 'warning');
        return;
    }
    
    try {
        const url = `${CONFIG.API_BASE_URL}/download/${currentSearchId}/${format}`;
        window.open(url, '_blank');
    } catch (error) {
        console.error('下載錯誤:', error);
        showAlert(`下載失敗: ${error.message}`, 'danger');
    }
}

/**
 * 載入支援的網站列表
 */
async function loadSupportedSites() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/sites`);
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.sites) {
                updateSitesDropdown(result.sites);
            }
        }
    } catch (error) {
        console.warn('無法載入支援的網站列表:', error);
    }
}

/**
 * 更新網站下拉選單
 */
function updateSitesDropdown(sites) {
    const selectElement = document.getElementById('selected_sites');
    if (!selectElement) return;
    
    // 保留現有的選項，只更新描述
    const options = selectElement.querySelectorAll('option');
    options.forEach(option => {
        const site = sites.find(s => s.value === option.value);
        if (site) {
            option.title = site.description;
        }
    });
}

/**
 * 處理鍵盤快捷鍵
 */
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + Enter 提交搜尋
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        if (elements.searchForm) {
            elements.searchForm.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape 鍵清除結果
    if (event.key === 'Escape') {
        hideResults();
    }
}

/**
 * 顯示載入狀態
 */
function showLoading(show) {
    if (elements.loadingSpinner) {
        elements.loadingSpinner.style.display = show ? 'block' : 'none';
    }
    
    if (elements.searchBtn) {
        elements.searchBtn.disabled = show;
        if (show) {
            elements.searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>搜尋中...';
        } else {
            elements.searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>開始搜尋';
        }
    }
}

/**
 * 顯示結果區域
 */
function showResults() {
    if (elements.resultsSection) {
        elements.resultsSection.style.display = 'block';
        elements.resultsSection.classList.add('fade-in-up');
    }
}

/**
 * 隱藏結果區域
 */
function hideResults() {
    if (elements.resultsSection) {
        elements.resultsSection.style.display = 'none';
        elements.resultsSection.classList.remove('fade-in-up');
    }
    
    if (elements.searchStats) {
        elements.searchStats.style.display = 'none';
    }
    
    if (elements.paginationNav) {
        elements.paginationNav.style.display = 'none';
    }
}

/**
 * 顯示警告訊息
 */
function showAlert(message, type = 'info') {
    // 移除現有的警告
    const existingAlert = document.querySelector('.alert-dismissible');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 創建新的警告
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 插入到搜尋表單上方
    const searchCard = document.querySelector('.search-card');
    if (searchCard) {
        searchCard.insertAdjacentHTML('beforebegin', alertHtml);
        
        // 自動隱藏
        setTimeout(() => {
            const alert = document.querySelector('.alert-dismissible');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
}

/**
 * 複製到剪貼板
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('連結已複製到剪貼板', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

/**
 * 備用複製方法
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showAlert('連結已複製到剪貼板', 'success');
    } catch (err) {
        showAlert('複製失敗，請手動複製', 'warning');
    }
    
    document.body.removeChild(textArea);
}

/**
 * 工具函數
 */

// 生成快取鍵
function generateCacheKey(params) {
    return JSON.stringify({
        query: params.query,
        location: params.location,
        results_wanted: params.results_wanted,
        hours_old: params.hours_old,
        selected_sites: params.selected_sites
    });
}

// 獲取薪資資訊
function getSalaryInfo(job) {
    if (!job.salary_min && !job.salary_max) {
        return '';
    }
    
    const currency = job.salary_currency || '';
    const min = job.salary_min ? formatNumber(job.salary_min) : '';
    const max = job.salary_max ? formatNumber(job.salary_max) : '';
    
    if (min && max) {
        return `<span><i class="fas fa-dollar-sign me-1"></i>${currency}${min} - ${max}</span>`;
    } else if (min) {
        return `<span><i class="fas fa-dollar-sign me-1"></i>${currency}${min}+</span>`;
    } else if (max) {
        return `<span><i class="fas fa-dollar-sign me-1"></i>最高 ${currency}${max}</span>`;
    }
    
    return '';
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '日期未知';
    
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return '1 天前';
        } else if (diffDays < 7) {
            return `${diffDays} 天前`;
        } else if (diffDays < 30) {
            const weeks = Math.floor(diffDays / 7);
            return `${weeks} 週前`;
        } else {
            return date.toLocaleDateString('zh-TW');
        }
    } catch (error) {
        return '日期未知';
    }
}

// 格式化數字
function formatNumber(num) {
    if (typeof num !== 'number') return num;
    return num.toLocaleString('zh-TW');
}

// 截斷文字
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// HTML 轉義
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 導出到全域作用域（用於 HTML 中的 onclick 事件）
window.copyToClipboard = copyToClipboard;
