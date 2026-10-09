// 大地圖普攻連拍＋左上頭像：node tests/slash_shots.mjs → art/check/slash/*.jpg（看手上有沒有武器、頭像有沒有對到臉）
import { serve, open, sleep } from './lib.mjs';
import { execSync } from 'node:child_process';
execSync('python3 src/build.py', { env: { ...process.env, START: 'm-cloud', PRESET: 'phase=cloud' } });
const s = await serve('dist/project.json'); const ui = await open(s.base, { width: 1280, height: 720 });
try {
  await ui.clickText('開始遊戲'); await sleep(3000);
  for (let i = 0; i < 15 && !/找江禾那一則/.test(await ui.text()); i++) { await ui.advance(); await sleep(700); }
  await sleep(1500); await ui.page.screenshot({ path: 'art/check/slash/hud.jpg', type: 'jpeg', quality: 80 });
  let n = 0;
  for (let k = 0; k < 3; k++) {
    await ui.page.keyboard.press('j');
    const end = Date.now() + 450;
    while (Date.now() < end) await ui.page.screenshot({ path: `art/check/slash/${String(n++).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 70 });
    await sleep(600);
  }
  console.log(n, ui.errors.length ? ui.errors : 'ok');
} finally { await ui.close(); s.kill(); execSync('python3 src/build.py'); }
