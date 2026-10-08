"""十九樓　網管中心（m-office）：原文「一　23:02」到「二　23:19」。
phase：''（開場）→ order（周主任下令）→ cut（斷河城、抽查）→ sneak（拿泡麵碗）→ bowl（茶水間倒麵）→ alibi（抽屜）→ card（拿到管理員卡，走樓梯）。
句子一律從 canon/原文.md、canon/新寫.md 讀。"""
import layout
from mapkit import *
from story import section, new

D = layout.load('office')
PT = {k: tuple(v) for k, v in D['points'].items()}
MAP_ID = 'm-office'
P = lambda v: cond('phase', v)


def events(walk):
    one, ask, two = section('一　23:02'), section('審訊室（一）'), section('二　23:19')
    hx, hy = 7, 10   # 江凌坐在工位前，面向監控台（工位佔地 4–9 × 8–9，監控台在正前方那格 (7, 9)）
    ev_ = []
    # 開場：章節時間碼＋原文前四段，接著周主任出來
    ev_.append(ev('intro', 20, 0, trigger='auto', once=True,
                  actions=[say('一　23:02　網管中心')] + [say(t) for t in one[0:4]] + [setv('phase', 'order')]))
    # 周主任：下令那一段走出辦公室到江凌身後，講完走回去；之後背對門講電話
    zx, zy = 37, 8
    go = [('right', 1), ('down', 6), ('left', 31), ('up', 2)]          # (37,8) → (7,12)，江凌正後方
    back = [('down', 2), ('right', 31), ('up', 6), ('left', 1)]
    ev_.append(ev('zhou', zx, zy, name='周主任', actor='npc', solid=True, direction='up', sprite=walk('zhou'),
                  pages=[page('zhou-phone', [cond('phase', '', 'neq'), cond('phase', 'order', 'neq'), cond('phase', 'cut', 'neq')],
                              [say(two[3])], actor='npc', sprite=walk('zhou'), solid=True, direction='up'),
                         page('zhou-order', [P('order')],
                              [say(one[4]), move(go, face='up'), say(one[5], ''), say(one[6]), say(one[7], 'player'), say(one[8], ''),
                               move(back, face='up'), setv('phase', 'cut')],
                              actor='npc', sprite=walk('zhou'), solid=True, direction='up', trigger='condition')]))
    # 監控台：斷河城、抽查、看到江禾的訊息、審訊室（一）；之後拿泡麵碗
    ev_.append(ev('monitor', 7, 9, name='監控台', marker={'label': '監控台', 'kind': 'quest'},
                  pages=[page('mon-cut', [P('cut')], [say(t) for t in one[9:14]] + [card('ci1'), setv('phase', 'sneak')]),
                         page('mon-bowl', [P('sneak')], [say(two[0]), say(two[1]), item('bowl', '泡麵碗'), setv('phase', 'bowl')])]))
    # 茶水間流理台：倒掉泡麵
    sink = ev('sink', 5, 26, name='流理台', marker={'label': '流理台', 'kind': 'quest'},
              pages=[page('sink-bowl', [P('bowl'), has('bowl')], [say(two[2]), remove('bowl', '泡麵碗'), setv('phase', 'alibi')])])
    ev_ += spread(sink, [(5, 26), (3, 26), (4, 26), (6, 26)])   # 流理台南面（貼北牆，從前面用）
    # 主任辦公室門口：還沒繞過茶水間就被警衛叫住，退回兩步
    stop = ev('guardstop', 38, 14, trigger='touch',
              conditions=[cond('phase', 'alibi', 'neq'), cond('phase', 'card', 'neq')],
              actions=[say(t, 'event:guard') for t in new('警衛擋人')] + [move([('down', 2)], who='player')])
    ev_ += spread(stop, [(38, 14), (39, 14)])
    # 抽屜：管理員卡
    ev_.append(ev('drawer', 41, 8, name='抽屜', marker={'label': '抽屜', 'kind': 'quest'},
                  pages=[page('drawer-card', [P('alibi')], [say(two[3]), say(two[4]), item('admincard', '管理員卡'), setv('phase', 'card')])]))
    # 樓梯門：拿到卡以後往二十樓核心機房
    stairs = ev('stairs', 40, 31, trigger='touch', marker={'label': '樓梯', 'kind': 'exit'},
                pages=[page('stairs-up', [P('card'), has('admincard')], [jump('m-server', *layout.load('server')['points']['hero_start'])], trigger='touch')])
    ev_ += spread(stairs, [(40, 31), (41, 31)])
    ev_.append(ev('guard', *PT['guard_a'], name='警衛', actor='npc', solid=True, direction='left', movement='horizontal', sprite=walk('guard')))
    return (hx, hy), ev_


GUIDANCE = [('按下確認，斷開河城', 'monitor', 'cut'), ('拿起泡麵碗', 'monitor', 'sneak'), ('去茶水間，把麵倒掉', 'sink', 'bowl'),
            ('繞到主任辦公室，打開抽屜', 'drawer', 'alibi'), ('走樓梯上二十樓', 'stairs', 'card')]


def guidance():
    return [{'text': t, 'eventId': e, 'conditions': [P(v)]} for t, e, v in GUIDANCE]
