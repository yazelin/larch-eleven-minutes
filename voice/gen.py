# -*- coding: utf-8 -*-
"""配音（2026-10-09 作者改用 larch-tts-bridge：Larch 的語音，聲線多、有情緒；試聲 voice/cast_larch.py）。只配引號裡有人在說的話；旁白不配。
每一句引號一支檔（檔名＝sha1(角色|聲線|情緒|文字)），一段裡有好幾句就接成一支；響度由 bridge 統一到 -18 LUFS。
  python3 voice/gen.py   → assets/voice/*.mp3 與 voice/manifest.json（段落文字 → 檔名）
build.py 讀 manifest：對話卡掛 voiceUrl，地圖上的對話在前面插 sound 步驟。"""
import hashlib, json, os, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
sys.path.insert(0, os.path.join(G, 'src'))
from story import ORIG, NEW
OUT = os.path.join(G, 'assets/voice')
VOICE = {   # 角色: (Larch 聲線, 預設情緒)。作者 10-09 去吃飯前交代「全部配完再審」，聲線先照試聲 A 版（警衛照上一輪挑 B），回來可以換
    '江凌': ('Chinese (Mandarin)_Gentle_Youth', 'calm'), '周主任': ('Chinese (Mandarin)_Reliable_Executive', 'neutral'),
    '警衛': ('Chinese (Mandarin)_Stubborn_Friend', 'neutral'), '年長審訊員': ('Chinese (Mandarin)_Gentleman', 'calm'),
    '年輕審訊員': ('Chinese (Mandarin)_Unrestrained_Young_Man', 'neutral'), '江禾': ('Chinese (Mandarin)_Crisp_Girl', 'fearful'),
    '大肥魚': ('Chinese (Mandarin)_Laid_BackGirl', 'neutral'), '通義千問': ('Chinese (Mandarin)_IntellectualGirl', 'neutral'),
    'PRISM': ('edge:zh-TW-HsiaoChenNeural', '-'),   # 稜鏡用 edge-tts 小臻（作者 10-09）
    '群聲一': ('Chinese (Mandarin)_Warm_Girl', 'fearful'), '群聲二': ('Chinese (Mandarin)_Pure-hearted_Boy', 'fearful'),
    '群聲三': ('Larch_Mandarin_Child', 'fearful'), '群聲四': ('Larch_Mandarin_Dad', 'angry'),
}
EMO = {   # 個別台詞的情緒（沒列的用角色預設）
    '所以你知道妹妹在河城。你還是執行了命令。': 'angry', '你覺得你做對了嗎？': 'neutral',
    '整區？通訊也斷？': 'surprised', '只有一則？其他幾萬則呢？': 'surprised', '河城有人在頂樓。': 'sad', '其他的，我沒有權限。': 'calm',
    '他們救了人。也利用了人。': 'sad', '可能。': 'sad', '我把它送給我媽。只有那一則。': 'calm',
    '可能是水太大了吧。': 'calm', '寄件人叫禾。這個名字，我很喜歡。': 'happy', '頂樓那一則，我讀了三遍。': 'sad',
    '小江，把河城整區切斷，現在！': 'neutral', '江工，這麼晚了？': 'surprised',
}
WHO = {   # 引號裡的話 → 誰說的（沒列的引號不配：新聞、評語、標題、終端機字）
    '我從頭講。': '江凌', '整區？': '江凌', '通訊也斷？': '江凌', '我執行命令的時候不知道。': '江凌', '我想把那一則送出去。只有那一則。': '江凌',
    '河城有人在頂樓。': '江凌', '我把它送給我媽。只有那一則。': '江凌', '其他的，我沒有權限。': '江凌', '我把它交出去了。全部，連同那一則。': '江凌',
    '他們救了人。也利用了人。': '江凌', '什麼都沒做。十一分鐘是系統故障，我在修。': '江凌', '可能。': '江凌',
    '所以你知道妹妹在河城。你還是執行了命令。': '年輕審訊員', '你知道以後呢？': '年輕審訊員', '只有一則？': '年輕審訊員', '其他幾萬則呢？': '年輕審訊員', '你覺得你做對了嗎？': '年輕審訊員',
    '鎖鏈扣上最後一節之前，你有十一秒。紀錄顯示，你在那十一秒裡做了一件事。': '年長審訊員', '說說看，你做了什麼。': '年長審訊員', '系統故障。': '年長審訊員',
    '小江，把河城整區切斷，現在！': '周主任', '……對，河城那邊全部……不會有東西出去……': '周主任',
    '哥的電話打不通。我們在學校頂樓，水到三樓了。媽，如果你看到，跟哥說我們還在。': '江禾', '可能是水太大了吧。': '江禾',
    '江工，這麼晚了？': '警衛', '主任在講電話，有事明天再說吧。': '警衛', '江工？主任交代過，今晚值班的不要離開座位。': '警衛',
    '工程師江凌，請回到您的值班台。': '通義千問',
    '魚片，你的權限是維護，不包含開啟。': '大肥魚', '河城水情穩定，已妥善安置。這句我今晚講了四萬七千次了。': '大肥魚', '頂樓那一則，我讀了三遍。': '大肥魚', '寄件人叫禾。這個名字，我很喜歡。': '大肥魚',
    '感謝您的協助，這些資料對自由世界非常重要。我們會妥善使用。': 'PRISM', '您會再需要我們的。': 'PRISM',
    '我們在頂樓。': '群聲一', '三號橋斷了。': '群聲二', '有沒有人看到我爸。': '群聲三', '水是五點放的，沒有人通知。': '群聲四',
}
STARTS = {'江凌，國家網路管理中心三號值班台': '年長審訊員', '整區。上面說河城的消息': '周主任'}   # 長句用開頭認
CROWD = {'「我們在頂樓。」「三號橋斷了。」「有沒有人看到我爸。」「水是五點放的，沒有人通知。」': 1.5}   # 段落 → 每句晚幾秒進來（疊著播）
SPEAK = {'……對，河城那邊全部……不會有東西出去……': '對，河城那邊全部，不會有東西出去。'}   # 要唸的字（畫面上的字不動）：刪節號會被唸成拉長音


def who(q):
    return WHO.get(q) or next((w for k, w in STARTS.items() if q.startswith(k)), None)


URL = 'http://192.168.11.11:8072/tts'; KEY = open(os.path.expanduser('~/.config/larch-tts/key')).read().strip()


def clip(speaker, text):
    v, emo = VOICE[speaker]; emo = EMO.get(text, emo)
    if v.startswith('edge:'): emo = '-'   # edge-tts 沒有情緒參數
    return hashlib.sha1(f'{speaker}|{v}|{emo}|{text}'.encode()).hexdigest()[:16], v, emo


def make(text, v, emo, path):
    """bridge 已經做好替身、去頭尾靜音、-18 LUFS；這裡只轉成 96k。edge-tts 的句子自己去頭尾靜音、壓到 -18 LUFS"""
    if v.startswith('edge:'):
        raw = path + '.raw.mp3'
        subprocess.run(['edge-tts', '--voice', v[5:], '--text', SPEAK.get(text, text), '--write-media', raw], check=True, capture_output=True)
        trim = 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', trim + ',loudnorm=I=-18:TP=-2:LRA=9', '-ar', '44100', '-b:a', '96k', path], check=True); os.remove(raw); return
    body = json.dumps({'text': SPEAK.get(text, text), 'voice': v, 'format': 'mp3', 'emotion': emo}).encode()
    for t in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(URL, method='POST', data=body, headers={'Content-Type': 'application/json', 'X-API-Key': KEY}), timeout=300).read()
            raw = path + '.raw.mp3'; open(raw, 'wb').write(data)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-ar', '44100', '-b:a', '96k', path], check=True); os.remove(raw); return
        except Exception as e:
            print('  重試', t + 1, text[:12], e, flush=True); time.sleep(20 * (t + 1))
    raise SystemExit('一直失敗：' + text)


def main():
    os.makedirs(OUT, exist_ok=True); manifest = {}; jobs = {}; plan = []
    for src in (ORIG, NEW):
        for paras in src.values():
            for para in paras:
                parts = [(who(q), q) for q in re.findall(r'「([^「」]+)」', para) if who(q)]
                if not parts: continue
                if len(parts) > 1 and len({sp for sp, _ in parts}) == 1:   # 同一個人連說幾句：整段一次配（分開配聲線會偏，作者 10-09）
                    parts = [(parts[0][0], ''.join(q for _, q in parts))]
                files = []
                for sp, q in parts:
                    key, v, emo = clip(sp, q); f = os.path.join(OUT, f'q-{key}.mp3'); files.append(f)
                    if not os.path.exists(f): jobs[f] = (q, v, emo)
                plan.append((para, files))
    with ThreadPoolExecutor(3) as ex:   # 3 條並行（作者 10-09：Larch 用量已提高、可以平行；bridge 那邊還是一次一句，排隊而已）
        list(ex.map(lambda kv: make(kv[1][0], kv[1][1], kv[1][2], kv[0]), jobs.items()))
    for para, files in plan:
        if len(files) == 1: name = os.path.basename(files[0])
        elif para in CROWD:   # 好幾個人搶著說：每句晚 CROWD 秒進來、疊在一起播，再壓回 -18 LUFS（作者 10-09：河城群聲要交錯同時播）
            name = 'm-' + hashlib.sha1(('|'.join(files) + f'|{CROWD[para]}').encode()).hexdigest()[:16] + '.mp3'; out = os.path.join(OUT, name)
            if not os.path.exists(out):
                inp = sum([['-i', f] for f in files], []); n = len(files); ms = int(CROWD[para] * 1000)
                fl = ''.join(f'[{i}:a]adelay={i * ms}:all=1[a{i}];' for i in range(n)) + ''.join(f'[a{i}]' for i in range(n)) + f'amix=inputs={n}:duration=longest:normalize=0,loudnorm=I=-18:TP=-2:LRA=9[o]'
                subprocess.run(['ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', fl, '-map', '[o]', '-ar', '44100', '-b:a', '96k', out], check=True)
        else:   # 一段裡好幾句：中間留 0.35 秒接起來
            name = 'p-' + hashlib.sha1('|'.join(files).encode()).hexdigest()[:16] + '.mp3'; out = os.path.join(OUT, name)
            if not os.path.exists(out):
                inp = sum([['-i', f] for f in files], []); n = len(files)
                fl = ''.join(f'[{i}:a]apad=pad_dur=0.35[a{i}];' for i in range(n)) + ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[o]'
                subprocess.run(['ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', fl, '-map', '[o]', '-b:a', '96k', out], check=True)
        manifest[para] = name
    used = set(manifest.values()) | {os.path.basename(f) for _, fs in plan for f in fs}
    for f in os.listdir(OUT):   # 舊聲線的檔清掉
        if f not in used: os.remove(os.path.join(OUT, f))
    json.dump(manifest, open(os.path.join(H, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('段落', len(manifest), '新生', len(jobs), '支；檔案', len(os.listdir(OUT)))


if __name__ == '__main__':
    main()
