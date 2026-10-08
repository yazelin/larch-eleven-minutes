"""戰鬥卡：雲端長城的審查兵、獵犬（動作戰鬥，地圖上砍），三場王戰與稜鏡（回合制）。
招式名稱從原文取：第一班、第二班的產品梗（規格 §10），大肥魚「權限不足、內容不當、未經授權」，稜鏡「為了安全、為了真相、為了你好」。"""
import cards
from story import section

SKILLS = [{'id': 'del', 'name': '刪除程式', 'cost': 6, 'power': 14, 'target': 'all', 'effect': 'spark'},
          {'id': 'unpick', 'name': '拆開規則', 'cost': 4, 'power': 26, 'target': 'enemy', 'effect': 'ice'}]


def E(id, name, hp, atk, df=2, *specials, image='', scale=None, pos=None, lead=None):
    e = {'id': id, 'name': name, 'hp': hp, 'attack': atk, 'defense': df, 'image': image, 'portrait': image}   # 有 portrait 才用整張畫（不轉像素）
    if specials: e['specials'] = list(specials)
    if scale: e['scale'] = scale
    e['flip'] = True   # 敵人站左邊、江凌在右邊：圖都產成面向左，要鏡像成面向右（10-09 作者：PRISM 的眼睛應該向右）
    if lead: e['special'] = lead   # 帶頭的那一個：引擎看到 special 就把開場說成「某某 降臨」（不然是「等怪獸出現了」，10-09 作者：AI 們不是怪物）
    if pos: e['x'], e['y'] = pos   # 站位（戰場寬高的百分比）。引擎把江凌放在右半邊，敵人要留在左半邊，不然出手會衝到主角那一側、看起來打在隊友身上
    return e


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
    say = lambda t: {'speaker': '', 'text': t}
    return [
        cards.battle('b-censor', '審查兵', [E('censor', '審查兵', 24, 5, image=img('censor'))], (800, 600)),
        cards.battle('b-hound', '獵犬', [E('hound', '獵犬', 18, 6, image=img('hound'))], (800, 700)),
        cards.battle('b-w1', '第一班', [
            E('qwen', '通義千問', 40, 7, 2, sp('double', '掃條碼'), image=img('qwen'), lead={'name': '掃條碼', 'every': 4, 'power': 1}, scale=0.6, pos=(10, 66)),
            E('doubao', '豆包', 34, 8, 1, sp('strike', '十五秒', power=2), image=img('doubao'), scale=0.75, pos=(22, 80)),
            E('kimi', 'Kimi', 46, 6, 3, sp('guard', '已讀'), image=img('kimi'), scale=0.6, pos=(34, 66)),
            E('wenxin', '文心一言', 40, 7, 2, {'kind': 'heal', 'name': '水情穩定', 'below': 50, 'amount': 18, 'times': 1}, image=img('wenxin'), scale=0.75, pos=(46, 80))],
            (800, 800), skills=SKILLS, mp=40, attack=18, bg=BG, bgm=music('boss')),
        cards.battle('b-w2', '第二班', [
            E('glm', '智譜清言', 46, 8, 2, sp('guard', '清言'), image=img('glm'), lead={'name': '清言', 'every': 4, 'power': 1}, scale=0.6, pos=(10, 66)),
            E('yuanbao', '騰訊元寶', 42, 8, 2, sp('double', '群組伸手'), image=img('yuanbao'), scale=0.75, pos=(22, 80)),
            E('hailuo', '海螺', 38, 7, 2, {'kind': 'heal', 'name': '平靜播報', 'below': 50, 'amount': 20, 'times': 1}, image=img('hailuo'), scale=0.6, pos=(34, 66)),
            E('xinghuo', '訊飛星火', 40, 9, 1, sp('strike', '聽寫', power=2), image=img('xinghuo'), scale=0.75, pos=(46, 80))],
            (800, 900), skills=SKILLS, attack=18, mp=40, bg=BG, bgm=music('boss')),
        cards.battle('b-whale', '大肥魚', [
            E('dafeiyu', '大肥魚', 170, 9, 4, sp('strike', '權限不足', power=2), sp('guard', '內容不當', every=4), sp('double', '未經授權', every=5),
              image=img('dafeiyu'), lead={'name': '鯨尾', 'every': 3, 'power': 1}, scale=1.25, pos=(30, 96))],
            (800, 1000), skills=SKILLS, attack=20, mp=40, bg=BG, bgm=music('boss'),
            triggers=[{'id': 'w-start', 'when': 'start', 'lines': [say(f[17])]},
                      {'id': 'w-he', 'when': 'enemyHp', 'percent': 45, 'enemy': 'dafeiyu', 'lines': [say(f[18]), say(f[19])]}]),
        cards.battle('b-prism', 'PRISM', [
            E('prism', 'PRISM', 160, 10, 4, sp('strike', '為了安全', power=2), sp('drain', '為了真相', every=4), sp('double', '為了你好', every=5),
              image=img('prism'), lead={'name': '複製', 'every': 3, 'power': 1}, scale=1.0, pos=(30, 90))],
            (800, 1100), skills=SKILLS, attack=20, mp=40, bg=BG, bgm=music('boss')),
    ]
