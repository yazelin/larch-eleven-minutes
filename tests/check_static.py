"""靜態檢查：原文已接上的章節每段都用上、動作與事件 id 唯一、步數與條件不超過引擎上限、事件點不在牆上（物件上的互動點除外）。
python3 tests/check_static.py；NEG=1 python3 tests/check_static.py 要失敗（負控制）"""
import json, os, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
import build, story, layout
DONE = list(story.ORIG)   # 原文全部章節都已接進遊戲
ON_OBJECT = {'intro', 'monitor', 'drawer', 'sink', 'sink-1', 'sink-2', 'sink-3'}   # 刻意放在物件佔地上、從旁邊按的互動點
OPS = {'eq', 'neq', 'gte', 'lte'}
if os.environ.get('NEG'):   # 負控制：原文多一段沒接進遊戲的，必須被抓到
    k = next(h for h in story.ORIG if h.startswith('四'))   # 地圖逐段取用的章節（整節進卡片的章節會連假段落一起放進去）
    story.ORIG[k] = story.ORIG[k] + ['（負控制：這段不在遊戲裡）']
p = build.build(); errs = []
texts = []
for n in p['nodes']:
    d = n['data']
    texts += [l['text'] for l in d.get('dialogueLines', [])]
    if d.get('pluginCardId') == 'battle':
        texts += [l['text'] for t in json.loads(d['pluginValues']['battle']).get('triggers', []) for l in t['lines']]
    if d.get('pluginId') == 'eleven-minutes':
        sc = json.loads(d['pluginValues']['script']); texts += [sc['intro'], sc['after']] + [x for st in sc['steps'] for x in ('`' + st['cmd'] + '`', st['out'])]
    if d.get('pluginCardId') != 'map': continue
    m = json.loads(d['pluginValues']['map']); dz = layout.load({b[0]: b[1] for b in build.MAPS}[n['id']]); wl = layout.walls(dz)
    ids = [e['id'] for e in m['events']]; cells = [(e['x'], e['y']) for e in m['events']]
    if len(ids) != len(set(ids)): errs.append('事件 id 重複')
    if len(cells) != len(set(cells)): errs.append('同一格有兩個事件')
    aids = []; aids_kinds = []
    def walk(acts, depth=0):
        if len(acts) > 32: errs.append(f'一串動作 {len(acts)} 步 > 32')
        for a in acts:
            aids.append(a['id']); aids_kinds.append(a)
            if a['kind'] == 'dialogue' and a.get('text'): texts.append(a['text'])
            for o in a.get('choice', {}).get('options', []): walk(o['actions'], depth + 1)
    for e in m['events']:
        for pg in [e] + e.get('pages', []):
            walk(pg.get('actions', []))
            for c in pg.get('conditions', []):
                if c.get('op', 'eq') not in OPS: errs.append(f"{e['id']} 條件運算子 {c['op']}")
            if len(pg.get('conditions', [])) > 16: errs.append(f"{e['id']} 條件超過 16")
        if not e.get('free') and e['trigger'] not in ('auto', 'condition') and (e['x'], e['y']) in wl and e['id'] not in ON_OBJECT: errs.append(f"{e['id']} 在牆上 {(e['x'], e['y'])}")
    if len(aids) != len(set(aids)): errs.append(f'{n["id"]} 動作 id 重複')
    nodes = {x['id'] for x in p['nodes']}
    for a_ in aids_kinds:
        if a_['kind'] in ('jump', 'battle') and not a_['cardId'].startswith('monsters:') and a_['cardId'] not in nodes: errs.append(f"{n['id']} {a_['kind']} 指向不存在的卡 {a_['cardId']}")
    for g in m['guidance']:
        if g['eventId'] not in ids: errs.append(f"任務提示指向不存在的事件 {g['eventId']}")
joined = '\n'.join(texts)
for sec in DONE:
    for i, para in enumerate(story.ORIG[sec]):
        if para not in texts and para not in joined: errs.append(f'原文沒用上：{sec} 第 {i} 段「{para[:20]}…」')
print('\n'.join(errs) or 'check_static ok'); sys.exit(1 if errs else 0)
