// 二十樓以後的試玩：二十樓 → 終端機卡 → 雲端長城 → 找江禾那一則 → 審查兵 → 四場王戰 → 審訊室（二）→ 選結局。
// node tests/play_rest.mjs [1|2|3]   （結局編號，預設 1；自己會用 START=m-server 重 build，跑完還原）
// 王戰：每回合先放「刪除程式」（全體），MP 不夠就普攻。打輸了按門重打，最多三次。
// 截圖存 art/check/play-rest-<步>.png。
import { serve, open, sleep, assert } from './lib.mjs';
import { execSync } from 'node:child_process';
const END = Number(process.argv[2] || 1);
const LABEL = { 1: '送出', 2: '交給 PRISM', 3: '修回去' }[END];
const EXPECT = { 1: /這是他四年來第一次說這句話/, 2: /他們會再需要彼此/, 3: /是他自己扣上的/ }[END];
execSync('python3 src/build.py', { env: { ...process.env, START: 'm-server' } });
const s = await serve('dist/project.json');
const ui = await open(s.base, { width: 1600, height: 900 });
const { page, text } = ui;
const shot = n => page.screenshot({ path: `art/check/play-rest-${n}.png` });
const visible = async t => { for (const f of page.frames()) if (await f.getByText(t, { exact: false }).first().isVisible().catch(() => false)) return true; return false; };
let seen = '';   // 途中出現過的畫面文字（結局後會自動回到標題，最後幾句可能一閃而過）
async function until(re, ms = 90000) {
  const end = Date.now() + ms;
  while (Date.now() < end) { const t = await text(); seen += t; if (re.test(t) || re.test(seen)) return t; await ui.advance(); await sleep(500); }
  throw new Error('等不到 ' + re + '\n畫面：' + (await text()).slice(-500));
}
async function note(t, ms = 60000) {   // 對話一路按掉，直到任務提示 t 可以點
  const end = Date.now() + ms;
  while (Date.now() < end) {   // 隔 1.5 秒連續兩次看得到才算（地圖載入慢時，開場對話會在任務提示出現之後才跳出來）
    if (await visible(t)) { await sleep(1500); if (await visible(t) && !/繼續探索/.test(await text())) return; }
    await ui.advance(); await sleep(600);
  }
  throw new Error('等不到任務提示「' + t + '」');
}
async function btn(t) {   // 點畫面上文字含 t 的可見按鈕
  for (const f of page.frames()) { const b = f.locator('button', { hasText: t }); const n = await b.count();
    for (let i = 0; i < n; i++) if (await b.nth(i).isVisible().catch(() => false)) { await b.nth(i).click().catch(() => {}); return true; } }
  return false;
}
async function battle(name, skill = '刪除程式', cost = 6) {   // 打到戰鬥畫面消失；回傳 true＝打贏（畫面回到地圖且沒有敗北字樣）
  await until(new RegExp('ENCOUNTER ' + name), 60000);
  for (let r = 0; r < 80; r++) {
    const t = await text();
    if (r % 10 === 0) { console.log('  ', name, '第', r, '步', (t.match(/江凌 HP \d+/) || [''])[0]); await shot(`5-${name}-live`); }
    if (!/ENCOUNTER/.test(t)) return true;
    if (/敗北|DEFEAT|全滅/.test(t)) return false;
    const mp = Number((t.match(/MP (\d+)/) || [0, 0])[1]);
    if (await btn('繼續')) {}                                  // 勝利畫面
    else if (await btn(skill)) {}                              // 技能選單開著
    else if (mp >= cost && await btn('技能')) { await sleep(400); await btn(skill); }
    else if (!(await btn('攻擊'))) await ui.advance();
    await sleep(1800);
  }
  throw new Error(name + ' 打太久');
}
try {
  await ui.clickText('開始遊戲'); await sleep(2000);
  await note('走到最裡面的終端機'); await shot('1-server');
  await ui.clickText('走到最裡面的終端機'); await sleep(8000); await page.keyboard.press('Space');
  await ui.waitText(/GFW CORE TERMINAL/, 30000); await sleep(1500); await shot('2-terminal');   // 只等、不按鍵（按鈕有焦點，Enter 會直接打指令）
  for (let i = 0; i < 40 && !(await visible('戴上頭盔')); i++) { if (!(await btn('輸入：'))) await sleep(500); await sleep(1500); }
  assert(await btn('戴上頭盔'), '終端機打完三個指令，出現「戴上頭盔」');
  await note('在灰色的山裡找江禾那一則'); await shot('3-cloud');
  assert(true, '終端機三個指令打完，戴上頭盔進雲海');
  await ui.clickText('在灰色的山裡找江禾那一則'); await sleep(9000); await page.keyboard.press('Space');
  await note('砍倒追來的審查兵');
  assert(true, '捧起江禾那一則');
  // 審查兵追過來：原地一直砍
  const end = Date.now() + 180000;
  while (Date.now() < end && !(await visible('走到牆中段的門前'))) { await page.keyboard.press('j'); await sleep(350); await ui.advance(); }
  await shot('4-hunt');
  await note('走到牆中段的門前');
  assert(true, '砍倒四個以上的審查兵，門前亮起人影');
  for (const [name, retry] of [['第一班', '走到牆中段的門前'], ['第二班', '回到門前，再打一次'], ['大肥魚', '回到門前，再打一次'], ['PRISM', '回到門前，再打一次']]) {
    let won = false;
    for (let k = 0; k < 3 && !won; k++) {
      if (name === '第一班' || k > 0) { await note(retry); await ui.clickText(retry); await sleep(8000); await page.keyboard.press('Space'); }
      won = await battle(name, /班/.test(name) ? '刪除程式' : '拆開規則', /班/.test(name) ? 6 : 4);
      await shot(`5-${name}-${k}`);
      if (!won) console.log('  打輸', name, '重打');
    }
    assert(won, '打贏 ' + name);
  }
  const t0 = Date.now(); let picked = false;
  while (!picked && Date.now() - t0 < 120000) {   // 對話按掉，直到結局選項按鈕出現
    for (const f of page.frames()) { const b = f.locator('button', { hasText: LABEL }); if (await b.first().isVisible().catch(() => false)) { await shot('6-choice'); await b.first().click(); picked = true; break; } }
    if (!picked) { await ui.advance(); await sleep(600); }
  }
  assert(picked, '審訊室（二）之後出現結局選項'); await sleep(1500); seen = '';
  await until(EXPECT, 120000); await shot('7-ending');
  assert(true, '結局 ' + LABEL);
  await until(/溟月|開始遊戲/, 60000); await shot('8-credits');
  assert(/溟月/.test(seen), '片尾署名出現過');
  console.log(ui.errors.length ? ui.errors : '沒有頁面錯誤');
} catch (e) { await shot('fail'); console.error(e.message); process.exitCode = 1; }
finally { await ui.close(); s.kill(); execSync('python3 src/build.py'); }
