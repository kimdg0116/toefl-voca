"""해커스 보카(초록) OCR 결과 -> data/toefl-words.json (폰에서 불러올 단어 파일).

순서:
  1. tools/ocr.swift 로 PDF 페이지 OCR -> <work>/pg/pNNN.tsv  (README 참고)
  2. python3 tools/build_words.py <work 폴더>
옵시디언 `토플 단어 Day NN.md` 의 복습 기록(<!--SR:...-->)과 발음기호를 같은 단어에 이어 붙인다.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = sys.argv[1] if len(sys.argv) > 1 else '.'
VAULT_DAYS = os.path.expanduser('~/Desktop/Obsidian_Dongkyu/04 Life/토플/단어')
OUT = os.path.join(HERE, '..', 'data', 'toefl-words.json')

sys.path.insert(0, HERE)
os.chdir(WORK)
import parse  # noqa: E402

# OCR 철자 교정 (맞춤법 검사 + 아래 단어 목록 대조로 찾은 것)
FIX = {
    '2oth': '20th', 'ASia': 'Asia', 'Arab-lsraeli': 'Arab-Israeli', 'adlj': 'adj', 'advy': 'adv', 'aqj': 'adj',
    'aifticult': 'difficult', 'aiiord': 'afford', 'alarge': 'a large', 'appiance': 'appliance', 'atfirst': 'at first',
    'atforded': 'afforded', 'atthe': 'at the', 'avish': 'lavish', 'battie': 'battle', 'butfer': 'buffer',
    'byforce': 'by force', 'chierfly': 'chiefly', 'ciken': 'liken', 'culturaly': 'culturally', 'cuture': 'culture',
    'detalls': 'details', 'devlate': 'deviate', 'dificult': 'difficult', 'diftusion': 'diffusion',
    'ditticult': 'difficult', 'dlassify': 'classify', 'dlictate': 'dictate', 'dlisintegrate': 'disintegrate',
    'dlistinguish': 'distinguish', 'dryup': 'dry up', 'easyto': 'easy to', 'eficacy': 'efficacy',
    'everyyear': 'every year', 'experlences': 'experiences', 'falil': 'fail', 'flm': 'film', 'forcetul': 'forceful',
    'fourish': 'flourish', 'futfill': 'fulfill', 'girliriend': 'girlfriend', 'graduallyincrease': 'gradually increase',
    'imporlant': 'important', 'indifierent': 'indifferent', 'inherenty': 'inherently', 'ining': 'lining',
    'intentiona': 'intentional', 'lawtully': 'lawfully', 'legrtimately': 'legitimately', 'lllness': 'illness',
    'lowa': 'Iowa', 'modity': 'modify', 'multip licity': 'multiplicity', 'nelp': 'help', 'pacitiers': 'pacifiers',
    'paintul': 'painful', 'pertormance': 'performance', 'pnysics': 'physics', 'prolitic': 'prolific',
    'protound': 'profound', 'reactionto': 'reaction to', 'relleved': 'relieved', 'requre': 'require',
    'rerinement': 'refinement', 'retrigerated': 'refrigerated', 'retuted': 'refuted', 'revolutlon': 'revolution',
    'satistactorily': 'satisfactorily', 'seli-assured': 'self-assured', 'soclety': 'society', 'steadtast': 'steadfast',
    'steadtastly': 'steadfastly', 'stiit': 'stiff', 'stratity': 'stratify', 'successtul': 'successful',
    'suosiStence': 'subsistence', 'surtace': 'surface', 'swel': 'swell', 'switly': 'swiftly', 'teature': 'feature',
    'thett': 'theft', 'tiberal': 'liberal', 'tikely': 'likely', 'toresee': 'foresee', 'tully': 'fully',
    'udicrous': 'ludicrous', 'uimited': 'limited', 'under uine': 'underline', 'uiving': 'living', 'ukely': 'likely',
    'unskilltul': 'unskillful', 'z00': 'zoo', 'periormo': 'perform이', 'personis': "person's", 'Lifelike': 'lifelike',
}
HEAD_FIX = {'atthe urging of': 'at the urging of', 'a rigidly': 'rigidly'}
# 포인트 글의 '의' 가 ol / o 로 읽힌 것
PARTICLE = re.compile(r'\b(acquisition|doubtful|entangle|hasten|maintain|perform|portable|time|train)ol\b|\b(determine|develop|postpone)o\b')


def fix(s):
    for a, b in FIX.items():
        s = re.sub(r'(?<![A-Za-z])' + re.escape(a) + r'(?![A-Za-z])', b, s)
    return PARTICLE.sub(lambda m: (m.group(1) or m.group(2)) + '의', s)


ABBR = {'Jr', 'Mr', 'Mrs', 'Ms', 'Dr', 'St', 'Mt', 'vs', 'etc', 'a.m', 'p.m', 'U.S', 'e.g', 'i.e'}


def fix_sentence(s):
    """예문을 자연스럽게 읽히게: OCR 이 쉼표를 마침표로 읽은 곳, 첫 글자, 끝 문장부호, 'lt'·'l|' 같은 잡음"""
    s = re.sub(r'([\w.]+)\. (?=[a-z])', lambda m: m.group(0) if m.group(1) in ABBR else m.group(1) + ', ', s)
    s = re.sub(r'^(?:adj|adv|n|v)\s+(?=[A-Z])', '', s)
    s = re.sub(r'^lt\b', 'It', s)
    s = s.replace('World War l|', 'World War II').replace('World War |', 'World War I')
    s = s[:1].upper() + s[1:]
    return s if re.search(r'[.!?"\']$', s) else s + '.'


def vault_seed():
    """Day 01·02 노트: 단어 -> (복습 상태, 발음기호)"""
    seed = {}
    for f in sorted(os.listdir(VAULT_DAYS)):
        m = re.match(r'토플 단어 Day (\d+)\.md', f)
        if not m:
            continue
        d = int(m.group(1))
        txt = open(os.path.join(VAULT_DAYS, f), encoding='utf-8').read()
        for blk in re.split(r'\n(?=\*\*[^*]+\*\* )', txt):
            h = re.match(r'\*\*([^*]+)\*\*[^\n]*?(\[[^\]]+\])?\s*$', blk.split('\n')[0])
            if not h:
                continue
            sr = re.search(r'<!--SR:!(\d{4}-\d\d-\d\d),(\d+),(\d+)-->', blk)
            seed[(d, h.group(1).strip().lower())] = {
                'ph': h.group(2),
                'sr': {'due': sr.group(1), 'ivl': int(sr.group(2)), 'ease': int(sr.group(3)), 'reps': 1, 'lapses': 0} if sr else None,
            }
    return seed


words, warn = parse.parse(19, 330)
parse.finish(words)
seed = vault_seed()
n_sr = 0
for w in words:
    w['w'] = HEAD_FIX.get(w['w'], fix(w['w']))
    for s in w['sen']:
        s['syn'] = [fix(x) for x in s['syn']]
        s['ko'] = re.sub(r'\s*:\s*', '; ', re.sub(r'\.\s', ', ', s.get('ko', ''))).strip(' .')  # OCR 이 쉼표·쌍반점을 . : 로 읽음
    for e in w['ex']:
        e['en'] = fix_sentence(fix(e['en']))
    w['der'] = [fix(x) for x in w['der']]
    w['pt'] = fix(w['pt'])
    sd = seed.get((w['d'], w['w']))
    if sd:
        if sd['ph']:
            w['ph'] = sd['ph']
        if sd['sr']:
            w['sr'] = sd['sr']; n_sr += 1
    del w['p']

# 아래 단어 목록에서 'up' 이 빠져 해석이 앞 단어에 몰린 페이지 (p297)
by = {w['id']: w for w in words}
by['27-51']['ex'][0]['ko'] = '로마인들은 많은 문화를 정복했음에도 불구하고, 그것들을 완전히 동질화시키지는 않았다.'
by['27-52']['ex'][0]['ko'] = '그 카페는 최근에 차와 커피 가격을 올렸다.'
by['12-17']['sen'][1]['ko'] = by['12-17']['sen'][1]['ko'] or '(미술품 등을) 제작하다'

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'app': 'toefl-voca', 'source': '해커스 보카 (초록) 30 Days', 'words': words},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'{len(words)} words, {n_sr} review states from vault, {len(warn)} parser warnings -> {os.path.normpath(OUT)}')
