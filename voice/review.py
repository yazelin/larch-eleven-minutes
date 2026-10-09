# -*- coding: utf-8 -*-
"""審稿頁：完整劇本照遊戲順序排，有配音的段落旁邊可以直接聽，標出角色、聲線、情緒。
python3 voice/review.py → voice/review.html（在 repo 根目錄開 http.server，音檔讀 assets/voice/）"""
import html, json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, os.path.join(G, 'src')); sys.path.insert(0, H)
from story import ORIG, NEW
import gen
GAME = open(os.path.join(G, 'dist/project.json'), encoding='utf-8').read()
man = json.load(open(os.path.join(H, 'manifest.json'), encoding='utf-8'))
ORDER = [('序　審訊室', '對話卡'), ('一　23:04', '十九樓地圖'), ('審訊室（一）', '對話卡（演在十九樓上）'), ('二　23:21', '十九樓地圖'),
         ('三　23:33', '二十樓地圖＋終端機卡'), ('四　23:37', '雲端長城地圖＋王戰'), ('五　23:49', '雲端長城地圖＋PRISM'), ('審訊室（二）', '對話卡（演在雲端上）'),
         ('結局一', '結局卡'), ('結局二', '結局卡'), ('結局三', '結局卡')]
NEWW = [('警衛擋人', '十九樓：還沒倒麵就走向主任辦公室'), ('警衛發現', '十九樓：被警衛手電筒照到'), ('周主任回頭', '十九樓：周主任轉身時開抽屜'),
        ('門還鎖著', '雲端：太早走到長城門'), ('審查兵還在追', '雲端：還沒砍完就走到門'), ('片尾', '片尾卡')]


def para_html(p):
    tags = []
    t = html.escape(p).replace('\n', '<br>')
    f = man.get(p)
    if not f: return f'<p>{t}</p>'
    if f not in GAME: tags.append('遊戲裡不會播：王戰中途的台詞，引擎不吃語音')
    for q in re.findall(r'「([^「」]+)」', p):
        w = gen.who(q)
        if w: _, v, emo = gen.clip(w, q); tags.append(f'{w}｜{v.replace("Chinese (Mandarin)_", "").replace("edge:zh-TW-HsiaoChenNeural", "edge-tts 小臻")}｜{emo}')
    return (f'<div class="v"><p>{t}</p><div class="ctl"><audio controls preload="none" src="../assets/voice/{f}"></audio>'
            f'<small>{html.escape("　／　".join(tags))}</small></div></div>')


out = []
for pre, where in ORDER:
    h = next(k for k in ORIG if k.startswith(pre))
    out.append(f'<h2>{html.escape(h)}<span>{where}</span></h2>' + ''.join(para_html(p) for p in ORIG[h]))
out.append('<h2>新寫的句子<span>原文沒有、遊戲需要的</span></h2>')
for k, where in NEWW:
    out.append(f'<h3>{k}<span>{where}</span></h3>' + ''.join(para_html(p) for p in NEW[k]))
cast = ''.join(f'<li><b>{w}</b>　{v.replace("Chinese (Mandarin)_", "").replace("edge:zh-TW-HsiaoChenNeural", "edge-tts 小臻")}　預設 {e}</li>' for w, (v, e) in gen.VOICE.items())
page = f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>十一分鐘　完整劇本與配音</title>
<style>body{{margin:0;background:#05070d;color:#e6fbff;font:17px/1.9 "Noto Sans TC",system-ui,sans-serif}}main{{max-width:860px;margin:0 auto;padding:24px 16px 80px}}
h1{{font-size:32px;margin:10px 0}}h2{{margin:44px 0 12px;padding-bottom:6px;border-bottom:1px solid #1d3b4a;color:#39f3ff}}h2 span,h3 span{{margin-left:12px;font-size:13px;color:#a9d6de;font-weight:400}}
h3{{color:#ff3fb4;margin:24px 0 6px}}p{{margin:0 0 .9em}}.v{{background:#0a1120;border-left:3px solid #ff3fb4;padding:10px 14px;margin:0 0 1em}}.v p{{margin:0 0 6px}}
.ctl{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}audio{{height:34px}}small{{color:#a9d6de}}ul{{columns:2;font-size:15px}}.note{{color:#a9d6de;font-size:15px}}</style>
<main><h1>十一分鐘　完整劇本與配音</h1>
<p class="note">照遊戲順序排。粉紅框是有配音的段落（只唸引號裡的話，旁白不配），旁邊標角色、聲線、情緒。聲線是我先選的（試聲 A 版，警衛照上一輪挑 B），要換跟我說角色和聲線就好。</p>
<ul>{cast}</ul>{"".join(out)}</main></html>'''
open(os.path.join(H, 'review.html'), 'w', encoding='utf-8').write(page); print('ok', len(man), '段配音')
