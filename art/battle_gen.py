# -*- coding: utf-8 -*-
"""戰鬥卡敵人圖：九個模型娘照定錨圖（art/anchor）重產在綠幕上再去背，加稜鏡、審查兵、獵犬與戰場背景。
定錨圖是白底，女僕裝、白髮直接 flood-fill 會被吃掉，所以不拿定錨去背，帶定錨當參考圖重產（cutout skill 第一步）。
產圖走 .11（art/codex11.py）。
  python3 art/battle_gen.py gen [名字…]   # 產原圖到 art/battle_raw/
  python3 art/battle_gen.py cut [名字…]   # 去背、縮到 768 高 → assets/battle/<名字>.webp
  python3 art/battle_gen.py sheet         # 全部排成一張給作者看 → art/check/battle-cast.jpg"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, H)
import codex11

RAW = os.path.join(H, 'battle_raw'); OUT = os.path.join(G, 'assets/battle')
CUTOUT = os.path.expanduser('~/.claude/skills/cutout/cutout.py')
POSE = ('Full body, the whole figure inside the frame with margin on every side, standing in a battle stance, body turned three-quarters '
        'toward the viewer\'s left (she faces an opponent at the lower left). ')
SCREEN = {'green': 'Background: one flat pure chroma green #00FF00, evenly lit. No shadow, no floor, no gradient, no vignette, no reflection, no text, no logo, no watermark.',
          'magenta': 'Background: one flat pure magenta #FF00FF, evenly lit. No shadow, no floor, no gradient, no vignette, no reflection, no text, no logo, no watermark.'}
SAME = 'Image 1 is the character design sheet: keep exactly the same character, face, hair, outfit, colors and props, redrawn in the same anime illustration style. '
CAST = {   # 名字：(定錨圖, 幕色, 姿勢與招式補充)
    'qwen': ('qwen_v2.png', 'green', 'She pushes her shopping cart full of glowing captured messages, holding a barcode scanner up.'),
    'doubao': ('doubao_v1.png', 'green', 'She holds up a phone showing a 15-second countdown, swiping with one finger.'),
    'kimi': ('kimi_v1.png', 'green', 'She pushes up her thick glasses, a long glowing scroll of text streaming past her.'),
    'wenxin': ('wenxin_v2.png', 'green', 'She raises one hand, a glowing search results page floating beside her.'),
    'glm': ('glm_v2.png', 'magenta', 'Sleepy half-closed eyes, one hand raised casting a thin line of light.'),
    'yuanbao': ('yuanbao_v2.png', 'green', 'Several small glowing chat bubbles orbit her as she reaches out a hand.'),
    'hailuo': ('hailuo_v2.png', 'green', 'She holds her conch to her ear, calm, a small sound wave ring glowing around it.'),
    'xinghuo': ('xinghuo_v2.png', 'green', 'She speaks into her headset mic, sparks flying around her hands.'),
    'dafeiyu': ('dafeiyu_v2.png', 'green', 'Heavy iron chains wrap her from her wrists down to her whale tail, the chains trail off to the right edge as if fixed to a wall '
                '(the chains end inside the frame). A big padlock hangs on her chest. She looks sleepy and stubborn, her whale tail raised to swing.'),
}
EXTRA = {
    'prism': ('magenta', 'A giant floating glass prism shaped like an eye: a faceted crystal octahedron with a calm glowing iris in the center, every facet reflecting a '
              'tiny glowing point of light. Cool white and pale blue glass, elegant, polite, unsettling. Anime game boss illustration, centered, whole object inside the frame. '),
    'censor': ('green', 'A censorship program shown as a soldier in a plain grey uniform and cap, no facial features at all, only one horizontal glowing red scan line across '
               'the blank face. Full body standing, holding a short grey baton. Anime game enemy illustration. '),
    'hound': ('green', 'A sniffer hound made of grey data: lean grey dog, no eyes, one glowing red scan line across its face, nose down sniffing, full body side view facing left. '
              'Anime game enemy illustration. '),
}
HERO = ('Image 1 is the game sprite of Jiang Ling, a modern Chinese network engineer about 28: short black hair, thin black-framed glasses, a dark charcoal zip-up hoodie open over '
        'a plain white T-shirt, a blue lanyard with a white ID card, dark jeans, grey sneakers (use the sprite only for his look). Redraw him as a full-body anime battle illustration in the same '
        'style as the boss art: standing in a fighting stance, body turned three-quarters toward the viewer\'s LEFT (he faces enemies on the left), one hand raised with glowing cyan lines of code '
        'and a delete cursor forming a blade of light, determined tired eyes. ')
BG = ('A battle background for an anime RPG boss fight, wide landscape, no characters. A sea of grey-blue clouds under a black sky, a colossal wall made of giant '
      'dark red neon chain links lying stacked, stretching from the left horizon to the right horizon, each link as tall as a building. Faint cyan grid lines float in '
      'the clouds. Small piles of grey glowing dots at the foot of the wall. Pixel-neon game art, crisp. No text, no logo.')


def gen(k):
    os.makedirs(RAW, exist_ok=True); out = os.path.join(RAW, f'{k}.png')
    if k == 'bg':
        return codex11.gen(BG, out, size='1536x1024')
    if k == 'jiangling':
        return codex11.gen(HERO + POSE.replace('she faces', 'he faces').replace("toward the viewer's left (", "toward the viewer's left (") + SCREEN['magenta'], out,
                           [os.path.join(G, 'art/scene_raw/ref-jiangling.png')], size='1024x1536')
    if k in CAST:
        ref, screen, act = CAST[k]
        return codex11.gen(SAME + POSE + act + ' ' + SCREEN[screen], out, [os.path.join(H, 'anchor', ref)], size='1024x1536')
    screen, desc = EXTRA[k]
    return codex11.gen(desc + POSE.replace('she faces', 'it faces') + SCREEN[screen], out, size='1024x1536')


def screen_of(k):
    if k == 'jiangling': return 'magenta'
    return CAST[k][1] if k in CAST else EXTRA[k][0]


def unpremul_resize(im, h):
    w = round(im.width * h / im.height)
    a = np.asarray(im, np.float32); al = a[..., 3:4] / 255.0
    pre = Image.fromarray(np.concatenate([a[..., :3] * al, a[..., 3:4]], -1).round().astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)
    r = np.asarray(pre, np.float32); al2 = np.clip(r[..., 3:4] / 255.0, 1e-4, 1)
    return Image.fromarray(np.concatenate([np.clip(r[..., :3] / al2, 0, 255), r[..., 3:4]], -1).round().astype(np.uint8), 'RGBA')


def cut(k):
    os.makedirs(OUT, exist_ok=True); src = os.path.join(RAW, f'{k}.png')
    if k == 'bg':
        Image.open(src).convert('RGB').resize((1536, 1024)).save(os.path.join(OUT, 'bg.jpg'), quality=88); return
    tmp = os.path.join(RAW, f'{k}-key.png'); key = screen_of(k)
    subprocess.run([sys.executable, CUTOUT, 'key', src, '-o', tmp, '--key', key], check=True, capture_output=True)
    im = Image.open(tmp).convert('RGBA'); im = im.crop(im.getbbox())
    a = np.asarray(im).copy(); a[..., 3][a[..., 3] > 225] = 255; im = Image.fromarray(a, 'RGBA')   # 白、淺粉這種低色度的地方算出來 α 約 245，整個人半透明，補回不透明
    out = os.path.join(OUT, f'{k}.png'); unpremul_resize(im, min(768, im.height)).save(out, optimize=True)
    subprocess.run([sys.executable, CUTOUT, 'despill', out, '--key', key], check=True, capture_output=True)
    os.replace(out.replace('.png', '-fixed.png'), out)   # despill 寫到 -fixed.png
    r = subprocess.run([sys.executable, CUTOUT, 'check', out, '--key', key], capture_output=True, text=True)
    os.remove(out.replace('.png', '-on-magenta.png')); os.remove(tmp); print(k, r.stdout.strip().splitlines()[:6])
    Image.open(out).save(out.replace('.png', '.webp'), quality=90, method=6); os.remove(out)   # 遊戲用 webp（小四倍）


def sheet():
    ks = [k for k in list(CAST) + list(EXTRA) if os.path.exists(os.path.join(OUT, f'{k}.webp'))]
    c = Image.new('RGB', (300 * len(ks), 460), (40, 20, 60))
    for i, k in enumerate(ks):
        im = Image.open(os.path.join(OUT, f'{k}.webp')); im.thumbnail((290, 450)); c.paste(im, (i * 300 + (300 - im.width) // 2, 455 - im.height), im)
    c.save(os.path.join(G, 'art/check/battle-cast.jpg'), quality=85); print('sheet', ks)


if __name__ == '__main__':
    cmd, names = sys.argv[1], sys.argv[2:] or list(CAST) + list(EXTRA) + ['bg']
    if cmd == 'gen':
        with ThreadPoolExecutor(3) as ex:
            def safe(k):
                try: return gen(k)
                except Exception as e: return f'FAIL {e}'
            for k, f in zip(names, ex.map(safe, names)): print(k, f, flush=True)
    elif cmd == 'cut':
        for k in names: cut(k)
    else:
        sheet()
