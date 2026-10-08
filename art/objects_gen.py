"""分層地圖：照設計檔產「純地面底圖」與「每種物件一張」（做法照《香布纏．續》xu/game/art/objects_gen.py）。
- 物件：純色幕單獨生成，image 1＝畫風定錨（art/style/<a>_style_v1.png）上那個物件附近的裁切（畫風、俯角、外觀）。
  去背後裁到不透明範圍，縮進圖框（frame w×h 格 × 48px），下緣貼齊圖框下緣、水平置中；一長排的段寬度拉滿。
- 綠色的東西（盆栽、逃生標誌）改用洋紅幕，避免去背把主體吃掉。
- 地面：art/compose.py 的地面色塊當構圖，定錨圖當畫風，生成後縮放到 W×H 格 × 48px。
用法：python3 art/objects_gen.py gen office [種類…] [--redo]
      python3 art/objects_gen.py ground office
      python3 art/objects_gen.py lines office [tea boss south fire glasscol whitecol]   → 整排的牆（產原圖）
      python3 art/objects_gen.py cut office      → assets/objects/office/<物件名>.png
      python3 art/objects_gen.py sheet office    → art/check/objgen-office.jpg"""
import glob, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path[:0] = [os.path.join(G, 'src'), H]
import layout, blocks, codex11   # 產圖走 .11（作者 2026-10-08）；本機 codex 只用過第一批十九樓

PX = 48
LOOK = {   # 每張地圖的畫風描述（定錨圖、物件、地面、整排的牆共用）
    'office': 'cyberpunk night office with cyan and magenta accents',
    'server': 'cold server room at night, rows of black server racks with blinking green lights, cyan and magenta neon accents',
    'cloud': 'a sea of grey-blue clouds under a black sky inside a digital world, a colossal wall of dark-red neon chain links, cyan grid lines, magenta accents',
}
FLOOR = {
    'office': 'night office, half of the ceiling lights on so the floor has alternating lit and dark bands, cool cyan accents',
    'server': 'cold server room, grey anti-static raised floor tiles, some perforated vent tiles glowing faint blue, cyan accents',
    'cloud': 'a soft sea of grey-blue clouds seen from above with faint cyan grid lines floating in it; the strip at the top is brighter blue-white sky clouds beyond the wall',
}
RAW = os.path.join(H, 'objgen_raw')
CUTOUT = os.path.expanduser('~/.claude/skills/cutout/cutout.py')
SEG = ("This is one section cut out of a long continuous row of the same thing: both left and right ends are cut straight off "
       "(several sections will be joined side by side), no corners, no end caps, same height and top outline at both ends; "
       "the object fills the full width of the image (only a very thin margin of background left and right).")

# 種類 → (圖框寬, 高, 佔地深, 描述, 一長排的段, 幕色)。圖框尺寸要跟設計檔一致（cut 時會檢查）
TYPES = {
    'window': (8, 3, 1, 'a floor-to-ceiling office window wall: grey aluminium frames dividing tall glass panes, rainy night city skyline with lit windows and rain streaks visible through the glass, a low dark sill at the bottom', True, 'green'),
    'bosswall': (11, 3, 1, 'a floor-to-ceiling office window wall with half-closed horizontal blinds, rainy night city lights behind, grey aluminium frames', True, 'green'),
    'glasscol': (1, 4, 1, 'one narrow section of a frosted glass office partition seen edge-on from the side: a thin vertical aluminium post with a sliver of frosted glass, tall and slender', False, 'green'),
    'glasswall': (6, 4, 1, 'a frosted glass office partition wall with slim aluminium frames, the glass slightly translucent pale blue, a darker aluminium base rail', True, 'green'),
    'glassdoor': (2, 4, 1, 'a glass office door frame with the glass door standing slightly ajar; the doorway in the middle is open and empty so the background shows through it; aluminium frame and handle', False, 'green'),
    'bossdesk': (5, 3, 2, 'a big dark executive wooden desk: a computer monitor, a desk lamp, a phone, and a neat stack of evaluation forms on top; drawers on the front (south) side', False, 'green'),
    'bosschair': (1, 2, 1, 'a black high-back leather executive office chair, seen from behind', False, 'green'),
    'bookshelf': (1, 6, 3, 'a tall narrow wooden bookshelf full of binders, standing against a wall, seen from the side so it looks tall and slim', False, 'green'),
    'desk': (6, 4, 2, 'an open-plan office workstation cluster: two rows of desks facing each other, each with dual glowing cyan monitors, keyboards, low grey partitions between them, black office chairs tucked in on both sides', False, 'green'),
    'deskjiang': (6, 4, 2, 'an open-plan office workstation cluster: two rows of desks facing each other with low grey partitions and black chairs; the seat on the south side in the middle has three glowing monitors (the middle one shows a blue map-like monitoring screen), a cup of instant noodles and a small green plastic toy dinosaur', False, 'magenta'),
    'pillar': (1, 6, 1, 'a square white office support pillar, floor to ceiling, with a small red poster on it (no readable text)', False, 'green'),
    'copier': (2, 3, 1, 'a large office photocopier with a small glowing green status light', False, 'magenta'),
    'plant': (3, 4, 1, 'a potted money tree with lush green leaves in a white pot', False, 'magenta'),
    'whitewall': (6, 4, 1, 'a white interior partition wall with a thin grey skirting at the bottom', True, 'green'),
    'whitecol': (1, 4, 1, 'one narrow section of a white interior partition wall seen edge-on from the side: a tall thin white wall end', False, 'green'),
    'counter': (6, 4, 2, 'an office pantry counter: white countertop with a sink and tap, an electric kettle, a microwave, cabinets below, white tiled backsplash', False, 'green'),
    'fridge': (2, 5, 2, 'a tall white two-door refrigerator', False, 'green'),
    'greywall': (10, 4, 1, 'a grey office corridor wall with a small recessed ceiling light glow at the top and a dark skirting at the bottom', True, 'green'),
    'elevator': (12, 5, 2, 'an elevator lobby wall with two silver stainless steel elevator doors, call buttons between them, a small floor indicator above each door (no readable text), beige stone wall panels', False, 'green'),
    'firedoor': (2, 4, 1, 'a dark grey steel fire exit door frame with the door open into darkness (the doorway is empty so the background shows through), a glowing green running-man exit sign above it (no text)', False, 'magenta'),
    # 二十樓（m-server）
    'crac': (3, 4, 1, 'a white precision air conditioning unit for a server room standing against the wall, front grille vents, a small status display glowing cyan', False, 'green'),
    'rack': (8, 5, 1, 'a long row of tall black server racks side by side, mesh front doors, rows of tiny blinking green and cyan status lights, cable bundles', False, 'magenta'),   # 整張縮進框（10-09 作者：機櫃被切掉）
    'terminal': (3, 3, 1, 'a plain steel desk with one black computer monitor showing only a single green text cursor, a keyboard, and a sleek black VR helmet resting beside it', False, 'magenta'),
    # 雲端長城（m-cloud）
    'mound1': (6, 4, 2, 'a small hill made of thousands of dim grey glowing dots piled up (each dot is a captured message), soft and loose like sand, faint grey glow', False, 'magenta'),
    'mound2': (7, 4, 2, 'a hill made of thousands of dim grey glowing dots piled up (each dot is a captured message), soft and loose like sand, faint grey glow', False, 'magenta'),
    'mound3': (7, 5, 2, 'the biggest hill made of thousands of dim grey glowing dots piled up (captured messages), and halfway up one single dot glowing faintly white and flickering', False, 'magenta'),
    'cloudpillar': (2, 5, 1, 'a pillar made of condensed grey-blue cloud with streams of cyan data light flowing up inside it', False, 'magenta'),
}


def type_of(o):
    n, k = o['name'], o['kind']
    if n.startswith('空調'): return 'crac'
    if n.startswith('機櫃'): return 'rack'
    if n == '終端機': return 'terminal'
    if n.startswith('光點山'): return 'mound' + str('一二三'.index(n[-1]) + 1)
    if n.startswith('雲柱'): return 'cloudpillar'
    if n.startswith('北窗'): return 'window'
    if n == '主任室北牆': return 'bosswall'
    if n.startswith('主任室西牆'): return 'glasscol'
    if n.startswith('主任室南牆'): return 'glasswall'
    if n.startswith('茶水間東牆'): return 'whitecol'
    if n.startswith('茶水間牆'): return 'whitewall'
    if n.startswith('南牆'): return 'greywall'
    return {'主任室門': 'glassdoor', '主任辦公桌': 'bossdesk', '主任椅': 'bosschair', '主任書櫃': 'bookshelf', '江凌工位': 'deskjiang',
            '印表機': 'copier', '盆栽': 'plant', '流理台': 'counter', '冰箱': 'fridge', '電梯': 'elevator', '樓梯門': 'firedoor'}.get(n) or \
           {'工位': 'desk', '柱': 'pillar'}[k]


def anchor(a):
    return os.path.join(H, f'style/{a}_style_v1.png')


def crop_ref(a, d, o):
    """定錨圖上這個物件附近的裁切（定錨圖整張對應整張地圖）"""
    im = Image.open(anchor(a)).convert('RGB'); W, Hh = d['map']['w'], d['map']['h']; sx, sy = im.width / W, im.height / Hh
    fx, fy, fw, fh = o['frame']; m = 2
    box = (max(0, (fx - m) * sx), max(0, (fy - m) * sy), min(im.width, (fx + fw + m) * sx), min(im.height, (fy + fh + m) * sy))
    os.makedirs(RAW, exist_ok=True); out = os.path.join(RAW, f"ref-{a}-{o['name']}.png")   # 用物件名（整排的牆沒有種類）
    im.crop(tuple(map(int, box))).save(out); return out


def prompt(t, a='office'):
    w, h, dd, desc, seg, key = TYPES[t]
    bg = '#00FF00 pure green' if key == 'green' else '#FF00FF pure magenta'
    p = (f"Game map object sprite, one single object only. Match the art style of image 1 exactly: image 1 is a crop of the same pixel-art game map "
         f"(16-bit style pixel art, crisp pixels, {LOOK[a]}), the same 3/4 top-down camera from the south "
         f"(about 50 degrees, showing the top and the south-facing front), the same lighting from the top left. Redraw the object cleanly and completely as a standalone sprite.\n"
         f"Draw: {desc}.\n"
         f"Proportions: the object's bounding box is {w} cells wide and {h} cells tall (width:height = {w}:{h}); the bottom {dd} cells are its footprint on the floor, "
         f"the top {h - dd} cells are the part rising up.\n")
    if seg: p += SEG + "\n"
    p += (f"Draw only this object: no floor, no cast shadow on the floor, no people, no other objects. Clean edges, no glow halo spilling outside the object.\n"
          f"Background: a completely flat opaque {bg} fill, no gradient, no shadow. No text, no letters, no watermark.")
    return p


def raw_path(a, t): return os.path.join(RAW, f'obj-{a}-{t}.png')


def gen(a, only=(), redo=False):
    d = layout.load(a); jobs = {}
    skip = {n for v in LINES_BY[a].values() for n in v['objs']}
    for o in layout.objects(d):
        if o['name'] in skip or any(o['name'].startswith(v['prefix']) for v in COLS_BY[a].values()): continue   # 整排的牆另外產（lines_gen）
        t = type_of(o)
        if (only and t not in only) or t in jobs or (not redo and os.path.exists(raw_path(a, t))): continue
        jobs[t] = crop_ref(a, d, o)
    def run(t):
        try: codex11.gen(prompt(t, a), raw_path(a, t), [jobs[t]], size='1024x1536' if TYPES[t][1] > TYPES[t][0] else '1536x1024'); print(t, 'ok', flush=True)
        except Exception as e: print(t, 'FAIL', e, flush=True)
    print(len(jobs), '張')
    with ThreadPoolExecutor(4) as ex: list(ex.map(run, jobs))


def style(a):
    """整張地圖的畫風定錨：色塊構圖（art/compose.py）＋十九樓的定錨當畫風 → art/style/<a>_style_v1.png；之後物件與地面都裁這張當參考"""
    subprocess.run([sys.executable, os.path.join(H, 'compose.py'), a], check=True, capture_output=True)
    d = layout.load(a); objs = '; '.join(f"{o['name']}: {o.get('desc', '')}" for o in d['objects'])
    p = (f"A complete top-down pixel-art game map. Follow EXACTLY the layout of image 1: each flat colour block is one thing, the darker block is its footprint on the floor and "
         f"the lighter block above it is the part rising up (seen from the south at about 50 degrees, so tall things show their south-facing front). "
         f"Match the art style of image 2 exactly (the same game, 16-bit pixel art, crisp pixels, the same camera angle and lighting). This map: {LOOK[a]}. "
         f"Floor: {FLOOR[a]}. Things on the map: {objs}. No people, no text, no letters, no UI.")
    out = anchor(a); codex11.gen(p, out, [os.path.join(G, f'art/check/compose-{a}.png'), anchor('office')], size='1536x1024'); print('style ok', out)


def ground(a):
    """地面：只有地面色塊的構圖 → 生成 → 縮放成 W×H 格"""
    d = layout.load(a); W, Hh = d['map']['w'], d['map']['h']; S = 32
    im = Image.new('RGB', (W * S, Hh * S)); dr = ImageDraw.Draw(im)
    for g in d['ground']:
        for x, y, w, h in g['rects']: dr.rectangle((x * S, y * S, (x + w) * S - 1, (y + h) * S - 1), fill=blocks.GROUND[g['kind']])
    os.makedirs(RAW, exist_ok=True); lay = os.path.join(RAW, f'ground-layout-{a}.png'); im.save(lay)
    desc = '; '.join(f"{g['name']}: {g.get('desc', '')}" for g in d['ground'] if g['kind'] != 'border')
    p = ("Top-down pixel-art game map floor texture only, following exactly the color-region layout of image 1 (each flat color is one floor material). "
         f"Match the art style, palette and lighting of image 2 exactly (16-bit pixel art, {FLOOR[a]}). "
         f"Floor materials: {desc}. The dark outer frame is the building's outer wall top, draw it as a dark wall edge. "
         "Draw ONLY the floor surfaces: no furniture, no walls rising up, no desks, no doors, no people, no objects at all. No text.")
    out = os.path.join(RAW, f'ground-{a}.png')
    codex11.gen(p, out, [lay, anchor(a)], size='1536x1024')
    Image.open(out).convert('RGB').resize((W * PX, Hh * PX), Image.LANCZOS).save(os.path.join(G, f'assets/maps/{a}_ground.png'))
    print('ground ok')


def key_out(src, key):
    out = src.replace('.png', '-key.png')
    subprocess.run([sys.executable, CUTOUT, 'key', src, '-o', out, '--key', key, '--fuzz', '18', '--erode', '2', '--band', '0'], check=True, capture_output=True)
    im = Image.open(out).convert('RGBA'); os.remove(out)
    return im.crop(im.getbbox())


def seg_slice(fig, fw, fh, idx):
    sw = round(fig.height * fw / fh)
    if sw >= fig.width: return fig
    span = fig.width - sw; x0 = (idx * sw) % (span + 1)
    return fig.crop((x0, 0, x0 + sw, fig.height))


def fit(fig, fw, fh, fill_w=False):
    """縮進圖框：等比（一長排的段寬度拉滿）；下緣貼齊、水平置中。像素風用 NEAREST 不糊"""
    W, Hh = fw * PX, fh * PX
    s = W / fig.width if fill_w else min(W / fig.width, Hh / fig.height)
    nw, nh = max(1, round(fig.width * s)), max(1, round(fig.height * s))
    f = fig.resize((nw, nh), Image.LANCZOS)
    if nh > Hh: f = f.crop((0, nh - Hh, nw, nh)); nh = Hh
    c = Image.new('RGBA', (W, Hh)); c.alpha_composite(f, ((W - nw) // 2, Hh - nh)); return c


def cut(a):
    d = layout.load(a); od = os.path.join(G, f'assets/objects/{a}'); os.makedirs(od, exist_ok=True)
    for f in glob.glob(os.path.join(od, '*.png')): os.remove(f)
    cache, alt = {}, {}
    for o in layout.objects(d):
        if o['name'] in {n for v in LINES_BY[a].values() for n in v['objs']} or any(o['name'].startswith(v['prefix']) for v in COLS_BY[a].values()): continue   # 整排的牆另外切（lines_cut）
        t = type_of(o); fx, fy, fw, fh = o['frame']; tw, th, *_ = TYPES[t]
        if not TYPES[t][4] and (fw, fh) != (tw, th): raise SystemExit(f"{o['name']} 圖框 {fw}×{fh} 跟種類 {t} 的 {tw}×{th} 不一致")
        if t not in cache:
            if not os.path.exists(raw_path(a, t)): raise SystemExit(f'缺 {t} 的產圖')
            cache[t] = key_out(raw_path(a, t), TYPES[t][5])
        fig = cache[t]; alt[t] = alt.get(t, 0) + 1
        if TYPES[t][4]: fig = seg_slice(fig, fw, fh, alt[t] - 1)
        fit(fig, fw, fh, fill_w=TYPES[t][4]).save(os.path.join(od, f"{o['name']}.png"))
    if all(os.path.exists(os.path.join(RAW, f'line-{a}-{k}.png')) for k in list(LINES_BY[a]) + list(COLS_BY[a])): lines_cut(a)
    print(od, len(layout.objects(d)), '個物件')


# ── 整排的牆（2026-10-09 作者：牆和門接不起來 → 照《續》嚴家 LINES）──
# 同一排的牆連門洞／電梯／門整排一張生成：牆延伸到畫面兩端不收邊，門在正中間；
# 切的時候縮到牆高＝圖框高、門洞中心對上設計的門洞欄，外側五分之一的牆鏡射接長到整排，再照各段圖框切。
# fire 那排的牆腳接在 south 那排上，接縫在 blend 那兩格交叉淡入。
LINES = {
    'tea': dict(objs=['茶水間牆西', '茶水間牆東'], gap=(8, 9), ref='茶水間牆西',
                desc='a white interior office partition wall with a thin grey skirting at the bottom; in the middle an open doorway with no door '
                     '(the doorway is empty and see-through, showing the background), slim white door jambs on both sides of the doorway'),
    'boss': dict(objs=['主任室南牆西', '主任室門', '主任室南牆東'], gap=(38, 39), ref='主任室門',
                 desc='a frosted pale-blue glass office partition wall with slim aluminium frames and a dark aluminium base rail; in the middle a glass door '
                      'swung fully open and folded flat against the partition beside the doorway, so the doorway itself is empty and see-through (showing the background)'),
    'south': dict(objs=['南牆茶水間', '南牆西', '電梯', '南牆中'], center=24, ref='電梯',
                  desc='a grey office corridor wall with a dark skirting at the bottom; in the middle, set into the same wall and the same height as the wall, '
                       'two silver stainless steel elevator doors with call buttons between them and a small floor indicator above each door (no readable text)'),
    'fire': dict(objs=['樓梯門', '南牆東'], gap=(40, 41), ref='樓梯門', base='south', blend=(36, 38),
                 desc='a grey office corridor wall with a dark skirting at the bottom (exactly the same wall as image 2); in the middle a dark grey steel fire exit door '
                      'set into the wall, the door open into darkness so the doorway is empty and see-through (showing the background), a glowing green running-man '
                      'exit sign above it (no text)', key='magenta'),
}
COLS = {   # 直的牆：整條一張，一格一格切（最下面那格帶著牆朝南的端面）
    'glasscol': dict(prefix='主任室西牆', desc='a frosted pale-blue glass office partition with slim aluminium frames'),
    'whitecol': dict(prefix='茶水間東牆', desc='a white interior office partition wall with a thin grey skirting'),
}
LINES_OFFICE, COLS_OFFICE = LINES, COLS
LINES_BY = {
    'office': LINES_OFFICE,
    'server': {
        'north': dict(objs=['北牆西', '北牆中', '北牆東'], center=16, ref='北牆中',
                      desc='a grey concrete server room wall with a metal cable tray running along the top and a row of small red warning lights, a dark skirting at the bottom; plain wall, nothing in the middle'),
        'south': dict(objs=['南牆西', '鐵門', '南牆東'], center=5.5, ref='鐵門',
                      desc='a low grey concrete wall (seen as a short wall near the camera); near the middle a heavy closed grey steel security door set into the same wall, a card reader with a red light beside it'),
    },
    'cloud': {
        'wall': dict(objs=['長城一', '長城二', '長城三', '長城門', '長城四', '長城五', '長城六'], center=28, ref='長城門',
                     desc='the Great Firewall: a colossal wall built from giant dark iron chain links lying stacked on top of each other, each link glowing dark-red neon along its edges, '
                          'as tall as a building; in the middle a tall closed iron gate set into the chain wall with a large padlock symbol glowing on it'),
    },
}
COLS_BY = {'office': COLS_OFFICE, 'server': {}, 'cloud': {}}
LINE_OBJS = {n for L in LINES_BY.values() for v in L.values() for n in v['objs']}


def line_prompt(desc, n_cells, up, a='office'):
    return (f"Game map object sprite. Match the art style of image 1 exactly: image 1 is a crop of the same pixel-art game map "
            f"(16-bit style pixel art, crisp pixels, {LOOK[a]}), the same 3/4 top-down camera from the south "
            f"(about 50 degrees, showing the top edge and the south-facing front), the same lighting from the top left.\n"
            f"Draw one long straight horizontal wall: {desc}.\n"
            f"The wall runs across the WHOLE width of the image and is cut off straight at the left and right image edges (more of the same wall continues beyond): "
            f"no corners, no end caps, no end posts; the top edge and the skirting stay at exactly the same height from left to right. "
            f"The wall is about {up + 1} cells tall where the image is about {n_cells} cells wide; place it in the lower part of the image. The feature is centered and left-right symmetric.\n"
            f"Draw only the wall: no floor, no cast shadow on the floor, no people. Clean edges.\n")


def col_prompt(desc, n, up, a='office'):
    return (f"Game map object sprite. Match the art style of image 1 exactly (16-bit style pixel art, crisp pixels, {LOOK[a]}), "
            f"the same 3/4 top-down camera from the south (about 50 degrees).\n"
            f"Draw {desc}, running straight north-south, away from the viewer, so on screen it is one long narrow vertical strip: "
            f"its long thin top edge runs from the very top of the image downward, and at the bottom end you see the wall's south-facing end face. "
            f"The strip is about 1 cell wide and {n + up} cells tall (the end face at the bottom is about {up + 1} cells tall). Centered, nothing else.\n"
            f"Draw only the wall: no floor, no shadow, no people. Clean edges.\n")


def screen(key):
    bg = '#00FF00 pure green' if key == 'green' else '#FF00FF pure magenta'
    return f"Background: a completely flat opaque {bg} fill, no gradient, no shadow. No text, no letters, no watermark."


def lines_gen(a, only=()):
    d = layout.load(a); obs = {o['name']: o for o in layout.objects(d)}
    def run(job):
        name, p, refs, size = job
        try: codex11.gen(p, os.path.join(RAW, f'line-{a}-{name}.png'), refs, size=size); print(name, 'ok', flush=True)
        except Exception as e: print(name, 'FAIL', e, flush=True)
    first, later = [], []
    for k, v in LINES_BY[a].items():
        if only and k not in only: continue
        o = obs[v['ref']]; up = o['up']; n = sum(obs[x]['foot'][2] for x in v['objs'])
        refs = [crop_ref(a, d, o)]
        if v.get('base'): refs.append(os.path.join(RAW, f"line-{a}-{v['base']}.png"))
        job = (k, line_prompt(v['desc'], min(n, 12), up, a) + screen(v.get('key', 'green')), refs, '1536x1024')
        (later if v.get('base') else first).append(job)
    for k, v in COLS_BY[a].items():
        if only and k not in only: continue
        cs = [o for o in layout.objects(d) if o['name'].startswith(v['prefix'])]
        first.append((k, col_prompt(v['desc'], len(cs), cs[0]['up'], a) + screen('green'), [crop_ref(a, d, cs[0])], '1024x1536'))
    with ThreadPoolExecutor(4) as ex: list(ex.map(run, first))
    with ThreadPoolExecutor(4) as ex: list(ex.map(run, later))   # 要拿 south 那張當牆的參考


def premul_resize(im, size):
    a = np.asarray(im.convert('RGBA'), np.float32); al = a[..., 3:4] / 255.0
    r = np.asarray(Image.fromarray(np.concatenate([a[..., :3] * al, a[..., 3:4]], -1).round().astype(np.uint8), 'RGBA').resize(size, Image.LANCZOS), np.float32)
    al2 = np.clip(r[..., 3:4] / 255.0, 1e-4, 1)
    return Image.fromarray(np.concatenate([np.clip(r[..., :3] / al2, 0, 255), r[..., 3:4]], -1).round().astype(np.uint8), 'RGBA')


def line_strip(a, d, k, MW):
    """一排牆 → 整張地圖寬的長條（下緣＝牆腳那一列的下緣）"""
    v = LINES_BY[a][k]; obs = {o['name']: o for o in layout.objects(d)}; rows = obs[v['objs'][0]]['frame'][3]
    fig = key_out(os.path.join(RAW, f'line-{a}-{k}.png'), v.get('key', 'green'))
    al = np.asarray(fig)[..., 3] > 128; wall_px = al[:, :max(2, fig.width // 20)].any(1).sum()   # 最左一小條（只有牆）的高度
    s = rows * PX / wall_px; im = premul_resize(fig, (round(fig.width * s), round(fig.height * s)))
    if 'gap' in v:
        A = np.asarray(im)[..., 3] > 128; row = A[int(im.height - PX * 0.5)]; c = im.width // 2; l = r = c
        while l > 0 and not row[l]: l -= 1
        while r < im.width - 1 and not row[r]: r += 1
        g0, g1 = v['gap']; sx = (g1 - g0 + 1) * PX / max(1, r - l)
        print(k, '門洞寬', round((r - l) / PX, 2), '格 → 左右縮放', round(sx, 2))
        if not .7 <= sx <= 1.3: raise SystemExit(f'{k} 門洞寬差太多（{round(sx, 2)}），重產')
        im = premul_resize(im, (round(im.width * sx), im.height)); l, r = round(l * sx), round(r * sx)
        x0 = round((g0 + g1 + 1) / 2 * PX - (l + r) / 2)
    else:
        x0 = round(v['center'] * PX - im.width / 2)
    strip = Image.new('RGBA', (MW, im.height)); strip.alpha_composite(im, (x0, 0)) if x0 >= 0 else strip.alpha_composite(im.crop((-x0, 0, im.width, im.height)), (0, 0))
    cw = im.width // 5; Lc, Rc = im.crop((0, 0, cw, im.height)), im.crop((im.width - cw, 0, im.width, im.height))
    x, flip = x0, True
    while x > 0:
        t = Lc.transpose(Image.FLIP_LEFT_RIGHT) if flip else Lc; x -= cw
        strip.alpha_composite(t, (x, 0)) if x >= 0 else strip.alpha_composite(t.crop((-x, 0, cw, im.height)), (0, 0)); flip = not flip
    x, flip = x0 + im.width, True
    while x < MW:
        t = Rc.transpose(Image.FLIP_LEFT_RIGHT) if flip else Rc; strip.alpha_composite(t.crop((0, 0, min(cw, MW - x), im.height)), (x, 0)); x += cw; flip = not flip
    return strip


def bottom_pad(im, h):
    if im.height >= h: return im.crop((0, im.height - h, im.width, im.height))
    c = Image.new('RGBA', (im.width, h)); c.alpha_composite(im, (0, h - im.height)); return c


def lines_cut(a):
    d = layout.load(a); obs = {o['name']: o for o in layout.objects(d)}; od = os.path.join(G, f'assets/objects/{a}'); MW = d['map']['w'] * PX
    strips = {}
    for k, v in LINES_BY[a].items():
        st = line_strip(a, d, k, MW)
        if v.get('base'):
            base = strips[v['base']]; h = max(base.height, st.height); base, st = bottom_pad(base, h), bottom_pad(st, h)
            b0, b1 = v['blend'][0] * PX, v['blend'][1] * PX
            B, S = np.asarray(base, np.float32), np.asarray(st, np.float32)
            w = np.clip((np.arange(MW) - b0) / (b1 - b0), 0, 1)[None, :, None]    # 0＝base、1＝這排
            st = Image.fromarray((B * (1 - w) + S * w).round().astype(np.uint8), 'RGBA'); strips[v['base']] = st
        strips[k] = st
    for k, v in LINES_BY[a].items():
        st = strips[k]
        for n in v['objs']:
            fx, fy, fw, fh = obs[n]['frame']
            bottom_pad(st.crop((fx * PX, 0, (fx + fw) * PX, st.height)), fh * PX).save(os.path.join(od, f'{n}.png'))
    for k, v in COLS_BY[a].items():
        cs = sorted([o for o in layout.objects(d) if o['name'].startswith(v['prefix'])], key=lambda o: o['foot'][1]); up = cs[0]['up']
        fig = key_out(os.path.join(RAW, f'line-{a}-{k}.png'), 'green'); fig = premul_resize(fig, (PX, (len(cs) + up) * PX))
        for i, o in enumerate(cs): fig.crop((0, i * PX, PX, (i + up + 1) * PX)).save(os.path.join(od, f"{o['name']}.png"))
    print('整排的牆切好', list(LINES_BY[a]), list(COLS_BY[a]))


def ground_patch(a):
    """地面底圖局部修補（不重產整張）：電梯 2026-10-09 改成嵌在牆裡，原本電梯前那塊石材地板露出一條 → 用往右 12 格（地毯花紋週期的整數倍）的地毯蓋掉"""
    if a != 'office': return
    p = os.path.join(G, 'assets/maps/office_ground.png'); im = Image.open(p).convert('RGB'); c = im.width // 48
    im.paste(im.crop((30 * c, 27 * c, 42 * c, 30 * c)), (18 * c, 27 * c)); im.save(p); print('地面修補：電梯前地板 → 地毯')


def sheet(a):
    fs = sorted(glob.glob(os.path.join(RAW, f'obj-{a}-*.png'))); tiles = []
    for f in fs:
        im = Image.open(f).convert('RGB'); im.thumbnail((300, 300)); tiles.append(im)
    cols = 5; out = Image.new('RGB', (cols * 300, ((len(tiles) + cols - 1) // cols) * 300), 'white')
    for i, t in enumerate(tiles): out.paste(t, ((i % cols) * 300, (i // cols) * 300))
    p = os.path.join(H, f'check/objgen-{a}.jpg'); out.save(p, quality=82); print(p)


if __name__ == '__main__':
    cmd, a, *rest = sys.argv[1:]
    if cmd == 'gen': gen(a, [r for r in rest if not r.startswith('--')], '--redo' in rest)
    elif cmd == 'lines': lines_gen(a, rest)
    elif cmd == 'all':   # 定錨 → 地面、物件、整排的牆 → 去背切段
        if not os.path.exists(anchor(a)): style(a)
        from concurrent.futures import ThreadPoolExecutor as T
        with T(3) as ex: list(ex.map(lambda f: f(), [lambda: ground(a), lambda: gen(a), lambda: lines_gen(a)]))
        cut(a)
    else: globals()[cmd](a)
