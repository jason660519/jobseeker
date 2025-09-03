// 1111 人力銀行（tw1111）Stagehand 隨機用戶流程測試（可選）
// 使用方式：
// 1) 安裝依賴：
//    npm i -D @browserbasehq/stagehand playwright
//    npx playwright install chromium
// 2) 執行：
//    node tests/integration/stagehand_tw1111_random_user.mjs
// 3) 參數：
//    將環境變數 PW_HEADLESS=0 可開啟有頭模式
//    若設定 OPENAI_API_KEY / BROWSERBASE_API_KEY / BROWSERBASE_PROJECT_ID，
//    Stagehand 會自動啟用對應能力；否則以本地瀏覽器 + 純 Playwright 方法執行

import process from 'node:process';

async function main() {
  let Stagehand;
  try {
    ({ Stagehand } = await import('@browserbasehq/stagehand'));
  } catch (e) {
    console.log('[stagehand] Package not installed. Skip test. Install with:');
    console.log('  npm i -D @browserbasehq/stagehand playwright');
    process.exit(0);
  }

  const headless = (process.env.PW_HEADLESS ?? '1') !== '0';

  // 隨機 UA 與視窗大小
  const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
  ];
  const userAgent = userAgents[Math.floor(Math.random() * userAgents.length)];

  // 隨機搜尋 URL
  const keywords = ['python', '工程師', '資料', '行銷', '測試', '前端', '後端'];
  const ks = keywords[Math.floor(Math.random() * keywords.length)];
  const pageNum = Math.floor(Math.random() * 2) + 1; // 1~2
  const col = Math.random() > 0.5 ? 'ab' : 'da';
  const sort = Math.random() > 0.5 ? 'desc' : 'asc';
  const url = `https://www.1111.com.tw/search/job?page=${pageNum}&col=${col}&sort=${sort}&ks=${encodeURIComponent(ks)}`;

  const localMode = !process.env.BROWSERBASE_API_KEY || !process.env.BROWSERBASE_PROJECT_ID;

  const stagehand = new Stagehand({
    verbose: 1,
    env: localMode ? 'LOCAL' : 'BROWSERBASE',
    // 僅使用本地瀏覽器時，不需要 LLM 金鑰；避免使用 act()/agent() 即可
    localBrowserLaunchOptions: {
      headless,
      viewport: { width: 1280, height: 900 },
      userAgent,
    },
    browserbaseSessionCreateParams: localMode ? undefined : {
      projectId: process.env.BROWSERBASE_PROJECT_ID,
      browserSettings: {
        blockAds: true,
        viewport: { width: 1280, height: 900 },
      },
    },
  });

  await stagehand.init();
  const page = stagehand.page;

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    // 滾動以觸發動態載入
    for (let i = 0; i < Math.floor(Math.random() * 3) + 1; i++) {
      await page.evaluate(() => window.scrollBy(0, window.document.body.scrollHeight * 0.6));
      await page.waitForTimeout(500 + Math.floor(Math.random() * 700));
    }

    const html = await page.content();
    if (/error-page|error-card/i.test(html)) {
      console.log('[stagehand] Detected potential anti-bot page, exiting gracefully.');
      return;
    }

    const jobLinks = page.locator('a[href^="/job/"]');
    const count = await jobLinks.count();
    if (count === 0) {
      console.log('[stagehand] No job links found; possibly UI variant.');
      return;
    }

    const idx = Math.min(Math.floor(Math.random() * count), 5);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      jobLinks.nth(idx).click({ force: true }),
    ]);

    const title = await page.title();
    const bodyText = (await page.innerText('body')).slice(0, 4000);
    if (!/1111|工作內容|職務/.test(title + ' ' + bodyText)) {
      throw new Error('Job detail page did not look valid.');
    }

    console.log('[stagehand] OK: Navigated to a valid job detail page.');
  } finally {
    await stagehand.close();
  }
}

main().catch((err) => {
  console.error('[stagehand] Error:', err?.message || err);
  process.exit(1);
});

