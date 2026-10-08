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


def map_node(id, title, m, var_names, pos=(0, 0)):
    data = {'type': 'plugin', 'title': title, 'text': '', 'pluginId': 'larch-rpg-system', 'pluginCardId': 'map',
            'pluginVersion': '0.4.0', 'pluginName': 'RPG 系統', 'pluginCardName': 'RPG 地圖', 'pluginIcon': 'map',
            'pluginColor': '#4a7358', 'pluginPresentation': 'fullscreen', 'pluginFrame': {'showTitle': False, 'showButton': False},
            'pluginSkippable': False, 'pluginReadVars': var_names, 'pluginWriteVars': var_names, 'pluginAssets': [], 'platforms': ['web'],
            'pluginValues': {'map': json.dumps(m, ensure_ascii=False)}, 'start': True}
    return {'id': id, 'type': 'story', 'position': {'x': pos[0], 'y': pos[1]}, 'data': data}
