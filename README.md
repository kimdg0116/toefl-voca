# 토플 단어 (toefl-voca)

해커스 보카(초록) 30 Days 를 폰에서 간격 반복으로 외우는 개인용 PWA.
옵시디언 `04 Life/토플/단어/` 카드 체계(Day 덱, 다시·어려움·좋음·쉬움, 동의어 퀴즈)를 그대로 옮겼다.

- 앱: https://kimdg0116.github.io/toefl-voca/ → 사파리에서 공유 → 홈 화면에 추가
- **단어 데이터는 저장소에 없다** (교재 저작권). `data/toefl-words.json` 을 AirDrop 으로 폰에 보내고 앱 설정에서 불러온다. 진도는 폰 localStorage 에만 저장 → 설정 > 진도 백업으로 가끔 내보내기.

## 단어 파일 다시 만들기

```bash
# 1) PDF 페이지 OCR (Apple Vision, 약 5분) -> <work>/pg/pNNN.tsv
swiftc -O tools/ocr.swift -o <work>/ocr
python3 -c "import pymupdf,subprocess,os;d=pymupdf.open(os.path.expanduser('~/Desktop/토플/해커스 vocabulary 초록.pdf'));os.makedirs('<work>/pg',exist_ok=True)
for i in range(19,331): p=f'<work>/pg/p{i:03d}.png'; d[i].get_pixmap(dpi=150).save(p); subprocess.run(['<work>/ocr',p])"
# 2) 구조화 + OCR 철자 교정 + 옵시디언 Day 01·02 복습 기록 이어붙이기
python3 tools/build_words.py <work>
```

아래 해석 줄을 OCR 이 놓친 페이지(46·197·212·270·297)는 300dpi 로 다시 인식해 `<work>/pg300/` 에 둔다 (`parse.lines` 가 자동 교체).

## 원어민 음성 파일

맥 프리미엄 목소리로 단어 1,701개 + 예문 약 1,870개를 녹음해 `data/toefl-audio.bin` (약 50MB) 을 만든다. git 에 올리지 않는다.

1. 맥: 시스템 설정 > 손쉬운 사용 > 읽기 및 말하기 > 시스템 음성 옆 (i) > 영어 > **Ava (프리미엄)** 받기
2. `python3 tools/build_audio.py` (목소리 자동 선택, 10~20분. 다시 돌리면 빠진 것만)
3. 폰으로 AirDrop → 앱 설정 > 원어민 음성 파일 > 불러오기. 없는 소리는 폰 목소리로 읽는다.

## 버전 올리기

`index.html` 의 `APP_VERSION`, `sw.js` 의 `VERSION`, `version.json` 세 곳을 같이 올린다.
