# -*- coding: utf-8 -*-
"""市集縮圖（settings.projectThumbnail）：標題封面＋霓虹片名字（字用程式疊，不讓生圖模型寫中文）。配色照霓虹訊號：#39f3ff、#ff3fb4。
python3 art/thumb.py → assets/cover/thumb.webp（1600×900）"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
MONO = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
NEON, PULSE = (57, 243, 255), (255, 63, 180)
im = Image.open(os.path.join(G, 'assets/cover/title.webp')).convert('RGB').resize((1600, 900))
shade = Image.linear_gradient('L').rotate(90).resize((1600, 900))                         # 左暗右亮
im = Image.composite(Image.new('RGB', im.size, (3, 5, 12)), im, shade.point(lambda v: int(v * .78)))
f = ImageFont.truetype(FONT, 168, index=2); t = '十一分鐘'; x, y = 96, 300
glow = Image.new('RGBA', im.size); g = ImageDraw.Draw(glow)
g.text((x - 6, y), t, font=f, fill=PULSE + (200,)); g.text((x + 6, y), t, font=f, fill=NEON + (200,))
glow = glow.filter(ImageFilter.GaussianBlur(14))
im = im.convert('RGBA'); im.alpha_composite(glow)
d = ImageDraw.Draw(im)
d.text((x - 3, y), t, font=f, fill=PULSE + (255,)); d.text((x + 3, y), t, font=f, fill=NEON + (255,)); d.text((x, y), t, font=f, fill=(242, 254, 255, 255))
s = ImageFont.truetype(MONO, 34, index=2)
d.text((x + 6, y + 228), '// 十月九日 23:47，防火長城開了十一分鐘。', font=s, fill=(230, 251, 255, 255))
d.text((x + 6, 96), '● GFW · 23:47', font=ImageFont.truetype(MONO, 26, index=2), fill=NEON + (255,))
for cx, cy, sx, sy in ((30, 30, 1, 1), (1570, 30, -1, 1), (30, 870, 1, -1), (1570, 870, -1, -1)):   # HUD 四角
    d.line((cx, cy, cx + 46 * sx, cy), fill=NEON, width=4); d.line((cx, cy, cx, cy + 46 * sy), fill=NEON, width=4)
out = os.path.join(G, 'assets/cover/thumb.webp'); im.convert('RGB').save(out, quality=90); print(out)
