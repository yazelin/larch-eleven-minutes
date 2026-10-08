"""對話卡（序、審訊室）。lines：字串＝旁白、(講者, 文字)。"""


def dialogue(id, title, lines, pos, bg='', start=False, bgm=''):
    dl = [{'id': f'{id}-l{i}', 'speaker': (l if isinstance(l, tuple) else ('', l))[0], 'text': (l if isinstance(l, tuple) else ('', l))[1]}
          for i, l in enumerate(lines)]
    data = {'type': 'dialogue', 'title': title, 'speaker': dl[0]['speaker'], 'text': dl[0]['text'], 'dialogueLines': dl, 'stage': {'actors': []}}
    if bg: data['background'] = bg
    if bgm: data.update(bgm=bgm, bgmVolume=0.35, bgmLoop=True)
    if start: data['start'] = True
    return {'id': id, 'type': 'story', 'position': {'x': pos[0], 'y': pos[1]}, 'data': data}


def link(board, a, b):
    board['edges'].append({'id': f'{a}--{b}', 'source': a, 'target': b, 'sourceHandle': 'right', 'targetHandle': 'left'})


def battle(id, name, enemies, pos, skills=(), triggers=(), attack=14, defense=3, mp=20, bg='', bgm=''):
    """RPG 回合制戰鬥卡。enemies：[{id, name, hp, attack, defense, image?, specials?}]（1–4）；地圖事件用 battle 步驟（combat:"turn"）叫它。"""
    import json
    cfg = {'version': 1, 'name': name, 'heroName': '江凌', 'heroImage': '', 'heroPortrait': '', 'arena': 'ruins', 'backgroundImage': bg,
           'attack': attack, 'defense': defense, 'mp': mp, 'skillName': '', 'skillCost': 0, 'skillPower': 0, 'skills': list(skills),
           'enemies': [dict({'image': ''}, **e) for e in enemies], 'triggers': list(triggers),
           'style': 'painted', 'allowEscape': False, 'rewardItemId': '', 'rewardItemName': '', 'rewardCount': 0}
    data = {'type': 'plugin', 'title': name, 'text': '', 'pluginId': 'larch-rpg-system', 'pluginCardId': 'battle',
            'pluginVersion': '0.4.0', 'pluginName': 'RPG 系統', 'pluginCardName': 'RPG 回合制戰鬥', 'pluginIcon': 'swords', 'pluginColor': '#8f564a',
            'pluginPresentation': 'fullscreen', 'pluginSkippable': False, 'platforms': ['web'], 'pluginAssets': [],
            'pluginReadVars': ['rpgHp', 'inventory', 'rpgState', 'rpgEquipment'], 'pluginWriteVars': ['rpgHp', 'inventory', 'rpgState', 'rpgEquipment'],
            'pluginValues': {'battle': json.dumps(cfg, ensure_ascii=False)}}
    if bgm: data.update(bgm=bgm, bgmVolume=0.4, bgmLoop=True)
    return {'id': id, 'type': 'story', 'position': {'x': pos[0], 'y': pos[1]}, 'data': data}
