// 王戰計算（10-10 作者：用算的、不要實機跑那麼久）：直接用 Larch 引擎自己的戰鬥規則（rpg-engine 匯出的 begin／act／intents），
// 讀 dist/project.json 裡的戰鬥卡，兩種打法各打一遍，印出勝負、回合數、江凌剩多少血。沒有動畫，幾秒跑完。
//   node tests/battle_sim.mjs            （先 python3 src/build.py）
// 打法：smart＝奧義集滿就放、預告下回合有大招就防禦、魔力夠就放技能（一群放群體技、單一隻放單體技）、否則普攻血最少的；naive＝隨便打（同樣放技能，但不放奧義、不防禦）
import { readFileSync } from 'node:fs';
const { g: R } = await import('/home/ct/larch-preview/vendor/larch/assets/rpg-engine-DYTM_xfT.js');
const p = JSON.parse(readFileSync(new URL('../dist/project.json', import.meta.url)));
const cards = Object.fromEntries(p.boards[0].nodes.filter(n => n.data.pluginCardId === 'battle').map(n => [n.id, R.parse(n.data.pluginValues.battle)]));
const HERO_HP = 100;
function fight(S, plan, hp = HERO_HP) {
  let v = R.begin(S, hp, HERO_HP, true, []);
  for (let turn = 0; turn < 60 && !v.result; turn++) {
    const alive = v.enemies.map((h, i) => [h, i]).filter(([h]) => h > 0);
    const weakest = alive.sort((a, b) => a[0] - b[0])[0]?.[1] ?? 0, first = v.enemies.findIndex(h => h > 0);
    const intents = (R.intents(S, v) || []).filter(Boolean);
    let a;
    if (plan === 'smart' && (v.limit ?? 0) >= 100) a = ['limit', weakest];
    else if (plan === 'smart' && intents.some(x => x.special)) a = ['guard', weakest];
    else if (alive.length > 1 && v.mp >= 6) a = ['skill', weakest, 'del'];          // 一群：群體技
    else if (alive.length === 1 && v.mp >= 4) a = ['skill', weakest, 'unpick'];  // 單一隻（王）：單體技
    else a = ['attack', plan === 'smart' ? weakest : first];
    const next = R.act(S, v, a[0], a[1], false, a[2], [], undefined, true, false);
    if (next === v) { v = R.act(S, v, 'attack', first, false, undefined, [], undefined, true, false); } else v = next;
  }
  return v;
}
for (const id of ['b-w1', 'b-w2', 'b-whale', 'b-prism']) {
  const S = cards[id]; if (!S) continue;
  const row = [id.padEnd(8), S.enemies.map(e => e.name + e.hp).join(' ')];
  for (const plan of ['smart', 'naive']) {
    const v = fight(S, plan);
    row.push(`${plan === 'smart' ? '用對方法' : '隨便打'}：${v.result === 'victory' ? '贏' : '輸'} ${v.turn - 1} 回合 剩 ${v.hp}`);
  }
  console.log(row.join('　'));
}
