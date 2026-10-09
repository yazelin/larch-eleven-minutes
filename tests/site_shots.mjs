// 公開站用的遊戲截圖（沒有預覽器工具列）：存 art/site_raw/<名>.png。node tests/site_shots.mjs
import { serve, open, sleep } from './lib.mjs';
import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
mkdirSync('art/site_raw', { recursive: true });
const hide = async page => { for (const f of page.frames()) await f.evaluate(() => { document.querySelectorAll('button,select,a').forEach(b => { if (/^(白板|雲端|回饋|素材庫)$/.test(b.innerText.trim()) || b.tagName === 'SELECT') b.style.display = 'none'; }); }).catch(() => {}); };
async function run(env, fn) {
  execSync('python3 src/build.py', { env: { ...process.env, ...env } });
  const s = await serve('dist/project.json'); const ui = await open(s.base, { width: 1600, height: 900 });
  try { await fn(ui); } finally { await ui.close(); s.kill(); }
}
const shot = async (ui, n) => { await hide(ui.page); await sleep(300); await ui.page.screenshot({ path: `art/site_raw/${n}.png` }); };
const freeMap = async (ui, re) => { for (let i = 0; i < 40; i++) { const t = await ui.text(); if (re.test(t) && !/繼續探索|繼續 ▶/.test(t)) return; await ui.page.mouse.click(800, 800); await sleep(700); } };
try {
  await run({ START: 'm-office', PRESET: 'phase=alibi,sneaking=1' }, async ui => { await ui.clickText('開始遊戲'); await sleep(9000); await shot(ui, 'office'); });
  await run({ START: 'm-server', PRESET: 'phase=card' }, async ui => { await ui.clickText('開始遊戲'); await freeMap(ui, /終端機/); await sleep(1500); await shot(ui, 'server'); });
  await run({ START: 'c-term' }, async ui => { await ui.clickText('開始遊戲'); await sleep(4000); for (let i = 0; i < 3; i++) { await ui.page.keyboard.press('Enter'); await sleep(9000); } await shot(ui, 'terminal'); });
  await run({ START: 'm-cloud', PRESET: 'phase=cloud' }, async ui => { await ui.clickText('開始遊戲'); await freeMap(ui, /江禾那一則/); await sleep(1500); await shot(ui, 'cloud'); });
  await run({ START: 'b-w1' }, async ui => { await ui.clickText('開始遊戲'); await sleep(7000); await shot(ui, 'battle-w1'); });
  await run({ START: 'b-w2' }, async ui => { await ui.clickText('開始遊戲'); await sleep(7000); await shot(ui, 'battle-w2'); });
} finally { execSync('python3 src/build.py'); }
