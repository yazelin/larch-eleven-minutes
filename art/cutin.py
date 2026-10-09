# -*- coding: utf-8 -*-
"""王戰大招插畫的橫幅圖（10-09 作者：星火燎原的臉被切掉）。
引擎把 cutIn 圖塞進一條很扁的斜橫幅（約 4:1，cover 對齊偏左上），全身立繪只會露出胸口那段 → 另做 1600×400 橫幅：
立繪取頭到胸放左邊，大招 CG 取主角那一帶。python3 art/cutin.py → assets/battle/cut-<名>.webp"""
import os
from PIL import Image
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1600, 400


def bg():
    im = Image.new('RGB', (W, H))
    for x in range(W):   # 深藍到洋紅
        t = x / W; im.paste((int(10 + 120 * t), int(14 + 10 * t), int(40 + 60 * t)), (x, 0, x + 1, H))
    return im


def from_portrait(k, top=0.0, bottom=0.32):
    src = Image.open(os.path.join(G, f'assets/battle/{k}.webp')).convert('RGBA')
    crop = src.crop((0, int(src.height * top), src.width, int(src.height * bottom)))
    crop = crop.resize((round(crop.width * H / crop.height), H), Image.LANCZOS)
    out = bg(); out.paste(crop, (80, 0), crop); return out


def from_cg(k, y0, x0=0, w=1536):   # CG 1536×1024 原圖，取一條 4:1；橫幅右半會被淡出，主角要在左邊四成以內
    src = Image.open(os.path.join(G, f'art/scene_raw/{k}.png')).convert('RGB')
    return src.crop((x0, y0, x0 + w, y0 + w // 4)).resize((W, H), Image.LANCZOS)


JOBS = {'qwen': lambda: from_portrait('qwen', bottom=0.34), 'xinghuo': lambda: from_portrait('xinghuo'),
        'tail': lambda: from_cg('tail', 20), 'copy': lambda: from_cg('copy', 110, x0=300, w=1236)}

if __name__ == '__main__':
    for k, f in JOBS.items():
        f().save(os.path.join(G, f'assets/battle/cut-{k}.webp'), quality=88); print('cut', k)
