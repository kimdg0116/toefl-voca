"""OCR tsv (pg/pNNN.tsv) -> words_raw.json. 해커스 보카(초록) 30 Days, 페이지 레이아웃 좌표로 구조화."""
import re, json, sys, os, statistics, difflib

HAN = re.compile(r'[가-힣]')
POSW = r'(adj|adji|adij|adi|adl|aclj|ad|adv|ady|n|v|phr|prep|conj|pron)'
POSFIX = {'adl': 'adj', 'adji': 'adj', 'adij': 'adj', 'adi': 'adj', 'aclj': 'adj', 'ad': 'adj', 'ady': 'adv'}
POS_ONLY = re.compile(rf'^{POSW}\s*[.,]?$', re.I)
SENSE = re.compile(rf'^{POSW}(?:\s*[.,]\s*|\s+(?=\d))(?:(\d)\s*[.,]\s*)?(.+)$', re.I)
NUMSYN = re.compile(r'^(\d)\s*[.,]\s*(.+)$')
DER = re.compile(rf'^{POSW}\s*[.,]\s*[A-Za-z]', re.I)
NUMHEAD = re.compile(r'^\d{1,2}\s*\S')
MERGED = re.compile(rf'\s{POSW}\s*\.\s', re.I)

def pos(p):
    p = p.lower()
    return POSFIX.get(p, p) + '.'

def raw(path):
    return open(path, encoding='utf-8').read().splitlines()

def lines(i):
    out = []
    rows = raw(f'pg/p{i:03d}.tsv')
    if os.path.exists(f'pg300/p{i:03d}.tsv'):  # 아래 해석 줄을 놓친 페이지: 300dpi 재인식본으로 교체
        hi = [l for l in raw(f'pg300/p{i:03d}.tsv') if 0.78 < float(l.split('\t')[1]) < 0.935]
        rows = [l for l in rows if not 0.78 < float(l.split('\t')[1]) < 0.935] + hi
    for l in rows:
        x0, y0, x1, y1, t = l.split('\t', 4)
        t = t.strip()
        # 영어 줄 끝에 붙는 OCR 잡음 한글 1~2자 제거
        if re.search(r'[A-Za-z]{3}', t) and len(HAN.findall(t)) <= 2:
            t = re.sub(r'[가-힣ㄱ-ㅎ]{1,2}$', '', t).strip()
        out.append([float(x0), float(y0), float(x1), float(y1), t])
    return sorted(out, key=lambda r: (r[1], r[0]))

def head_word(t):
    """표제어 줄 -> (단어, 별 문자열, 붙어버린 뜻 줄)"""
    rest = None
    m = MERGED.search(t)
    if m:
        t, rest = t[:m.start()], t[m.start():].strip()
    t = re.sub(r'^[^A-Za-z]+', '', t)
    tok = t.split()
    if len(tok) > 1 and (re.search(r'[^A-Za-z\-\']', tok[0]) or (len(tok[0]) <= 2 and set(tok[0].lower()) <= set('slio'))):
        t = ' '.join(tok[1:])
    m = re.match(r'^([A-Za-z][A-Za-z\s\-’\']*?)\s*([^A-Za-z]*)$', t)
    if not m:
        return None
    w = m.group(1).strip().lower().replace('’', "'")
    return w, m.group(2), rest

def stars(s):
    n = s.count('*')
    return n if 1 <= n <= 3 else None

def split_ko(s):
    m = re.search(r'\s(\(?[^\sA-Za-z]*[가-힣].*)$', s)
    return (s[:m.start()], m.group(1)) if m else (s, None)

def add_sense(cur, p, text, y):
    syn, ko = split_ko(text)
    s = {'p': p, 'syn': clean_syn(syn), 'y': y}
    cur['sen'].append(s)
    if ko:
        cur.setdefault('_ko', []).append((y, ko))

def clean_syn(s):
    s = re.sub(r'\s+', ' ', re.sub(r'\.\s', ', ', s)).strip(' ,;.')
    return [p.strip() for p in re.split(r'\s*[,;]\s*', s) if p.strip()]

def parse(first, last):
    words, warn = [], []
    cur, day, active = None, 0, False
    hx_by_parity = {0: 0.12, 1: 0.12}
    for i in range(first, last + 1):
        L = lines(i)
        title = [r for r in L if 'Hackers Voca' in r[4] and r[1] < 0.25]
        if title:
            day += 1; active = True; cur = None
        if not active:
            continue
        top_y = title[0][1] + 0.1 if title else 0
        quiz_y = min((r[1] for r in L if re.fullmatch(r'qu[il1]z', r[4], re.I)), default=None)
        bot = [r for r in L if 0.74 < r[1] < 0.935 and 0.24 < r[0] < 0.33 and HAN.search(r[4])]
        bot_y = min((r[1] for r in bot), default=0.935) - 0.005
        stop = min(quiz_y or 1, bot_y)
        nh = [r[0] for r in L if r[0] < 0.2 and top_y < r[1] < stop and NUMHEAD.match(r[4])]
        hx = statistics.median(nh) if nh else hx_by_parity[i % 2]
        hx_by_parity[i % 2] = hx
        mode, pend_pos, pend_der = None, None, None
        def is_head(r):
            return r[0] < 0.2 and (abs(r[0] - hx) < 0.013 or (NUMHEAD.match(r[4]) and abs(r[0] - hx) < 0.045)) \
                and '[' not in r[4] and ']' not in r[4] and not DER.match(r[4]) and top_y <= r[1] < stop
        queue = sorted(L, key=lambda r: (r[1] - (0.015 if is_head(r) else 0), r[0]))
        k = 0
        while k < len(queue):
            x0, y0, x1, y1, t = queue[k]; k += 1
            if y0 >= stop or y0 > 0.935 or y0 < top_y or x0 > 0.9 or not t:
                continue
            if is_head([x0, y0, x1, y1, t]):
                hw = head_word(t)
                if hw and len(hw[0]) > 1:
                    cur = {'d': day, 'n': sum(1 for w in words if w['d'] == day) + 1, 'w': hw[0],
                           's': stars(hw[1]), 'sen': [], 'ex': [], 'der': [], 'pt': '', 'p': i, 'y': y0}
                    words.append(cur); mode = None; pend_pos = None
                    if hw[2]:
                        queue.insert(k, [0.36, y0, x1, y1, hw[2]])
                    continue
            if cur is None:
                continue
            if x0 < hx + 0.12:  # 왼쪽 칸: 발음기호 / 파생어
                if POS_ONLY.match(t):
                    pend_der = POS_ONLY.match(t).group(1); continue
                if pend_der and re.fullmatch(r'[A-Za-z\-]+', t):
                    cur['der'].append(pos(pend_der) + ' ' + t); pend_der = None; continue
                if DER.match(t):
                    m = DER.match(t)
                    cur['der'].append(pos(m.group(1)) + ' ' + re.sub(rf'^{POSW}\s*[.,]\s*', '', t, flags=re.I))
                elif not (t.startswith('[') or ']' in t or not re.search(r'[A-Za-z]{2}', t)):
                    warn.append(f'p{i} left? {cur["w"]}: {t}')
                continue
            if x0 > 0.6 and HAN.search(t):
                cur.setdefault('_ko', []).append((y0, t.lstrip('•·.-— ')))
                continue
            if '포인트' in t or '최신출제' in t:
                mode = 'pt'; continue
            if not re.search(r'[A-Za-z가-힣]{2}', t):
                continue  # 별표·기호 잡음
            if POS_ONLY.match(t):
                pend_pos = (POS_ONLY.match(t).group(1), y0); continue
            sm, nm = SENSE.match(t), NUMSYN.match(t)
            if sm and not (mode == 'pt' and HAN.search(t)):
                add_sense(cur, pos(sm.group(1)), sm.group(3), y0)
                mode = 'sen'; pend_pos = None; continue
            if pend_pos and abs(pend_pos[1] - y0) < 0.015 and not HAN.search(t):
                add_sense(cur, pos(pend_pos[0]), nm.group(2) if nm else t, y0)
                mode = 'sen'; pend_pos = None; continue
            short = len(t.split()) <= 4
            if nm and not HAN.search(t) and (',' in t or short):
                add_sense(cur, '', nm.group(2), y0)
                mode = 'sen'; pend_pos = None; continue
            if mode is None and not cur['sen'] and not HAN.search(t) and (',' in t or short or t[:1].islower()) and not t.endswith('.'):
                add_sense(cur, '', t, y0)  # 품사 표시를 OCR 이 놓친 뜻 줄
                mode = 'sen'; continue
            if mode == 'pt':
                cur['pt'] = (cur['pt'] + ' ' + t).strip(); continue
            if HAN.search(t) and len(re.findall(r'[A-Za-z]', t)) < 5:
                warn.append(f'p{i} mid-han? {cur["w"]}: {t}'); continue
            if mode == 'ex' and cur['ex']:
                cur['ex'][-1]['en'] += ' ' + t
            else:
                cur['ex'].append({'en': t})
            mode = 'ex'
        # 아래쪽 예문 해석: 단어 목록의 y 로 표제어별 묶음
        bl = sorted((r[1], r[4]) for r in L if bot_y < r[1] < 0.935 and r[0] < 0.24 and not HAN.search(r[4]) and re.search(r'[A-Za-z]', r[4]))
        tl = sorted((r[1], r[4]) for r in bot)
        pw = [w for w in words if w['p'] == i]
        if bl and len(bl) != len(pw):
            warn.append(f'p{i} headword count: list {[t for y, t in bl]} vs parsed {[w["w"] for w in pw]}')
            names = [t.lower() for y, t in bl]
            pairs = [(w, difflib.get_close_matches(w['w'], names, 1, 0.75)) for w in pw]
            pw = [w for w, m in pairs if m]
            bl = [bl[names.index(m[0])] for w, m in pairs if m]
        if bl:
            for j, w in enumerate(pw):
                ylo = bl[j][0] - 0.007
                yhi = bl[j + 1][0] - 0.007 if j + 1 < len(bl) else 1
                ks = [t for y, t in tl if ylo <= y < yhi]
                if len(ks) == len(w['ex']):
                    for e, t in zip(w['ex'], ks):
                        e['ko'] = t
                else:
                    warn.append(f'p{i} trans {w["w"]}: ex={len(w["ex"])} ko={len(ks)} {[e["en"][:50] for e in w["ex"]]} {[x[:30] for x in ks]}')
        if quiz_y:
            active = False; cur = None
    return words, warn

def fit_stars(ws):
    """Day 안의 별점은 *** -> ** -> * 순서. OCR 이 놓친 별이 있어도 어긋남이 가장 적은 경계 두 개를 고른다."""
    raw = [w['s'] for w in ws]
    n, best = len(raw), None
    for a in range(n + 1):
        for b in range(a, n + 1):
            cost = sum(1 for k, r in enumerate(raw) if r is not None and r != (3 if k < a else 2 if k < b else 1))
            if best is None or cost < best[0]:
                best = (cost, a, b)
    _, a, b = best
    for k, w in enumerate(ws):
        w['s'] = 3 if k < a else 2 if k < b else 1

def finish(words):
    for d in sorted({w['d'] for w in words}):
        fit_stars([w for w in words if w['d'] == d])
    for w in words:
        w['id'] = f"{w['d']}-{w['n']}"
        for y, t in sorted(w.pop('_ko', [])):
            if w['sen']:
                b = min(w['sen'], key=lambda s: abs(s['y'] - y))
                b['ko'] = (b.get('ko', '') + ' ' + t).strip()
        for s in w['sen']:
            s.pop('y', None)
        for e in w['ex']:
            e['en'] = re.sub(r'\s+', ' ', e['en']).strip()
        del w['y']
    return words

if __name__ == '__main__':
    words, warn = parse(int(sys.argv[1]), int(sys.argv[2]))
    finish(words)
    json.dump(words, open('words_raw.json', 'w'), ensure_ascii=False, indent=1)
    print(len(words), 'words', len(warn), 'warnings')
    print('\n'.join(warn))
