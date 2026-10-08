"""對話卡（序、審訊室）。lines：字串＝旁白、(講者, 文字)。"""


def dialogue(id, title, lines, pos, bg='', start=False):
    dl = [{'id': f'{id}-l{i}', 'speaker': (l if isinstance(l, tuple) else ('', l))[0], 'text': (l if isinstance(l, tuple) else ('', l))[1]}
          for i, l in enumerate(lines)]
    data = {'type': 'dialogue', 'title': title, 'speaker': dl[0]['speaker'], 'text': dl[0]['text'], 'dialogueLines': dl, 'stage': {'actors': []}}
    if bg: data['background'] = bg
    if start: data['start'] = True
    return {'id': id, 'type': 'story', 'position': {'x': pos[0], 'y': pos[1]}, 'data': data}


def link(board, a, b):
    board['edges'].append({'id': f'{a}--{b}', 'source': a, 'target': b, 'sourceHandle': 'right', 'targetHandle': 'left'})
