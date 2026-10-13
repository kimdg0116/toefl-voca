/**
 * 토플 단어 진도 동기화 서버 — 폰 앱과 맥 앱이 같은 진도(카드·기록·취약 단어)를 쓰게 한다.
 * 진도는 이 스크립트의 Script Properties 에만 둔다 (gzip + base64, 8000자씩 나눠서). 단어 데이터는 오지 않는다.
 *
 * 앱 → fetch POST {code, base, state?}
 *   base = 그 기기가 마지막으로 맞춘 rev. 서버 rev 와 같으면 state 를 저장하고 새 rev 를 준다
 *   다르면 저장하지 않고 서버 진도를 준다 → 앱이 합쳐서(merge) 그 rev 로 다시 보낸다
 * 연결 코드는 Secret.js 의 CODE (git 제외, clasp 로만 올라감)
 *
 * 반영: cd sync && ~/Desktop/app/dosimetrist-calendar-server/tools/node_modules/.bin/clasp push -f
 *       && …/clasp redeploy <배포 ID>   (배포 ID 는 앱 SYNC_URL 의 /s/…/exec 사이, URL 유지)
 */
const CH = 8000;                                             // Script Properties 값 하나는 9KB 까지
const props = () => PropertiesService.getScriptProperties();

function doPost(e) {
  let q;
  try { q = JSON.parse(e.postData.contents); } catch (x) { return out_({ err: 'bad' }); }
  if (q.code !== CODE) return out_({ err: 'code' });
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const rev = props().getProperty('rev') || '';
    if (q.base !== rev) return out_({ rev, state: rev ? load_() : null });
    if (!q.state) return out_({ rev });
    save_(q.state);
    const r = String(Date.now());
    props().setProperty('rev', r);
    return out_({ rev: r });
  } finally { lock.releaseLock(); }
}

function out_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

function save_(st) {
  const s = Utilities.base64Encode(Utilities.gzip(Utilities.newBlob(JSON.stringify(st))).getBytes());
  const p = { n: String(Math.ceil(s.length / CH)) };
  for (let i = 0; i * CH < s.length; i++) p['s' + i] = s.slice(i * CH, (i + 1) * CH);
  props().setProperties(p);                                  // 예전에 더 길었으면 뒤 조각이 남지만 n 까지만 읽는다
}

function load_() {
  const all = props().getProperties(), n = +all.n || 0;
  let s = '';
  for (let i = 0; i < n; i++) s += all['s' + i];
  return JSON.parse(Utilities.ungzip(Utilities.newBlob(Utilities.base64Decode(s), 'application/x-gzip')).getDataAsString());
}
