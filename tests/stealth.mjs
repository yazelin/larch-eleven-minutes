// 十九樓潛行的負控制（10-09）：倒完麵（alibi）站到茶水間門口警衛旁邊，等他輪到茶水間那一班 → 要被叫回茶水間；
// 對照組：同一個位置但還拿著泡麵碗（bowl）→ 不會被叫住。另外測抽屜：周主任轉身時開抽屜 → 退到門外。
// node tests/stealth.mjs
import { serve, open, sleep, assert } from './lib.mjs';
import { readFileSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
async function trial(phase, hero, wantRe, ms = 20000, press = false, delay = 0, pace = false) {
  execSync('python3 src/build.py', { env: { ...process.env, START: 'm-office', PRESET: 'phase=' + phase + (phase === 'alibi' ? ',sneaking=1' : '') } });
  const p = JSON.parse(readFileSync('dist/project.json', 'utf8'));
  const node = p.boards[0].nodes.find(n => n.id === 'm-office'); const m = JSON.parse(node.data.pluginValues.map);
  const h = m.events.find(e => e.id === 'hero'); [h.x, h.y] = hero; h.direction = 'up';
  node.data.pluginValues.map = JSON.stringify(m); writeFileSync('dist/test-stealth.json', JSON.stringify(p));
  const s = await serve('dist/test-stealth.json'); const ui = await open(s.base, { width: 1400, height: 800 });
  try {
    await ui.clickText('開始遊戲'); if (delay) { await sleep(delay); await ui.page.keyboard.press('Space'); } const end = Date.now() + ms; let hit = false;
    let k = 0;
    while (Date.now() < end) {
      if (press) await ui.page.keyboard.press('Space');
      if (pace) { const key = pace === 'ud' ? ((k++ % 4) < 2 ? 'ArrowDown' : 'ArrowUp') : ((k++ % 6) < 3 ? 'ArrowRight' : 'ArrowLeft'); await ui.page.keyboard.down(key); await sleep(260); await ui.page.keyboard.up(key); }   // 在茶水間裡左右來回走，走進警衛手電筒照得到的範圍
      await sleep(400); if (wantRe.test(await ui.text())) { hit = true; break; }
      if (k === 8) await ui.page.screenshot({ path: 'art/check/stealth-walk.png' });
    }
    await ui.page.screenshot({ path: 'art/check/stealth-' + phase + '.png' }); return hit;
  } finally { await ui.close(); s.kill(); }
}
try {
  assert(await trial('alibi', [4, 27], /值班的不要離開座位/, 30000, false, 0, true), '倒完麵在茶水間門口來回走，警衛走到茶水間那一頭時：被叫住');
  assert(!(await trial('bowl', [4, 27], /值班的不要離開座位/, 25000, false, 0, true)), '對照組：還拿著泡麵碗，同樣來回走，不會被叫住');
  // 走路時也會看（10-09 作者）：站在電梯口往茶水間那段路的旁邊（不在任何站點的視線裡），他走過來時要被叫住
  assert(await trial('alibi', [14, 20], /值班的不要離開座位/, 40000, false, 0, 'ud'), '在警衛走路的路線旁邊上下踱步：他走過來時被叫住');
  // 周主任 4.5 秒背對、2 秒轉身輪流：在不同時間點各按一次抽屜，至少有一次要被看到、至少有一次拿到卡
  const res = [];
  for (const d of [3000, 4500, 5500, 6500, 7500]) res.push([await trial('alibi', [41, 9], /轉過身來/, 4000, false, d), d]);
  console.log('  ', res.map(([h, d]) => d + 'ms:' + (h ? '被看到' : '沒被看到')).join(' '));
  assert(res.some(r => r[0]), '周主任轉身時開抽屜：被看到');
  assert(res.some(r => !r[0]), '背對時開抽屜：沒被看到');
} finally { execSync('python3 src/build.py'); }
