"""二十樓　核心機房（m-server）：原文「三　23:31」第一段。終端機那幾段在插件卡 c-term（plugin.py），卡片連到雲端長城。"""
import layout, plugin
from mapkit import *
from story import section

D = layout.load('server')
PT = {k: tuple(v) for k, v in D['points'].items()}
MAP_ID = 'm-server'


def events(walk):
    s = section('三　23:31')
    ev_ = [ev('intro', 16, 0, trigger='auto', once=True, actions=[say('三　23:31　核心機房'), say(s[0])])]
    term = ev('terminal', *PT['terminal'], name='終端機', marker={'label': '終端機', 'kind': 'quest'}, actions=[jump(plugin.NODE)])
    ev_ += spread(term, [PT['terminal'], (26, 10), (28, 10)])
    return PT['hero_start'], ev_


def guidance():
    return [{'text': '走到最裡面的終端機', 'eventId': 'terminal', 'conditions': []}]
