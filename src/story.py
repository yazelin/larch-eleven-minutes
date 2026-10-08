"""讀 canon/原文.md 與 canon/新寫.md：遊戲裡的句子一律從這裡取，不在程式裡手打（照《起跑總在開始前》的規則）。
原文：section('一　23:04') → 那一節的段落（引用區塊 > 開頭的連續幾行合成一段）。"""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
USED = set()   # 用過的段落（check_static 用來比對原文是否全用上）


def _sections(path):
    out, head = {}, None
    for raw in path.read_text(encoding='utf-8').splitlines():
        l = raw.rstrip()
        if l.startswith('## '): head = l[3:].strip(); out[head] = []; continue
        if head is None: continue
        if not l.strip(): out[head].append(None); continue
        if l.startswith('>'):
            t = l.lstrip('> ').strip()
            if out[head] and out[head][-1] is not None and out[head][-1].startswith('＞'): out[head][-1] += '\n' + t
            else: out[head].append('＞' + t)
            continue
        out[head].append(l.strip())
    return {h: [p.lstrip('＞') for p in ps if p] for h, ps in out.items()}


ORIG = _sections(ROOT / 'canon/原文.md')
NEW = _sections(ROOT / 'canon/新寫.md')


def section(prefix, src=None):
    src = src or ORIG
    hits = [h for h in src if h.startswith(prefix)]
    if len(hits) != 1: raise KeyError(f'{prefix}：找到 {len(hits)} 節 {hits}')
    ps = src[hits[0]]
    if src is ORIG: USED.update((hits[0], i) for i in range(len(ps)))
    return ps


def new(key):
    return section(key, NEW)


if __name__ == '__main__':
    for h, ps in ORIG.items(): print(h, len(ps))
