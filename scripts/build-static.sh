#!/bin/bash

# JobSpy 靜態前端構建腳本
# 用於 GitHub Actions 自動化部署

set -e

echo "🚀 開始構建 JobSpy 靜態前端..."

# 設置變數
DIST_DIR="dist"
STATIC_DIR="static_frontend"
TEMPLATES_DIR="web_app/templates"

# 創建分發目錄
echo "📁 創建分發目錄..."
rm -rf $DIST_DIR
mkdir -p $DIST_DIR

# 複製靜態文件
echo "📋 複製靜態文件..."
cp -r $STATIC_DIR/* $DIST_DIR/

# 複製必要的模板文件（如果需要）
if [ -d "$TEMPLATES_DIR" ]; then
    echo "📄 複製模板文件..."
    mkdir -p $DIST_DIR/templates
    cp $TEMPLATES_DIR/*.html $DIST_DIR/templates/ 2>/dev/null || true
fi

# 複製文檔
echo "📚 複製文檔..."
if [ -d "docs" ]; then
    cp -r docs $DIST_DIR/
fi

# 創建 README
echo "📝 創建 README..."
cat > $DIST_DIR/README.md << 'EOF'
# JobSpy 靜態前端

這是 JobSpy 的靜態前端版本，部署在 GitHub Pages 上。

## 功能特色

- 🎯 智能職位搜尋
- 🌐 多平台整合
- 📱 響應式設計
- ⚡ 快速載入
- 🔍 即時搜尋

## 使用方式

1. 在搜尋框中輸入職位關鍵字
2. 選擇地點和搜尋條件
3. 點擊「開始搜尋」
4. 瀏覽結果並下載

## API 配置

前端需要連接到後端 API 服務。請確保 `app.js` 中的 `API_BASE_URL` 配置正確。

## 部署

此靜態前端通過 GitHub Actions 自動部署到 GitHub Pages。

## 技術棧

- HTML5
- CSS3 (Bootstrap 5)
- JavaScript (ES6+)
- Font Awesome 圖標

## 授權

開源專案，歡迎貢獻。
EOF

# 創建 .nojekyll 文件（避免 Jekyll 處理）
echo "🔧 創建 .nojekyll 文件..."
touch $DIST_DIR/.nojekyll

# 創建 CNAME 文件（如果配置了自定義域名）
if [ -n "$CUSTOM_DOMAIN" ]; then
    echo "🌐 設置自定義域名: $CUSTOM_DOMAIN"
    echo "$CUSTOM_DOMAIN" > $DIST_DIR/CNAME
fi

# 優化文件
echo "⚡ 優化文件..."

# 壓縮 CSS（如果沒有壓縮）
if command -v uglifycss &> /dev/null; then
    echo "🗜️ 壓縮 CSS..."
    uglifycss $DIST_DIR/styles.css > $DIST_DIR/styles.min.css
    mv $DIST_DIR/styles.min.css $DIST_DIR/styles.css
fi

# 壓縮 JavaScript（如果沒有壓縮）
if command -v uglifyjs &> /dev/null; then
    echo "🗜️ 壓縮 JavaScript..."
    uglifyjs $DIST_DIR/app.js -o $DIST_DIR/app.min.js
    mv $DIST_DIR/app.min.js $DIST_DIR/app.js
fi

# 生成文件清單
echo "📋 生成文件清單..."
find $DIST_DIR -type f -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.json" | sort > $DIST_DIR/files.txt

# 顯示構建結果
echo "✅ 構建完成！"
echo "📊 文件統計："
echo "  - HTML 文件: $(find $DIST_DIR -name "*.html" | wc -l)"
echo "  - CSS 文件: $(find $DIST_DIR -name "*.css" | wc -l)"
echo "  - JS 文件: $(find $DIST_DIR -name "*.js" | wc -l)"
echo "  - 總文件數: $(find $DIST_DIR -type f | wc -l)"
echo "  - 總大小: $(du -sh $DIST_DIR | cut -f1)"

echo "🎉 靜態前端構建完成，準備部署到 GitHub Pages！"
