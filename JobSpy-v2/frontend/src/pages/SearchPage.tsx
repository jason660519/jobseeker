import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface SearchQuery {
  jobTitle: string;
  location: string;
  platforms?: string[];
}

/**
 * 搜尋頁面組件 - 使用 Bootstrap 5 樣式
 * 提供職位搜尋功能和統計資訊展示
 */
export const SearchPage: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<SearchQuery>({
    jobTitle: '',
    location: '',
    platforms: []
  });
  
  /**
   * 處理表單提交
   * @param e - 表單事件
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // 構建查詢字符串
      const query = `${formData.jobTitle} ${formData.location}`.trim();
      
      // 發送請求到後端
      const response = await fetch('http://localhost:8000/api/v1/jobs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          platforms: formData.platforms
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Search results:', result);
      
      // TODO: 處理搜尋結果，導航到結果頁面
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="container-fluid">
      {/* 搜尋表單 */}
      <div className="search-section">
        <div className="row justify-content-center">
          <div className="col-lg-10">
            <div className="card shadow-lg border-0 search-card">
              <div className="card-body p-4">
                <h3 className="card-title text-center mb-4">
                  <i className="fas fa-search me-2 text-primary"></i>
                  智能職位搜尋
                </h3>
                
                <form onSubmit={handleSubmit}>
                  <div className="row g-3">
                    <div className="col-md-6">
                      <div className="form-floating">
                        <input
                          type="text"
                          className="form-control"
                          id="jobTitle"
                          placeholder="職位名稱"
                          value={formData.jobTitle}
                          onChange={(e) => setFormData(prev => ({ ...prev, jobTitle: e.target.value }))}
                          required
                        />
                        <label htmlFor="jobTitle">
                          <i className="fas fa-briefcase me-2"></i>
                          職位名稱
                        </label>
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="form-floating">
                        <input
                          type="text"
                          className="form-control"
                          id="location"
                          placeholder="工作地點"
                          value={formData.location}
                          onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                        />
                        <label htmlFor="location">
                          <i className="fas fa-map-marker-alt me-2"></i>
                          工作地點
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center mt-4">
                    <button 
                      type="submit" 
                      className="btn btn-primary btn-lg px-5"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                          搜尋中...
                        </>
                      ) : (
                        <>
                          <i className="fas fa-search me-2"></i>
                          開始搜尋
                        </>
                      )}
                    </button>
                    <div className="mt-3">
                      <small className="text-muted">
                        <i className="fas fa-shield-alt me-1"></i>
                        我們重視您的隱私，搜尋過程完全匿名
                      </small>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* 載入中動畫 */}
      {isLoading && (
        <div className="loading-container" style={{display: 'block'}}>
          <div className="loading-animation">
            <div className="spinner"></div>
            <div className="loading-text">
              <h4>正在搜尋職位...</h4>
              <p>我們正在為您搜尋最適合的工作機會</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};