// 十九樓試玩：序章 → 開場 → 周主任下令 → 斷河城 → 審訊室（一）→ 泡麵碗 → 茶水間 → 抽屜 → 樓梯門 → 二十樓開場。
// 每一步點任務提示（引擎會把江凌走到那個事件）再按互動鍵，對話一路按下去，等下一個任務提示出現。
// 截圖存 art/check/play-office-<步>.png。node tests/play_office.mjs   （先 python3 src/build.py；HEADED=1 看畫面）
import { serve, open, sleep, assert } from './lib.mjs';
const s = await serve('dist/project.json');
const ui = await open(s.base, { width: 1600, height: 900 });
const { page, text } = ui;
const shot = n => page.screenshot({ path: `art/check/play-office-${n}.png` });
async function until(re, ms = 90000) {   // 一直往下按，直到畫面出現 re
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const t = await text();
    if (re.test(t)) return t;
    await ui.advance(); await sleep(450);
  }
  throw new Error('等不到 ' + re + '\n畫面：' + (await text()).slice(-500));
}
let caughtTimes = 0;
async function step(note, expect, name) {   // 走過去按；被警衛叫住或被周主任看到就重來（10-09 加了潛行），最多 12 次
  for (let k = 0; k < 12; k++) {
    await ui.clickText(note); await sleep(5000);
    await page.keyboard.press('Space'); await sleep(800);
    const end = Date.now() + 25000; let t = '';
    while (Date.now() < end) { t = await text(); if (expect.test(t)) { await shot(name); return t; }
      if (/值班的不要離開座位|轉過身來/.test(t)) { caughtTimes++; console.log('  被發現，重來'); break; }
      await ui.advance(); await sleep(450); }
    for (let i = 0; i < 8; i++) { await ui.advance(); await sleep(500); }
    if (!(await visible(note))) await sleep(1000);
  }
  throw new Error('一直被發現：' + note);
}
const visible = async t => { for (const f of page.frames()) if (await f.getByText(t, { exact: false }).first().isVisible().catch(() => false)) return true; return false; };
try {
  await ui.clickText('開始遊戲'); await sleep(1500);
  await until(/那天晚上下雨/);                   // 序章對話卡 → 地圖開場
  await shot('1-intro');
  // 任務提示依序出現；江凌開場就站在監控台前，按鍵可能直接把前幾步觸發掉，所以畫面已經是後面的步驟就跳過
  const NOTES = ['按下確認，斷開河城', '拿起泡麵碗', '去茶水間，把麵倒掉', '等警衛走回電梯口', '走樓梯上二十樓'];
  const SHOTS = ['3-cut', '4-bowl', '5-sink', '6-drawer'];
  const reNotes = i => new RegExp(NOTES.slice(i).join('|'));
  let t = await until(reNotes(0)); await shot('2-order');
  for (let i = 0; i < 4; i++) {
    t = await text();
    if (!t.includes(NOTES[i])) { assert(reNotes(i + 1).test(t), '已經過了「' + NOTES[i] + '」'); continue; }
    await step(NOTES[i], reNotes(i + 1), SHOTS[i]);
    assert(true, '完成「' + NOTES[i] + '」');
  }
  await ui.clickText('走樓梯上二十樓'); await sleep(7000);
  await until(/核心機房在二十樓/, 30000); await shot('7-stairs');
  assert(true, '走到樓梯門');
  console.log('被發現次數', caughtTimes);
  console.log(ui.errors.length ? ui.errors : '沒有頁面錯誤');
} catch (e) { await shot('fail'); console.error(e.message); process.exitCode = 1; }
finally { await ui.close(); s.kill(); }
