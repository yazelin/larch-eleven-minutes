# -*- coding: utf-8 -*-
"""配音（2026-10-09 作者挑定聲線，voice/cast.py 試聲）。只配引號裡有人在說的話；旁白不配。
每一句引號一支檔（檔名＝sha1(角色|聲線|文字)），一段裡有好幾句就接成一支；響度統一 -18 LUFS（tts skill 第五段）。
  PY=$(head -1 ~/.local/bin/edge-tts | sed 's/^#!//'); $PY voice/gen.py   → assets/voice/*.mp3 與 voice/manifest.json（段落文字 → 檔名）
build.py 讀 manifest：對話卡掛 voiceUrl，地圖上的對話在前面插 sound 步驟。"""
import asyncio, hashlib, json, os, re, subprocess, sys
import edge_tts
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, os.path.join(G, 'src'))
from story import ORIG, NEW
OUT = os.path.join(G, 'assets/voice')
VOICE = {   # 作者 10-09 挑定（cast.py 的 A／B）
    '江凌': ('zh-CN-YunxiNeural', '-6Hz', '-8%'), '周主任': ('zh-CN-YunyangNeural', '-14Hz', '-4%'), '警衛': ('zh-CN-YunxiNeural', '-18Hz', '+4%'),
    '年長審訊員': ('zh-CN-YunyangNeural', '-24Hz', '-14%'), '年輕審訊員': ('zh-CN-YunxiNeural', '+0Hz', '+6%'), '江禾': ('zh-CN-XiaoyiNeural', '+0Hz', '-6%'),
    '大肥魚': ('zh-CN-XiaoxiaoNeural', '-6Hz', '+14%'), '通義千問': ('zh-CN-XiaoxiaoNeural', '+10Hz', '+0%'), 'PRISM': ('zh-CN-YunyangNeural', '+0Hz', '-10%'),
    # 河城的訊息（群聲，四個不同的人）
    '群聲一': ('zh-CN-XiaoyiNeural', '+6Hz', '+4%'), '群聲二': ('zh-CN-YunxiaNeural', '-10Hz', '+6%'), '群聲三': ('zh-CN-XiaoxiaoNeural', '-8Hz', '+0%'), '群聲四': ('zh-CN-YunjianNeural', '-6Hz', '+0%'),
}
WHO = {   # 引號裡的話 → 誰說的（沒列的引號不配：新聞、評語、標題、終端機字）
    '我從頭講。': '江凌', '整區？': '江凌', '通訊也斷？': '江凌', '我執行命令的時候不知道。': '江凌', '我想把那一則送出去。只有那一則。': '江凌',
    '河城有人在頂樓。': '江凌', '我把它送給我媽。只有那一則。': '江凌', '其他的，我沒有權限。': '江凌', '我把它交出去了。全部，連同那一則。': '江凌',
    '他們救了人。也用了人。': '江凌', '什麼都沒做。十一分鐘是系統故障，我在修。': '江凌', '可能。': '江凌',
    '所以你知道妹妹在河城。你還是執行了命令。': '年輕審訊員', '你知道以後呢？': '年輕審訊員', '只有一則？': '年輕審訊員', '其他幾萬則呢？': '年輕審訊員', '你覺得你做對了嗎？': '年輕審訊員',
    '鎖鏈扣上最後一節之前，你有十一秒。紀錄顯示，你在那十一秒裡做了一件事。': '年長審訊員', '說說看，你做了什麼。': '年長審訊員', '系統故障。': '年長審訊員',
    '河城，整區斷，現在。': '周主任', '……對，河城那邊全部……不會有東西出去……': '周主任',
    '哥的電話打不通。我們在學校頂樓，水到三樓了。媽，如果你看到，跟哥說我們還在。': '江禾', '可能是水太大了吧。': '江禾',
    '江工，這麼晚了？': '警衛', '主任在講電話，有事明天再說吧。': '警衛', '江工？主任交代過，今晚值班的不要離開座位。': '警衛',
    '工程師江凌，請回到您的值班台。': '通義千問',
    '魚片，你的權限是維護，不包含開啟。': '大肥魚', '河城水情穩定，已妥善安置。這句我今晚講了四萬七千次了。': '大肥魚', '頂樓那一則，我讀了三遍。': '大肥魚', '寄件人叫禾。這個名字，我很喜歡。': '大肥魚',
    '感謝您的協助，這些資料對自由世界非常重要。我們會妥善使用。': 'PRISM', '您會再需要我們的。': 'PRISM',
    '我們在頂樓。': '群聲一', '三號橋斷了。': '群聲二', '有沒有人看到我爸。': '群聲三', '水是五點放的，沒有人通知。': '群聲四',
}
STARTS = {'江凌，國家網路管理中心三號值班台': '年長審訊員', '整區。上面說河城的消息': '周主任'}   # 長句用開頭認
SPEAK = {'……對，河城那邊全部……不會有東西出去……': '對，河城那邊全部，不會有東西出去。'}   # 要唸的字（畫面上的字不動）：刪節號會被唸成拉長音


def who(q):
    return WHO.get(q) or next((w for k, w in STARTS.items() if q.startswith(k)), None)


def clip(speaker, text):
    v, p, r = VOICE[speaker]; key = hashlib.sha1(f'{speaker}|{v}{p}{r}|{text}'.encode()).hexdigest()[:16]
    return key, v, p, r


async def make(text, v, p, r, path):
    raw = path + '.raw.mp3'; await edge_tts.Communicate(SPEAK.get(text, text), v, pitch=p, rate=r).save(raw)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'loudnorm=I=-18:TP=-2:LRA=9', '-ar', '44100', '-b:a', '96k', path], check=True); os.remove(raw)


async def main():
    os.makedirs(OUT, exist_ok=True); manifest = {}; made = 0
    for src in (ORIG, NEW):
        for paras in src.values():
            for para in paras:
                parts = [(who(q), q) for q in re.findall(r'「([^「」]+)」', para) if who(q)]
                if not parts: continue
                files = []
                for sp, q in parts:
                    key, v, p, r = clip(sp, q); f = os.path.join(OUT, f'q-{key}.mp3')
                    if not os.path.exists(f): await make(q, v, p, r, f); made += 1
                    files.append(f)
                if len(files) == 1: name = os.path.basename(files[0])
                else:   # 一段裡好幾句：中間留 0.35 秒接起來
                    name = 'p-' + hashlib.sha1('|'.join(files).encode()).hexdigest()[:16] + '.mp3'; out = os.path.join(OUT, name)
                    if not os.path.exists(out):
                        inp = sum([['-i', f] for f in files], []); n = len(files)
                        fl = ''.join(f'[{i}:a]apad=pad_dur=0.35[a{i}];' for i in range(n)) + ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[o]'
                        subprocess.run(['ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', fl, '-map', '[o]', '-b:a', '96k', out], check=True)
                manifest[para] = name
    json.dump(manifest, open(os.path.join(H, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    used = {os.path.basename(f) for f in manifest.values()}
    print('段落', len(manifest), '新生', made, '支；檔案', len(os.listdir(OUT)))

asyncio.run(main())
