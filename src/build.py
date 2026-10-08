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


TITLE_STATUS = 'GFW · 23:47'
TITLE_SUB = next(l for l in (ROOT / 'canon/介紹文.md').read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')).strip()   # 介紹文第一句


def music(k):
    """配樂（art/music.py 產的，還沒產就空著）"""
    return f'/files/assets/bgm/{k}.mp3' if (ROOT / f'assets/bgm/{k}.mp3').exists() else ''


MAP_BGM = {'m-office': 'office', 'm-server': 'server', 'm-cloud': 'cloud'}


def scene(k):
    """對話卡背景（art/scene_gen.py 產的，還沒產就空著）"""
    return f'/files/assets/scenes/{k}.webp' if (ROOT / f'assets/scenes/{k}.webp').exists() else ''


VARS = {'phase': ('string', ''), 'kills': ('number', 0), 'wall': ('string', '')}   # 全部故事變數只在這裡定義


def database():
    hero = {'id': 'jiangling', 'name': '江凌', 'title': '', 'profile': '', 'role': 'party', 'walk': mapkit.walker('/files/assets/walk/walk-jiangling.png'),
            'portrait': '', 'join': 'later', 'kit': 'none', 'rig': '', 'joinVariable': '', 'speed': 2}   # 細格一步半格，速度加倍
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
    N(cards.dialogue('ci1', '審訊室（一）', section('審訊室（一）'), (400, 300), bg=scene('interrogation')))
    N(plugin.card_node((1200, 0)))
    N(cards.dialogue('ci2', '審訊室（二）', section('審訊室（二）'), (1600, 300), bg=scene('interrogation')))
    for i, (k, t) in enumerate(ENDINGS):
        N(cards.dialogue(k, t, [t] + section(t), (2000, i * 200), bg=scene(k), bgm=music('ending')))
        cards.link(board, k, 'credits')
    N(cards.dialogue('credits', '片尾', new('片尾'), (2400, 200), bg='/files/assets/cover/title.webp' if (ROOT / 'assets/cover/title.webp').exists() else ''))
    for n in battles.nodes(): N(n)
    cards.link(board, 'c0', 'm-office'); cards.link(board, plugin.NODE, 'm-cloud')
    test_start(p)
    return p


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
