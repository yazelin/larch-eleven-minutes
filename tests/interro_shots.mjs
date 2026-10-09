// 審訊室（一）換句時的連拍：node tests/interro_shots.mjs → art/check/interro/<n>.jpg（看換句時背景有沒有閃掉）
import { serve, open, sleep } from './lib.mjs';
import { execSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
rmSync('art/check/interro', { recursive: true, force: true }); mkdirSync('art/check/interro', { recursive: true });
execSync('python3 src/build.py', { env: { ...process.env, START: 'm-office', PRESET: 'phase=cut' } });
const s = await serve('dist/project.json'); const ui = await open(s.base, { width: 1280, height: 720 });
try {
  await ui.clickText('開始遊戲'); await sleep(2500);
  await ui.clickText('按下確認，斷開河城'); await sleep(6000);
  for (let i = 0; i < 12 && !/年輕的審訊員/.test(await ui.text()); i++) { await ui.advance(); await sleep(900); }
  let n = 0;
  for (let k = 0; k < 4; k++) {   // 每句：先連拍 0.8 秒，再按下一句時連拍換句那一刻
    await ui.advance();
    const end = Date.now() + 900;
    while (Date.now() < end) await ui.page.screenshot({ path: `art/check/interro/${String(n++).padStart(3, '0')}.jpg`, type: 'jpeg', quality: 50 });
    await sleep(1500);
  }
  console.log(n, ui.errors.length ? ui.errors : 'ok');
} finally { await ui.close(); s.kill(); execSync('python3 src/build.py'); }
