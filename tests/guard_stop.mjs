// 負向測試：phase=sneak（還沒去茶水間）時直接走向主任辦公室門口，警衛要把人叫住、往回退；phase=alibi 時不攔（對照組）。
// node tests/guard_stop.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { serve, open, sleep, assert } from './lib.mjs';
async function run(phase) {
  const p = JSON.parse(readFileSync('dist/project.json', 'utf8'));
  p.variables.find(v => v.name === 'phase').defaultValue = phase;
  const node = p.boards[0].nodes.find(n => n.id === 'm-office'); const m = JSON.parse(node.data.pluginValues.map);
  m.events = m.events.filter(e => e.id !== 'intro'); Object.assign(m.events.find(e => e.id === 'hero'), { x: 38, y: 17, direction: 'up' });
  node.data.pluginValues.map = JSON.stringify(m); writeFileSync('dist/test-guard.json', JSON.stringify(p));
  const s = await serve('dist/test-guard.json');
  await fetch(s.base + '/api/lp/card', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ card: 'm-office', line: 0 }) });
  const ui = await open(s.base, { width: 1600, height: 900 });
  try {
    await sleep(6000);
    for (let i = 0; i < 6; i++) { await ui.page.keyboard.down('ArrowUp'); await sleep(260); await ui.page.keyboard.up('ArrowUp'); await sleep(150); }
    await sleep(1500);
    const t = await ui.text();
    await ui.page.screenshot({ path: `art/check/guard-${phase}.png` });
    console.log(phase, /江工，這麼晚了/.test(t)); return /江工，這麼晚了/.test(t);
  } finally {
    await fetch(s.base + '/api/lp/card', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ card: null }) }).catch(() => {});
    await ui.close(); s.kill();
  }
}
assert(await run('sneak'), 'sneak：走到辦公室門口被警衛叫住');
assert(!(await run('alibi')), 'alibi（對照組）：繞過茶水間之後不攔');
