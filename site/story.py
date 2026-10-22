# -*- coding: utf-8 -*-
"""公開站完整劇情頁：canon/原文.md → docs/story/index.html。
遊戲台詞也是從原文.md 取（src/story.py），所以這頁跟遊戲同一份文字；原文改了重跑這支就好。
結局詳解是另外寫的，在 site/story_endings.html。
用法：python3 site/story.py"""
import html, re
from pathlib import Path

H = Path(__file__).resolve().parent.parent
SRC, OUT = H / 'canon/原文.md', H / 'docs/story/index.html'
M = 'https://cdn.jsdelivr.net/gh/yazelin/larch-eleven-minutes@site-media-3/docs/media/'
# 每一節開頭配的圖（照劇情順序；結局三張就是結局 CG）
ART = {'序': 'cg-interrogation.webp', '一': 'shot-office.webp', '二': 'shot-terminal.webp', '三': 'shot-server.webp',
       '四': 'shot-cloud.webp', '五': 'cg-unchained.webp', '結局一': 'cg-e1.webp', '結局二': 'cg-e2.webp', '結局三': 'cg-e3.webp'}


def inline(s):
    s = html.escape(s, quote=False)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', s)


def sections():
    out, cur = [], None
    for block in re.split(r'\n\s*\n', SRC.read_text(encoding='utf-8')):
        block = block.strip()
        if not block or block.startswith('# ') or block.startswith('（草稿'):
            continue
        if block.startswith('## '):
            cur = {'head': block[3:].strip(), 'body': []}
            out.append(cur)
            continue
        if block.startswith('>'):
            lines = [l.lstrip('>').strip() for l in block.splitlines()]
            cur['body'].append('<blockquote class="msg">' + '<br>'.join(inline(l) for l in lines) + '</blockquote>')
        elif block.startswith('`') and block.endswith('`') and block.count('`') == 2:
            cur['body'].append('<pre class="cmd">$ ' + html.escape(block.strip('`')) + '</pre>')
        else:
            cur['body'].append('<p>' + inline(block) + '</p>')
    return out


def render():
    secs = sections()
    assert len(secs) == 11, [s['head'] for s in secs]   # 序、審訊室一、一到五、審訊室二、三個結局
    nav, body = [], []
    for i, s in enumerate(secs):
        parts = s['head'].split('　')
        key, rest = parts[0], parts[1:]
        sid = f's{i}'
        if key.startswith('結局'):
            label, time = '　'.join(parts), parts[0]
        elif key == '審訊室（一）' or key == '審訊室（二）':
            label, time = key, '審訊室'
        else:
            label, time = '　'.join(parts), ' '.join(p for p in rest if re.match(r'\d', p)) or key
        title = rest[-1] if rest and not key.startswith('結局') else (rest[0] if rest else key)
        nav.append(f'<a href="#{sid}">{html.escape(label)}</a>')
        art = ART.get(key)
        img = f'<img src="{M}{art}" alt="" loading="lazy">' if art else ''
        cls = 'ch end' if key.startswith('結局') else 'ch'
        body.append(f'<section class="{cls}" id="{sid}">{img}<div class="tc">{html.escape(time)}</div>'
                    f'<h2>{html.escape(title)}</h2>' + '\n'.join(s['body']) + '</section>')
    tpl = (H / 'site/story_template.html').read_text(encoding='utf-8')
    endings = (H / 'site/story_endings.html').read_text(encoding='utf-8')
    out = tpl.replace('<!--NAV-->', ''.join(nav)).replace('<!--BODY-->', '\n'.join(body)).replace('<!--ENDINGS-->', endings)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding='utf-8')
    print(OUT, len(secs), 'sections')


if __name__ == '__main__':
    render()
