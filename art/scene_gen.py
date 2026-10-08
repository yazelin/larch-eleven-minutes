# -*- coding: utf-8 -*-
"""場面圖：標題封面、審訊室、三個結局的背景（2026-10-09 作者：照建議把介面風格做齊）。
每張寫明「在場」的角色，在場的人一定帶定錨圖（檢查器硬擋，照 feedback_cg_presence_anchors_hard_rule）。
江凌只有走路圖、沒有正面立繪 → 一律畫背影；大肥魚帶戰鬥圖。其他人（審訊員、媽媽）不露臉。
  python3 art/scene_gen.py gen [名字…]   → art/scene_raw/<名字>.png
  python3 art/scene_gen.py cut          → assets/scenes/<名字>.webp（1600×900，封面另存 assets/cover/title.webp）
  python3 art/scene_gen.py sheet        → art/check/scenes.jpg"""
import os, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, H)
import codex11

RAW = os.path.join(H, 'scene_raw'); OUT = os.path.join(G, 'assets/scenes')
STYLE = ('Anime illustration, cinematic wide shot, painterly digital art with clean anime line work (the same style as the character art in the reference images), '
         'night, cool dark palette with neon cyan #39f3ff and neon magenta #ff3fb4 accents, soft scanline-free image. No text, no letters, no readable writing, no logo, no watermark.')
ANCHOR = {   # 在場角色 → (定錨圖, 說明)
    '江凌': ('art/scene_raw/ref-jiangling.png', 'Jiang Ling, a young Chinese network engineer: short black hair, black hoodie, dark jeans (image is his small game sprite, use it only for hair and clothes)'),
    '大肥魚': ('assets/battle/dafeiyu.webp', 'Da Fei Yu, a giant whale-girl maid: long blue gradient hair with one ahoge, whale fin ears, navy and white maid dress, a big whale tail, iron chains wrapped from wrists to tail, a padlock on her chest'),
}
JOBS = {
    'title': dict(present=['江凌', '大肥魚'], prompt=(
        'Title screen key art. The LEFT 40% of the image is dark, calm night sky over a sea of clouds with only faint cyan grid lines, keep it empty (the game title and menu go there). '
        'On the right: the Great Firewall in the clouds, a colossal wall of giant dark-red neon chain links lying stacked, running from the horizon. In front of it, as tall as the wall, '
        'the giant whale-girl maid from the reference, chained to the wall, sleepy and stubborn, looking down. In the foreground at the lower right, tiny in scale, the young engineer '
        'seen from BEHIND, standing on the clouds, holding up one faint flickering grey point of light in both hands. Little grey glowing dots piled in small mounds at the foot of the wall.')),
    'interrogation': dict(present=['江凌'], prompt=(
        'An interrogation room. Harsh flat white light from a single ceiling panel, bare grey walls, an iron table. On the table an open folder and one sheet of paper with a single line of '
        'unreadable writing, a faint padlock watermark printed on the folder. Across the table two interrogators in dark suits, faces in shadow: an older man holding the folder open and a '
        'younger man leaning back. In the left foreground, the back and shoulder of the young engineer from the reference, seen from behind, sitting. Keep the lower third of the image '
        'simple and dark (a dialogue box goes there).')),
    'e1': dict(present=[], prompt=(
        'A small apartment on the US east coast in the morning. Soft morning light through a window with blinds. On a small kitchen table, a smartphone lights up with a cyan glowing message '
        'notification (unreadable). A middle-aged East Asian mother seen from behind, in a cardigan, reaching for the phone, her face not shown. Quiet, hopeful. Keep the lower third simple.')),
    'e2': dict(present=[], prompt=(
        'A US television newsroom wall of many screens all showing the same blurred photo of a schoolgirl on a flooded school rooftop at night, cold white studio light, a faint glass prism '
        'glare reflecting across the screens like an eye, an audience silhouette applauding in the dark foreground. No readable text, no logos. Unsettling. Keep the lower third simple.')),
    'e3': dict(present=['江凌'], prompt=(
        'The 19th floor network control center at night, rain on a big window, city lights blurred. The young engineer from the reference seen from BEHIND, sitting at his desk with three '
        'monitors; the middle monitor shows a blue sea of clouds crossed by a long wall made of giant dark-red neon CHAIN LINKS lying stacked (not a brick wall, not the historical Great Wall), whole again. A cup of instant noodles and a small green plastic toy dinosaur on the desk. '
        'Half the ceiling lights off. Lonely. Keep the lower third simple.')),
}


def check():
    """在場的人都要有定錨圖"""
    errs = [f'{k}：{n} 沒有定錨' for k, j in JOBS.items() for n in j['present'] if n not in ANCHOR or not os.path.exists(os.path.join(G, ANCHOR[n][0]))]
    if errs: raise SystemExit('\n'.join(errs))


def jiangling_ref():
    """江凌的定錨：走路圖正面第二格放大（只拿髮型與衣服）"""
    out = os.path.join(G, ANCHOR['江凌'][0]); os.makedirs(os.path.dirname(out), exist_ok=True)
    sh = Image.open(os.path.join(G, 'assets/walk/walk-jiangling.png')).convert('RGBA'); fw, fh = sh.width // 3, sh.height // 4
    fr = sh.crop((fw, 0, 2 * fw, fh)); bg = Image.new('RGBA', fr.size, (200, 200, 200, 255)); bg.alpha_composite(fr)
    bg.convert('RGB').resize((fw * 4, fh * 4), Image.NEAREST).save(out)


def gen(k):
    j = JOBS[k]; refs = [os.path.join(G, ANCHOR[n][0]) for n in j['present']]
    who = ' '.join(f'Image {i + 1} is {ANCHOR[n][1]}.' for i, n in enumerate(j['present']))
    os.makedirs(RAW, exist_ok=True)
    return codex11.gen(f'{who} {j["prompt"]} {STYLE}', os.path.join(RAW, f'{k}.png'), refs, size='1536x1024')


def cut():
    os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(G, 'assets/cover'), exist_ok=True)
    for k in JOBS:
        src = os.path.join(RAW, f'{k}.png')
        if not os.path.exists(src): continue
        im = Image.open(src).convert('RGB'); w, h = im.size; th = round(w * 9 / 16)   # 3:2 → 16:9 裁上下
        im = im.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((1600, 900), Image.LANCZOS)
        im.save(os.path.join(G, 'assets/cover/title.webp') if k == 'title' else os.path.join(OUT, f'{k}.webp'), quality=88)
    print('cut ok')


def sheet():
    ks = [k for k in JOBS if os.path.exists(os.path.join(RAW, f'{k}.png'))]
    c = Image.new('RGB', (800 * 2, 450 * ((len(ks) + 1) // 2)), 'black')
    for i, k in enumerate(ks):
        im = Image.open(os.path.join(RAW, f'{k}.png')).convert('RGB'); im.thumbnail((800, 450)); c.paste(im, ((i % 2) * 800, (i // 2) * 450))
    c.save(os.path.join(H, 'check/scenes.jpg'), quality=85); print('sheet', ks)


if __name__ == '__main__':
    cmd, names = sys.argv[1], sys.argv[2:] or list(JOBS)
    jiangling_ref(); check()
    if cmd == 'gen':
        def safe(k):
            try: return gen(k)
            except Exception as e: return f'FAIL {e}'
        with ThreadPoolExecutor(3) as ex:
            for k, r in zip(names, ex.map(safe, names)): print(k, r, flush=True)
    else: globals()[cmd]()
