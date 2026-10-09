# -*- coding: utf-8 -*-
"""公開站用的素材：從 assets/ 與 art/site_raw/（tests/site_shots.mjs 拍的遊戲截圖）縮成小檔，放進 docs/media/。
檔名一律 ASCII。python3 site/media.py"""
import os, subprocess
from PIL import Image
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(G, 'docs/media')
IMG = {   # 輸出名: (來源, 最長邊)
    'cover.webp': ('assets/cover/title.webp', 1600), 'og.jpg': ('assets/cover/thumb.webp', 1200),
    'cg-interrogation.webp': ('assets/scenes/interrogation.webp', 1280), 'cg-unchained.webp': ('assets/scenes/unchained.webp', 1280),
    'cg-e1.webp': ('assets/scenes/e1.webp', 1280), 'cg-e2.webp': ('assets/scenes/e2.webp', 1280), 'cg-e3.webp': ('assets/scenes/e3.webp', 1280),
    'shot-office.webp': ('art/site_raw/office.png', 1280), 'shot-server.webp': ('art/site_raw/server.png', 1280),
    'shot-terminal.webp': ('art/site_raw/terminal.png', 1280), 'shot-cloud.webp': ('art/site_raw/cloud.png', 1280),
    'shot-w1.webp': ('art/site_raw/battle-w1.png', 1280), 'shot-w2.webp': ('art/site_raw/battle-w2.png', 1280),
}
for k in ['jiangling', 'dafeiyu', 'dafeiyu_free', 'prism_r', 'qwen', 'doubao', 'kimi', 'wenxin', 'glm', 'yuanbao', 'hailuo', 'xinghuo', 'censor', 'hound']:
    IMG[f'char-{k.replace("_", "-")}.webp'] = (f'assets/battle/{k}.webp', 560)
AUDIO = ['title', 'office', 'server', 'cloud', 'boss', 'ending']

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, (src, edge) in IMG.items():
        im = Image.open(os.path.join(G, src)); im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') and name.endswith('.webp') else 'RGB')
        im.thumbnail((edge, edge), Image.LANCZOS)
        p = os.path.join(OUT, name)
        im.save(p, quality=82, method=6) if name.endswith('.webp') else im.convert('RGB').save(p, quality=86)
    for k in AUDIO:   # 循環版 60 秒，128k
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(G, f'assets/bgm/{k}.mp3'), '-b:a', '128k', os.path.join(OUT, f'bgm-{k}.mp3')], check=True)
    tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(len(os.listdir(OUT)), '個檔', round(tot / 1e6, 1), 'MB')
