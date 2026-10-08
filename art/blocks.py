# -*- coding: utf-8 -*-
"""單色塊驗證（2026-10-08 作者：先用單色塊填格確認分層，再產真的物件）。
讀 art/objects_<a>.yaml，產：
  assets/maps/<a>_blocks.png       純色地面（每種地面一個顏色、淡格線）
  assets/blocks/<a>/<名>.png       每個物件一張：佔地部分深色、往上長的部分淺色半透明、標名字
  art/check/blocks-<a>-plan.png    整張設計圖：格線、佔地（實線）、視覺圖框（虛線）、排序列
用法：python3 art/blocks.py office"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, os.path.join(G, 'src'))
import layout

PX = 24   # 每細格幾 px（色塊不需要高解析；引擎照 free 的格數縮放）
FONT = lambda s: ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', s)
GROUND = {'border': (40, 40, 40), 'carpet': (70, 80, 105), 'office': (150, 120, 90), 'tile': (215, 220, 225), 'lobby': (160, 160, 170), 'cloud': (200, 215, 235), 'void': (20, 25, 45)}


KIND = {'窗牆': (90, 110, 140), '玻璃牆': (140, 180, 200), '門': (120, 160, 120), '桌': (130, 95, 70), '椅': (60, 60, 60), '櫃': (110, 100, 130),
        '工位': (100, 120, 150), '柱': (150, 150, 160), '雜物': (120, 110, 100), '植物': (60, 120, 70), '隔間牆': (170, 170, 175),
        '電梯': (180, 185, 195), '機櫃': (40, 60, 80), '終端機': (50, 140, 160), '長城': (150, 60, 70), '光點山': (120, 120, 130), '雲柱': (190, 205, 230)}


def ground(d, a):
    W, Hh = d['map']['w'], d['map']['h']
    im = Image.new('RGB', (W * PX, Hh * PX), GROUND['carpet']); dr = ImageDraw.Draw(im)
    for g in d['ground']:
        for x, y, w, h in g['rects']:
            dr.rectangle((x * PX, y * PX, (x + w) * PX - 1, (y + h) * PX - 1), fill=GROUND[g['kind']])
    for x in range(W): dr.line((x * PX, 0, x * PX, Hh * PX), fill=(120, 120, 120), width=1)   # 淡格線
    for y in range(Hh): dr.line((0, y * PX, W * PX, y * PX), fill=(120, 120, 120), width=1)
    out = os.path.join(G, f'assets/maps/{a}_blocks.png'); im.save(out); return out


def block(o):
    fx, fy, fw, fh = o['frame']; x, y, w, h = o['foot']
    c = KIND[o['kind']]
    im = Image.new('RGBA', (fw * PX, fh * PX), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    # 往上長的部分（不佔空間）：淺色半透明
    light = tuple(min(255, int(v * 1.35 + 40)) for v in c) + (225,)   # 往上長的部分：淺色、幾乎不透明（驗證人被蓋住要看得出來），斜線表示不佔地
    if y > fy: dr.rectangle((0, 0, fw * PX - 1, (y - fy) * PX - 1), fill=light)
    if o.get('side'):   # 樹冠兩邊多出來的
        dr.rectangle((0, 0, fw * PX - 1, fh * PX - 1), fill=light)
    for k in range(-fh * PX, fw * PX, 10): dr.line((k, 0, k + fh * PX, fh * PX), fill=(255, 255, 255, 70), width=2)
    # 佔地：深色不透明（門洞挖空）
    for (i, j) in layout.foot_cells(o):
        dr.rectangle(((i - fx) * PX, (j - fy) * PX, (i - fx + 1) * PX - 1, (j - fy + 1) * PX - 1), fill=tuple(int(v * .6) for v in c) + (235,))
    dr.rectangle((0, 0, fw * PX - 1, fh * PX - 1), outline=(255, 255, 255, 255), width=2)
    f = FONT(max(10, min(18, int(PX * .7))))
    dr.text((3, 2), o['name'], fill=(255, 255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    return im


def plan(d, a):
    W, Hh = d['map']['w'], d['map']['h']; S = 30
    im = Image.open(os.path.join(G, f'assets/maps/{a}_blocks.png')).convert('RGBA').resize((W * S, Hh * S), Image.NEAREST)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(lay); f = FONT(13)
    for o in layout.objects(d):
        fx, fy, fw, fh = o['frame']
        dr.rectangle((fx * S, fy * S, (fx + fw) * S - 1, (fy + fh) * S - 1), outline=(255, 255, 255, 230), width=1)
        for (i, j) in layout.foot_cells(o):
            dr.rectangle((i * S + 1, j * S + 1, (i + 1) * S - 2, (j + 1) * S - 2), fill=KIND[o['kind']] + (200,))
        dr.line((fx * S, (o['sort'] + 1) * S - 1, (fx + fw) * S, (o['sort'] + 1) * S - 1), fill=(255, 60, 60, 255), width=2)
        dr.text((fx * S + 2, fy * S + 1), o['name'], fill=(255, 255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for k, (x, y) in d['points'].items():
        dr.ellipse((x * S + 6, y * S + 6, x * S + S - 6, y * S + S - 6), fill=(255, 220, 0, 255))
        dr.text((x * S + S, y * S + 2), k, fill=(255, 240, 120, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for x in range(0, W, 2): dr.text((x * S + 2, 2), str(x), fill=(255, 255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for y in range(0, Hh, 2): dr.text((2, y * S + 2), str(y), fill=(255, 255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    im.alpha_composite(lay)
    out = os.path.join(G, f'art/check/blocks-{a}-plan.png'); im.convert('RGB').save(out); return out


def doors(d, a, od):
    """門板疊圖（關／半開／全開 × 上下兩半），細格單位寫進 doors.json。上半：門洞上方 up 格到門洞前一列；下半：門洞那幾列"""
    import json
    meta = {}
    for dr_ in d['doors']:
        xs, rows = dr_['x'], dr_['opens_rows']; x0, w = min(xs), len(xs)
        up = 4 if len(rows) > 1 else 3
        parts = {'top': (x0, min(rows) - up, w, up), 'bot': (x0, min(rows), w, len(rows))}
        meta[dr_['name']] = {'states': {}}
        for st, keep in (('closed', 1.0), ('half', 0.36), ('open', 0.14)):
            meta[dr_['name']]['states'][st] = {'parts': {}}
            for k, (px, py, pw, ph) in parts.items():
                im = Image.new('RGBA', (pw * PX, ph * PX), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
                lw = int(pw * PX * keep / (1 if keep == 1.0 else 1))
                if keep == 1.0: g.rectangle((0, 0, pw * PX - 1, ph * PX - 1), fill=(110, 60, 30, 240))
                else:
                    side = int(pw * PX * keep / 2) if keep < 1 else pw * PX
                    g.rectangle((0, 0, side, ph * PX - 1), fill=(110, 60, 30, 240)); g.rectangle((pw * PX - side - 1, 0, pw * PX - 1, ph * PX - 1), fill=(110, 60, 30, 240))
                g.rectangle((0, 0, pw * PX - 1, ph * PX - 1), outline=(255, 220, 160, 255), width=1)
                fn = f"door-{dr_['name']}-{st}-{k}.png"; im.save(os.path.join(od, fn))
                meta[dr_['name']]['states'][st]['parts'][k] = {'file': fn, 'x': px, 'y': py, 'w': pw, 'h': ph}
    json.dump(meta, open(os.path.join(od, 'doors.json'), 'w'), ensure_ascii=False, indent=1)


def main(a):
    d = layout.load(a); errs = layout.check(d)
    if errs: raise SystemExit('設計檔有問題：\n' + '\n'.join(errs))
    ground(d, a)
    od = os.path.join(G, f'assets/blocks/{a}'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    obs = layout.objects(d)
    for o in obs: block(o).save(os.path.join(od, f"{o['name']}.png"))
    print(plan(d, a), len(obs), '個物件')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'office')
