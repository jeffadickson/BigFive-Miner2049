const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  await p.goto('http://localhost:8765/index.html', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1500);
  const ids = process.argv.slice(2);
  await p.screenshot({ path: '/tmp/claude-0/top.png' });
  for (const id of ids) {
    const el = await p.$('#fig-' + id);
    if (!el) { errs.push('no fig ' + id); continue; }
    await el.scrollIntoViewIfNeeded(); await p.waitForTimeout(1200);
    await el.screenshot({ path: '/tmp/claude-0/fig-' + id + '.png' });
  }
  console.log(errs.join('\n') || 'no errors');
  await b.close();
})();
