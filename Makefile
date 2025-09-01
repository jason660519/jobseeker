# JobSpy 專案 Makefile
# 提供便捷的開發和測試命令

.PHONY: help install test test-unit test-integration test-performance test-network test-all test-quick test-smoke
.PHONY: coverage lint format check clean build docs serve-docs
.PHONY: setup-dev setup-ci docker-build docker-test

# 預設目標
help:
	@echo "JobSpy 專案可用命令:"
	@echo ""
	@echo "安裝和設置:"
	@echo "  make install        - 安裝專案依賴"
	@echo "  make install-dev    - 安裝開發依賴"
	@echo "  make install-test   - 安裝測試依賴"
	@echo "  make setup-dev      - 設置開發環境"
	@echo "  make setup-ci       - 設置 CI 環境"
	@echo ""
	@echo "測試:"
	@echo "  make test           - 執行所有測試"
	@echo "  make test-unit      - 執行單元測試"
	@echo "  make test-integration - 執行整合測試"
	@echo "  make test-performance - 執行效能測試"
	@echo "  make test-network   - 執行網路測試"
	@echo "  make test-quick     - 執行快速測試"
	@echo "  make test-smoke     - 執行冒煙測試"
	@echo "  make coverage       - 執行測試並生成覆蓋率報告"
	@echo ""
	@echo "程式碼品質:"
	@echo "  make lint           - 執行程式碼檢查"
	@echo "  make format         - 格式化程式碼"
	@echo "  make check          - 執行所有品質檢查"
	@echo ""
	@echo "建置和部署:"
	@echo "  make build          - 建置專案"
	@echo "  make clean          - 清理建置檔案"
	@echo "  make docs           - 生成文檔"
	@echo "  make serve-docs     - 啟動文檔伺服器"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - 建置 Docker 映像"
	@echo "  make docker-test    - 在 Docker 中執行測試"
	@echo ""

# ==================== 安裝和設置 ====================

install:
	@echo "📦 安裝專案依賴..."
	pip install -r requirements.txt

install-dev:
	@echo "📦 安裝開發依賴..."
	pip install -r requirements-dev.txt || pip install black isort flake8 mypy pre-commit

install-test:
	@echo "📦 安裝測試依賴..."
	pip install -r requirements-test.txt

setup-dev: install install-dev install-test
	@echo "🔧 設置開發環境..."
	pre-commit install || echo "pre-commit 未安裝，跳過 hook 設置"
	@echo "✅ 開發環境設置完成"

setup-ci: install install-test
	@echo "🔧 設置 CI 環境..."
	@echo "✅ CI 環境設置完成"

# ==================== 測試 ====================

test:
	@echo "🧪 執行所有測試..."
	python test_runner.py --all

test-unit:
	@echo "🧪 執行單元測試..."
	python test_runner.py --unit

test-integration:
	@echo "🧪 執行整合測試..."
	python test_runner.py --integration

test-performance:
	@echo "🧪 執行效能測試..."
	python test_runner.py --performance

test-network:
	@echo "🧪 執行網路測試..."
	python test_runner.py --network

test-quick:
	@echo "🧪 執行快速測試..."
	python test_runner.py --quick

test-smoke:
	@echo "🧪 執行冒煙測試..."
	python test_runner.py --smoke

coverage:
	@echo "📊 執行測試並生成覆蓋率報告..."
	python test_runner.py --all --coverage --report test-report.md

# ==================== 程式碼品質 ====================

lint:
	@echo "🔍 執行程式碼檢查..."
	python test_runner.py --check

format:
	@echo "🎨 格式化程式碼..."
	black . || echo "Black 未安裝，跳過格式化"
	isort . || echo "isort 未安裝，跳過導入排序"

check: lint
	@echo "✅ 程式碼品質檢查完成"

# ==================== 建置和清理 ====================

build:
	@echo "🏗️ 建置專案..."
	python -m build || python setup.py sdist bdist_wheel

clean:
	@echo "🧹 清理建置檔案..."
	python test_runner.py --cleanup
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ test-results.xml coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true

# ==================== 文檔 ====================

docs:
	@echo "📚 生成文檔..."
	sphinx-build -b html docs/ docs/_build/html/ || echo "Sphinx 未安裝，跳過文檔生成"

serve-docs:
	@echo "🌐 啟動文檔伺服器..."
	python -m http.server 8000 -d docs/_build/html/ || python -m SimpleHTTPServer 8000

# ==================== Docker ====================

docker-build:
	@echo "🐳 建置 Docker 映像..."
	docker build -t jobspy:latest .

docker-test:
	@echo "🐳 在 Docker 中執行測試..."
	docker run --rm -v $(PWD):/app -w /app jobspy:latest python test_runner.py --all

# ==================== 開發工具 ====================

# 啟動開發伺服器（如果有的話）
dev:
	@echo "🚀 啟動開發環境..."
	@echo "JobSpy 是一個爬蟲庫，沒有開發伺服器"
	@echo "請使用 'make test' 來測試功能"

# 執行範例
example:
	@echo "📝 執行範例程式..."
	python complete_async_integration_example.py

# 效能基準測試
benchmark:
	@echo "⚡ 執行效能基準測試..."
	python test_runner.py --performance --report benchmark-report.md

# 安全檢查
security:
	@echo "🔒 執行安全檢查..."
	bandit -r jobspy/ || echo "Bandit 未安裝，跳過安全檢查"
	safety check || echo "Safety 未安裝，跳過依賴安全檢查"

# 類型檢查
type-check:
	@echo "🔍 執行類型檢查..."
	mypy jobspy/ || echo "MyPy 未安裝，跳過類型檢查"

# 完整檢查（包含所有品質檢查）
full-check: format lint type-check security
	@echo "✅ 完整品質檢查完成"

# 發布前檢查
pre-release: clean full-check test coverage build
	@echo "🚀 發布前檢查完成"

# 快速開發循環
quick: format test-quick
	@echo "⚡ 快速開發循環完成"

# 完整開發循環
full: clean format lint test coverage
	@echo "🔄 完整開發循環完成"

# ==================== 資料庫和快取 ====================

# 清理快取
clean-cache:
	@echo "🧹 清理快取..."
	rm -rf .jobspy_cache/ || true
	find . -name "*.cache" -delete 2>/dev/null || true

# 重置測試資料
reset-test-data:
	@echo "🔄 重置測試資料..."
	rm -rf tests/fixtures/temp/ || true
	mkdir -p tests/fixtures/temp

# ==================== 監控和分析 ====================

# 程式碼複雜度分析
complexity:
	@echo "📊 分析程式碼複雜度..."
	radon cc jobspy/ || echo "Radon 未安裝，跳過複雜度分析"

# 程式碼重複檢查
duplication:
	@echo "🔍 檢查程式碼重複..."
	pylint --disable=all --enable=duplicate-code jobspy/ || echo "Pylint 未安裝，跳過重複檢查"

# 依賴分析
deps:
	@echo "📦 分析依賴..."
	pipdeptree || pip list

# 程式碼統計
stats:
	@echo "📊 程式碼統計..."
	cloc jobspy/ tests/ || find jobspy/ tests/ -name "*.py" | wc -l

# ==================== 特殊目標 ====================

# 初始化新的開發環境
init: clean setup-dev
	@echo "🎉 開發環境初始化完成"
	@echo "現在可以開始開發了！"
	@echo "執行 'make test' 來確保一切正常"

# 每日檢查
daily: clean format lint test-quick
	@echo "📅 每日檢查完成"

# 週期性完整檢查
weekly: clean full-check test coverage
	@echo "📅 週期性檢查完成"

# 發布檢查
release-check: pre-release
	@echo "🚀 發布檢查完成，可以發布了！"

# ==================== Windows 特定命令 ====================

# Windows 清理命令
clean-windows:
	@echo "🧹 Windows 清理..."
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist *.egg-info rmdir /s /q *.egg-info
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist htmlcov rmdir /s /q htmlcov
	if exist __pycache__ rmdir /s /q __pycache__
	del /s /q *.pyc 2>nul || echo.
	del /s /q *.pyo 2>nul || echo.

# Windows 測試命令
test-windows:
	@echo "🧪 Windows 測試..."
	python test_runner.py --all

# ==================== 說明 ====================

# 顯示專案資訊
info:
	@echo "JobSpy 專案資訊:"
	@echo "================="
	@echo "專案名稱: JobSpy"
	@echo "描述: 職位資訊爬蟲工具"
	@echo "Python 版本: >= 3.8"
	@echo "主要功能: 多網站職位爬取、非同步處理、智能快取"
	@echo ""
	@echo "目錄結構:"
	@echo "  jobspy/          - 主要程式碼"
	@echo "  tests/           - 測試程式碼"
	@echo "  docs/            - 文檔"
	@echo "  examples/        - 範例程式碼"
	@echo ""
	@echo "開始使用:"
	@echo "  1. make setup-dev    # 設置開發環境"
	@echo "  2. make test         # 執行測試"
	@echo "  3. make example      # 執行範例"

# 顯示測試資訊
test-info:
	@echo "測試資訊:"
	@echo "========"
	@echo "測試框架: pytest"
	@echo "測試目錄: tests/"
	@echo "測試類型:"
	@echo "  - 單元測試 (tests/unit/)"
	@echo "  - 整合測試 (tests/integration/)"
	@echo "  - 效能測試 (tests/performance/)"
	@echo "  - 網路測試 (標記為 requires_network)"
	@echo ""
	@echo "測試執行:"
	@echo "  make test-quick      # 快速測試"
	@echo "  make test-unit       # 單元測試"
	@echo "  make test-all        # 所有測試"
	@echo "  make coverage        # 覆蓋率報告"