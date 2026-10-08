"""雲海裡的防火長城（m-cloud）：原文「四　23:37」「五　23:49」，最後接審訊室（二）與三個結局。
phase：cloud（進來；從十九樓帶來的 card 在這裡蓋掉）→ hunt（捧起江禾那一則，審查兵追來）→ gate（砍倒四個以上，門前亮起人影）
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


def cam():
    """鏡頭移到長城門前（10-09 作者：打王時人多半還在第三座山那邊，看不到門前的大肥魚）；事件結束才回到江凌"""
    return A('camera', camera={'x': 28, 'y': 7, 'moveMs': 1200, 'holdMs': 0, 'back': False})


def stages():
    f, v = section('四　23:37'), section('五　23:49')
    return {
        'gate': [cam(), say(f[7]), say(f[8]), heal(), fight('b-w1'), setv('phase', 'w2')],
        'w2': [say(f[9]), heal(), fight('b-w2'), setv('phase', 'whale')],
        'whale': [cam(), say(f[10]), say(f[11]), say(f[12]), say(f[13]), say(f[14]), say(f[15], 'player'), say(f[16]),
                  heal(), fight('b-whale'), say(f[20]), setv('phase', 'free')],
        'free': [cam(), say(v[0]), setv('wall', 'down'), fx('flash', 0.8, 900, '#e8f6ff'), say(v[1]), fx('shake', 0.7, 1200), say(v[2]), say(v[3]),
                 say(v[4]), say(v[5]), say(v[6]), say(v[7]), say(v[8]), say(v[9]), heal(), fight('b-prism'),
                 say(v[10]), say(v[11]), setv('wall', ''), fx('shake', 0.5, 1500), say(v[12]), setv('phase', 'end'),
                 card('ci2'), A('choice', text='', choice={'options': [{'id': f'end-{k}', 'label': lbl, 'actions': [jump(k)]} for lbl, k in ENDINGS]})],
    }


def events(walk):
    f = section('四　23:37')
    st = stages()
    # 10-09 修：從十九樓一路玩過來時 phase 是 card（拿到管理員卡），雲端的事件原本都寫 phase=='' → 全部不會啟動。進場就把進度設成 cloud
    ev_ = [ev('intro', 20, 0, trigger='auto', once=True, actions=[setv('phase', 'cloud'), say('四　23:37　防火長城'), say(f[0]), say(f[1]), say(f[2])])]
    # 第三座山：走到山腳那一排任何一格就捧起來（10-09 作者：走到那一則前沒有反應 → 原本要面對它按鍵）
    mound = ev('mound3', *PT['mound3'], name='第三座山', marker={'label': '江禾那一則', 'kind': 'quest'}, trigger='touch',
               pages=[page('mound-he', [P('cloud')], [say(f[3]), item('he', '江禾那一則'), say(f[4]), setv('phase', 'hunt')], trigger='touch')])
    ev_ += spread(mound, [PT['mound3']] + [(x, 20) for x in range(38, 45) if x != PT['mound3'][0]])
    # 審查兵與獵犬：一進來就在巡牆（看得到、不追人）；捧起那一則以後轉過頭來追（動作戰鬥，砍倒化成日誌飄走）
    # 10-09 作者：進雲端長城看不到任何兵 → 第一頁巡邏、第二頁追人
    for k, xy in PT.items():
        if not k.startswith(('censor', 'hound')): continue
        dog = k.startswith('hound'); spr = walk('hound' if dog else 'censor')
        chase = page(f'{k}-chase', [P('hunt')], [A('battle', cardId='b-hound' if dog else 'b-censor'), add('kills')], actor='npc', sprite=spr,
                     movement='approach', approach=20, trigger='touch', once=True, after='vanish', solid=False)
        ev_.append(ev(k, *xy, name='獵犬' if dog else '審查兵', actor='npc', kind='monster', sprite=spr, movement='horizontal' if dog else 'vertical', trigger='action',   # 原位附近來回巡邏，不會走出追擊範圍（random 會漂走）
                      badge={'icon': 'swords', 'color': '#8f564a'}, conditions=[P('cloud')], actions=[], pages=[chase]))
    ev_.append(ev('hunted', 21, 0, trigger='condition', once=True, conditions=[P('hunt'), cond('kills', 4, 'gte')],
                  actions=[say(f[5]), say(f[6]), setv('phase', 'gate')]))
    # 門：每一班一頁（打輸再按一次重打）；第一班要走到門前按，之後自動接
    # 太早走到門前：說明現在該做什麼（新寫，待作者定稿）
    early = [page('gate-early', [P('cloud')], [say(t) for t in new('門還鎖著')], trigger='touch'), page('gate-hunt', [P('hunt')], [say(t) for t in new('審查兵還在追')], trigger='touch')]
    gate = ev('gate', *PT['gate'], name='長城門', marker={'label': '長城門', 'kind': 'quest'}, trigger='touch',   # 走到門前就觸發（10-09）
              pages=early + [page(f'gate-{k}', [P(k)], fresh(acts), trigger='touch') for k, acts in st.items()])
    ev_ += spread(gate, [PT['gate'], (28, 10), (29, 10), (26, 10)])
    for i, k in enumerate(['gate', 'w2', 'whale', 'free']):   # 第一班也自動接（10-09：門改成走到才觸發，站在門前的人等不到）
        ev_.append(ev(f'next-{k}', 25 + i, 0, trigger='condition', once=True, conditions=[P(k)], actions=fresh(st[k])))
    # 地圖上的王：大肥魚比牆還高，站在門前、畫在牆前面；鎖開了以後稜鏡從牆外的雲層升起來
    big = lambda id, x, k, fx, fy, fw, fh: ev(id, x, 0, name=id, conditions=[P(k)],
                                              free={'url': f'/files/assets/battle/{id.split("-")[0]}.webp', 'x': fx, 'y': fy, 'w': fw, 'h': fh})
    ev_ += [big('dafeiyu-map', 30, 'whale', 23.6, 0, 8.8, 12), big('dafeiyu-free', 31, 'free', 23.6, 0, 8.8, 12),   # 圖框下緣在第 11 列：畫在長城（第 9 列）前面，不被牆蓋掉；12 格高，頭頂高過長城（原文：比牆還高）
            big('prism-map', 32, 'free', 38, 0, 5.5, 8)]
    return PT['hero_start'], ev_


def wall_conditions(name):
    """長城段與門：鎖鏈崩開的時候消失"""
    return [cond('wall', 'down', 'neq')] if name.startswith('長城') else []


GUIDANCE = [('在灰色的山裡找江禾那一則', 'mound3', 'cloud'), ('走到牆中段的門前', 'gate', 'gate'),
            ('回到門前，再打一次', 'gate', 'w2'), ('回到門前，再打一次', 'gate', 'whale'), ('回到門前，再打一次', 'gate', 'free')]


def guidance():
    g = [{'text': t, 'eventId': e, 'conditions': [P(v)]} for t, e, v in GUIDANCE]
    hunt = [{'text': f'砍倒追來的審查兵（還差 {4 - k} 個）', 'eventId': 'gate', 'conditions': [P('hunt'), cond('kills', k)]} for k in range(4)]
    return g[:1] + hunt + g[1:]
