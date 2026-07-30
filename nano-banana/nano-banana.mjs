#!/usr/bin/env node
// nano-banana.mjs - Direct Nano Banana (Gemini image) pipeline. No web UI.
//
// Generate: node nano-banana.mjs "a centurion portrait" --name marcus
// Iterate:  node nano-banana.mjs "same character, now smiling" --ref out/marcus-1.png --name marcus-v2
//
// Options:
//   --ref <path>   reference image, repeatable (up to 14 on Pro). Previous
//                  renders passed as refs = character consistency.
//   --model <id>   default: gemini-3-pro-image (Nano Banana Pro).
//                  fast/cheap: gemini-3.1-flash-image, gemini-2.5-flash-image
//   --out <dir>    output dir (default C:/Users/silas/Pictures/nano-banana)
//   --name <base>  output file basename (default: timestamp)
//   --ar <ratio>   aspect ratio: 1:1 2:3 3:2 3:4 4:3 4:5 5:4 9:16 16:9 21:9
//   --size <s>     1K | 2K | 4K (Pro models only)
//   --no-open      do not auto-open the results
//
// Auth: GEMINI_API_KEY env var, else read from C:/Users/silas/.gemini/.env

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';

const DEFAULT_MODEL = 'gemini-3-pro-image';
// NOTE: do NOT default under C:/Users/silas/Pictures - the Claude Code Bash
// sandbox hangs (not errors) node fs writes there. Documents + tool dirs work.
const DEFAULT_OUT = 'C:/Users/silas/tools/nano-banana/out';
const EXT_MIME = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
};

function fail(msg) {
  console.error('ERROR: ' + msg);
  process.exit(1);
}

// ---- args ----
const argv = process.argv.slice(2);
let prompt = null;
const refs = [];
let model = DEFAULT_MODEL;
let outDir = DEFAULT_OUT;
let name = null;
let ar = null;
let size = null;
let open = true;
let timeoutMs = 90000;
let retries = 2;

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--ref') refs.push(argv[++i]);
  else if (a === '--model') model = argv[++i];
  else if (a === '--out') outDir = argv[++i];
  else if (a === '--name') name = argv[++i];
  else if (a === '--ar') ar = argv[++i];
  else if (a === '--size') size = argv[++i];
  else if (a === '--no-open') open = false;
  else if (a === '--timeout') timeoutMs = parseInt(argv[++i], 10) * 1000;
  else if (a === '--retries') retries = parseInt(argv[++i], 10);
  else if (prompt === null) prompt = a;
  else fail('Unexpected argument: ' + a);
}
if (!prompt) fail('No prompt given. Usage: node nano-banana.mjs "prompt" [--ref img.png ...]');

// ---- api key ----
let key = process.env.GEMINI_API_KEY;
if (!key) {
  const envPath = path.join(os.homedir(), '.gemini', '.env');
  if (fs.existsSync(envPath)) {
    const m = fs.readFileSync(envPath, 'utf8').match(/GEMINI_API_KEY=([^\r\n]+)/);
    if (m) key = m[1].trim();
  }
}
if (!key) fail('GEMINI_API_KEY not found in env or ~/.gemini/.env');

// ---- request body ----
const parts = [];
for (const r of refs) {
  if (!fs.existsSync(r)) fail('Reference image not found: ' + r);
  const mime = EXT_MIME[path.extname(r).toLowerCase()];
  if (!mime) fail('Unsupported reference type: ' + r);
  parts.push({ inline_data: { mime_type: mime, data: fs.readFileSync(r).toString('base64') } });
}
parts.push({ text: prompt });

// Image models return images by default; responseModalities is NOT needed and
// the API has been observed holding connections open indefinitely on some
// requests, so every attempt gets a hard timeout + retry instead.
const req = { contents: [{ parts }] };
if (ar || size) {
  req.generationConfig = { imageConfig: {} };
  if (ar) req.generationConfig.imageConfig.aspectRatio = ar;
  if (size) req.generationConfig.imageConfig.imageSize = size;
}

const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent';
const body = JSON.stringify(req);

// ---- call ----
console.log('Model: ' + model + (refs.length ? ' | refs: ' + refs.length : '') + ' | prompt: ' + prompt.slice(0, 80) + (prompt.length > 80 ? '...' : ''));
const t0 = Date.now();
let res = null;
let data = null;
for (let attempt = 1; attempt <= 1 + retries; attempt++) {
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': key },
      body,
      signal: AbortSignal.timeout(timeoutMs),
    });
    data = await res.json();
    if (res.ok || res.status < 500) break;
    console.error('Attempt ' + attempt + ': HTTP ' + res.status + ', retrying...');
  } catch (e) {
    if (attempt > retries) fail('All attempts failed. Last error: ' + e.message);
    console.error('Attempt ' + attempt + ': ' + (e.name === 'TimeoutError' ? 'no response in ' + timeoutMs / 1000 + 's (API held the connection)' : e.message) + ', retrying...');
  }
}
if (!res || !data) fail('No response after ' + (1 + retries) + ' attempts.');
if (!res.ok) fail('API ' + res.status + ': ' + JSON.stringify(data.error || data).slice(0, 500));

const cand = data.candidates && data.candidates[0];
if (!cand || !cand.content || !cand.content.parts) {
  fail('No candidate returned. finishReason=' + (cand && cand.finishReason) +
    ' promptFeedback=' + JSON.stringify(data.promptFeedback || {}));
}

// ---- save ----
fs.mkdirSync(outDir, { recursive: true });
const base = name || new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19);
let n = 0;
const saved = [];
for (const p of cand.content.parts) {
  if (p.text) console.log('[model text] ' + p.text.trim());
  const img = p.inlineData || p.inline_data;
  if (img && img.data) {
    n++;
    const ext = (img.mimeType || img.mime_type || 'image/png').includes('jpeg') ? '.jpg' : '.png';
    const file = path.join(outDir, base + '-' + n + ext);
    fs.writeFileSync(file, Buffer.from(img.data, 'base64'));
    saved.push(file);
    console.log('SAVED: ' + file);
  }
}
console.log('Done in ' + ((Date.now() - t0) / 1000).toFixed(1) + 's, ' + saved.length + ' image(s).');
if (!saved.length) fail('Response contained no image data. finishReason=' + cand.finishReason);

if (open) {
  try {
    for (const f of saved) spawn('cmd', ['/c', 'start', '', f.replace(/\//g, '\\')], { detached: true, stdio: 'ignore' }).unref();
  } catch (e) {
    console.error('OPEN-FAILED (' + e.message + ') - open manually: ' + saved.join(' '));
  }
}
process.exit(0);
