import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface SearchQuery {
  jobTitle: string;
  location: string;
  platforms?: string[];
}

export const SearchPage: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<SearchQuery>({
    jobTitle: '',
    location: '',
    platforms: []
  });
  
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
      
      // TODO: 處理搜尋結果
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* 歡迎區塊 */}
        <div className="text-center mb-12">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-5xl font-bold text-gray-900 mb-4">
                <i className="fas fa-search text-blue-600 mr-3"></i>
                找到您的理想工作
              </h1>
              <p className="text-xl text-gray-600 mb-6">
                使用 AI 驅動的智能搜尋引擎，從多個求職平台為您找到最適合的職位機會
              </p>
              <div className="flex flex-wrap justify-center gap-2 mb-6">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  <i className="fas fa-robot mr-1"></i>AI 智能路由
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  <i className="fas fa-globe mr-1"></i>9+ 平台支援
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                  <i className="fas fa-bolt mr-1"></i>即時搜尋
                </span>
              </div>
            </div>

            {/* 統計數據 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 text-center">
                <div className="text-3xl text-blue-600 mb-2">
                  <i className="fas fa-globe"></i>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">9</h3>
                <p className="text-gray-600">支援平台</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 text-center">
                <div className="text-3xl text-green-600 mb-2">
                  <i className="fas fa-map-marker-alt"></i>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">50+</h3>
                <p className="text-gray-600">國家地區</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 text-center">
                <div className="text-3xl text-purple-600 mb-2">
                  <i className="fas fa-robot"></i>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">AI</h3>
                <p className="text-gray-600">智能路由</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 text-center">
                <div className="text-3xl text-orange-600 mb-2">
                  <i className="fas fa-clock"></i>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">24/7</h3>
                <p className="text-gray-600">即時搜尋</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* 搜尋表單 */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg border border-gray-200">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 rounded-t-lg">
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                <i className="fas fa-search mr-2 text-blue-600"></i>
                智能職位搜尋
              </h4>
              <p className="text-gray-600">
                告訴我們您想要什麼工作，AI 會為您找到最適合的機會
              </p>
            </div>
            <div className="p-6">
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  {/* 職位名稱 */}
                  <div>
                    <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700 mb-2">
                      <i className="fas fa-briefcase mr-2"></i>職位名稱
                    </label>
                    <input
                      type="text"
                      id="jobTitle"
                      value={formData.jobTitle}
                      onChange={(e) => setFormData(prev => ({ ...prev, jobTitle: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                      placeholder="例如：軟體工程師、產品經理"
                    />
                  </div>
                  
                  {/* 工作地點 */}
                  <div>
                    <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                      <i className="fas fa-map-marker-alt mr-2"></i>工作地點
                    </label>
                    <input
                      type="text"
                      id="location"
                      value={formData.location}
                      onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                      placeholder="例如：台北、新加坡、遠端"
                    />
                  </div>
                </div>
                
                {/* 平台選擇 */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <i className="fas fa-globe mr-2"></i>搜尋平台
                  </label>
                  <button
                    type="button"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg text-left hover:bg-gray-50 transition-colors"
                  >
                    <i className="fas fa-cog mr-2"></i>選擇平台
                    <span className="float-right bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">全部</span>
                  </button>
                </div>
                
                {/* 搜尋按鈕 */}
                <div className="text-center">
                  <button
                    type="submit"
                    disabled={isLoading || (!formData.jobTitle && !formData.location)}
                    className="inline-flex items-center px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        正在搜尋...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-search mr-2"></i>
                        開始搜尋職位
                      </>
                    )}
                  </button>
                  <div className="mt-3">
                    <small className="text-gray-500">
                      <i className="fas fa-shield-alt mr-1"></i>
                      搜尋過程安全且隱私保護
                    </small>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
        
        {/* 載入中動畫 */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-md mx-4 text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">正在搜尋職位...</h4>
              <p className="text-gray-600">我們正在為您搜尋最適合的工作機會</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};