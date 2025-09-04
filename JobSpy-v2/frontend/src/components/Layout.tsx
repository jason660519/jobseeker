import React from 'react';
import { Outlet } from 'react-router-dom';

/**
 * 基礎佈局組件 - 使用 Bootstrap 5 樣式
 * 包含完整的三欄式佈局：header、左側邊欄、主內容區、右側邊欄和 footer
 */
export const Layout: React.FC = () => {
  return (
    <div className="min-vh-100">
      {/* 頂部導航欄 */}
      <nav className="navbar navbar-expand-lg navbar-dark fixed-top" style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div className="container-fluid">
          <a className="navbar-brand" href="/">
            <i className="fas fa-briefcase me-2"></i>
            jobseeker
          </a>
          
          <button 
            className="navbar-toggler" 
            type="button" 
            data-bs-toggle="collapse" 
            data-bs-target="#topNavbar"
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          
          {/* 搜尋欄 */}
          <div className="nav-search mx-auto my-2 my-lg-0">
            <form className="d-flex" role="search">
              <div className="input-group">
                <input
                  type="search"
                  className="form-control"
                  placeholder="輸入想找的工作、地點或需求..."
                />
                <button className="btn btn-outline-light" type="button">
                  <i className="fas fa-microphone"></i>
                </button>
                <button className="btn btn-light" type="submit">
                  <i className="fas fa-search me-1"></i>搜尋
                </button>
              </div>
            </form>
          </div>
          
          <div className="collapse navbar-collapse" id="topNavbar">
            <ul className="navbar-nav ms-auto align-items-lg-center">
              <li className="nav-item">
                <a className="nav-link text-white" href="#">
                  <i className="fas fa-book me-1"></i> Doc
                </a>
              </li>
              <li className="nav-item">
                <a className="nav-link text-white" href="#">
                  <i className="fas fa-download me-1"></i> Downloads
                </a>
              </li>
              <li className="nav-item">
                <a className="nav-link text-white" href="#">
                  <i className="fas fa-heart me-1"></i> Donate
                </a>
              </li>
              <li className="nav-item">
                <a className="nav-link text-white" href="#">
                  <i className="fas fa-envelope me-1"></i> 聯絡我們
                </a>
              </li>
              <li className="nav-item">
                <button className="btn btn-outline-light me-2" title="切換右側邊欄">
                  <i className="fas fa-columns"></i>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      {/* 主要佈局容器 */}
      <div className="main-container" style={{ paddingTop: '76px' }}>
        <div className="row g-0">
          {/* 左側邊欄 */}
          <div className="col-md-3 col-lg-2">
            <div className="sidebar" style={{ height: 'calc(100vh - 76px)', overflowY: 'auto' }}>
              <div className="sidebar-content p-3">
                {/* 用戶資訊卡片 */}
                <div className="user-card mb-4">
                  <div className="d-flex align-items-center">
                    <div className="user-avatar me-3">
                      <i className="fas fa-user-circle fa-2x text-primary"></i>
                    </div>
                    <div className="user-info">
                      <h6 className="user-name mb-0">歡迎使用 JobSpy</h6>
                      <small className="user-status text-success">
                        <i className="fas fa-circle"></i> 系統正常
                      </small>
                    </div>
                  </div>
                </div>

                {/* 快速統計 */}
                <div className="stats-widget mb-4">
                  <h6 className="stats-title">
                    <i className="fas fa-chart-line me-2"></i>今日統計
                  </h6>
                  <div className="row">
                    <div className="col-6">
                      <div className="text-center">
                        <div className="h5 mb-0 text-primary">0</div>
                        <small className="text-muted">搜尋次數</small>
                      </div>
                    </div>
                    <div className="col-6">
                      <div className="text-center">
                        <div className="h5 mb-0 text-success">0</div>
                        <small className="text-muted">找到職位</small>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 主要功能 */}
                <div className="mb-4">
                  <h6 className="section-title">
                    <i className="fas fa-rocket me-2"></i>主要功能
                  </h6>
                  <ul className="list-unstyled">
                    <li className="mb-2">
                      <a href="/" className="d-flex align-items-center text-decoration-none">
                        <div className="nav-icon me-3">
                          <i className="fas fa-home"></i>
                        </div>
                        <div className="nav-content">
                          <span className="nav-text">首頁搜尋</span>
                          <br />
                          <small className="text-muted">智能職位搜尋</small>
                        </div>
                      </a>
                    </li>
                    <li className="mb-2">
                      <a href="/results" className="d-flex align-items-center text-decoration-none">
                        <div className="nav-icon me-3">
                          <i className="fas fa-chart-bar"></i>
                        </div>
                        <div className="nav-content">
                          <span className="nav-text">測試結果</span>
                          <br />
                          <small className="text-muted">查看搜尋結果</small>
                        </div>
                      </a>
                    </li>
                  </ul>
                </div>

                {/* 工具與資源 */}
                <div className="mb-4">
                  <h6 className="section-title">
                    <i className="fas fa-tools me-2"></i>工具與資源
                  </h6>
                  <ul className="list-unstyled">
                    <li className="mb-2">
                      <a href="#" className="d-flex align-items-center text-decoration-none">
                        <div className="nav-icon me-3">
                          <i className="fas fa-download"></i>
                        </div>
                        <div className="nav-content">
                          <span className="nav-text">下載範例CSV</span>
                          <br />
                          <small className="text-muted">資料格式範例</small>
                        </div>
                      </a>
                    </li>
                    <li className="mb-2">
                      <a href="https://github.com/jason660519/jobseeker" target="_blank" className="d-flex align-items-center text-decoration-none">
                        <div className="nav-icon me-3">
                          <i className="fab fa-github"></i>
                        </div>
                        <div className="nav-content">
                          <span className="nav-text">GitHub 專案</span>
                          <br />
                          <small className="text-muted">開源代碼</small>
                        </div>
                      </a>
                    </li>
                  </ul>
                </div>

                {/* 系統狀態 */}
                <div className="system-status">
                  <div className="d-flex align-items-center mb-2">
                    <div className="bg-success rounded-circle me-2" style={{ width: '8px', height: '8px' }}></div>
                    <span className="small">所有平台正常</span>
                  </div>
                  <div className="d-flex align-items-center">
                    <div className="bg-success rounded-circle me-2" style={{ width: '8px', height: '8px' }}></div>
                    <span className="small">AI 路由運行中</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 主內容區域 */}
          <div className="col-md-6">
            <main className="main-content">
              <Outlet />
            </main>
          </div>

          {/* 右側邊欄 */}
          <div className="col-md-3">
            <div className="right-sidebar" style={{ height: 'calc(100vh - 76px)', overflowY: 'auto' }}>
              <div className="right-sidebar-content p-3">
                {/* 搜尋歷史 */}
                <div className="search-history-widget mb-4">
                  <h6 className="stats-title">
                    <i className="fas fa-history me-2"></i>搜尋歷史
                  </h6>
                  <div className="history-item mb-2 p-2 border rounded">
                    <div className="d-flex align-items-center">
                      <i className="fas fa-search me-2 text-muted"></i>
                      <div>
                        <div className="small">軟體工程師 台北</div>
                        <div className="text-muted" style={{ fontSize: '0.75rem' }}>2小時前</div>
                      </div>
                    </div>
                  </div>
                  <div className="history-item mb-2 p-2 border rounded">
                    <div className="d-flex align-items-center">
                      <i className="fas fa-search me-2 text-muted"></i>
                      <div>
                        <div className="small">前端開發 遠端</div>
                        <div className="text-muted" style={{ fontSize: '0.75rem' }}>1天前</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 熱門搜尋 */}
                <div className="trending-widget mb-4">
                  <h6 className="stats-title">
                    <i className="fas fa-fire me-2"></i>熱門搜尋
                  </h6>
                  <div className="trending-item mb-2 p-2 border rounded">
                    <div className="d-flex justify-content-between align-items-center">
                      <div className="d-flex align-items-center">
                        <span className="badge bg-primary me-2">1</span>
                        <span className="small">軟體工程師</span>
                      </div>
                      <span className="text-muted small">1.2k</span>
                    </div>
                  </div>
                  <div className="trending-item mb-2 p-2 border rounded">
                    <div className="d-flex justify-content-between align-items-center">
                      <div className="d-flex align-items-center">
                        <span className="badge bg-primary me-2">2</span>
                        <span className="small">前端開發</span>
                      </div>
                      <span className="text-muted small">856</span>
                    </div>
                  </div>
                  <div className="trending-item mb-2 p-2 border rounded">
                    <div className="d-flex justify-content-between align-items-center">
                      <div className="d-flex align-items-center">
                        <span className="badge bg-primary me-2">3</span>
                        <span className="small">產品經理</span>
                      </div>
                      <span className="text-muted small">743</span>
                    </div>
                  </div>
                </div>

                {/* 即時通知 */}
                <div className="notifications-widget">
                  <h6 className="stats-title">
                    <i className="fas fa-bell me-2"></i>即時通知
                  </h6>
                  <div className="alert alert-info alert-sm">
                    <i className="fas fa-info-circle me-2"></i>
                    <small>系統運行正常</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 頁腳 */}
      <footer className="bg-dark text-light py-4">
        <div className="container">
          <div className="row">
            <div className="col-md-6">
              <h5>
                <i className="fas fa-briefcase me-2"></i>
                jobseeker
              </h5>
              <p className="mb-0">智能職位搜尋平台</p>
            </div>
            <div className="col-md-6 text-md-end">
              <p className="mb-0">
                <i className="fas fa-heart text-danger me-1"></i>
                Made with AI Technology
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};