"""產圖走 .11 codex-image（作者 2026-10-08：之後產圖改走 .11，多帳號輪替、不吃本機額度）。
這台連 ching-tech.ddns.net 會被擋（hairpin），走內網 https://192.168.11.11/codex-image、不驗憑證。
參考圖先縮成長邊 1024 的 JPEG（透明圖先鋪灰底）再送，照 larch-taoyuan/buchan/cg_jobs.py。
用法（模組）：codex11.gen(prompt, out_path, refs=[...], size='1024x1024')；回傳 out_path，失敗丟例外
用法（指令）：python3 art/codex11.py "<prompt>" <out.png> [ref…]"""
import base64, io, json, os, ssl, sys, time, urllib.request
from PIL import Image

BASE = 'https://192.168.11.11/codex-image'
KEY = next(l.split('=', 1)[1].strip().strip('"') for l in open(os.path.expanduser('~/.bashrc')) if 'CODEX_IMAGE_KEY=' in l)
CTX = ssl._create_unverified_context()


def _ref(path):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (200, 200, 200, 255)); bg.alpha_composite(im); im = bg
    im = im.convert('RGB'); im.thumbnail((1024, 1024))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=90); return base64.b64encode(b.getvalue()).decode()


def _call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=120, context=CTX))


def gen(prompt, out, refs=(), size='1024x1024'):
    body = {'prompt': prompt, 'size': size, 'quality': 'high', 'count': 1, 'reference_images_base64': [_ref(p) for p in refs]}
    job = _call('POST', '/v1/images/jobs', body)['id']
    while True:
        time.sleep(15)
        st = _call('GET', f'/v1/images/jobs/{job}')
        if st.get('status') == 'succeeded':
            data = urllib.request.urlopen(st['images'][0]['url'].replace('https://ching-tech.ddns.net', 'https://192.168.11.11'), timeout=120, context=CTX).read()
            im = Image.open(io.BytesIO(data))
            if im.mode == 'RGBA':   # 它有時直接回透明底（alpha 約 254）：鋪回純色幕，讓後面的去背流程一致
                a = im.getchannel('A')
                if a.getextrema()[0] < 200: print('注意：回傳是透明底', out, file=sys.stderr)
            im.save(out)
            json.dump({'job': job, 'prompt': prompt, 'refs': list(refs)}, open(os.path.splitext(out)[0] + '.json', 'w'), ensure_ascii=False, indent=1)
            return out
        if st.get('status') in ('failed', 'error'):
            raise RuntimeError(f'{out}: {st.get("error")}')


if __name__ == '__main__':
    print(gen(sys.argv[1], sys.argv[2], sys.argv[3:]))
