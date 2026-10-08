"""自製插件 eleven-minutes：二十樓核心機房的終端機卡。句子從原文「三　23:33」讀。"""
import json, pathlib
from story import section

HERE = pathlib.Path(__file__).resolve().parent / 'plugin'
PLUGIN_ID, VERSION = 'eleven-minutes', '1.0.0'
NODE = 'c-term'
# traceroute 的跳點只是畫面（原文：一跳，兩跳，三跳，第四跳停在「GFW／主控」）
HOPS = ['1  10.19.0.1', '2  10.20.0.1', '3  202.97.0.1', '4  GFW／主控  * * *']


def script():
    s = section('三　23:33'); cmd = lambda t: t.strip('`')
    return {'intro': s[1], 'steps': [{'cmd': cmd(s[2]), 'out': s[3]}, {'cmd': cmd(s[4]), 'out': s[5], 'hops': HOPS},
                                     {'cmd': cmd(s[6]), 'out': s[7], 'bad': True}],
            'after': s[8], 'done': '戴上頭盔'}


def html():
    src = (HERE / 'terminal.html').read_text(encoding='utf-8')
    return src.replace('<script src="common.js"></script>', '<script>' + (HERE / 'common.js').read_text(encoding='utf-8') + '</script>')


def card_node(pos):
    return {'id': NODE, 'type': 'story', 'position': {'x': pos[0], 'y': pos[1]}, 'data': {
        'type': 'plugin', 'title': '終端機', 'text': '', 'pluginId': PLUGIN_ID, 'pluginCardId': 'terminal',
        'pluginName': '十一分鐘', 'pluginCardName': '終端機', 'pluginVersion': VERSION, 'pluginIcon': 'terminal',
        'pluginColor': '#1aa6b7', 'pluginHtml': html(), 'pluginPresentation': 'fullscreen',
        'pluginValues': {'script': json.dumps(script(), ensure_ascii=False)}, 'pluginAssets': [], 'pluginReadVars': [], 'pluginWriteVars': [],
        'pluginSkippable': False, 'pluginFrame': {'showTitle': False, 'showButton': False}, 'platforms': ['web']}}


def settings_entry():
    return {'enabled': True, 'playback': {'version': VERSION, 'permissions': [], 'defaults': {}, 'huds': []}}


def manifest():
    return {'id': PLUGIN_ID, 'name': '十一分鐘', 'version': VERSION, 'author': '林亞澤',
            'description': '《十一分鐘》專用：核心機房的終端機，一個一個打指令。', 'categories': ['card'], 'icon': 'terminal',
            'permissions': ['flow:control'],
            'cards': [{'id': 'terminal', 'name': '終端機', 'description': '核心機房的終端機', 'icon': 'terminal', 'color': '#1aa6b7',
                       'presentation': 'fullscreen', 'fields': [{'key': 'script', 'kind': 'longText', 'label': '腳本（JSON）'}], 'html': html()}]}
