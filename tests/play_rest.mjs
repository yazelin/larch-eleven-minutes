// 二十樓以後的試玩：二十樓 → 終端機卡 → 雲端長城 → 找江禾那一則 → 審查兵 → 四場王戰 → 審訊室（二）→ 選結局。
// node tests/play_rest.mjs [1|2|3]   （結局編號，預設 1；自己會用 START=m-server 重 build，跑完還原）
// 王戰：每回合先放「刪除程式」（全體），MP 不夠就普攻。打輸了按門重打，最多三次。
// 截圖存 art/check/play-rest-<步>.png。
import { serve, open, sleep, assert } from './lib.mjs';
import { execSync } from 'node:child_process';
const END = Number(process.argv[2] || 1);
const LABEL = { 1: '只把那一則送給媽媽', 2: '全部交給 PRISM', 3: '把長城修回去' }[END];   // 選項文字（10-09 改），結局名稱不變
execSync('python3 src/build.py', { env: { ...process.env, START: 'm-server', PRESET: 'phase=card' } });   // 帶著十九樓結束時的進度（card）進場，跟真實流程一樣
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
// 打法（10-10 作者：不要隨便打都贏）：SMART=1（預設）＝奧義集滿就放、預告下回合有大招就防禦、魔力夠放群體技、否則普攻；
// SMART=0＝隨便打（只放群體技和普攻），是負控制：要打輸才對
const SMART = process.env.SMART !== '0';
const special = async () => { for (const f of page.frames()) if (await f.locator('.is-special').first().isVisible().catch(() => false)) return true; return false; };
async function battle(name, skill = '刪除程式', cost = 6) {   // 回傳 true＝打贏（看到「戰鬥勝利」），false＝打輸
  await until(new RegExp('(ENCOUNTER|BOSS BATTLE) ' + name), 60000);
  await until(/第 \d+ 回合/, 30000);   // 重打時上一場的 ENCOUNTER 字樣還在，要等到回合數出現才算真的開打
  let won = false, lost = false, round = 0, hp = '';
  for (let r = 0; r < 120; r++) {
    const t = await text();
    round = Number((t.match(/第 (\d+) 回合/) || [0, round])[1]) || round; hp = (t.match(/江凌 HP (\d+)/) || ['', hp])[1] || hp;
    if (/戰鬥勝利|Victory/.test(t)) won = true;
    if (/敗北|DEFEAT|全滅|失去戰鬥能力/.test(t)) lost = true;
    if (!/ENCOUNTER|BOSS BATTLE/.test(t)) { console.log(`   ${name}：${won && !lost ? '贏' : '輸'}，${round} 回合，江凌剩 ${hp} HP（${SMART ? '用對方法' : '隨便打'}）`); return won && !lost; }
    const mp = Number((t.match(/MP (\d+)/) || [0, 0])[1]);
    if (await btn('繼續')) {}                                  // 勝利／敗北畫面
    else if (SMART && await btn('奧義')) {}                    // 大招集滿就放
    else if (SMART && await special() && await btn('防禦')) {} // 預告下回合有大招：防禦
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
  let lastWalk = Date.now();
  while (Date.now() < end && !/ENCOUNTER|BOSS BATTLE/.test(await text())) {   // 砍倒第四隻以後第一班自動開打
    await page.keyboard.press('j'); await sleep(350); await ui.advance();
    if (process.env.DEBUG && Date.now() % 7 < 1) { const tt = await text(); console.log('  hunt', tt.slice(-120).replace(/\s+/g, ' ')); }
    if (Date.now() - lastWalk > 25000) { lastWalk = Date.now(); await ui.clickText('砍倒追來的審查兵', 3000).catch(() => {}); }   // 站著等不到就往門走，路上遇到再砍
  }
  await shot('4-hunt');
  assert(true, '砍倒四個以上的審查兵，門前亮起人影');
  for (const [name, retry] of [['第一班', '走到牆中段的門前'], ['第二班', '回到門前，再打一次'], ['大肥魚', '回到門前，再打一次'], ['PRISM', '回到門前，再打一次']]) {
    let won = false;
    for (let k = 0; k < 3 && !won; k++) {
      if (k > 0) { await note(retry); await ui.clickText(retry); await sleep(8000); }   // 第一場在門前亮起人影後自動開打；打輸才走回門前（走到就觸發）
      if (name === '大肥魚' && k === 0) { const t0 = await until(/靠近了才看清楚|BOSS BATTLE 大肥魚/, 60000); if (/靠近了才看清楚/.test(t0)) { await sleep(1500); await shot('5-大肥魚-map'); } }   // 鏡頭移到門前，看得到地圖上的大肥魚
      won = await battle(name, /班/.test(name) ? '刪除程式' : '拆開規則', /班/.test(name) ? 6 : 4);
      await shot(`5-${name}-${k}`);
      if (!won) console.log('  打輸', name, '重打');
    }
    assert(won, '打贏 ' + name);
    if (name === '大肥魚') {   // 插卡：打贏以後要自己走到她面前（10-09 作者：沒玩到把卡插進胸前的鎖）
      await note('把管理員卡插進她胸口的鎖'); await ui.clickText('把管理員卡插進她胸口的鎖'); await sleep(6000);
      await until(/胸口的鎖頭露出來了/, 30000); assert(true, '走到大肥魚面前插卡');
    }
  }
  const t0 = Date.now(); let picked = false;
  while (!picked && Date.now() - t0 < 120000) {   // 對話按掉，直到結局選項按鈕出現
    for (const f of page.frames()) { const b = f.locator('button', { hasText: LABEL }); if (await b.first().isVisible().catch(() => false)) { await shot('6-choice'); await b.first().click(); picked = true; break; } }
    if (!picked) { await ui.advance(); await sleep(600); }
  }
  assert(picked, '審訊室（二）之後出現結局選項'); await sleep(1500); seen = '';
  // 結局判定看 CG 解鎖紀錄（結局卡一播就寫進去），不靠抓打字中的最後一句（打太快會漏，10-09 偶發失敗）
  const cgDone = async () => (await page.evaluate(() => Object.keys(localStorage).filter(k => k.startsWith('larch-cg-')).map(k => localStorage.getItem(k)).join(''))).includes(`scenes/e${END}.webp`);
  for (let i = 0; i < 200 && !(await cgDone()); i++) { await ui.advance(); await sleep(500); }
  assert(await cgDone(), '結局卡播出（CG 解鎖紀錄有 e' + END + '）'); await shot('7-ending');
  assert((await page.evaluate(() => Object.keys(localStorage).filter(k => k.startsWith('larch-cg-')).map(k => localStorage.getItem(k)).join(''))).includes('scenes/interrogation.webp'), 'CG 審訊室也解鎖');
  assert(true, '結局 ' + LABEL);
  await until(/溟月|開始遊戲/, 60000); await shot('8-credits');
  console.log(ui.errors.length ? ui.errors : '沒有頁面錯誤');
} catch (e) { await shot('fail'); console.error(e.message); process.exitCode = 1; }
finally { await ui.close(); s.kill(); execSync('python3 src/build.py'); }
