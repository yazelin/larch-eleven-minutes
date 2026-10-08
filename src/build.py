"""組出 dist/project.json（本機 larch-preview 用）。目前只有十九樓的色塊驗證版。python3 src/build.py"""
import json, os, pathlib, shutil, sys
import layout, mapkit, cards, map_office
from story import section
ROOT = pathlib.Path(__file__).resolve().parent.parent
TITLE = '十一分鐘'


def skeleton():
    return {'schemaVersion': 1, 'id': 'project-cloudwar-local', 'name': TITLE, 'description': '', 'locale': 'zh-Hant',
            'languages': [{'code': 'zh-Hant', 'label': '繁體中文'}], 'nodes': [], 'edges': [], 'media': [], 'characters': [],
            'variables': [{'id': i, 'name': n, 'label': n, 'type': t, 'defaultValue': d} for i, n, t, d in mapkit.RPG_VARS]
                         + [{'id': k, 'name': k, 'label': k, 'type': t, 'defaultValue': d} for k, (t, d) in VARS.items()],
            'settings': {'resolution': {'width': 1920, 'height': 1080}, 'textSpeed': 32, 'typingEffect': True, 'autoAdvanceDelay': 1800,
                         'showRpgHud': False, 'aiMode': 'authored', 'plugins': {'larch-rpg-system': {'enabled': True, 'settings': {}}}},
            'boards': [{'id': 'main', 'name': '十一分鐘', 'description': '', 'kind': 'story', 'nodes': [], 'edges': []}],
            'activeBoardId': 'main'}


VARS = {'phase': ('string', '')}   # 全部故事變數只在這裡定義


def database():
    hero = {'id': 'jiangling', 'name': '江凌', 'title': '', 'profile': '', 'role': 'party', 'walk': mapkit.walker('/files/assets/walk/walk-jiangling.png'),
            'portrait': '', 'join': 'later', 'kit': 'none', 'rig': '', 'joinVariable': '', 'speed': 2}   # 細格一步半格，速度加倍
    return {'version': 1, 'heroId': 'jiangling', 'actors': [hero]}


def office_map():
    d = layout.load('office'); errs = layout.check(d)
    if errs: sys.exit('設計檔有問題：\n' + '\n'.join(errs))
    kind = 'blocks' if os.environ.get('BLOCKS') else 'objects'   # BLOCKS=1：單色塊驗證版
    urls = {o['name']: f"/files/assets/{kind}/office/{o['name']}.png" for o in layout.objects(d)}
    walk = lambda i: mapkit.walker(f'/files/assets/walk/walk-{i}.png')
    (hx, hy), npcs = map_office.events(walk)
    hero = mapkit.ev('hero', hx, hy, actor='player', direction='up', sprite=walk('jiangling'))
    m = mapkit.map_dict('十九樓　網管中心', d['map']['w'], d['map']['h'], f'/files/assets/maps/office_{"blocks" if kind == "blocks" else "ground"}.png', layout.walls(d),
                        [hero] + npcs + layout.events(d, urls), map_office.guidance())
    names = [n for _, n, _, _ in mapkit.RPG_VARS] + list(VARS)
    node = mapkit.map_node('m-office', '十九樓　網管中心', m, names, pos=(400, 0)); node['data'].pop('start')
    return node


def build():
    p = skeleton(); board = p['boards'][0]
    p['nodes'], p['edges'] = board['nodes'], board['edges']
    p['settings']['plugins']['larch-rpg-system']['settings']['database'] = json.dumps(database(), ensure_ascii=False)
    board['nodes'].append(cards.dialogue('c0', '序　審訊室', section('序　審訊室'), (0, 0), start=True))
    board['nodes'].append(office_map())
    board['nodes'].append(cards.dialogue('ci1', '審訊室（一）', section('審訊室（一）'), (400, 300)))
    cards.link(board, 'c0', 'm-office')
    return p


def main():
    out = ROOT / 'dist/project.json'; out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(build(), ensure_ascii=False))
    dst = out.parent / 'assets'; shutil.rmtree(dst, ignore_errors=True)   # serve.py 不給符號連結，複製一份進 dist
    shutil.copytree(ROOT / 'assets', dst)
    print('wrote', out)


if __name__ == '__main__':
    main()
