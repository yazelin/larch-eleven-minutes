"""雲海裡的防火長城（m-cloud）：原文「四　23:35」「五　23:47」，最後接審訊室（二）與三個結局。
phase：''（進來）→ hunt（捧起江禾那一則，審查兵追來）→ gate（砍倒四個以上，門前亮起人影）
       → w2（第一班倒下）→ whale（第二班倒下）→ free（大肥魚的鎖開了）→ end（備援系統扣回來）。
wall：'' 牆在／down 鎖鏈崩開（牆段圖片看這個變數消失）。
王戰都是回合制：門前按一下開打；打輸事件停下，再按門一次從那一班重打。打贏以後下一班由 condition 事件自動接上。"""
import layout
from mapkit import *
from story import section, new

D = layout.load('cloud')
PT = {k: tuple(v) for k, v in D['points'].items()}
MAP_ID = 'm-cloud'
P = lambda v: cond('phase', v)
ENDINGS = [('送出', 'e1'), ('交給 PRISM', 'e2'), ('修回去', 'e3')]


def stages():
    f, v = section('四　23:35'), section('五　23:47')
    return {
        'gate': [say(f[7]), say(f[8]), heal(), fight('b-w1'), setv('phase', 'w2')],
        'w2': [say(f[9]), heal(), fight('b-w2'), setv('phase', 'whale')],
        'whale': [say(f[10]), say(f[11]), say(f[12]), say(f[13]), say(f[14]), say(f[15], 'player'), say(f[16]),
                  heal(), fight('b-whale'), say(f[20]), setv('phase', 'free')],
        'free': [say(v[0]), setv('wall', 'down'), fx('flash', 0.8, 900, '#e8f6ff'), say(v[1]), fx('shake', 0.7, 1200), say(v[2]), say(v[3]),
                 say(v[4]), say(v[5]), say(v[6]), say(v[7]), say(v[8]), say(v[9]), heal(), fight('b-prism'),
                 say(v[10]), say(v[11]), setv('wall', ''), fx('shake', 0.5, 1500), say(v[12]), setv('phase', 'end'),
                 card('ci2'), A('choice', text='', choice={'options': [{'id': f'end-{k}', 'label': lbl, 'actions': [jump(k)]} for lbl, k in ENDINGS]})],
    }


def events(walk):
    f = section('四　23:35')
    st = stages()
    ev_ = [ev('intro', 20, 0, trigger='auto', once=True, actions=[say('四　23:35　防火長城'), say(f[0]), say(f[1]), say(f[2])])]
    ev_.append(ev('mound3', *PT['mound3'], name='第三座山', marker={'label': '江禾那一則', 'kind': 'quest'},
                  pages=[page('mound-he', [P('')], [say(f[3]), item('he', '江禾那一則'), say(f[4]), setv('phase', 'hunt')])]))
    # 審查兵與獵犬：一進來就在巡牆（看得到、不追人）；捧起那一則以後轉過頭來追（動作戰鬥，砍倒化成日誌飄走）
    # 10-09 作者：進雲端長城看不到任何兵 → 第一頁巡邏、第二頁追人
    for k, xy in PT.items():
        if not k.startswith(('censor', 'hound')): continue
        dog = k.startswith('hound'); spr = walk('hound' if dog else 'censor')
        chase = page(f'{k}-chase', [P('hunt')], [A('battle', cardId='b-hound' if dog else 'b-censor'), add('kills')], actor='npc', sprite=spr,
                     movement='approach', approach=20, trigger='touch', once=True, after='vanish', solid=False)
        ev_.append(ev(k, *xy, name='獵犬' if dog else '審查兵', actor='npc', kind='monster', sprite=spr, movement='random', trigger='action',
                      badge={'icon': 'swords', 'color': '#8f564a'}, conditions=[P('')], actions=[], pages=[chase]))
    ev_.append(ev('hunted', 21, 0, trigger='condition', once=True, conditions=[P('hunt'), cond('kills', 4, 'gte')],
                  actions=[say(f[5]), say(f[6]), setv('phase', 'gate')]))
    # 門：每一班一頁（打輸再按一次重打）；第一班要走到門前按，之後自動接
    # 太早走到門前：說明現在該做什麼（新寫，待作者定稿）
    early = [page('gate-early', [P('')], [say(t) for t in new('門還鎖著')]), page('gate-hunt', [P('hunt')], [say(t) for t in new('審查兵還在追')])]
    gate = ev('gate', *PT['gate'], name='長城門', marker={'label': '長城門', 'kind': 'quest'},
              pages=early + [page(f'gate-{k}', [P(k)], fresh(acts)) for k, acts in st.items()])
    ev_ += spread(gate, [PT['gate'], (28, 10), (29, 10), (26, 10)])
    for i, k in enumerate(['w2', 'whale', 'free']):
        ev_.append(ev(f'next-{k}', 22 + i, 0, trigger='condition', once=True, conditions=[P(k)], actions=fresh(st[k])))
    # 地圖上的王：大肥魚比牆還高，站在門前（圖框下緣貼門那一列，江凌站在她前面）；鎖開了以後稜鏡從牆外的雲層升起來
    big = lambda id, x, k, fx, fy, fw, fh: ev(id, x, 0, name=id, conditions=[P(k)],
                                              free={'url': f'/files/assets/battle/{id.split("-")[0]}.webp', 'x': fx, 'y': fy, 'w': fw, 'h': fh})
    ev_ += [big('dafeiyu-map', 30, 'whale', 24.3, 0, 7.3, 10), big('dafeiyu-free', 31, 'free', 24.3, 0, 7.3, 10),
            big('prism-map', 32, 'free', 38, 0, 5.5, 8)]
    return PT['hero_start'], ev_


def wall_conditions(name):
    """長城段與門：鎖鏈崩開的時候消失"""
    return [cond('wall', 'down', 'neq')] if name.startswith('長城') else []


GUIDANCE = [('在灰色的山裡找江禾那一則', 'mound3', ''), ('走到牆中段的門前', 'gate', 'gate'),
            ('回到門前，再打一次', 'gate', 'w2'), ('回到門前，再打一次', 'gate', 'whale'), ('回到門前，再打一次', 'gate', 'free')]


def guidance():
    g = [{'text': t, 'eventId': e, 'conditions': [P(v)]} for t, e, v in GUIDANCE]
    hunt = [{'text': f'砍倒追來的審查兵（還差 {4 - k} 個）', 'eventId': 'gate', 'conditions': [P('hunt'), cond('kills', k)]} for k in range(4)]
    return g[:1] + hunt + g[1:]
