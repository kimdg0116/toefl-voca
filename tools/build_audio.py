"""단어·예문 원어민 음성 파일: 맥 프리미엄 목소리(say) → AAC → data/toefl-audio.bin

폰 앱 설정 > 원어민 음성 파일 > 불러오기 로 넣는다 (AirDrop). 교재 예문이 들어 있어 git 에 올리지 않는다.

    python3 tools/build_audio.py                         프리미엄 목소리 자동 선택 (Ava > Zoe > Evan …)
    python3 tools/build_audio.py --voice "Ava (Premium)"
    python3 tools/build_audio.py --voice Samantha --limit 30   시험용

한 번 만든 소리는 data/audio-cache/<목소리>/ 에 남아 다시 돌리면 빠진 것만 만든다.
파일 형식: b'TVAUDIO1' + uint32(LE) 머리 길이 + 머리 JSON {voice, items: {키: [위치, 길이]}} + AAC(ADTS) 이어붙임.
키: 'w:<id>' 표제어, 'e:<id>:<예문 번호>' 예문.
"""
import argparse, concurrent.futures as cf, json, os, re, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
PREFER = ['Ava', 'Zoe', 'Evan', 'Nathan', 'Allison', 'Susan', 'Tom', 'Noelle', 'Joelle']


def voices():
    out = []
    for line in subprocess.run(['say', '-v', '?'], capture_output=True, text=True).stdout.splitlines():
        m = re.match(r'^(.+?)\s{2,}(\w\w_\w\w)\s+#', line)
        if m:
            out.append((m.group(1).strip(), m.group(2)))
    return out


def pick_voice():
    best = None
    for name, lang in voices():
        if not lang.startswith('en_'):
            continue
        tier = 2 if re.search(r'Premium|프리미엄', name) else 1 if re.search(r'Enhanced|향상', name) else 0
        if not tier:
            continue
        base = name.split(' (')[0]
        key = (tier, lang == 'en_US', -PREFER.index(base) if base in PREFER else -99)
        if best is None or key > best[0]:
            best = (key, name)
    return best and best[1]


def render(voice, key, text, path):
    if os.path.exists(path):
        return
    with tempfile.TemporaryDirectory() as t:
        aiff = os.path.join(t, 'a.aiff')
        subprocess.run(['say', '-v', voice, '-o', aiff, text], check=True)
        subprocess.run(['afconvert', '-f', 'adts', '-d', 'aac@22050', '-b', '32000', '-c', '1', aiff, path + '.tmp'], check=True)
    os.replace(path + '.tmp', path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--jobs', type=int, default=6)
    a = ap.parse_args()
    voice = a.voice or pick_voice()
    if not voice:
        sys.exit('프리미엄(또는 향상된) 영어 목소리가 없어요.\n'
                 '시스템 설정 > 손쉬운 사용 > 읽기 및 말하기 > 시스템 음성 옆 (i) > 영어 > Ava (프리미엄) 을 받은 뒤 다시 실행하세요.')
    words = json.load(open(os.path.join(DATA, 'toefl-words.json'), encoding='utf-8'))['words']
    items = []
    for w in words:
        items.append((f"w:{w['id']}", w['w'] + '.'))                 # 마침표: 단어만 읽을 때 끝을 자연스럽게 내린다
        items += [(f"e:{w['id']}:{i}", e['en']) for i, e in enumerate(w['ex'])]
    if a.limit:
        items = items[:a.limit]
    cache = os.path.join(DATA, 'audio-cache', re.sub(r'[^\w가-힣-]+', '_', voice))
    os.makedirs(cache, exist_ok=True)
    path = lambda k: os.path.join(cache, k.replace(':', '_') + '.aac')
    todo = [(k, t) for k, t in items if not os.path.exists(path(k))]
    print(f'목소리: {voice} · {len(items)}개 중 새로 만들 것 {len(todo)}개', flush=True)
    done = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for f in cf.as_completed([ex.submit(render, voice, k, t, path(k)) for k, t in todo]):
            f.result()
            done += 1
            if done % 200 == 0 or done == len(todo):
                print(f'  {done}/{len(todo)}', flush=True)
    idx, blobs, off = {}, [], 0
    for k, _ in items:
        b = open(path(k), 'rb').read()
        idx[k] = [off, len(b)]
        blobs.append(b)
        off += len(b)
    head = json.dumps({'voice': voice, 'items': idx}, ensure_ascii=False, separators=(',', ':')).encode()
    out = os.path.join(DATA, 'toefl-audio.bin')
    with open(out, 'wb') as f:
        f.write(b'TVAUDIO1' + struct.pack('<I', len(head)) + head)
        for b in blobs:
            f.write(b)
    print(f'만듦: {os.path.normpath(out)} · {len(items)}개 · {os.path.getsize(out) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
