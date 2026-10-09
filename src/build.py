"""組出 dist/project.json（本機 larch-preview 用）。BLOCKS=1 換成單色塊驗證版；沒有正式圖的地圖自動用色塊。python3 src/build.py"""
import json, os, pathlib, shutil, sys
import layout, mapkit, cards, plugin, battles, map_office, map_server, map_cloud
from story import section, new
ROOT = pathlib.Path(__file__).resolve().parent.parent
TITLE = '十一分鐘'
PROJECT_ID = 'project-fc97ad09-681c-47f9-80b9-e12753877b9c'   # Larch 上的專案


def skeleton():
    return {'schemaVersion': 1, 'id': 'project-cloudwar-local', 'name': TITLE, 'description': '', 'locale': 'zh-Hant',
            'languages': [{'code': 'zh-Hant', 'label': '繁體中文'}], 'nodes': [], 'edges': [], 'media': [], 'characters': [],
            'variables': [{'id': i, 'name': n, 'label': n, 'type': t, 'defaultValue': d} for i, n, t, d in mapkit.RPG_VARS]
                         + [{'id': k, 'name': k, 'label': k, 'type': t, 'defaultValue': d} for k, (t, d) in VARS.items()],
            'settings': {'resolution': {'width': 1920, 'height': 1080}, 'textSpeed': 32, 'typingEffect': True, 'autoAdvanceDelay': 1800,
                         'showRpgHud': False, 'aiMode': 'authored', 'plugins': {'larch-rpg-system': {'enabled': True, 'settings': {}}}},
            'boards': [{'id': 'main', 'name': '十一分鐘', 'description': '', 'kind': 'story', 'nodes': [], 'edges': []}],
            'activeBoardId': 'main'}


def interface(p):
    """介面：作者在 Larch 套用的官方「霓虹訊號」（2026-10-09 從雲端讀回 src/ui/interface.json）。我們改過的部位寫在 src/ui/<部位>.css|html，蓋過原本的"""
    ui = json.loads((ROOT / 'src/ui/interface.json').read_text(encoding='utf-8'))
    for part, v in ui['customInterfaces'].items():
        for ext in ('css', 'html'):
            f = ROOT / f'src/ui/{part}.{ext}'
            if f.exists(): v['html'] = f.read_text(encoding='utf-8')
    keep = ('resolution', 'textSpeed', 'autoAdvanceDelay', 'typingEffect')   # 這幾個以本機為準
    p['settings'].update({k: v for k, v in ui.items() if k not in keep})
    # 2026-10-09 作者「依建議做齊」：標題狀態列換成故事的時間、副標用介紹文第一句（不然會顯示整段專案介紹）、封面
    p['settings']['customInterfaces']['title']['params'] = {'status': TITLE_STATUS, **({'bgm': music('title')} if music('title') else {})}
    p['settings']['titleScreen'] = {'layers': [{'id': 'skin-description', 'kind': 'text', 'role': 'description', 'x': 8, 'y': 44, 'size': 1.6,
                                                'width': 44, 'align': 'left', 'hidden': True, 'text': TITLE_SUB}]}
    if (ROOT / 'assets/cover/title.webp').exists(): p['settings']['titleCoverImage'] = '/files/assets/cover/title.webp'
    if (ROOT / 'assets/cover/thumb.webp').exists(): p['settings']['projectThumbnail'] = '/files/assets/cover/thumb.webp'   # 市集縮圖（art/thumb.py）
    # CG 收藏（10-09 作者：直接做）：霓虹訊號把它做成監視器牆，鎖住的顯示 NO SIGNAL。結局圖要打到那個結局才解鎖
    gallery = [('cover/title.webp', '十一分鐘', False), ('scenes/interrogation.webp', '審訊室', True), ('scenes/unchained.webp', '鎖開了', True),
               ('scenes/e1.webp', '送出', True), ('scenes/e2.webp', '交給 PRISM', True), ('scenes/e3.webp', '修回去', True)]
    p['settings'].update(cgGalleryEnabled=True, cgGallerySource='picked',
                         cgGalleryItems=[{'url': f'/files/assets/{f}', 'title': t, 'locked': lk} for f, t, lk in gallery if (ROOT / f'assets/{f}').exists()])


TITLE_STATUS = 'GFW · 23:49'
TITLE_SUB = next(l for l in (ROOT / 'canon/介紹文.md').read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')).strip()   # 介紹文第一句


VOICE = json.loads((ROOT / 'voice/manifest.json').read_text(encoding='utf-8')) if (ROOT / 'voice/manifest.json').exists() else {}   # 段落 → 配音檔（voice/gen.py）


def voiced(text):
    f = VOICE.get(text); return f'/files/assets/voice/{f}' if f and (ROOT / f'assets/voice/{f}').exists() else ''


SPLIT = {}   # 演在地圖上的對話卡 → 逐句拆開的卡 id（地圖播對話卡不放 voiceUrl，10-09 作者：審訊室年輕的開口沒播）


def split_card(cid, title, lines, bg):
    """一句一張卡（第一張沿用原 id），地圖上逐句播、每句前面插配音"""
    ids = [cid] + [f'{cid}-{i}' for i in range(1, len(lines))]; SPLIT[cid] = ids
    return [cards.dialogue(i, title if k == 0 else f'{title}（{k + 1}）', [l], (0, 0), bg=bg) for k, (i, l) in enumerate(zip(ids, lines))]


def voice_actions(acts, cardtext=None):
    """地圖上的對話：有配音的那句前面插 sound 步驟（引擎的地圖對話沒有語音欄位）；拆過的對話卡展開成逐句"""
    out = []
    for a in acts:
        if a.get('choice'):
            for o in a['choice']['options']: o['actions'] = voice_actions(o['actions'], cardtext)
        if a['kind'] == 'dialogue' and a.get('cardId') in SPLIT:
            for i in SPLIT[a['cardId']]:
                u = voiced(cardtext[i]) if cardtext else ''
                if u: out.append(mapkit.A('sound', audio={'url': u, 'volume': 0.9}, label='配音'))
                out.append(dict(a, id=mapkit.A('x')['id'], cardId=i))
            continue
        u = voiced(a.get('text', '')) if a['kind'] == 'dialogue' else ''
        if u: out.append(mapkit.A('sound', audio={'url': u, 'volume': 0.9}, label='配音'))
        out.append(a)
    return out


def music(k):
    """配樂（art/music.py 產的，還沒產就空著）"""
    return f'/files/assets/bgm/{k}.mp3' if (ROOT / f'assets/bgm/{k}.mp3').exists() else ''


MAP_BGM = {'m-office': 'office', 'm-server': 'server', 'm-cloud': 'cloud'}


def scene(k):
    """對話卡背景（art/scene_gen.py 產的，還沒產就空著）"""
    return f'/files/assets/scenes/{k}.webp' if (ROOT / f'assets/scenes/{k}.webp').exists() else ''


VARS = {'phase': ('string', ''), 'kills': ('number', 0), 'wall': ('string', ''), 'eye': ('string', ''), 'guard_at': ('string', ''), 'zhou_look': ('string', ''), 'sneaking': ('string', ''), 'guard_dir': ('string', ''), 'leg': ('string', '0')}   # 全部故事變數只在這裡定義


def database():
    hero = {'id': 'jiangling', 'name': '江凌', 'title': '', 'profile': '', 'role': 'party', 'walk': mapkit.walker('/files/assets/walk/walk-jiangling.png'),
            'portrait': '/files/assets/battle/jiangling-face.webp', 'join': 'later', 'kit': 'none', 'rig': '', 'joinVariable': '', 'speed': 2,
            'attack': 'magic', 'battleArt': '/files/assets/battle/jiangling.webp', 'battlePainted': True}   # 回合制戰鬥的立繪：引擎拿資料庫主角的 battleArt，會蓋掉戰鬥卡上的 heroArt   # 大地圖普攻：magic（10-09 作者：不要拳頭，也不要顯示劍）   # 細格一步半格，速度加倍
    return {'version': 1, 'heroId': 'jiangling', 'actors': [hero]}


MAPS = [  # (地圖 id、設計檔、模組、標題、白板位置)
    ('m-office', 'office', map_office, '十九樓　網管中心', (400, 0)),
    ('m-server', 'server', map_server, '二十樓　核心機房', (800, 0)),
    ('m-cloud', 'cloud', map_cloud, '防火長城', (1600, 0)),
]


def map_card(mid, a, mod, title, pos):
    d = layout.load(a); errs = layout.check(d)
    if errs: sys.exit(f'{a} 設計檔有問題：\n' + '\n'.join(errs))
    real = not os.environ.get('BLOCKS') and (ROOT / f'assets/maps/{a}_ground.png').exists() and \
        all((ROOT / f"assets/objects/{a}/{o['name']}.png").exists() for o in layout.objects(d))   # 地面與每個物件都產好了才換正式圖，不然用色塊
    kind = 'objects' if real else 'blocks'
    urls = {o['name']: f"/files/assets/{kind}/{a}/{o['name']}.png" for o in layout.objects(d)}
    walk = lambda i: mapkit.walker(f'/files/assets/walk/walk-{i}.png')
    (hx, hy), evs = mod.events(walk)
    hero = mapkit.ev('hero', hx, hy, actor='player', direction='up', sprite=walk('jiangling'))
    # 區域名牌：看不見的事件掛名牌，沒有動作（設計檔 labels）
    evs += [mapkit.ev(f'label-{i}', x, y, name=n.strip(), marker={'label': n.strip(), 'kind': 'talk'}) for i, (n, (x, y)) in enumerate(d.get('labels', {}).items())]
    m = mapkit.map_dict(title, d['map']['w'], d['map']['h'], f'/files/assets/maps/{a}_{"ground" if real else "blocks"}.png', layout.walls(d),
                        [hero] + evs + layout.events(d, urls, getattr(mod, 'wall_conditions', lambda n: [])), mod.guidance())
    lights = getattr(mod, 'return_lights', [])
    if lights: m['environment'] = {'weather': 'clear', 'intensity': 0, 'darkness': 0.35, 'shake': 0, 'lights': lights}   # 十九樓：燈只開一半、警衛手電筒；室內不下雨（雨畫在落地窗外，10-09 作者：內建雨太整齊）
    if mod is map_cloud: m['combat'] = 'action'
    names = [n for _, n, _, _ in mapkit.RPG_VARS] + list(VARS)
    node = mapkit.map_node(mid, title, m, names, pos=pos, bgm=music(MAP_BGM[mid])); node['data'].pop('start')
    return node


ENDINGS = [('e1', '結局一　送出'), ('e2', '結局二　交給 PRISM'), ('e3', '結局三　修回去')]


def build():
    p = skeleton(); board = p['boards'][0]; interface(p)
    p['nodes'], p['edges'] = board['nodes'], board['edges']
    p['settings']['plugins']['larch-rpg-system']['settings']['database'] = json.dumps(database(), ensure_ascii=False)
    p['settings']['plugins'][plugin.PLUGIN_ID] = plugin.settings_entry()
    N = board['nodes'].append
    N(cards.dialogue('c0', '序　審訊室', section('序　審訊室'), (0, 0), bg=scene('interrogation'), start=True, bgm=music('title')))
    for m in MAPS: N(map_card(*m))
    for nd in split_card('ci1', '審訊室（一）', section('審訊室（一）'), scene('interrogation')): N(nd)
    N(plugin.card_node((1200, 0)))
    N(cards.dialogue('cu', '鎖開了', section('五　23:49')[0:2], (4, 0), bg=scene('unchained')))   # 大肥魚解開鎖鏈的 CG，演在雲端地圖上（10-09 作者）
    for nd in split_card('ci2', '審訊室（二）', section('審訊室（二）'), scene('interrogation')): N(nd)
    for i, (k, t) in enumerate(ENDINGS):
        N(cards.dialogue(k, t, [t] + section(t), (2000, i * 200), bg=scene(k), bgm=music('ending')))
        cards.link(board, k, 'credits')
    N(cards.dialogue('credits', '片尾', new('片尾'), (2400, 200), bg='/files/assets/cover/title.webp' if (ROOT / 'assets/cover/title.webp').exists() else ''))
    for n in battles.nodes(): N(n)
    # CG 解鎖（10-09 作者問什麼時候解鎖）：看到序章解鎖審訊室，進哪個結局解鎖那張
    # 審訊室掛在開場卡上實測不會解鎖（開始卡不跑 cgOps）→ 改成每個結局一起解鎖審訊室與那個結局
    for nid in ('e1', 'e2', 'e3'):
        fs = ['scenes/interrogation.webp', 'scenes/unchained.webp', f'scenes/{nid}.webp']   # 鎖開了那張演在地圖上（地圖不跑 cgOps），結局時一起解鎖
        next(n for n in board['nodes'] if n['id'] == nid)['data']['cgOps'] = [{'id': f'cg-{nid}-{i}', 'mode': 'unlock', 'url': f'/files/assets/{f}'} for i, f in enumerate(fs) if (ROOT / f'assets/{f}').exists()]
    cards.link(board, 'c0', 'm-office'); cards.link(board, plugin.NODE, 'm-cloud')
    # 片尾之後：第二章＝內嵌公開站（照《起跑總在開始前》的做法；10-09 作者）
    N({'id': 'to-site', 'type': 'story', 'position': {'x': 0, 'y': 0}, 'data': {
        'type': 'boardJump', 'title': '前往第二章', 'text': '', 'jumpBoardId': SITE_BOARD, 'jumpNodeId': 'site'}})
    cards.link(board, 'credits', 'to-site')
    p['boards'].append(site_board())
    cardtext = {n['id']: n['data']['dialogueLines'][0]['text'] for n in board['nodes'] if n['data'].get('dialogueLines')}
    for n in board['nodes']:   # 地圖：配音 sound 步驟、拆開的對話卡（要等全部卡片都建好）
        if n['data'].get('pluginCardId') != 'map': continue
        m = json.loads(n['data']['pluginValues']['map'])
        for e in m['events']:
            e['actions'] = voice_actions(e.get('actions', []), cardtext)
            for pg in e.get('pages', []): pg['actions'] = voice_actions(pg['actions'], cardtext)
        n['data']['pluginValues']['map'] = json.dumps(m, ensure_ascii=False)
    for n in board['nodes']:   # 對話卡：每一句掛 voiceUrl
        for l in n['data'].get('dialogueLines', []):
            u = voiced(l['text'])
            if u: l['voiceUrl'] = u
    layout_board(board)
    test_start(p)
    return p


SITE_BOARD = 'board-site'
SITE_URL = 'https://yazelin.github.io/larch-eleven-minutes/'


def site_board():
    """第二章：全螢幕小遊戲卡，用 iframe 嵌入公開站。看完按「略過」結束"""
    shell = ('<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
             '<style>html,body{margin:0;height:100%;background:#05070d}iframe{width:100%;height:100%;border:0;display:block}</style>'
             f'<iframe src="{SITE_URL}" allow="fullscreen; autoplay"></iframe>'
             "<script>parent.postMessage({type:'larch:ready'},'*');</script></html>")
    n = {'id': 'site', 'type': 'story', 'position': {'x': 100, 'y': 200}, 'data': {
        'type': 'miniGame', 'title': '第二章・幕後與原聲帶', 'text': '作品介紹、人物、時間線、CG、六首原聲帶。看完按「略過」結束。',
        'miniGameHtml': shell, 'miniGamePresentation': 'fullscreen', 'miniGameSkippable': True,
        'miniGameReadVars': [], 'miniGameWriteVars': [], 'miniGameNote': f'薄殼而已，內容在 {SITE_URL}',
        'start': True, 'voiceMode': 'off', 'stage': {'actors': []}}}
    return {'id': SITE_BOARD, 'kind': 'story', 'mode': 'story', 'name': '第二章・幕後與原聲帶', 'description': '', 'nodes': [n], 'edges': []}


# 白板排版（10-09 作者：好好排版）：上面一排是玩家走的主線（左到右），
# 主線底下是演在那張地圖上的卡（審訊室一、二），王戰的戰鬥卡排在雲端長城底下，結局三張直排、片尾在最右。
X, Y = 460, 300
BOARD_POS = {   # 群組框之間留空（10-09：框重疊）
    'c0': (0, 0), 'm-office': (1, 0), 'm-server': (2, 0), 'c-term': (3, 0),
    'm-cloud': (4.4, 0), 'cu': (4.4, 1.2), 'ci2': (5.2, 1.2),
    'e1': (6.6, -1), 'e2': (6.6, 0), 'e3': (6.6, 1), 'credits': (7.6, 0), 'to-site': (8.6, 0),
    'ci1': (1, 1.2),
    'b-censor': (3.4, 5.6), 'b-hound': (3.4, 6.6), 'b-w1': (4.4, 5.6), 'b-w2': (4.4, 6.6), 'b-whale': (5.4, 5.6), 'b-prism': (5.4, 6.6),
}


# 群組框（10-09 作者：白板上地圖之間沒有連線不好讀）：群組只是整理用的框，不進遊戲流程；子卡座標相對群組
GROUPS = [('g-real', '現實層：審訊室倒敘、十九樓、二十樓（地圖之間用事件跳轉，沒有連線；審訊室一句一張卡，地圖上逐句播配音）', '#4a6b7a', ['c0', 'm-office', 'm-server', 'c-term', 'ci1']),
          ('g-cloud', '雲端層：防火長城（鎖開了、審訊室（二）演在地圖上）', '#6b4a7a', ['m-cloud', 'cu', 'ci2']),
          ('g-end', '三個結局與片尾（審訊室（二）之後的選擇跳過來；片尾接第二章：內嵌公開站）', '#7a5a4a', ['e1', 'e2', 'e3', 'credits', 'to-site']),
          ('g-battle', '戰鬥卡（雲端地圖的事件叫它們，不在白板流程上）', '#5a5a5a', ['b-censor', 'b-hound', 'b-w1', 'b-w2', 'b-whale', 'b-prism'])]
CW, CH, PAD, HEAD = 310, 220, 50, 70


def layout_board(board):
    for cid, ids in SPLIT.items():   # 拆開的對話卡排在原卡底下一直列
        bx, by = BOARD_POS[cid]
        for k, i in enumerate(ids[1:], 1): BOARD_POS[i] = (bx, by + k * 0.8)
    for n in board['nodes']:
        if n['id'] in BOARD_POS:
            gx, gy = BOARD_POS[n['id']]; n['position'] = {'x': round(gx * X), 'y': round(gy * Y)}
    missing = [n['id'] for n in board['nodes'] if n['id'] not in BOARD_POS]
    assert not missing, f'白板排版沒寫到：{missing}'
    by = {n['id']: n for n in board['nodes']}; groups = []
    for gid, title, color, kids in GROUPS:
        kids = kids + [i for k in kids for i in SPLIT.get(k, [])[1:]]   # 拆開的卡跟原卡同一個群組
        xs = [by[k]['position']['x'] for k in kids]; ys = [by[k]['position']['y'] for k in kids]
        gx, gy = min(xs) - PAD, min(ys) - PAD - HEAD
        w, h = max(xs) - min(xs) + CW + 2 * PAD, max(ys) - min(ys) + CH + 2 * PAD + HEAD
        groups.append({'id': gid, 'type': 'story', 'position': {'x': gx, 'y': gy}, 'width': w, 'height': h,
                       'data': {'type': 'group', 'title': title, 'text': '', 'groupColor': color, 'groupCollapsed': False}})
        for k in kids:
            by[k]['parentId'] = gid; by[k]['position'] = {'x': by[k]['position']['x'] - gx, 'y': by[k]['position']['y'] - gy}
    board['nodes'][:0] = groups   # 群組要排在子卡前面


def test_start(p):
    """測試用：START=<卡片 id> 從那張卡開始；PRESET=phase=gate,kills=4 改變數初始值（tests/play_*.mjs 用）"""
    if os.environ.get('START'):
        for n in p['nodes']: n['data'].pop('start', None)
        next(n for n in p['nodes'] if n['id'] == os.environ['START'])['data']['start'] = True
    for kv in filter(None, os.environ.get('PRESET', '').split(',')):
        k, v = kv.split('=')
        next(x for x in p['variables'] if x['name'] == k)['defaultValue'] = int(v) if v.isdigit() else v


def main():
    out = ROOT / 'dist/project.json'; out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(build(), ensure_ascii=False))
    dst = out.parent / 'assets'; shutil.rmtree(dst, ignore_errors=True)   # serve.py 不給符號連結，複製一份進 dist
    shutil.copytree(ROOT / 'assets', dst)
    print('wrote', out)


if __name__ == '__main__':
    main()
