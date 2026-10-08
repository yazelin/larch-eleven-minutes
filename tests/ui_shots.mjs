// 介面截圖：標題、序章對話卡、地圖狀態列與任務、暫停選單、終端機卡、王戰戰鬥畫面。存 art/check/ui-<名>.png。
// node tests/ui_shots.mjs   （自己會 build；王戰用 START=m-cloud PRESET=phase=gate,kills=4，跑完還原）
import { serve, open, sleep } from './lib.mjs';
import { execSync } from 'node:child_process';
async function run(env, fn) {
  execSync('python3 src/build.py', { env: { ...process.env, ...env } });
  const s = await serve('dist/project.json'); const ui = await open(s.base, { width: 1600, height: 900 });
  try { await fn(ui); console.log(ui.errors.length ? ui.errors : 'ok'); } finally { await ui.close(); s.kill(); }
}
const shot = (ui, n) => ui.page.screenshot({ path: `art/check/ui-${n}.png` });
try {
  await run({}, async ui => {
    await sleep(4000); await shot(ui, '1-title');
    await ui.clickText('開始遊戲'); await sleep(2500); await shot(ui, '2-dialogue');
    for (let i = 0; i < 40 && !/按下確認|拿起泡麵碗/.test(await ui.text()); i++) { await ui.advance(); await sleep(500); }
    await sleep(800); await shot(ui, '3-map');
    await ui.page.keyboard.press('Escape'); await sleep(1500); await shot(ui, '4-pause');
    await ui.page.keyboard.press('Escape'); await sleep(800);
  });
  await run({ START: 'c-term' }, async ui => {
    await ui.clickText('開始遊戲'); await sleep(5000); await shot(ui, '7-terminal-1');
    for (let i = 0; i < 3; i++) { await ui.page.keyboard.press('Enter'); await sleep(9000); }
    await shot(ui, '7-terminal-2');
  });
  await run({ START: 'm-cloud', PRESET: 'phase=gate,kills=4' }, async ui => {
    await ui.clickText('開始遊戲'); await sleep(2500);
    for (let i = 0; i < 20 && !(await ui.page.getByText('走到牆中段的門前').first().isVisible().catch(() => false)); i++) { await ui.advance(); await sleep(700); }
    await ui.clickText('走到牆中段的門前'); await sleep(8000); await ui.page.keyboard.press('Space');
    for (let i = 0; i < 15 && !/ENCOUNTER/.test(await ui.text()); i++) { await sleep(900); await shot(ui, '5-map-dialogue'); await ui.advance(); }
    await sleep(3000); await shot(ui, '6-battle');
  });
} finally { execSync('python3 src/build.py'); }
