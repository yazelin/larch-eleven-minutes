// 十九樓：江凌、周主任、警衛放進地圖截圖（看大小、畫風、遮擋）。node tests/cast_shot.mjs
import { serve, open, sleep } from './lib.mjs';
const s = await serve('dist/project.json');
try {
  await fetch(s.base + '/api/lp/card', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ card: 'm-office', line: 0 }) });
  const ui = await open(s.base, { width: 2560, height: 1320 });
  await sleep(8000);
  await ui.page.screenshot({ path: 'art/check/cast-office.png' });
  console.log(ui.errors.length ? ui.errors : 'ok');
  await ui.close();
} finally {
  await fetch(s.base + '/api/lp/card', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ card: null }) }).catch(() => {});
  s.kill();
}
