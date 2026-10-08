"""RPG 地圖事件與地圖卡的產生函式（從《香布纏．續》xu/game/src/mapkit.py 精簡來的，格式照 Larch RPG 規格）。
座標一律是細格：tileSize 48，人物走路圖 288×384、scale 3.2（寬 3.2 格、高約 3.4 格）。"""
import itertools, json

_ids = itertools.count(1)
INVISIBLE = {'url': '', 'width': 32, 'height': 32, 'frames': 1, 'rows': 1, 'offsetX': 0, 'offsetY': 0, 'idleFrame': 0}
TILESET = {'id': 'kn-dungeon', 'name': '地城', 'url': 'https://pub-4b20b43f5acf4dfaa3f6ab842daa51cf.r2.dev/2d3b0242-9a6d-4051-9825-46aa4efd064a/larch/built-in-assets/packs/kenney-rpg/tilesets/1790278984532_tiny-dungeon.png', 'tileSize': 16, 'columns': 12, 'rows': 11}
RPG_VARS = [('hp', 'rpgHp', 'number', 100), ('bag', 'inventory', 'string', '[]'), ('equipment', 'rpgEquipment', 'string', '{}'),
            ('state', 'rpgState', 'string', ''), ('used', 'inventoryLastUsed', 'string', ''), ('count', 'inventoryCount', 'number', 0)]


def walker(url):
    return {'url': url, 'width': 288, 'height': 384, 'frames': 3, 'rows': 4, 'offsetX': 0, 'offsetY': 0, 'idleFrame': 1, 'scale': 3.2, 'smooth': True}


def A(kind, **kw):
    a = {'id': f'a{next(_ids)}', 'kind': kind, 'text': '', 'cardId': '', 'itemId': '', 'itemName': '', 'variable': '', 'value': '', 'amount': 1}
    a.update(kw)
    return a


def ev(id, x, y, **kw):
    e = {'id': id, 'name': id, 'x': x, 'y': y, 'actor': 'none', 'trigger': 'action', 'movement': 'still', 'solid': False,
         'once': False, 'conditions': [], 'actions': [], 'direction': 'down', 'sprite': INVISIBLE}
    e.update(kw)
    return e


def collision_layer(width, height, walls):
    return {'id': 'walk', 'name': '通行設定', 'visible': False, 'locked': False, 'collision': True, 'damage': 0, 'above': False,
            'tiles': ['kn-dungeon:0' if (i % width, i // width) in walls else None for i in range(width * height)]}


def map_dict(name, width, height, picture, walls, events, guidance=None, environment=None):
    m = {'version': 1, 'name': name, 'width': width, 'height': height, 'tileSize': 48, 'tilesets': [TILESET],
         'layers': [collision_layer(width, height, walls)], 'events': events, 'hp': 100, 'hpVariable': 'rpgHp',
         'bagVariable': 'inventory', 'stateVariable': 'rpgState', 'hideDesktopControls': False, 'combat': 'none',
         'view': {'mode': '2d', 'tilt': 48, 'zoom': 1, 'depthOfField': 0, 'atmosphere': 'day'},
         'picture': {'url': picture}, 'guidance': guidance or []}   # 不設 camera＝蓋滿地圖（細格用 normal 會變兩倍大）
    if environment: m['environment'] = environment
    return m


def map_node(id, title, m, var_names, pos=(0, 0), bgm=''):
    data = {'type': 'plugin', 'title': title, 'text': '', 'pluginId': 'larch-rpg-system', 'pluginCardId': 'map',
            'pluginVersion': '0.4.0', 'pluginName': 'RPG 系統', 'pluginCardName': 'RPG 地圖', 'pluginIcon': 'map',
            'pluginColor': '#4a7358', 'pluginPresentation': 'fullscreen', 'pluginFrame': {'showTitle': False, 'showButton': False},
            'pluginSkippable': False, 'pluginReadVars': var_names, 'pluginWriteVars': var_names, 'pluginAssets': [], 'platforms': ['web'],
            'pluginValues': {'map': json.dumps(m, ensure_ascii=False)}, 'start': True}
    if bgm: data.update(bgm=bgm, bgmVolume=0.35, bgmLoop=True)
    return {'id': id, 'type': 'story', 'position': {'x': pos[0], 'y': pos[1]}, 'data': data}


def say(t, speaker='narrator'):
    """地圖上的一句話。speaker：narrator（旁白）、player（江凌）、''（這個事件）、event:<id>"""
    return A('dialogue', text=t, presentation='text', speaker=speaker)


def card(card_id):
    """把一張對話卡演在地圖上（不離開地圖）"""
    return A('dialogue', cardId=card_id, presentation='text')


def setv(name, value):
    return A('variable', variable=name, value=str(value))


def cond(name, value, op='eq'):
    return {'kind': 'variable', 'variable': name, 'op': op, 'value': str(value), 'itemId': '', 'count': 1}


def has(item_id):
    return {'kind': 'item', 'variable': '', 'op': 'gte', 'value': '', 'itemId': item_id, 'count': 1}


def item(item_id, name):
    return A('item', itemId=item_id, itemName=name, amount=1)


def remove(item_id, name):
    return A('removeItem', itemId=item_id, itemName=name, amount=1)


def move(route, who='self', face=None):
    """route：[(方向, 步數)]，一段超過 20 步自動拆開（引擎每段 1–20 步、最多 8 段）"""
    segs = [(d, min(20, n - k)) for d, n in route for k in range(0, n, 20)]
    assert len(segs) <= 8, segs
    m = {'who': who, 'route': [{'dir': d, 'steps': n} for d, n in segs], 'wait': True}
    if face: m['face'] = face
    return A('move', move=m)


def page(id, conditions, actions, **kw):
    p = {'id': id, 'conditions': conditions, 'actor': 'none', 'sprite': INVISIBLE, 'movement': 'still', 'solid': False,
         'trigger': 'action', 'once': False, 'actions': actions}
    p.update(kw)
    return p


def fresh(actions):
    """複製一串動作並換新 id（同一張地圖裡動作 id 要唯一）"""
    out = []
    for a in actions:
        b = dict(a, id=f'a{next(_ids)}')
        if 'choice' in a: b['choice'] = dict(a['choice'], options=[dict(o, actions=fresh(o['actions'])) for o in a['choice']['options']])
        out.append(b)
    return out


def spread(e, cells):
    """一個事件鋪到好幾格（從哪一格按都按得到）：第一格保留原 id，其餘複製並換新的事件 id 與動作 id"""
    out = []
    for i, (x, y) in enumerate(cells):
        c = dict(e, x=x, y=y)
        if i:
            c.update(id=f"{e['id']}-{i}", name=f"{e['id']}-{i}", actions=fresh(e.get('actions', [])))
            c.pop('marker', None)   # 名牌只留第一格
            if e.get('pages'): c['pages'] = [dict(p, id=f"{p['id']}-{i}", actions=fresh(p['actions'])) for p in e['pages']]
        out.append(c)
    return out


def jump(node, x=None, y=None, face='up'):
    a = A('jump', cardId=node)
    if x is not None: a['arrive'] = {'x': x, 'y': y, 'direction': face}
    return a


def add(name, n=1):
    return A('variable', variable=name, value=str(n), op='add')


def heal():
    return A('heal', value='full')


def fight(card_id):
    """回合制戰鬥（動作地圖上的王也留在戰鬥畫面）。打贏才跑後面的步驟；打輸事件停下，可以再按一次重打。"""
    return A('battle', cardId=card_id, combat='turn')


def fx(effect, strength=0.6, ms=600, color=None):
    s = {'effect': effect, 'strength': strength, 'durationMs': ms}
    if color: s['color'] = color
    return A('screen', screen=s)
