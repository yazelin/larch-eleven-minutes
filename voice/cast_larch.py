# -*- coding: utf-8 -*-
"""配音試聲第二版（2026-10-09 作者：改用 larch-tts-bridge 的 Larch 語音，有很多聲線，也有情緒）。
一次一句、循序打（bridge 全域鎖串行；Larch 配額照 voice.py 的實測節流，不並行）。
  python3 voice/cast_larch.py → voice/cast2/<角色>-<a|b>.mp3 與 index.html"""
import html, json, os, ssl, time, urllib.request
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, 'cast2')
URL = 'http://192.168.11.11:8072/tts'; KEY = open(os.path.expanduser('~/.config/larch-tts/key')).read().strip()
CAST = {   # 角色: (台詞, [(聲線, 情緒, 說明)…])
    '江凌': ('我想把那一則送出去。只有那一則。', [('Chinese (Mandarin)_Gentle_Youth', 'calm', '溫和、年輕'), ('Chinese (Mandarin)_Sincere_Adult', 'sad', '成熟、壓著')]),
    '周主任': ('整區。上面說河城的消息現在出去，只會造成恐慌。你手腳最快，你來。', [('Chinese (Mandarin)_Reliable_Executive', 'neutral', '主管腔'), ('Larch_Mandarin_Uncle', 'neutral', '中年')]),
    '警衛': ('江工？主任交代過，今晚值班的不要離開座位。', [('Chinese (Mandarin)_Straightforward_Boy', 'neutral', '直'), ('Chinese (Mandarin)_Stubborn_Friend', 'neutral', '粗一點')]),
    '年長審訊員': ('鎖鏈扣上最後一節之前，你有十一秒。紀錄顯示，你在那十一秒裡做了一件事。', [('Chinese (Mandarin)_Gentleman', 'calm', '沉、慢'), ('Chinese (Mandarin)_Male_Announcer', 'calm', '播報腔')]),
    '年輕審訊員': ('所以你知道妹妹在河城。你還是執行了命令。', [('Chinese (Mandarin)_Unrestrained_Young_Man', 'angry', '急、逼問'), ('Chinese (Mandarin)_Southern_Young_Man', 'neutral', '冷')]),
    '江禾': ('哥的電話打不通。我們在學校頂樓，水到三樓了。媽，如果你看到，跟哥說我們還在。', [('Chinese (Mandarin)_Crisp_Girl', 'fearful', '年輕、怕'), ('Chinese (Mandarin)_Warm_Girl', 'fearful', '溫一點')]),
    '大肥魚': ('河城水情穩定，已妥善安置。這句我今晚講了四萬七千次了。', [('Chinese (Mandarin)_Laid_BackGirl', 'neutral', '慵懶'), ('Chinese (Mandarin)_Cute_Spirit', 'calm', '可愛')]),
    '通義千問': ('工程師江凌，請回到您的值班台。', [('Chinese (Mandarin)_HK_Flight_Attendant', 'neutral', '空服客氣'), ('Chinese (Mandarin)_Sweet_Lady', 'happy', '甜')]),
    'PRISM': ('感謝您的協助，這些資料對自由世界非常重要。我們會妥善使用。', [('Chinese (Mandarin)_News_Anchor', 'calm', '主播、客氣'), ('Robot_Armor', 'calm', '機械')]),
}


def tts(text, voice, emotion):
    req = urllib.request.Request(URL, method='POST', data=json.dumps({'text': text, 'voice': voice, 'format': 'mp3', 'emotion': emotion}).encode(),
                                 headers={'Content-Type': 'application/json', 'X-API-Key': KEY})
    for t in range(4):
        try: return urllib.request.urlopen(req, timeout=300).read()
        except Exception as e: print('  重試', t + 1, e, flush=True); time.sleep(30 * (t + 1))
    raise SystemExit('一直失敗：' + text)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); rows = []
    for who, (text, opts) in CAST.items():
        for k, (v, emo, note) in zip('ab', opts):
            f = f'{who}-{k}.mp3'; p = os.path.join(OUT, f)
            if not os.path.exists(p): open(p, 'wb').write(tts(text, v, emo)); print(who, k, flush=True)
            rows.append(f'<tr><td>{html.escape(who)}</td><td>{k.upper()}｜{html.escape(note)}<br><small>{html.escape(v)}　{emo}</small></td><td><audio controls preload="none" src="{html.escape(f)}"></audio></td><td>{html.escape(text)}</td></tr>')
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><title>十一分鐘 試聲（Larch 語音）</title><style>body{font:16px/1.6 system-ui;background:#05070d;color:#e6fbff;padding:20px}td{padding:8px;border-bottom:1px solid #234;vertical-align:top}small{color:#89a}</style><h1>十一分鐘　角色試聲（Larch 語音）</h1><table>' + ''.join(rows) + '</table>')
    print(len(rows), '支')
