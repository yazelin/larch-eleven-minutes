// 分層色塊驗證（照《續》tests/layer_shots.mjs）：在各物件後面／前面／旁邊放站著不動的探針人物（跟主角同一套前後排序），
// 主角站到每一區（鏡頭跟著主角），2560×1320 截圖到 art/check/layer-<地圖>-<區>.png。
// behind＝物件北邊、在圖框裡（應被蓋住）；front＝南邊（應畫在物件上面）；side＝旁邊。
// 用法：node tests/layer_shots.mjs   （先 python3 src/build.py）
import { readFileSync, writeFileSync } from 'node:fs';
import { serve, open, sleep } from './lib.mjs';

const MAP = 'm-office';
const SPOTS = [
  ['江凌工位-behind', 7, 7, 'down'], ['江凌工位-front', 5, 10, 'up'],
  ['工位A3-behind', 27, 7, 'down'], ['工位A3-front', 27, 10, 'up'],
  ['北窗-front', 20, 5, 'up'], ['盆栽-behind', 32, 5, 'down'], ['盆栽-front', 32, 7, 'up'],
  ['主任室西牆-in', 35, 8, 'left'], ['主任室西牆-out', 33, 9, 'right'],
  ['主任桌-behind', 40, 6, 'down'], ['主任桌-front', 40, 9, 'up'], ['書櫃-side', 43, 11, 'right'],
  ['主任室南牆-in', 36, 12, 'down'], ['主任室南牆-out', 36, 14, 'up'],
  ['柱子西-behind', 12, 19, 'down'], ['柱子西-front', 12, 21, 'up'],
  ['印表機-behind', 37, 16, 'down'], ['印表機-front', 37, 18, 'up'],
  ['茶水間牆-behind', 4, 22, 'down'], ['茶水間牆-front', 4, 24, 'up'],
  ['冰箱-behind', 10, 28, 'down'], ['流理台-behind', 5, 28, 'down'],
  ['電梯-behind', 24, 29, 'down'], ['南牆中-behind', 34, 30, 'down'],
];
const ZONES = [['西北', [10, 12]], ['東北', [38, 11]], ['西南', [9, 26]], ['東南', [33, 26]]];

const proj = JSON.parse(readFileSync('dist/project.json', 'utf8'));
const node = proj.boards.flatMap(b => b.nodes).find(n => n.id === MAP);
const base = JSON.parse(node.data.pluginValues.map);
const walls = new Set(); base.layers.filter(l => l.collision).forEach(l => l.tiles.forEach((t, i) => t && walls.add(`${i % base.width},${Math.floor(i / base.width)}`)));
const taken = new Set(base.events.map(e => `${e.x},${e.y}`));
for (const [id, x, y] of SPOTS) {
  if (walls.has(`${x},${y}`)) throw new Error(`${id} 站在牆上 ${x},${y}`);
  if (taken.has(`${x},${y}`)) throw new Error(`${id} 那一格已經有事件 ${x},${y}`);
}
for (const [zone, [hx, hy]] of ZONES) {
  const m = JSON.parse(JSON.stringify(base));
  const hero = m.events.find(e => e.id === 'hero'); hero.x = hx; hero.y = hy;
  SPOTS.forEach(([id, x, y, dir], i) => { if (!(x === hx && y === hy))
    m.events.push({ ...hero, id: 'probe-' + i, name: id, x, y, actor: 'npc', solid: true, trigger: 'action', actions: [], conditions: [], direction: dir }); });
  node.data.pluginValues.map = JSON.stringify(m);
  writeFileSync('dist/test-layer.json', JSON.stringify(proj));
  const s = await serve('dist/test-layer.json');
  try {
    await fetch(s.base + '/api/lp/card', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ card: MAP, line: 0 }) });
    const ui = await open(s.base, { width: 2560, height: 1320 });
    await sleep(8000);
    await ui.page.screenshot({ path: `art/check/layer-office-${zone}.png` });
    console.log(zone, ui.errors.length ? ui.errors : 'ok');
    await ui.close();
  } finally {
    await fetch(s.base + '/api/lp/card', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ card: null }) }).catch(() => {});
    s.kill();
  }
}
