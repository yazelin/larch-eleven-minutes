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


SIGHT = 6        # 警衛站定時看得多遠（細格）。10-09 作者：原本 3 格太近，像要跟他對話才會被發現
SIGHT_WALK = 4   # 走路時往前看多遠（10-09 作者：走路時也要看得到人）
CHUNK = 3        # 走路的視線每幾步更新一次
DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
ANGLE = {'right': 0, 'down': 90, 'left': 180, 'up': 270}
return_lights = []


def sight(d, px, py, rng, wide=True):
    """警衛面前的扇形：往 d 方向 rng 格，越遠越寬（站定時每兩格寬一格；走路時固定左右各一格，引擎一張地圖最多 256 個事件）"""
    fx, fy = DIRS[d]; out = []
    for k in range(1, rng + 1):
        half = (k // 2 + 1) if wide else 1
        for w in range(-half, half + 1):
            out.append((px + fx * k + fy * w, py + fy * k + fx * w))
    return out


def patrol_legs(posts, legs):
    """巡邏：每一段路切成每 CHUNK 步一小段，每小段開始時記下「在哪、面向哪」（guard_at、guard_dir），各自有一塊視線。
    posts：{名字: ((x, y), 面向, 停幾毫秒)}；legs：[(從, 到, [(方向, 步數)…])]。回傳 (每段的動作串, {狀態: (方向, x, y, 視距)})"""
    states, pages = {}, []
    for li, (frm, to, route) in enumerate(legs):
        (x, y), face, ms = posts[frm]
        acts = [setv('guard_at', frm), setv('guard_dir', face), A('wait', amount=ms)]
        states[frm] = (face, x, y, SIGHT); k = 0
        for d, n in route:
            for c0 in range(0, n, CHUNK):
                st = f'L{li}c{k}'; k += 1; c = min(CHUNK, n - c0)
                states[st] = (d, x, y, SIGHT_WALK)
                acts += [setv('guard_at', st), setv('guard_dir', d), move([(d, c)])]
                x, y = x + DIRS[d][0] * c, y + DIRS[d][1] * c
        acts.append(setv('leg', str((li + 1) % len(legs))))
        assert len(acts) <= 32, (li, len(acts))
        pages.append(acts)
    return pages, states


def guard_lights():
    """手電筒：跟著警衛、照向他面對的方向（guard_dir）"""
    return [{'id': f'flash-{d}', 'x': 24, 'y': 26, 'radius': SIGHT + 1, 'color': '#fff2c4', 'flicker': False, 'shape': 'spot',
             'angle': a, 'spread': 60, 'strength': 0.55, 'follow': 'guard', 'when': {'variable': 'guard_dir', 'value': d}} for d, a in ANGLE.items()]


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
    # 警衛（10-09 作者三輪回饋：兩個警衛輪流出現像閃現 → 同一個人真的走；看太近 → 扇形 6 格＋手電筒；走路時也要看）
    # 倒完麵到走進樓梯門之間（sneaking）他在電梯口、茶水間門口、樓梯那一頭之間巡邏，走路時也一路往前看。
    # 視線是看不見的觸發格：每一格一個事件，哪些狀態看得到這格就有幾頁（一格只能放一個事件）。
    (gx, gy), (tx, ty), (sx, sy) = PT['guard_a'], PT['guard_tea'], PT['guard_stairs']
    # 茶水間門口面朝走廊（right）、不看進茶水間：茶水間是等警衛走開的安全區（10-09 作者：第一次偷卡幾乎固定失敗）
    posts = {'lift': ((gx, gy), 'left', 4000), 'tea': ((tx, ty), 'right', 5000), 'lift2': ((gx, gy), 'left', 4000), 'stairs': ((sx, sy), 'right', 5000)}
    legs = [('lift', 'tea', [('up', gy - ty), ('left', gx - tx)]), ('tea', 'lift2', [('right', gx - tx), ('down', gy - ty)]),
            ('lift2', 'stairs', [('right', sx - gx), ('down', sy - gy)]), ('stairs', 'lift', [('up', sy - gy), ('left', sx - gx)])]
    leg_pages, states = patrol_legs(posts, legs)
    SNEAK = cond('sneaking', '1')
    gpage = lambda i, acts: page(f'guard-leg{i}', [SNEAK, cond('leg', str(i)) if i else cond('leg', '1', 'neq')] + ([cond('leg', '2', 'neq'), cond('leg', '3', 'neq')] if not i else []),
                                 acts, actor='npc', sprite=walk('guard'), solid=True, direction='left', trigger='parallel')
    ev_.append(ev('guard', gx, gy, name='警衛', actor='npc', solid=True, direction='left', movement='still', sprite=walk('guard'),
                  pages=[gpage(i, acts) for i, acts in enumerate(leg_pages)]))
    caught = [say(t, 'event:guard') for t in new('警衛發現')] + [A('hop', hop={'who': 'player', 'times': 1, 'to': {'x': 6, 'y': 27}})]
    taken = {(e['x'], e['y']) for e in ev_} | {tuple(v) for v in PT.values()} | {tuple(v) for v in D.get('labels', {}).values()}   # 區域名牌也是事件
    wl = layout.walls(D); W, H = D['map']['w'], D['map']['h']; seen = {}
    for st, (d, x, y, rng) in states.items():
        for c in sight(d, x, y, rng, wide=st in posts):
            if 0 <= c[0] < W and 0 <= c[1] < H and c not in wl and c not in taken: seen.setdefault(c, []).append(st)
    for i, (c, sts) in enumerate(sorted(seen.items())):
        pg = [page(f'sight{i}-{j}', [SNEAK, cond('guard_at', st)], fresh(caught), trigger='touch') for j, st in enumerate(sts[1:])]
        ev_.append(ev(f'sight{i}', *c, trigger='touch', conditions=[SNEAK, cond('guard_at', sts[0])], actions=fresh(caught), pages=pg))
    return_lights.extend(guard_lights())
    # 周主任講電話時偶爾轉過身來（變數 zhou_look）：他轉身的時候開抽屜會被看到，退到門外
    ev_.append(ev('zhou-clock', 23, 0, trigger='parallel', conditions=[P('alibi')],
                  actions=[setv('zhou_look', ''), A('wait', amount=4500), setv('zhou_look', 'turn'), A('wait', amount=2000), A('loop', loop={})]))
    return (hx, hy), ev_


GUIDANCE = [('按下確認，斷開河城', 'monitor', 'cut'), ('拿起泡麵碗', 'monitor', 'sneak'), ('去茶水間，把麵倒掉', 'sink', 'bowl'),
            ('等警衛走回電梯口，繞去主任辦公室，趁周主任背對門開抽屜', 'drawer', 'alibi'), ('走樓梯上二十樓', 'stairs', 'card')]


def guidance():
    return [{'text': t, 'eventId': e, 'conditions': [P(v)]} for t, e, v in GUIDANCE]
