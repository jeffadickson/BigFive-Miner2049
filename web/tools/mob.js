const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: require('fs').readFileSync('shot.js','utf8').match(/executablePath: '([^']+)'/)[1] });
  const p = await b.newPage({ viewport: { width: 400, height: 800 }, colorScheme: 'dark' });
  await p.goto('http://localhost:8765/index.html', { waitUntil: 'networkidle' });
  const w = await p.evaluate(() => [document.documentElement.scrollWidth, [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > 401 && !e.closest('.figbody,.tbl,pre,.listing')).slice(0,8).map(e => e.tagName + '.' + e.className)]);
  console.log(JSON.stringify(w));
  await p.screenshot({ path: '/tmp/claude-0/mob.png' });
  await p.evaluate(() => document.getElementById('fig-claim').scrollIntoView());
  await p.waitForTimeout(800);
  await p.screenshot({ path: '/tmp/claude-0/mob2.png' });
  await b.close();
})();
