import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SearchPage } from './pages/SearchPage';
import { ResultsPage } from './pages/ResultsPage';
import './i18n';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="bg-white shadow-lg border-b border-gray-200">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-20">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <h1 className="text-3xl font-bold text-gray-900">
                      <i className="fas fa-search text-blue-600 mr-2"></i>
                      jobseeker
                    </h1>
                    <p className="text-sm text-gray-600">
                      智能職位搜尋平台
                    </p>
                  </div>
                </div>
                
                <nav className="hidden md:flex space-x-8">
                  <a
                    href="/"
                    className="text-gray-900 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    <i className="fas fa-home mr-1"></i>
                    首頁
                  </a>
                  <a
                    href="/results"
                    className="text-gray-500 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    <i className="fas fa-list mr-1"></i>
                    搜尋結果
                  </a>
                </nav>
              </div>
            </div>
          </header>
          
          {/* Main Content */}
          <main>
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/results" element={<ResultsPage />} />
            </Routes>
          </main>
          
          {/* Footer */}
          <footer className="bg-white border-t border-gray-200 mt-16">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="text-center text-gray-600">
                <p>&copy; 2024 jobseeker. All rights reserved.</p>
                <p className="mt-2 text-sm">
                  AI 驅動的智能職位搜尋平台，為您找到最適合的工作機會
                </p>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;