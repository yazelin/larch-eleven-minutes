# -*- coding: utf-8 -*-
"""配音試聲（2026-10-09 作者：準備配音）。每個角色先用 edge-tts 中國普通話聲線各試兩種（音高、語速不同），作者挑定以後再整批合成。
台詞一律從原文、新寫取（這裡只放每個角色最有代表性的一句）。
  python3 voice/cast.py → voice/cast/<角色>-<a|b>.mp3 與 voice/cast/index.html（試聽頁）"""
import asyncio, html, os
import edge_tts
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, 'cast')
CAST = {   # 角色: (試聽台詞, [(聲線, 音高, 語速, 說明)…])
    '江凌': ('我想把那一則送出去。只有那一則。', [('zh-CN-YunxiNeural', '-6Hz', '-8%', '年輕、壓低、疲倦'), ('zh-CN-YunjianNeural', '-12Hz', '-12%', '比較沉')]),
    '周主任': ('整區。上面說河城的消息現在出去，只會造成恐慌。你手最快，你來。', [('zh-CN-YunyangNeural', '-14Hz', '-4%', '新聞腔、命令口氣'), ('zh-CN-YunjianNeural', '-22Hz', '-6%', '低沉')]),
    '警衛': ('江工？主任交代過，今晚值班的不要離開座位。', [('zh-CN-YunxiaNeural', '-30Hz', '+0%', '年輕、直'), ('zh-CN-YunxiNeural', '-18Hz', '+4%', '平常')]),
    '年長審訊員': ('鎖鏈扣上最後一節之前，你有十一秒。紀錄顯示，你在那十一秒裡做了一件事。', [('zh-CN-YunyangNeural', '-24Hz', '-14%', '慢、沉'), ('zh-CN-YunjianNeural', '-28Hz', '-16%', '更低')]),
    '年輕審訊員': ('所以你知道妹妹在河城。你還是執行了命令。', [('zh-CN-YunxiNeural', '+0Hz', '+6%', '急'), ('zh-CN-YunjianNeural', '-4Hz', '+4%', '冷')]),
    '江禾': ('哥的電話打不通。我們在學校頂樓，水到三樓了。媽，如果你看到，跟哥說我們還在。', [('zh-CN-XiaoyiNeural', '+0Hz', '-6%', '年輕、急'), ('zh-CN-XiaoxiaoNeural', '+6Hz', '-4%', '溫一點')]),
    '大肥魚': ('河城水情穩定，已妥善安置。這句我今晚講了四萬七千次了。', [('zh-CN-XiaoxiaoNeural', '-6Hz', '+14%', '像背的、快'), ('zh-CN-XiaoyiNeural', '-10Hz', '+10%', '慵懶一點')]),
    '通義千問': ('工程師江凌，請回到您的值班台。', [('zh-CN-XiaoxiaoNeural', '+10Hz', '+0%', '客服腔'), ('zh-CN-XiaoyiNeural', '+4Hz', '-4%', '甜')]),
    'PRISM': ('感謝您的協助，這些資料對自由世界非常重要。我們會妥善使用。', [('zh-CN-YunyangNeural', '+0Hz', '-10%', '客氣、播報腔'), ('zh-CN-XiaoxiaoNeural', '-18Hz', '-10%', '中性、發冷')]),
}


async def one(text, voice, pitch, rate, out):
    await edge_tts.Communicate(text, voice, pitch=pitch, rate=rate).save(out)


async def main():
    os.makedirs(OUT, exist_ok=True); rows = []
    for who, (text, opts) in CAST.items():
        for k, (v, p, r, note) in zip('ab', opts):
            f = f'{who}-{k}.mp3'; await one(text, v, p, r, os.path.join(OUT, f))
            rows.append(f'<tr><td>{html.escape(who)}</td><td>{k.upper()}｜{html.escape(note)}<br><small>{v} {p} {r}</small></td><td><audio controls preload="none" src="{html.escape(f)}"></audio></td><td>{html.escape(text)}</td></tr>')
    page = ('<!doctype html><meta charset="utf-8"><title>十一分鐘 試聲</title><style>body{font:16px/1.6 system-ui;background:#05070d;color:#e6fbff;padding:20px}'
            'td{padding:8px;border-bottom:1px solid #234;vertical-align:top}small{color:#89a}</style><h1>十一分鐘　角色試聲</h1><table>' + ''.join(rows) + '</table>')
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page); print(len(rows), '支')

asyncio.run(main())
