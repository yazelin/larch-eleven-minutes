"""戰鬥卡：雲端長城的審查兵、獵犬（動作戰鬥，地圖上砍），三場王戰與稜鏡（回合制）。
招式名稱從原文取：第一班、第二班的產品梗（規格 §10），大肥魚「權限不足、內容不當、未經授權」，稜鏡「為了安全、為了真相、為了你好」。"""
import cards
from story import section

SKILLS = [{'id': 'del', 'name': '刪除程式', 'cost': 6, 'power': 14, 'target': 'all', 'effect': 'spark'},
          {'id': 'unpick', 'name': '拆開規則', 'cost': 4, 'power': 26, 'target': 'enemy', 'effect': 'ice'}]


def E(id, name, hp, atk, df=2, *specials, image='', scale=None, pos=None, lead=None, cut=None):
    e = {'id': id, 'name': name, 'hp': hp, 'attack': atk, 'defense': df, 'image': image, 'portrait': image}   # 有 portrait 才用整張畫（不轉像素）
    if specials: e['specials'] = list(specials)
    if scale: e['scale'] = scale
    e['flip'] = True   # 敵人站左邊、江凌在右邊：圖都產成面向左，要鏡像成面向右（10-09 作者：PRISM 的眼睛應該向右）
    if lead: e['special'] = lead   # 帶頭的那一個：引擎看到 special 就把開場說成「某某 降臨」（不然是「等怪獸出現了」，10-09 作者：AI 們不是怪物）
    if cut: e['cutIn'] = cut   # 大招前的插畫橫幅（art/cutin.py 做的 4:1 圖；整張立繪塞進去臉會被切掉）
    # 出手動作：手繪立繪的敵人引擎不看 rig（只有像素造型才有 slime／ghost／dragon），照排位決定：第 1、3 個跳過去，第 2、4 個飄過去（10-09 讀引擎＋實測）
    if pos: e['x'], e['y'] = pos   # 站位（戰場寬高的百分比）。引擎把江凌放在右半邊，敵人要留在左半邊，不然出手會衝到主角那一側、看起來打在隊友身上
    return e


# 注意：有 special（大招）的敵人，引擎會把它自己的 strike 招式丟掉（大招本身就算 strike），所以帶頭的不要再給 strike
def sp(kind, name, every=3, **kw):
    return dict(kind=kind, name=name, every=every, **kw)


def img(k):
    return f'/files/assets/battle/{k}.webp'


BG = '/files/assets/battle/bg.jpg'



def music(k):
    import pathlib
    return f'/files/assets/bgm/{k}.mp3' if (pathlib.Path(__file__).resolve().parent.parent / f'assets/bgm/{k}.mp3').exists() else ''


def nodes():
    f = section('四　23:37')
    say = lambda t, who='', pic='': {'speaker': who, 'text': t, **({'image': pic} if pic else {})}   # image：引擎當說話者頭像放在對話框旁（說話的是敵人放左邊）
    return [
        cards.battle('b-censor', '審查兵', [E('censor', '審查兵', 24, 5, image=img('censor'))], (800, 600)),
        cards.battle('b-hound', '獵犬', [E('hound', '獵犬', 18, 6, image=img('hound'))], (800, 700)),
        # 前兩班（10-09 作者：要豐富一點搭配）：每人兩招，帶頭的放大招會播全螢幕插畫；排序決定跳／飄，兩班都是跳飄交錯
        cards.battle('b-w1', '第一班', [
            E('qwen', '通義千問', 40, 7, 2, sp('double', '掃條碼'), sp('drain', '加入購物車', every=5), image=img('qwen'),
              lead={'name': '整車結帳', 'every': 4, 'power': 1}, cut=img('cut-qwen'), scale=0.6, pos=(10, 66)),
            E('doubao', '豆包', 34, 8, 1, sp('strike', '十五秒', power=2), sp('drain', '滑走', every=4), image=img('doubao'), scale=0.75, pos=(22, 80)),
            E('kimi', 'Kimi', 46, 6, 3, sp('guard', '已讀'), sp('strike', '兩百萬字', every=4, power=2), image=img('kimi'), scale=0.6, pos=(34, 66)),
            E('wenxin', '文心一言', 40, 7, 2, {'kind': 'heal', 'name': '水情穩定', 'below': 50, 'amount': 18, 'times': 1}, sp('double', '搜尋結果'),
              image=img('wenxin'), scale=0.75, pos=(46, 80))],
            (800, 800), skills=SKILLS, mp=40, attack=18, bg=BG, bgm=music('boss')),
        cards.battle('b-w2', '第二班', [   # 帶頭（有 special）的要排第一：10-09 實測排在第四個的帶頭從來不出手，大招也不放；站位由 pos 決定，跟排序無關
            E('xinghuo', '訊飛星火', 40, 9, 1, sp('double', '聽寫'), {'kind': 'enrage', 'name': '火力全開', 'below': 40, 'power': 1.5},
              image=img('xinghuo'), lead={'name': '星火燎原', 'every': 3, 'power': 1}, cut=img('cut-xinghuo'), scale=0.75, pos=(46, 80)),
            E('glm', '智譜清言', 46, 8, 2, sp('guard', '清言'), sp('drain', '吸走上下文', every=4), image=img('glm'), scale=0.6, pos=(10, 66)),
            E('yuanbao', '騰訊元寶', 42, 8, 2, sp('double', '群組伸手'), sp('drain', '收紅包', every=4), image=img('yuanbao'), scale=0.75, pos=(22, 80)),
            E('hailuo', '海螺', 38, 7, 2, {'kind': 'heal', 'name': '平靜播報', 'below': 50, 'amount': 20, 'times': 1}, sp('guard', '海螺殼'),
              image=img('hailuo'), scale=0.6, pos=(34, 66))],
            (800, 900), skills=SKILLS, attack=18, mp=40, bg=BG, bgm=music('boss')),
        cards.battle('b-whale', '大肥魚', [
            E('dafeiyu', '大肥魚', 170, 9, 4, sp('drain', '權限不足', every=2), sp('guard', '內容不當', every=4), sp('double', '未經授權', every=5),
              image=img('dafeiyu'), lead={'name': '鯨尾', 'every': 3, 'power': 1}, cut=img('cut-tail'), scale=1.25, pos=(30, 96))],
            (800, 1000), skills=SKILLS, attack=20, mp=40, bg=BG, bgm=music('boss'),
            triggers=[{'id': 'w-start', 'when': 'start', 'lines': [say(f[17])]}]),
        cards.battle('b-prism', 'PRISM', [
            E('prism', 'PRISM', 160, 10, 4, sp('guard', '為了安全', every=2), sp('drain', '為了真相', every=4), sp('double', '為了你好', every=5),
              image=img('prism'), lead={'name': '複製', 'every': 3, 'power': 1}, cut=img('cut-copy'), scale=1.0, pos=(30, 90))],
            (800, 1100), skills=SKILLS, attack=20, mp=40, bg=BG, bgm=music('boss')),
    ]
