// 戰鬥中途台詞截圖：node tests/talk_shots.mjs b-whale '頂樓那一則' → art/check/talk-<卡>.png（一直打到那句台詞出現）
import { serve, open, sleep } from './lib.mjs';
import { execSync } from 'node:child_process';
const card = process.argv[2] || 'b-whale', want = process.argv[3] || '頂樓那一則';
execSync('python3 src/build.py', { env: { ...process.env, START: card } });
// 只看樣子：觸發門檻改成 99%，打一下就跳台詞
execSync(`python3 -c "import re,pathlib;p=pathlib.Path('dist/project.json');p.write_text(re.sub(r'(percent[^0-9]{1,6})\\d+', lambda m: m.group(1)+'99', p.read_text()))"`);
const s = await serve('dist/project.json'); const ui = await open(s.base, { width: 1600, height: 900 });
const btn = async t => { for (const f of ui.page.frames()) { const b = f.locator('button', { hasText: t }); const n = await b.count();
  for (let i = 0; i < n; i++) if (await b.nth(i).isVisible().catch(() => false)) { await b.nth(i).click().catch(() => {}); return true; } } return false; };
try {
  await ui.clickText('開始遊戲'); await sleep(3000);
  let ok = false;
  for (let i = 0; i < 40 && !ok; i++) {
    if ((await ui.text()).includes(want)) { await sleep(1200); await ui.page.screenshot({ path: `art/check/talk-${card}.png` }); ok = true; break; }
    if (!(await btn('繼續'))) { if (await btn('刪除程式')) {} else if (!(await btn('技能') && (await sleep(300), await btn('刪除程式')))) await btn('攻擊'); }
    await sleep(900);
  }
  console.log(ok ? 'ok 截到「' + want + '」' : '沒等到「' + want + '」', ui.errors.length ? ui.errors : '');
} finally { await ui.close(); s.kill(); execSync('python3 src/build.py'); }
