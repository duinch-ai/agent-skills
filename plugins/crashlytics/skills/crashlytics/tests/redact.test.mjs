// node --test plugins/crashlytics/skills/crashlytics/tests/redact.test.mjs
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { redactJson, redactText, redactTrace } from '../scripts/redact.mjs';

test('masks user data in free text', () => {
  const cases = [
    ['user a.b+c@mail.example.com failed', 'user <email> failed'],
    ['call +84 912 345 678 now', 'call <number> now'],
    ['phone=0912345678', 'phone=<number>'],
    ['GET https://api.example.com/v1/me?uid=42&sig=abc failed', 'GET https://api.example.com/v1/me?<query> failed'],
    ['jwt eyJhbGciOi.eyJzdWIiOiIx.c2lnbmF0dXJl end', 'jwt <jwt> end'],
    ['Authorization: Bearer abc.def-123', 'Authorization: Bearer <redacted>'],
    ['password=hunter2; next', 'password=<redacted>; next'],
    ['token: 1a2b3c', 'token: <redacted>'],
    ['device 123e4567-e89b-12d3-a456-426614174000 gone', 'device <uuid> gone'],
    ['connect 192.168.1.20 refused', 'connect <ip> refused'],
    ['connect fe80:0:0:0:1ff:fe23:4567:890a refused', 'connect <ip> refused'],
    ['open /Users/jane/Library/x.db', 'open /Users/<user>/Library/x.db'],
    ['open C:\\Users\\jane\\x.db', 'open C:\\Users\\<user>\\x.db'],
    ['key AbCdEf0123456789AbCdEf0123456789xyz used', 'key <token> used'],
    ['hash 83a3ef15e086a2dd53aec49eb77569e7 seen', 'hash <token> seen'],
  ];
  for (const [input, expected] of cases) assert.equal(redactText(input), expected, input);
});

test('keeps epoch timestamps and the run\'s issue ids, masks other ids', () => {
  assert.equal(redactText('at 1731234567 and 1731234567890'), 'at 1731234567 and 1731234567890');
  assert.equal(redactText('user 2731234567 and +1731234567'), 'user <number> and <number>');
  const keep = new Set(['83a3ef15e086a2dd53aec49eb77569e7']);
  assert.equal(redactText('issue 83a3ef15e086a2dd53aec49eb77569e7 install 0f1e2d3c4b5a69788796a5b4c3d2e1f0', keep),
    'issue 83a3ef15e086a2dd53aec49eb77569e7 install <token>');
  assert.equal(JSON.parse(redactJson(JSON.stringify(['83a3ef15e086a2dd53aec49eb77569e7']), keep))[0], '83a3ef15e086a2dd53aec49eb77569e7');
});

test('leaves crash facts readable', () => {
  const kept = [
    'Fatal Exception: java.lang.StringIndexOutOfBoundsException: length=0; index=0',
    'Fatal Exception: java.lang.IllegalStateException: Cannot invalidate item decorations during a scroll or layout',
    'Z:ZMediaHandlerThread:',
    'main (runnable):tid=1 systid=16524',
    'Caused by: java.io.IOException: timeout after 30000 ms at 13:34:08',
    'com.example.feature.ui.SomeVeryLongClassNameWithoutDigitsInIt',
  ];
  for (const line of kept) assert.equal(redactText(line), line);
});

test('trace: drops the session, keeps header and frames, masks messages', () => {
  const trace = [
    '# Crashlytics - ',
    '# Application: com.example.app',
    '# Version: 25.02.01.r1S (25021795)',
    '# Issue: 83a3ef15e086a2dd53aec49eb77569e7',
    '# Session: 6AF2D11A02C20001142FB625D7D74283_DNE_1_v2',
    '# Date: Tue Nov 10 2026 15:12:26 GMT+0700 (Indochina Time)',
    '',
    'Fatal Exception: java.lang.IllegalArgumentException: bad user jane@example.com 0912345678',
    '       at com.example.Foo.bar(Foo.kt:42)',
    '#00 pc 0x00000000000a1b2c  /system/lib64/libc.so (abort+164)',
    '0  CoreFoundation  0x0000000180a1b2c4 __exceptionPreprocess + 164',
    '#0      Foo.bar (package:app/foo.dart:12:5)',
  ].join('\n');
  const out = redactTrace(trace).split('\n');
  assert.ok(!out.some(l => l.startsWith('# Session:')));
  assert.ok(out.includes('# Issue: 83a3ef15e086a2dd53aec49eb77569e7'));
  assert.ok(out.includes('# Version: 25.02.01.r1S (25021795)'));
  assert.ok(out.includes('Fatal Exception: java.lang.IllegalArgumentException: bad user <email> <number>'));
  for (const frame of trace.split('\n').slice(8)) assert.ok(out.includes(frame), frame);
});

test('RPC bodies: strings masked, still valid JSON, numbers kept', () => {
  const body = JSON.stringify([['user', 'jane@example.com'], ['url', 'https://x.example.com/a?t=1"x'], ['events', 912345678]]);
  assert.deepEqual(JSON.parse(redactJson(body)), [['user', '<email>'], ['url', 'https://x.example.com/a?<query>"x'], ['events', 912345678]]);
  assert.equal(redactJson('not json jane@example.com'), 'not json <email>');
});
