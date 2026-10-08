"""雲端之戰的走路圖：直接沿用《香布纏．續》的 xu/game/art/walk.py（.11 codex-image、3 欄×4 列、每格 288×384、俯角、分方向產）。
參考圖＝暫代人物（《續》魏續十八歲）的正面那排：作者 2026-10-08「拿現在的某個人當參考來產生對應的版本」，只借視角、姿勢、比例與畫風。
用法：python3 art/walk.py gen [id…]   python3 art/walk.py cut [id…]"""
import importlib.util, os, sys
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('xuwalk', os.path.expanduser('~/larch-taoyuan/xu/game/art/walk.py'))
W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)   # 它會 chdir 到 larch-taoyuan，參考圖一律給絕對路徑
W.RAW, W.OUT, W.CHK = os.path.join(G, 'art/walk_raw'), os.path.join(G, 'assets/walk'), os.path.join(G, 'art/check')
W.MIRROR_LEFT, W.MIRROR_RIGHT = set(), {'censor'}   # 審查兵往右那排產成臉朝左（2026-10-09），用左向鏡射
REF = os.path.join(G, 'art/walk_raw/ref-placeholder-front.png')
DIFF = ("a DIFFERENT person from image 1 (image 1 only shows the camera angle, the walking poses, the body proportions and the painting style to copy; "
        "do NOT copy his face, hair or ancient clothes): ")
W.CAST = {
    'jiangling': ([REF], 1.0, DIFF + "a modern Chinese network engineer about 28, slim, short neat black hair, thin black-framed glasses, tired eyes, "
                  "a dark charcoal zip-up hoodie open over a plain white T-shirt, a blue lanyard with a white ID card on his chest, dark jeans, grey sneakers, "
                  "empty hands."),
    'zhou': ([REF], 0.97, DIFF + "a modern Chinese office manager about 52, slightly heavy with a small belly, receding short black hair with grey at the temples, "
             "a stern tired face, a white long-sleeve dress shirt with sleeves rolled up, a dark tie loosened, dark grey slacks, black leather shoes, "
             "a blue lanyard with an ID card tucked into the shirt pocket, empty hands."),
    'guard': ([REF], 1.0, DIFF + "a modern Chinese office building security guard about 35, sturdy, short cropped black hair, a dark navy security uniform "
              "with a peaked cap, a walkie-talkie clipped on the shoulder, a black belt with a baton holster, black boots, expressionless, empty hands."),
    # 雲端長城的敵人（2026-10-09）：圖 2 是戰鬥卡那張，臉、制服、配色照它
    'censor': ([REF, os.path.join(G, 'assets/battle/censor.webp')], 1.0, DIFF + "a censorship program shown as a soldier, exactly like image 2: a plain grey uniform and cap, "
               "NO facial features at all, the face is a blank grey surface with one horizontal glowing red scan line across it, grey gloves, black boots, "
               "a short grey baton in one hand."),
    'hound': ([REF, os.path.join(G, 'assets/battle/hound.webp')], 0.8, "NOT a person: a four-legged sniffer hound made of grey data blocks, exactly like image 2 "
              "(image 1 only shows the camera angle, the frame layout and the painting style to copy): lean grey dog, no eyes, one glowing red scan line across its face, "
              "walking on all four legs with its nose low."),
}
if __name__ == '__main__':
    cmd, ids = sys.argv[1], sys.argv[2:] or list(W.CAST)
    if cmd == 'gen': W.gen(ids)
    elif cmd == 'cut':
        for i in ids: W.cut(i)
