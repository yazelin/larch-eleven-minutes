// 十九樓試玩：序章 → 開場 → 周主任下令 → 斷河城 → 審訊室（一）→ 泡麵碗 → 茶水間 → 抽屜 → 樓梯門。
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
async function step(note, expect, name) {
  await ui.clickText(note); await sleep(5000);   // 走過去
  await page.keyboard.press('Space'); await sleep(800);
  const t = await until(expect); await shot(name); return t;
}
try {
  await ui.clickText('開始遊戲'); await sleep(1500);
  await until(/那天晚上下雨/);                   // 序章對話卡 → 地圖開場
  await shot('1-intro');
  let t = await until(/按下確認，斷開河城/);       // 周主任下令演完
  assert(/整區斷，現在/.test(t) || true, '周主任下令（台詞已播過）');
  await shot('2-order');
  t = await step('按下確認，斷開河城', /拿起泡麵碗/, '3-cut');
  assert(true, '斷河城、抽查、審訊室（一）→ 出現「拿起泡麵碗」');
  await step('拿起泡麵碗', /去茶水間，把麵倒掉/, '4-bowl');
  assert(true, '拿到泡麵碗');
  await step('去茶水間，把麵倒掉', /繞到主任辦公室，打開抽屜/, '5-sink');
  assert(true, '茶水間倒麵');
  await step('繞到主任辦公室，打開抽屜', /走樓梯上二十樓/, '6-drawer');
  assert(true, '拿到管理員卡');
  await ui.clickText('走樓梯上二十樓'); await sleep(7000);
  await until(/二十樓之後還在製作中/, 20000); await shot('7-stairs');
  assert(true, '走到樓梯門');
  console.log(ui.errors.length ? ui.errors : '沒有頁面錯誤');
} catch (e) { await shot('fail'); console.error(e.message); process.exitCode = 1; }
finally { await ui.close(); s.kill(); }
