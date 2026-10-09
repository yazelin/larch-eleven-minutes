// 戰鬥出手動作連拍：node tests/rig_shots.mjs b-w2 [秒數] → art/check/rig/<卡>-<n>.jpg（約每 0.25 秒一張；只按「防禦」讓敵人出手，看跳／飄／噴火與大招插畫）
import { serve, open, sleep } from './lib.mjs';
import { execSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
const card = process.argv[2] || 'b-w2', secs = Number(process.argv[3] || 60);
rmSync('art/check/rig', { recursive: true, force: true }); mkdirSync('art/check/rig', { recursive: true });
execSync('python3 src/build.py', { env: { ...process.env, START: card } });
const s = await serve('dist/project.json'); const ui = await open(s.base, { width: 1600, height: 900 });
const btn = async t => { for (const f of ui.page.frames()) { const b = f.locator('button', { hasText: t }); const n = await b.count();
  for (let i = 0; i < n; i++) if (await b.nth(i).isVisible().catch(() => false)) { await b.nth(i).click().catch(() => {}); return true; } } return false; };
try {
  await ui.clickText('開始遊戲'); await sleep(3000);
  const end = Date.now() + secs * 1000; let n = 0;
  while (Date.now() < end) {
    await ui.page.screenshot({ path: `art/check/rig/${card}-${String(n++).padStart(3, '0')}.jpg`, type: 'jpeg', quality: 60 });
    if (n % 25 === 0) { if (!(await btn('繼續')) && !(await btn('防禦'))) await btn('攻擊'); }
    await sleep(60);
  }
  console.log(n, ui.errors.length ? ui.errors : 'ok');
} finally { await ui.close(); s.kill(); execSync('python3 src/build.py'); }
