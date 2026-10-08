"""分層地圖：照設計檔產「純地面底圖」與「每種物件一張」（做法照《香布纏．續》xu/game/art/objects_gen.py）。
- 物件：純色幕單獨生成，image 1＝畫風定錨（art/style/<a>_style_v1.png）上那個物件附近的裁切（畫風、俯角、外觀）。
  去背後裁到不透明範圍，縮進圖框（frame w×h 格 × 48px），下緣貼齊圖框下緣、水平置中；一長排的段寬度拉滿。
- 綠色的東西（盆栽、逃生標誌）改用洋紅幕，避免去背把主體吃掉。
- 地面：art/compose.py 的地面色塊當構圖，定錨圖當畫風，生成後縮放到 W×H 格 × 48px。
用法：python3 art/objects_gen.py gen office [種類…] [--redo]
      python3 art/objects_gen.py ground office
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
}


def type_of(o):
    n, k = o['name'], o['kind']
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
    os.makedirs(RAW, exist_ok=True); out = os.path.join(RAW, f'ref-{a}-{type_of(o)}.png')
    im.crop(tuple(map(int, box))).save(out); return out


def prompt(t):
    w, h, dd, desc, seg, key = TYPES[t]
    bg = '#00FF00 pure green' if key == 'green' else '#FF00FF pure magenta'
    p = (f"Game map object sprite, one single object only. Match the art style of image 1 exactly: image 1 is a crop of the same pixel-art game map "
         f"(16-bit style pixel art, crisp pixels, cyberpunk night office with cyan and magenta accents), the same 3/4 top-down camera from the south "
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
    for o in layout.objects(d):
        t = type_of(o)
        if (only and t not in only) or t in jobs or (not redo and os.path.exists(raw_path(a, t))): continue
        jobs[t] = crop_ref(a, d, o)
    def run(t):
        try: codex11.gen(prompt(t), raw_path(a, t), [jobs[t]], size='1024x1536' if TYPES[t][1] > TYPES[t][0] else '1536x1024'); print(t, 'ok', flush=True)
        except Exception as e: print(t, 'FAIL', e, flush=True)
    print(len(jobs), '張')
    with ThreadPoolExecutor(4) as ex: list(ex.map(run, jobs))


def ground(a):
    """地面：只有地面色塊的構圖 → 生成 → 縮放成 W×H 格"""
    d = layout.load(a); W, Hh = d['map']['w'], d['map']['h']; S = 32
    im = Image.new('RGB', (W * S, Hh * S)); dr = ImageDraw.Draw(im)
    for g in d['ground']:
        for x, y, w, h in g['rects']: dr.rectangle((x * S, y * S, (x + w) * S - 1, (y + h) * S - 1), fill=blocks.GROUND[g['kind']])
    os.makedirs(RAW, exist_ok=True); lay = os.path.join(RAW, f'ground-layout-{a}.png'); im.save(lay)
    desc = '; '.join(f"{g['name']}: {g.get('desc', '')}" for g in d['ground'] if g['kind'] != 'border')
    p = ("Top-down pixel-art game map floor texture only, following exactly the color-region layout of image 1 (each flat color is one floor material). "
         "Match the art style, palette and lighting of image 2 exactly (16-bit pixel art, night office, half of the ceiling lights on so the floor has alternating lit and dark bands, cool cyan accents). "
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
        t = type_of(o); fx, fy, fw, fh = o['frame']; tw, th, *_ = TYPES[t]
        if not TYPES[t][4] and (fw, fh) != (tw, th): raise SystemExit(f"{o['name']} 圖框 {fw}×{fh} 跟種類 {t} 的 {tw}×{th} 不一致")
        if t not in cache:
            if not os.path.exists(raw_path(a, t)): raise SystemExit(f'缺 {t} 的產圖')
            cache[t] = key_out(raw_path(a, t), TYPES[t][5])
        fig = cache[t]; alt[t] = alt.get(t, 0) + 1
        if TYPES[t][4]: fig = seg_slice(fig, fw, fh, alt[t] - 1)
        fit(fig, fw, fh, fill_w=TYPES[t][4]).save(os.path.join(od, f"{o['name']}.png"))
    print(od, len(layout.objects(d)), '個物件')


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
    else: globals()[cmd](a)
