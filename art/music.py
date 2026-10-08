# -*- coding: utf-8 -*-
"""配樂：走 .11 的 gemini-web /api/music（作者 2026-10-09 指定），產完切 60 秒循環、量響度（沿用 larch-taoyuan/bgm.py 的 find_start／make／seam_score）。
服務偶爾逾時，重試就好（記憶：音樂會撞 548 秒逾時，跟 worker 無關）。這台連 ddns 會被擋，走內網 IP、不驗憑證。
  python3 art/music.py gen [名字…]   → art/music_raw/<名字>.mp3
  python3 art/music.py loop [名字…]  → assets/bgm/<名字>.mp3（60 秒循環、-16 LUFS）"""
import base64, importlib.util, json, os, ssl, subprocess, sys, threading, urllib.request
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
RAW, OUT = os.path.join(H, 'music_raw'), os.path.join(G, 'assets/bgm')
URL = 'https://192.168.11.11/gemini-web/api/music'
CTX = ssl._create_unverified_context()
TRACKS = {
    'title': 'Dark cinematic synthwave title theme, a lonely clock-like synth arpeggio ticking over a deep warm pad, distant rain, a single soft piano motif of four notes '
             'that repeats like a countdown, neon city at midnight, melancholic and tense, 80 BPM, minor key, instrumental, no vocals, loopable',
    'office': 'Quiet tense ambient electronic for a stealth scene in a half-lit government network office at night, rain on the windows, a low pulsing sub bass, '
              'soft ticking hi-hat, sparse muted synth notes, fluorescent hum, held breath, 70 BPM, minor, no melody development, instrumental, no vocals, loopable',
    'server': 'Cold minimal electronic drone inside a roaring server room, air conditioning hiss, blinking green lights as tiny glassy synth blips, a slow ominous low note, '
              'mechanical and lonely, 60 BPM, instrumental, no vocals, loopable',
    'cloud': 'Epic cyberpunk orchestral electronic, a vast sea of clouds under a black sky with a colossal wall of red neon chains, driving synth bass ostinato, '
             'big taiko-like drums, a soaring erhu-like lead over cold synth pads, determined and defiant, 110 BPM, minor, instrumental, no vocals, loopable',
    'boss': 'Intense boss battle music, cyberpunk electronic with heavy industrial drums, distorted synth bass, fast arpeggios, a sharp erhu-like lead line, '
            'chains clanking as percussion, urgent and grand, 140 BPM, minor, instrumental, no vocals, loopable',
    'ending': 'Gentle aftermath piano with soft strings and a faint warm synth pad, rain stopping, morning light after a long night, bittersweet, a quiet four-note motif '
              'resolving, 66 BPM, instrumental, no vocals, loopable',
}


def key():
    for line in open(os.path.expanduser('~/.bashrc'), encoding='utf-8'):
        if line.startswith('export GEMINI_IMAGE_KEY='): return line.split('=', 1)[1].strip().strip('"')
    raise RuntimeError('找不到 GEMINI_IMAGE_KEY')


def one(name, k, tries=4):
    os.makedirs(RAW, exist_ok=True)
    for n in range(tries):
        req = urllib.request.Request(URL, method='POST', data=json.dumps({'prompt': TRACKS[name], 'timeout': 720}).encode(),
                                     headers={'Content-Type': 'application/json', 'x-goog-api-key': k})
        try: d = json.load(urllib.request.urlopen(req, timeout=900, context=CTX))
        except Exception as e: print(f'{name} 第{n + 1}次 例外 {e!r}', flush=True); continue
        if d.get('success'):
            p = os.path.join(RAW, f'{name}.mp3'); open(p, 'wb').write(base64.b64decode(d['audio']))
            print(f"{name} 好了 worker={d.get('worker_id')} {d.get('elapsed_seconds', 0):.0f} 秒", flush=True); return
        print(f"{name} 第{n + 1}次 失敗 {d.get('message') or d.get('error')}", flush=True)
    print(f'{name} 四次都失敗', flush=True)


def loop(name):
    spec = importlib.util.spec_from_file_location('tybgm', os.path.expanduser('~/larch-taoyuan/bgm.py'))
    B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)   # 只借函式，不跑它的 main（它的路徑是桃園的）
    src = os.path.join(RAW, f'{name}.mp3'); os.makedirs(OUT, exist_ok=True); out = os.path.join(OUT, f'{name}.mp3')
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    B.LEN = min(60, int(dur) - 4)
    base, best = B.find_start(src), None
    for off in [0, .5, -.5, 1, -1, 1.5, -1.5, 2, -2]:
        s = max(0.0, base + off); B.make(src, s, out); z, d = B.seam_score(out)
        if best is None or abs(z) < abs(best[0]): best = (z, s, d)
        if abs(z) < 3: break
    z, s, d = best; B.make(src, s, out)
    print(f'{name} 原曲 {dur:.0f} 秒 → 循環 {d:.1f} 秒，從 {s:.0f} 秒起，接縫 z={z:+.1f}', flush=True)


if __name__ == '__main__':
    cmd, names = sys.argv[1], sys.argv[2:] or list(TRACKS)
    if cmd == 'gen':
        k = key(); ts = [threading.Thread(target=one, args=(n, k)) for n in names]
        for t in ts: t.start()
        for t in ts: t.join()
    else:
        for n in names: loop(n)
