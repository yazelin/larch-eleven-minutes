// 手機版截圖（iPhone 13 直向，以及橫向）：標題、序章、十九樓、終端機、雲端、王戰、結局選項。存 art/check/mobile-<名>.png
// node tests/mobile_shots.mjs   （自己會 build，跑完還原）
import { serve, open, sleep, devices } from './lib.mjs';
import { chromium } from '/home/ct/larch-preview/node_modules/playwright-core/index.mjs';
import { execSync } from 'node:child_process';
const shotDir = 'art/check/';
async function run(env, tag, landscape, fn) {
  execSync('python3 src/build.py', { env: { ...process.env, ...env } });
  const s = await serve('dist/project.json');
  const browser = await chromium.launch({ executablePath: '/home/ct/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome', headless: true, args: ['--disable-gpu'] });
  const d = devices['iPhone 13']; const vp = landscape ? { width: d.viewport.height, height: d.viewport.width } : d.viewport;
  const ctx = await browser.newContext({ ...d, viewport: vp, locale: 'zh-TW' }); const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto(s.base + '/'); await sleep(4000);
  const text = async () => (await Promise.all(page.frames().map(f => f.locator('body').innerText().catch(() => '')))).join(' | ');
  const tap = async t => { for (const f of page.frames()) { const l = f.getByText(t, { exact: false }); if (await l.count() && await l.first().isVisible().catch(() => false)) { await l.first().click(); return true; } } return false; };
  const shot = n => page.screenshot({ path: `${shotDir}mobile-${tag}-${n}.png` });
  try { await fn({ page, text, tap, shot }); console.log(tag, errors.length ? errors : 'ok'); } finally { await browser.close(); s.kill(); }
}
const adv = async (page, n = 1) => { for (let i = 0; i < n; i++) { await page.mouse.click(200, 300); await sleep(600); } };
try {
  const only = process.env.ONLY;
  for (const land of [false, true]) {
    const tag = land ? 'land' : 'port';
    await run({}, tag, land, async ({ page, tap, shot, text }) => {
      await shot('1-title'); await tap('開始遊戲'); await sleep(2500); await shot('2-prologue');
      for (let i = 0; i < 40 && !/按下確認，斷開河城/.test(await text()); i++) await adv(page);
      await sleep(1500); await shot('3-office');
    });
    await run({ START: 'c-term' }, tag, land, async ({ page, tap, shot }) => { await tap('開始遊戲'); await sleep(6000); await shot('4-terminal'); });
    await run({ START: 'm-cloud', PRESET: 'phase=cloud' }, tag, land, async ({ page, tap, shot }) => { await tap('開始遊戲'); await sleep(5000); await adv(page, 4); await sleep(2000); await shot('5-cloud'); });
    await run({ START: 'b-w1' }, tag, land, async ({ tap, shot }) => { await tap('開始遊戲'); await sleep(7000); await shot('6-battle'); });
    await run({ START: 'b-whale' }, tag, land, async ({ tap, shot }) => { await tap('開始遊戲'); await sleep(7000); await shot('7-whale'); });
  }
} finally { execSync('python3 src/build.py'); }
