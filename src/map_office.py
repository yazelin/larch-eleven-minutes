"""十九樓　網管中心（m-office）：原文「一　23:04」到「二　23:21」。
phase：''（開場）→ order（周主任下令）→ cut（斷河城、抽查）→ sneak（拿泡麵碗）→ bowl（茶水間倒麵）→ alibi（抽屜）→ card（拿到管理員卡，走樓梯）。
句子一律從 canon/原文.md、canon/新寫.md 讀。"""
import layout
from mapkit import *
from story import section, new

D = layout.load('office')
PT = {k: tuple(v) for k, v in D['points'].items()}
MAP_ID = 'm-office'
P = lambda v: cond('phase', v)


SIGHT = 6   # 警衛看得多遠（細格）。10-09 作者：原本 3 格太近，像要跟他對話才會被發現
FACE = {'tea': (0, 1), 'lift': (-1, 0), 'stairs': (1, 0)}   # 茶水間門口面向茶水間（往下）、電梯口面向走廊（往左）、樓梯那一頭面向樓梯門（往右，10-09 作者）
return_lights = []


def sight(at, px, py):
    """警衛面前的扇形：往前 SIGHT 格，越遠越寬（每兩格寬一格）"""
    fx, fy = FACE[at]; out = []
    for d in range(1, SIGHT + 1):
        for w in range(-(d // 2 + 1), d // 2 + 2):
            out.append((px + fx * d + fy * w, py + fy * d + fx * w))
    return out


def guard_lights(post):
    """手電筒：跟著警衛的扇形光，照出看得到的範圍；只在他站著的那一頭亮"""
    ang = {'tea': 90, 'lift': 180, 'stairs': 0}
    return [{'id': f'flash-{at}', 'x': x, 'y': y, 'radius': SIGHT + 1, 'color': '#fff2c4', 'flicker': False, 'shape': 'spot',
             'angle': ang[at], 'spread': 60, 'strength': 0.55, 'follow': 'guard', 'when': {'variable': 'guard_at', 'value': at}}
            for at, (x, y) in post.items()]


def events(walk):
    one, ask, two = section('一　23:04'), section('審訊室（一）'), section('二　23:21')
    hx, hy = 7, 10   # 江凌坐在工位前，面向監控台（工位佔地 4–9 × 8–9，監控台在正前方那格 (7, 9)）
    ev_ = []
    # 開場：章節時間碼＋原文前四段，接著周主任出來
    ev_.append(ev('intro', 20, 0, trigger='auto', once=True, conditions=[P('')],   # 只在剛開始（讀檔回來不重演、不重設進度）
                  actions=[say('一　23:04　網管中心')] + [say(t) for t in one[0:4]] + [setv('phase', 'order')]))
    # 周主任：下令那一段走出辦公室到江凌身後，講完走回去；之後背對門講電話
    zx, zy = 37, 8
    go = [('right', 1), ('down', 6), ('left', 31), ('up', 2)]          # (37,8) → (7,12)，江凌正後方
    back = [('down', 2), ('right', 31), ('up', 6), ('left', 1)]
    # 下令前後：在辦公桌前（走出來下令再走回去）
    ev_.append(ev('zhou', zx, zy, name='周主任', actor='npc', solid=True, direction='up', sprite=walk('zhou'),
                  conditions=[cond('phase', 'sneak', 'neq'), cond('phase', 'bowl', 'neq'), cond('phase', 'alibi', 'neq'), cond('phase', 'card', 'neq')],
                  pages=[page('zhou-order', [P('order')],
                              [say(one[4]), move(go, face='up'), say(one[5], ''), say(one[6]), say(one[7], 'player'), say(one[8], ''),
                               move(back, face='up'), setv('phase', 'cut')],
                              actor='npc', sprite=walk('zhou'), solid=True, direction='up', trigger='condition')]))
    # 之後：站到北邊落地窗前背對門講電話（10-09 作者：讓江凌從他背後偷走管理員卡的感覺更明顯）
    ev_.append(ev('zhou-phone', *PT['zhou_phone'], name='周主任', actor='npc', solid=True, direction='up', sprite=walk('zhou'),
                  conditions=[cond('phase', p_, 'neq') for p_ in ('', 'order', 'cut')], actions=[say(two[3])],
                  pages=[page('zhou-turn', [P('alibi'), cond('zhou_look', 'turn')], [say(two[3])], actor='npc', sprite=walk('zhou'), solid=True, direction='down')]))
    # 監控台：斷河城、抽查、看到江禾的訊息、審訊室（一）；之後拿泡麵碗
    ev_.append(ev('monitor', 7, 9, name='監控台', marker={'label': '監控台', 'kind': 'quest'},
                  pages=[page('mon-cut', [P('cut')], [say(t) for t in one[9:14]] + [card('ci1'), setv('phase', 'sneak')]),
                         page('mon-bowl', [P('sneak')], [say(two[0]), say(two[1]), item('bowl', '泡麵碗'), setv('phase', 'bowl')])]))
    # 茶水間流理台：倒掉泡麵
    sink = ev('sink', 5, 26, name='流理台', marker={'label': '流理台', 'kind': 'quest'},
              pages=[page('sink-bowl', [P('bowl'), has('bowl')], [say(two[2]), remove('bowl', '泡麵碗'), setv('phase', 'alibi'), setv('sneaking', '1')])])
    ev_ += spread(sink, [(5, 26), (3, 26), (4, 26), (6, 26)])   # 流理台南面（貼北牆，從前面用）
    # 主任辦公室門口：還沒繞過茶水間就被警衛叫住，退回兩步
    stop = ev('guardstop', 38, 14, trigger='touch',
              conditions=[cond('phase', 'alibi', 'neq'), cond('phase', 'card', 'neq')],
              actions=[say(t, 'event:guard') for t in new('警衛擋人')] + [move([('down', 2)], who='player')])
    ev_ += spread(stop, [(38, 14), (39, 14)])
    # 抽屜：管理員卡
    ev_.append(ev('drawer', 41, 8, name='抽屜', marker={'label': '抽屜', 'kind': 'quest'},
                  pages=[page('drawer-card', [P('alibi')], [say(two[3]), say(two[4]), item('admincard', '管理員卡'), setv('phase', 'card')]),
                         page('drawer-seen', [P('alibi'), cond('zhou_look', 'turn')],
                              [say(t) for t in new('周主任回頭')] + [A('hop', hop={'who': 'player', 'times': 1, 'to': {'x': 38, 'y': 15}})])]))
    # 樓梯門：拿到卡以後往二十樓核心機房
    stairs = ev('stairs', 40, 31, trigger='touch', marker={'label': '樓梯', 'kind': 'exit'},
                pages=[page('stairs-up', [P('card'), has('admincard')], [setv('sneaking', ''), jump('m-server', *layout.load('server')['points']['hero_start'])], trigger='touch')])
    ev_ += spread(stairs, [(40, 31), (41, 31)])
    # 警衛（10-09 作者：躲警衛和偷卡完全沒有玩法）：原文「每四分鐘從電梯口走到茶水間，再走回來」。
    # 倒完麵以後（alibi）手上沒東西，被看到就會被叫回茶水間：警衛輪流站在茶水間門口、電梯口（變數 guard_at，背景計時切換），
    # 站著的那一個四格內看得到人，會走過來叫住。要等他走回電梯口，再從茶水間另一頭繞出去。
    # 同一個警衛真的在兩頭之間走（10-09 作者：兩個警衛輪流出現看起來像閃現）：倒完麵以後（alibi）他從電梯口走到茶水間門口、站一下、再走回去。
    # 他站著的那一頭附近三格是「看得到」的範圍（看不見的觸發格），走進去會被叫回茶水間；他在路上走的時候不抓人。
    post = {'lift': PT['guard_a'], 'tea': PT['guard_tea'], 'stairs': PT['guard_stairs']}
    gx, gy = post['lift']; tx, ty = post['tea']; sx, sy = post['stairs']
    patrol = [setv('guard_at', 'lift'), A('wait', amount=4000), setv('guard_at', ''),
              move([('up', gy - ty), ('left', gx - tx)], face='down'), setv('guard_at', 'tea'), A('wait', amount=5000), setv('guard_at', ''),
              move([('right', gx - tx), ('down', gy - ty)], face='left'), setv('guard_at', 'lift'), A('wait', amount=4000), setv('guard_at', ''),
              move([('right', sx - gx), ('down', sy - gy)], face='right'), setv('guard_at', 'stairs'), A('wait', amount=5000), setv('guard_at', ''),
              move([('up', sy - gy), ('left', sx - gx)], face='left'), A('loop', loop={})]
    SNEAK = cond('sneaking', '1')   # 倒完麵到走進樓梯門之間都要躲警衛（拿到卡以後往樓梯走也是）
    ev_.append(ev('guard', gx, gy, name='警衛', actor='npc', solid=True, direction='left', movement='still', sprite=walk('guard'),
                  pages=[page('guard-patrol', [SNEAK], patrol, actor='npc', sprite=walk('guard'), solid=True, direction='left', trigger='parallel')]))
    caught = [say(t, 'event:guard') for t in new('警衛發現')] + [A('hop', hop={'who': 'player', 'times': 1, 'to': {'x': 6, 'y': 27}})]
    taken = {(e['x'], e['y']) for e in ev_} | {tuple(v) for v in PT.values()} | {tuple(v) for v in D.get('labels', {}).values()}   # 區域名牌也是事件
    wl = layout.walls(D)
    for at, (px, py) in post.items():
        cells = [c for c in sight(at, px, py) if c not in wl and c not in taken]
        ev_ += spread(ev(f'sight-{at}', *cells[0], trigger='touch', conditions=[SNEAK, cond('guard_at', at)], actions=fresh(caught)), cells)
    return_lights.extend(guard_lights(post))
    # 周主任講電話時偶爾轉過身來（變數 zhou_look）：他轉身的時候開抽屜會被看到，退到門外
    ev_.append(ev('zhou-clock', 23, 0, trigger='parallel', conditions=[P('alibi')],
                  actions=[setv('zhou_look', ''), A('wait', amount=4500), setv('zhou_look', 'turn'), A('wait', amount=2000), A('loop', loop={})]))
    return (hx, hy), ev_


GUIDANCE = [('按下確認，斷開河城', 'monitor', 'cut'), ('拿起泡麵碗', 'monitor', 'sneak'), ('去茶水間，把麵倒掉', 'sink', 'bowl'),
            ('等警衛走回電梯口，繞去主任辦公室，趁周主任背對門開抽屜', 'drawer', 'alibi'), ('走樓梯上二十樓', 'stairs', 'card')]


def guidance():
    return [{'text': t, 'eventId': e, 'conditions': [P(v)]} for t, e, v in GUIDANCE]
