"""色塊構圖（不標字、不畫格線）：給生圖當構圖參考。python3 art/compose.py office → art/check/compose-office.png"""
import os, sys
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, os.path.join(G, 'src')); sys.path.insert(0, H)
import layout, blocks
S = 32
a = sys.argv[1] if len(sys.argv) > 1 else 'office'
d = layout.load(a); W, Hh = d['map']['w'], d['map']['h']
im = Image.new('RGB', (W * S, Hh * S), blocks.GROUND['carpet']); dr = ImageDraw.Draw(im)
for g in d['ground']:
    for x, y, w, h in g['rects']: dr.rectangle((x * S, y * S, (x + w) * S - 1, (y + h) * S - 1), fill=blocks.GROUND[g['kind']])
for o in sorted(layout.objects(d), key=lambda o: o['sort']):
    c = blocks.KIND[o['kind']]; fx, fy, fw, fh = o['frame']; x, y, w, h = o['foot']
    dr.rectangle((fx * S, fy * S, (fx + fw) * S - 1, y * S - 1), fill=tuple(min(255, int(v * 1.3 + 30)) for v in c))   # 往上長（正面）
    for (i, j) in layout.foot_cells(o): dr.rectangle((i * S, j * S, (i + 1) * S - 1, (j + 1) * S - 1), fill=c)
out = os.path.join(G, f'art/check/compose-{a}.png'); im.save(out); print(out)
