// Best-effort masking of user data in Crashlytics output before an agent reads it. Pattern-based: it
// catches emails, phone numbers, ids, tokens and the like, not names or free-form text.

const RULES = [
  [/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g, '<email>'],
  [/\beyJ[\w-]+\.[\w-]+\.[\w-]+/g, '<jwt>'],
  // values stop at a backslash too, so a JSON escape (\") in an RPC body is never cut in half
  [/(https?:\/\/[^\s?#"'\\]+)\?[^\s#"'\\]*/gi, '$1?<query>'],
  [/\bbearer\s+[^\s"',;&\\]+/gi, 'Bearer <redacted>'],
  [/\b(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|auth|authorization|session|sid|cookie)(\s*[:=]\s*)(?!bearer\b|<)[^\s"',;&\\]+/gi, '$1$2<redacted>'],
  [/\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi, '<uuid>'],
  [/(\/Users\/|\/home\/|[A-Za-z]:\\Users\\)[^/\\\s"']+/g, '$1<user>'],
  [/\b(?:[0-9a-f]{1,4}:){3,7}[0-9a-f]{1,4}\b/gi, '<ip>'],
  [/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '<ip>'],
  // 9+ digits: phone numbers, user ids; plain epoch seconds or milliseconds (1xxxxxxxxx) are kept for timing
  [/(?<![\w.])\+?\d(?:[\s-]?\d){8,}(?![\w.])/g, s => (/^1\d{9}(?:\d{3})?$/.test(s) ? s : '<number>')],
];
const TOKEN = /[A-Za-z0-9+/_=-]{32,}/g;

// keep: strings to leave as they are, such as the issue ids of the run (installation ids look the same).
export function redactText(text, keep = new Set()) {
  const out = RULES.reduce((acc, [pattern, replacement]) => acc.replace(pattern, replacement), text);
  // long opaque strings (keys, tokens, hashes, device ids) that mix letters and digits
  return out.replace(TOKEN, s => (keep.has(s) || !/\d/.test(s) || !/[A-Za-z]/.test(s) ? s : '<token>'));
}

// RPC bodies are JSON: mask string values only, so the result still parses and counts stay numbers.
export function redactJson(body, keep) {
  const walk = v => typeof v === 'string' ? redactText(v, keep)
    : Array.isArray(v) ? v.map(walk)
    : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x)]))
    : v;
  try { return JSON.stringify(walk(JSON.parse(body))); } catch { return redactText(body, keep); }
}

// Stack frames (Java/Kotlin/JS "at ...", native "#00 pc ...", Dart "#0 ...", Apple "0 Module 0x...") are code,
// and the trace header names the app build, so both stay as they are; only messages and other free text are masked.
const FRAME = /^\s*(?:at\s|#\d+\s|\d+\s+\S+\s+0x[0-9a-f]+|\.\.\. \d+ more)/i;
const HEADER = /^# (?:Crashlytics|Application|Platform|Version|Issue|Date)\b/;

export function redactTrace(text, keep) {
  return text.split('\n')
    .filter(line => !/^# Session:/.test(line))
    .map(line => (FRAME.test(line) || HEADER.test(line) ? line : redactText(line, keep)))
    .join('\n');
}
