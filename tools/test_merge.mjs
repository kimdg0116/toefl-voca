// 기기 연동 합치기(merge) 확인: node tools/test_merge.mjs
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
const src = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const code = src.slice(src.indexOf('const prog ='), src.indexOf('// 보낼 게 있으면'));
const { merge, canon, prog } = new Function(code + 'return { merge, canon, prog };')();

const card = (reps, due) => ({ ease: 250, ivl: 3, due, reps, lapses: 0 });
const phone = { cards: { a: card(3, '2026-10-20'), b: card(1, '2026-10-15'), c: card(2, '2026-10-16') },
  log: { '2026-10-13': { rev: 10, nw: 57, again: 3, quiz: [{ t: 'Day 3 퀴즈', sc: 8, n: 10 }], day: 3 } }, weak: { a: 2, b: 1 }, set: { exam: '2026-11-30', voice: 'iphone' } };
const mac = { cards: { a: card(4, '2026-10-25'), d: card(1, '2026-10-15') },
  log: { '2026-10-13': { rev: 12, nw: 57, again: 1, quiz: [] }, '2026-10-14': { rev: 5, nw: 0, again: 0, quiz: [] } }, weak: { b: 3 }, set: { exam: '2026-12-01', voice: 'mac' } };

const m = merge(phone, mac);
assert.deepEqual(Object.keys(m.cards).sort(), ['a', 'b', 'c', 'd'], '카드는 어느 쪽도 잃지 않는다');
assert.equal(m.cards.a.reps, 4, '더 많이 본 쪽이 이긴다');
assert.deepEqual(m.log['2026-10-13'], { rev: 12, nw: 57, again: 3, day: 3, quiz: phone.log['2026-10-13'].quiz }, '같은 날 기록은 큰 값');
assert.ok(m.log['2026-10-14'], '한쪽에만 있는 날도 남는다');
assert.deepEqual(m.weak, { a: 2, b: 3 }, '연동 전(wu 같음)이면 취약 단어를 합친다');
assert.equal(m.set.voice, 'iphone', '설정은 기기마다 따로');
assert.equal(canon(prog(m)), canon(prog(merge(mac, phone))), '어느 기기에서 합쳐도 같은 진도');
assert.equal(canon({ b: 1, a: { d: 1, c: 2 } }), canon({ a: { c: 2, d: 1 }, b: 1 }), '키 순서는 비교에 안 들어간다');

const later = merge({ ...phone, wu: 100 }, { ...mac, wu: 200 });
assert.deepEqual(later.weak, { b: 3 }, '취약 단어는 나중에 바뀐 쪽');
assert.equal(merge({ ...phone, wu: 300 }, { ...mac, wu: 200 }).weak, phone.weak);

const empty = merge(phone, { cards: {}, log: {}, weak: {} });
assert.equal(canon(prog(empty)), canon(prog(phone)), '빈 서버와 합치면 그대로');
console.log('ok');
