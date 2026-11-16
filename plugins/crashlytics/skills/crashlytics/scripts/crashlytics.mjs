#!/usr/bin/env node
// Dumps Crashlytics issues from the Firebase console: the issue list for one filter, then each issue's
// stack trace (the console's own "Download stack trace" file); --rpc also keeps the raw dashboard RPC
// responses (~2 MB per issue: keys, logs, breadcrumbs). Can also add notes to, close or mute issues.
// Drives a dedicated Chrome profile over the DevTools protocol, so it uses the console's quota, not the
// public API's. Stateless: the project comes from a console link, the repo's Firebase config, or options.
// No npm dependencies (Node >= 22).
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, relative, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { redactJson, redactText, redactTrace } from './redact.mjs';

const CHROMES = {
  darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'],
  linux: ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'],
  win32: [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA]
    .filter(Boolean).map(d => join(d, 'Google', 'Chrome', 'Application', 'chrome.exe')),
}[process.platform] ?? [];

const { values: opt, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    login: { type: 'boolean', default: false },
    type: { type: 'string' },
    version: { type: 'string', multiple: true, default: [] },
    query: { type: 'string' },
    time: { type: 'string' },
    state: { type: 'string' },
    max: { type: 'string', default: '0' },
    rpc: { type: 'boolean', default: false },
    issue: { type: 'string', multiple: true, default: [] },
    note: { type: 'string' },
    close: { type: 'boolean', default: false },
    mute: { type: 'boolean', default: false },
    'dry-run': { type: 'boolean', default: false },
    raw: { type: 'boolean', default: false },
    help: { type: 'boolean', short: 'h', default: false },
    out: { type: 'string', default: 'build/crashlytics' },
    profile: { type: 'string', default: join(homedir(), '.crashlytics-chrome') },
    chrome: { type: 'string', default: CHROMES.find(p => existsSync(p)) },
    project: { type: 'string' },
    app: { type: 'string' },
    platform: { type: 'string' },
  },
});
if (opt.help) {
  console.log(`Firebase Crashlytics through the console (dedicated Chrome profile, no public API quota).

Usage
  crashlytics.mjs [<link>] [options]
    The project and app come from, in order: --project/--app, a Crashlytics console <link>
    (issue list or one issue, with its filters), or the Firebase config in the current repo
    (google-services.json / GoogleService-Info.plist). The first line logged names the project,
    app and platform (Android, iOS, or Flutter / React Native / Unity with the app's platform).

  crashlytics.mjs --login [<link>]               sign in once; exits when the console is signed in
  crashlytics.mjs [<link>] [dump options]        list issues and download each stack trace;
                                                 an issue link downloads just that issue
  crashlytics.mjs [<link>] --issue <id> [--issue <id>] [--note "text"] [--close | --mute] [--dry-run]

Dump options (each overrides the link's own filter)
  --type <crash|nonfatal|ANR>   event type; ANR is Android only    (default crash)
  --version "<name> (<code>)"   repeatable, as the console shows it (default all versions)
  --query <text>                console search, title and stack    (default none)
  --state <console value>       only "open" verified so far        (default open)
  --time <7d|30d|90d>                                              (default 7d)
  --max <n>                     issues per version by event count; the console pages at most 400
  --rpc                         also save keys, logs, breadcrumbs (~2 MB per issue)
  --out <dir>                                                      (default build/crashlytics)
  --raw                         keep user data; by default emails, phone numbers, ids, tokens, IPs,
                                URL queries and the session id are masked in every file written
  Output: <out>/<type>-<query>/<version>/index.tsv and <id>.txt (the console's stack trace file)

Issue actions (an issue link counts as --issue)
  --note "text"   add a note (runs first)
  --close         close an open issue
  --mute          mute the issue (exclusive with --close)
  --dry-run       print the plan without clicking

Other
  --project <id>    Firebase project id
  --app <id>        console app id, e.g. android:com.example.app or ios:com.example.app
  --platform <android|ios>  pick that platform's app when the repo has both
  --profile <dir>   Chrome profile        (default ~/.crashlytics-chrome)
  --chrome <path>   Chrome binary         (default: found in the usual install paths)
  -h, --help

One run at a time: every run uses the same Chrome profile.`);
  process.exit(0);
}

const fail = msg => { console.error(msg); process.exit(2); };
const mask = text => (opt.raw ? text : redactText(text));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.error(new Date().toISOString().slice(11, 19), ...a);

function parseLink(link) {
  let url;
  try { url = new URL(link); } catch { fail(`Not a link: ${link}`); }
  const m = url.hostname === 'console.firebase.google.com'
    && url.pathname.match(/\/project\/([^/]+)\/crashlytics\/app\/([^/]+)(?:\/issues\/([0-9a-f]{32}))?/);
  if (!m) fail('Not a Crashlytics console link: expected https://console.firebase.google.com/.../project/<id>/crashlytics/app/<app>/...');
  const p = url.searchParams;
  return { project: m[1], app: decodeURIComponent(m[2]), issue: m[3], types: p.get('types'), time: p.get('time'),
    state: p.get('state'), versions: p.get('versions'), query: p.get('issuesQuery') };
}

const SKIP = new Set(['build', 'node_modules', 'Pods', 'DerivedData']);
function findFirebaseApps(dir, depth = 4, found = []) {
  let entries;
  try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return found; }
  for (const e of entries) {
    const path = join(dir, e.name);
    if (e.isDirectory()) {
      if (depth > 0 && !e.name.startsWith('.') && !SKIP.has(e.name)) findFirebaseApps(path, depth - 1, found);
    } else if (e.name === 'google-services.json') {
      try {
        const d = JSON.parse(readFileSync(path, 'utf8'));
        for (const c of d.client ?? []) {
          const pkg = c.client_info?.android_client_info?.package_name;
          if (pkg) found.push({ project: d.project_info.project_id, app: `android:${pkg}`, path });
        }
      } catch { /* not a Firebase config after all: skip it */ }
    } else if (e.name === 'GoogleService-Info.plist') {
      const xml = readFileSync(path, 'utf8');
      const get = key => xml.match(new RegExp(`<key>${key}</key>\\s*<string>([^<]+)</string>`))?.[1];
      if (get('PROJECT_ID') && get('BUNDLE_ID')) found.push({ project: get('PROJECT_ID'), app: `ios:${get('BUNDLE_ID')}`, path });
    }
  }
  return found;
}

function detectFramework(dir) {
  const has = file => existsSync(join(dir, file));
  if (has('pubspec.yaml')) return 'Flutter';
  if (has('package.json') && /"react-native"\s*:/.test(readFileSync(join(dir, 'package.json'), 'utf8'))) return 'React Native';
  if (has('ProjectSettings/ProjectVersion.txt')) return 'Unity';
  return null;
}

const ref = positionals[0] ? parseLink(positionals[0]) : {};
let project = opt.project ?? ref.project;
let app = opt.app ?? ref.app;
let source = positionals[0] ? 'link' : 'options';
let framework = null;
if (!project || !app) {
  const apps = [...new Map(findFirebaseApps(process.cwd())
    .filter(a => (!project || a.project === project) && (!app || a.app === app)
      && (!opt.platform || a.app.startsWith(`${opt.platform.toLowerCase()}:`)))
    .map(a => [`${a.project} ${a.app}`, a])).values()];
  if (apps.length === 1) {
    ({ project, app } = apps[0]);
    source = relative(process.cwd(), apps[0].path);
    framework = detectFramework(process.cwd());
  } else if (apps.length > 1 && !opt.login) {
    fail('Several Firebase apps in this repo; pass --platform <android|ios>, a link, or one of:\n'
      + apps.map(a => `  --project ${a.project} --app ${a.app}   (${relative(process.cwd(), a.path)})`).join('\n'));
  }
}
if (!opt.login && (!project || !app)) {
  fail('Which project? Run inside the app repo (google-services.json / GoogleService-Info.plist), pass a Crashlytics console link, or --project and --app.');
}
const platform = app?.startsWith('android:') ? 'Android' : 'iOS';
if (project) log(`project ${project}, app ${app}, platform ${framework ? `${framework} (${platform})` : platform} (from ${source})`);
if (!opt.chrome) fail('Google Chrome not found; pass --chrome <path>');

const acting = !!(opt.note || opt.close || opt.mute);
if (ref.issue && acting) opt.issue.push(ref.issue);
const single = ref.issue && !acting ? ref.issue : null;
opt.type ??= ref.types ?? 'crash';
if (!opt.login && opt.type.toUpperCase() === 'ANR' && platform !== 'Android') fail(`ANR exists only for Android apps; ${app} is ${platform}. Use --type crash or nonfatal.`);
opt.time ??= ref.time ?? '7d';
opt.state ??= ref.state ?? 'open';
opt.query ??= ref.query ?? '';
if (!opt.version.length && ref.versions) opt.version.push(ref.versions);
const BASE = project && `https://console.firebase.google.com/u/0/project/${project}/crashlytics/app/${app}`;
// The tab title is "<project display name> - <page title> - Firebase console".
const PAGE_TITLE = `document.title.replace(/ - Firebase console$/, '').replace(/^.*? - /, '')`;

async function launch() {
  mkdirSync(opt.profile, { recursive: true });
  const portFile = join(opt.profile, 'DevToolsActivePort');
  if (existsSync(portFile)) writeFileSync(portFile, '');
  const args = [`--user-data-dir=${opt.profile}`, '--remote-debugging-port=0', '--no-first-run',
    '--no-default-browser-check', '--window-size=1600,1200'];
  if (!opt.login) args.push('--headless=new');
  const first = opt.login ? BASE ?? 'https://console.firebase.google.com/' : 'about:blank';
  const proc = spawn(opt.chrome, [...args, first], { stdio: 'ignore' });
  for (let i = 0; i < 100; i++) {
    const [port, path] = existsSync(portFile) ? readFileSync(portFile, 'utf8').split('\n') : [];
    if (port && path) return { proc, ws: `ws://127.0.0.1:${port}${path}` };
    await sleep(200);
  }
  proc.kill();
  throw new Error('Chrome did not open a DevTools port (profile in use, or a Keychain prompt is waiting)');
}

function cdp(url) {
  const ws = new WebSocket(url);
  let id = 0;
  const pending = new Map(), listeners = [];
  ws.onmessage = ({ data }) => {
    const m = JSON.parse(data);
    if (m.id && pending.has(m.id)) {
      const { ok, ko } = pending.get(m.id); pending.delete(m.id);
      m.error ? ko(new Error(`${m.error.message}`)) : ok(m.result);
    } else if (m.method) listeners.forEach(l => l(m));
  };
  let closed = false;
  ws.onclose = () => {
    closed = true;
    pending.forEach(({ ko }) => ko(new Error('Chrome closed the DevTools connection (quit or crashed)')));
    pending.clear();
  };
  const send = (method, params = {}, sessionId) => new Promise((ok, ko) => {
    if (closed) return ko(new Error('Chrome closed the DevTools connection (quit or crashed)'));
    pending.set(++id, { ok, ko });
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });
  return new Promise(r => { ws.onopen = () => r({ send, on: f => listeners.push(f), close: () => ws.close() }); });
}

async function openPage(c) {
  const { targetId } = await c.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await c.send('Target.attachToTarget', { targetId, flatten: true });
  const s = (m, p) => c.send(m, p, sessionId);
  await s('Network.enable', { maxResourceBufferSize: 50e6, maxTotalBufferSize: 200e6 });
  await s('Page.enable');
  const rpc = new Map(); // requestId -> url, for crashlytics-pa dashboard RPCs
  const bodies = [];
  c.on(async m => {
    if (m.sessionId !== sessionId) return;
    if (m.method === 'Network.responseReceived' && /crashlytics-pa\.clients6/.test(m.params.response.url)) rpc.set(m.params.requestId, m.params.response.url);
    if (m.method === 'Network.loadingFinished' && rpc.has(m.params.requestId)) {
      const url = rpc.get(m.params.requestId); rpc.delete(m.params.requestId);
      try {
        const { body } = await s('Network.getResponseBody', { requestId: m.params.requestId });
        bodies.push({ rpc: url.replace(/^.*\$rpc\/[^/]*\./, ''), body });
      } catch { /* evicted: the stack trace file still covers the essentials */ }
    }
  });
  const evaluate = async expr => (await s('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result.value;
  const go = async url => { bodies.length = 0; await s('Page.navigate', { url }); };
  const waitFor = async (expr, ms = 30000) => {
    for (const end = Date.now() + ms; Date.now() < end; await sleep(500)) if (await evaluate(expr)) return true;
    return false;
  };
  return { s, evaluate, go, waitFor, bodies, targetId };
}

// ListFirebaseTopOpenIssues -> [[issue, ...], ...]; issue = [id, _, events, ..., [title, subtitle, ...], ...]
function parseIssues(body) {
  const found = [];
  const walk = v => {
    if (!Array.isArray(v)) return;
    if (typeof v[0] === 'string' && /^[0-9a-f]{32}$/.test(v[0]) && typeof v[2] === 'string' && /^\d+$/.test(v[2])) {
      const text = v.find(x => Array.isArray(x) && typeof x[0] === 'string' && typeof x[1] === 'string');
      const versions = v.filter(x => typeof x === 'string' && /^\d+\.\d+/.test(x));
      found.push({ id: v[0], events: +v[2], users: /^\d+$/.test(v[12] ?? '') ? +v[12] : null,
        firstVersion: versions[0] ?? '', lastVersion: versions[1] ?? '', title: text?.[0] ?? '', subtitle: text?.[1] ?? '' });
      return;
    }
    v.forEach(walk);
  };
  walk(JSON.parse(body));
  return found;
}

if (opt.close && opt.mute) fail('--close and --mute are exclusive');
if (opt.issue.length && !acting) fail('--issue needs --note, --close or --mute');
const { proc, ws } = await launch();
const c = await cdp(ws);
if (opt.login) {
  log('Sign in to the Firebase console in the window that opened; this exits once you are signed in.');
  // closing the window does not quit Chrome on macOS, so wait for the signed-in console instead and quit
  // cleanly, which also flushes the session cookies to the profile
  for (;;) {
    const pages = (await c.send('Target.getTargets')).targetInfos.filter(t => t.type === 'page');
    if (!pages.length) break;
    const { cookies } = await c.send('Storage.getCookies');
    const signedIn = cookies.some(k => k.name === 'SID' && k.domain === '.google.com');
    if (signedIn && pages.some(t => t.url.startsWith('https://console.firebase.google.com/'))) break;
    await sleep(1000);
  }
  await sleep(3000);
  await c.send('Browser.close').catch(() => {});
  log('Signed in. Run again without --login.');
  process.exit(0);
}
async function updateIssues(page) {
  const btn = re => `[...document.querySelectorAll('button')].find(b => b.offsetParent && ${re}.test((b.innerText || '').replace(/\\s+/g, ' ').trim()))`;
  const state = `(${btn('/^(Close|Reopen|Unmute)$/')}?.innerText || '').trim() || 'unknown'`;
  for (const id of opt.issue) {
    if (!/^[0-9a-f]{32}$/.test(id)) { log(`${id}: not a 32-hex issue id, skipped`); continue; }
    await page.go(`${BASE}/issues/${id}`);
    if (!(await page.waitFor(`!!${btn('/^\\d+ notes?$/')}`, 45000))) { log(`${id}: issue page did not load`); process.exitCode = 1; continue; }
    await page.waitFor(`(${state}) !== 'unknown'`, 20000);
    await page.waitFor(`/ - .* - Firebase console$/.test(document.title)`, 5000);
    const title = mask(await page.evaluate(PAGE_TITLE));
    const before = await page.evaluate(state);
    log(`${id}: "${title}", state button: ${before}`);
    if (opt['dry-run']) { log(`  dry run: would ${[opt.note && `add note "${opt.note}"`, opt.close && 'close', opt.mute && 'mute'].filter(Boolean).join(', then ')}`); continue; }
    if (opt.note) {
      const count = () => page.evaluate(`+((${btn('/^\\d+ notes?$/')}?.innerText || '0').match(/\\d+/) || [0])[0]`);
      const n0 = await count();
      await page.evaluate(`${btn('/^\\d+ notes?$/')}.click()`);
      await page.waitFor(`!!document.querySelector('textarea[placeholder="Add a note here"]')`, 10000);
      await page.evaluate(`document.querySelector('textarea[placeholder="Add a note here"]').focus()`);
      await page.s('Input.insertText', { text: opt.note });
      await page.evaluate(`${btn('/^Add note$/')}.click()`);
      const ok = await page.waitFor(`+((${btn('/^\\d+ notes?$/')}?.innerText || '0').match(/\\d+/) || [0])[0] > ${n0}`, 15000);
      log(`  note ${ok ? 'added' : 'NOT confirmed'} (${n0} -> ${await count()})`);
      if (!ok) { process.exitCode = 1; continue; }
    }
    if (opt.close) {
      if (before !== 'Close') { log(`  not open (state button "${before}"), close skipped`); continue; }
      await page.evaluate(`${btn('/^Close$/')}.click()`);
      const ok = await page.waitFor(`(${state}) !== 'Close'`, 15000);
      log(`  close ${ok ? 'done' : 'NOT confirmed'}, state button now: ${await page.evaluate(state)}`);
      if (!ok) process.exitCode = 1;
    }
    if (opt.mute) {
      await page.evaluate(`[...document.querySelectorAll('button')].find(b => b.getAttribute('aria-label') === 'More options' && /keyboard_arrow_down/.test(b.innerText)).click()`);
      const open = await page.waitFor(`!!${'[...document.querySelectorAll(\'[role=menuitem]\')].find(m => /^Mute\\b/.test(m.innerText.trim()))'}`, 10000);
      if (!open) { log('  mute menu item not found'); process.exitCode = 1; continue; }
      await page.evaluate(`[...document.querySelectorAll('[role=menuitem]')].find(m => /^Mute\\b/.test(m.innerText.trim())).click()`);
      const ok = await page.waitFor(`(${state}) === 'Unmute' || /\\bMuted\\b/.test(document.body.innerText)`, 15000);
      log(`  mute ${ok ? 'done' : 'NOT confirmed'}, state button now: ${await page.evaluate(state)}`);
      if (!ok) process.exitCode = 1;
    }
  }
}

const notSignedIn = async page => (await page.evaluate('location.host')).startsWith('accounts.');

async function listIssues(page, version, q) {
  log(`list ${version ?? 'all versions'}`);
  await page.go(`${BASE}/issues?${q}`);
  await sleep(4000);
  if (await notSignedIn(page)) throw new Error('Not signed in: run once with --login');
  const issues = new Map();
  for (let pageNo = 1; ; pageNo++) {
    const seen = issues.size;
    for (let i = 0; i < 60 && issues.size === seen; i++) {
      for (const b of page.bodies.filter(b => b.rpc.endsWith('ListFirebaseTopOpenIssues'))) parseIssues(b.body).forEach(x => issues.set(x.id, x));
      await sleep(500);
    }
    log(`  page ${pageNo}: ${issues.size} issues`);
    if (issues.size === seen || (+opt.max && issues.size >= +opt.max)) break;
    page.bodies.length = 0;
    const moved = await page.evaluate(`(() => { const b = [...document.querySelectorAll('button')].find(b => b.getAttribute('aria-label') === 'Next page'); if (!b || b.disabled) return false; b.click(); return true; })()`);
    if (!moved) break;
  }
  const total = await page.evaluate(`(document.body.innerText.match(/\\d+ – \\d+ of (\\d+)/) || [])[1] || ''`);
  if (total && +total > issues.size && !+opt.max) {
    log(`  the console pages at most ${issues.size} of ${total} issues; the rest are the lowest by event count`);
  }
  return [...issues.values()].slice(0, +opt.max || undefined);
}

try {
  const page = await openPage(c);
  if (opt.issue.length) await updateIssues(page);
  const typeParam = opt.type.toUpperCase() === 'ANR' ? 'ANR' : opt.type.toLowerCase();
  const filter = new URLSearchParams({ time: opt.time, types: typeParam, state: opt.state, tag: 'all', sort: 'eventCount' });
  const outRoot = resolve(opt.out, `${opt.type.toLowerCase()}-${opt.query || 'all'}`);
  for (const version of opt.issue.length ? [] : single || !opt.version.length ? [null] : opt.version) {
    const q = new URLSearchParams(filter);
    if (version) q.set('versions', version);
    if (opt.query) q.set('issuesQuery', opt.query);
    const dir = single ? resolve(opt.out, 'issues') : join(outRoot, (version ?? 'all-versions').replace(/[^\w.()-]+/g, '_'));
    mkdirSync(dir, { recursive: true });
    const list = single
      ? [{ id: single, events: '', users: null, firstVersion: '', lastVersion: '', title: '', subtitle: '' }]
      : await listIssues(page, version, q);
    for (const x of list) x.title = mask(x.title), x.subtitle = mask(x.subtitle);
    if (!single) writeFileSync(join(dir, 'issues.json'), JSON.stringify(list, null, 1));

    await c.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dir, eventsEnabled: true });
    const keep = new Set(list.map(x => x.id));
    let done = 0;
    for (const issue of list) {
      const target = join(dir, `${issue.id}.txt`);
      if (existsSync(target)) { done++; continue; }
      const before = new Set(readdirSync(dir));
      await page.go(`${BASE}/issues/${issue.id}?${q}`);
      const ready = await page.waitFor(`!!document.querySelector('[aria-label="Download stack trace"]')`, 45000);
      if (!ready && await notSignedIn(page)) throw new Error('Not signed in: run once with --login');
      if (!ready) { log(`  ${issue.id}: no stack trace button, skipped`); continue; }
      await sleep(1500); // let the selected event finish rendering before downloading it
      if (single) issue.title = mask(await page.evaluate(PAGE_TITLE));
      await page.evaluate(`document.querySelector('[aria-label="Download stack trace"]').click()`);
      let file;
      for (let i = 0; i < 60 && !file; i++) {
        await sleep(500);
        file = readdirSync(dir).find(f => !before.has(f) && !f.endsWith('.crdownload'));
      }
      if (file) {
        renameSync(join(dir, file), target);
        if (!opt.raw) writeFileSync(target, redactTrace(readFileSync(target, 'utf8'), keep));
      }
      if (opt.rpc) {
        const bodies = opt.raw ? page.bodies : page.bodies.map(b => ({ ...b, body: redactJson(b.body, keep) }));
        writeFileSync(join(dir, `${issue.id}.rpc.json`), JSON.stringify(bodies, null, 1));
      }
      log(`  ${++done}/${list.length} ${issue.id} ${file ? 'saved' : 'download missing'} ${issue.title}`);
    }
    if (single) { console.log(join(dir, `${single}.txt`)); continue; }
    const tsv = ['id\tevents\tusers\tfirst\tlast\ttitle\tsubtitle\tstacktrace',
      ...list.map(x => [x.id, x.events, x.users ?? '', x.firstVersion, x.lastVersion, x.title, x.subtitle.replace(/\s+/g, ' '),
        existsSync(join(dir, `${x.id}.txt`)) ? `${x.id}.txt` : ''].join('\t'))];
    writeFileSync(join(dir, 'index.tsv'), tsv.join('\n') + '\n');
    console.log(join(dir, 'index.tsv'));
  }
} finally {
  c.close();
  proc.kill();
}
