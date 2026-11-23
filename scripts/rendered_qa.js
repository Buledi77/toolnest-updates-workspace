const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:8765';
const OUTPUT_DIR = path.join(__dirname, '..', 'reports', 'phase3', 'screenshots');

const pages = [
  { path: '/', name: 'homepage' },
  { path: '/tools/index.html', name: 'tools_directory' },
  { path: '/category/developer-tools.html', name: 'developer_tools_category' },
  { path: '/tools/cursor.html', name: 'cursor' },
  { path: '/tools/github-copilot.html', name: 'github_copilot' },
  { path: '/tools/lovable.html', name: 'lovable' },
  { path: '/tools/bolt.html', name: 'bolt' },
  { path: '/tools/heygen.html', name: 'heygen' },
  { path: '/tools/ideogram.html', name: 'ideogram' },
  { path: '/compare/cursor-vs-github-copilot.html', name: 'cursor_vs_copilot' },
  { path: '/compare/lovable-vs-bolt.html', name: 'lovable_vs_bolt' },
  { path: '/compare/heygen-vs-synthesia.html', name: 'heygen_vs_synthesia' },
  { path: '/compare/ideogram-vs-midjourney.html', name: 'ideogram_vs_midjourney' },
  { path: '/tools/decision-engine.html', name: 'decision_engine_beta' },
  { path: '/tools/stack-analyzer.html', name: 'stack_analyzer_beta' },
  { path: '/tools/mozpro.html', name: 'mozpro' },
  { path: '/tools/semrush.html', name: 'semrush' },
  { path: '/tools/ahrefs.html', name: 'ahrefs' },
  { path: '/tools/surferseo.html', name: 'surferseo' },
  { path: '/tools/browseai.html', name: 'browseai' },
  { path: '/tools/callrail.html', name: 'callrail' },
  { path: '/tools/campaignmonitor.html', name: 'campaignmonitor' },
  { path: '/tools/keap.html', name: 'keap' },
  { path: '/tools/overlap-checker.html', name: 'overlap_checker' },
  { path: '/compare/mozpro-vs-semrush.html', name: 'mozpro_vs_semrush' },
  { path: '/compare/claude-vs-gemini.html', name: 'claude_vs_gemini' },
  { path: '/tools/screamingfrog.html', name: 'screamingfrog' },
  { path: '/tools/systeme.html', name: 'systeme' },
  { path: '/best/best-sales-tools.html', name: 'best_sales_tools' },
  { path: '/compare/monday-vs-notion.html', name: 'monday_vs_notion' },
];

const viewports = [
  { name: 'desktop', width: 1280, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 375, height: 667 },
  { name: 'mobile-small', width: 320, height: 568 },
];

async function checkPage(page, url, viewportName) {
  const results = {
    url,
    viewport: viewportName,
    status: 'ok',
    errors: [],
    warnings: [],
  };

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 15000 });

    // Check title
    const title = await page.title();
    if (!title || title.length < 5) {
      results.warnings.push('Title missing or too short');
    }

    // Check for blank content
    const bodyText = await page.evaluate(() => document.body.innerText.length);
    if (bodyText < 100) {
      results.warnings.push(`Body text very short: ${bodyText} chars`);
    }

    // Check for JS errors (already captured in console)
    // Check for horizontal overflow
    const overflow = await page.evaluate(() => {
      const body = document.body;
      return body.scrollWidth > body.clientWidth + 5;
    });
    if (overflow) {
      results.warnings.push('Horizontal overflow detected');
    }

    // Check navigation exists
    const navExists = await page.evaluate(() => {
      return !!document.querySelector('nav, [role="navigation"], .nav, header a');
    });
    if (!navExists) {
      results.warnings.push('No navigation element found');
    }

    // Check links
    const linkCount = await page.evaluate(() => document.querySelectorAll('a[href]').length);
    results.linkCount = linkCount;

    // Check for logo
    const logoExists = await page.evaluate(() => {
      const logos = document.querySelectorAll('img[alt*="logo"], img[alt*="Logo"], img[src*="logo"]');
      return logos.length > 0;
    });
    results.hasLogo = logoExists;

    // Check for affiliate disclosure (on tool pages)
    if (url.includes('/tools/') && !url.includes('index.html')) {
      const disclosure = await page.evaluate(() => {
        const text = document.body.innerText.toLowerCase();
        return text.includes('affiliate') || text.includes('disclosure') || text.includes('commission');
      });
      results.hasAffiliateDisclosure = disclosure;
      if (!disclosure) {
        results.warnings.push('No affiliate disclosure found on tool page');
      }
    }

    // Screenshot
    const safeName = url.replace(/[^a-zA-Z0-9]/g, '_');
    const screenshotPath = path.join(OUTPUT_DIR, `${viewportName}_${safeName}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    results.screenshot = screenshotPath;

  } catch (err) {
    results.status = 'error';
    results.errors.push(err.message);
  }

  return results;
}

(async () => {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const allResults = [];
  let totalErrors = 0;
  let totalWarnings = 0;

  for (const vp of viewports) {
    const page = await browser.newPage();
    await page.setViewport({ width: vp.width, height: vp.height });

    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    for (const pg of pages) {
      const url = BASE_URL + pg.path;
      consoleErrors.length = 0; // reset per page
      const result = await checkPage(page, url, vp.name);
      result.jsErrors = [...consoleErrors];
      if (consoleErrors.length > 0) {
        result.warnings.push(`${consoleErrors.length} JS console errors`);
      }
      allResults.push(result);
      totalErrors += result.errors.length;
      totalWarnings += result.warnings.length;
      console.log(`${vp.name} ${pg.name}: ${result.status} (${result.warnings.length} warnings)`);
    }

    await page.close();
  }

  await browser.close();

  // Write report
  const report = {
    timestamp: new Date().toISOString(),
    base_url: BASE_URL,
    total_pages: pages.length * viewports.length,
    total_errors: totalErrors,
    total_warnings: totalWarnings,
    results: allResults,
  };

  const reportPath = path.join(OUTPUT_DIR, '..', 'rendered-qa-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\nReport written to ${reportPath}`);
  console.log(`Total: ${totalErrors} errors, ${totalWarnings} warnings`);
})();
