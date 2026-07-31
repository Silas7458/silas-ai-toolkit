#!/usr/bin/env node
// veo.mjs - image-to-video via Veo (Gemini API). Companion to nano-banana.mjs.
// Usage: node veo.mjs "motion prompt" --img frame.jpg --name shot1 [--model id]
//        [--seconds 6] [--res 720p] [--out dir] [--timeout 420]
// Auth: GEMINI_API_KEY env or C:/Users/silas/.gemini/.env

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const DEFAULT_MODEL = 'veo-3.1-fast-generate-preview';
const DEFAULT_OUT = 'C:/Users/silas/Documents/last-roman/clips';

function fail(msg) { console.error('ERROR: ' + msg); process.exit(1); }

const argv = process.argv.slice(2);
let prompt = null, img = null, name = null;
let model = DEFAULT_MODEL, outDir = DEFAULT_OUT, seconds = 6, res = '720p', timeoutS = 420;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--img') img = argv[++i];
  else if (a === '--name') name = argv[++i];
  else if (a === '--model') model = argv[++i];
  else if (a === '--seconds') seconds = parseInt(argv[++i], 10);
  else if (a === '--res') res = argv[++i];
  else if (a === '--out') outDir = argv[++i];
  else if (a === '--timeout') timeoutS = parseInt(argv[++i], 10);
  else if (prompt === null) prompt = a;
  else fail('Unexpected argument: ' + a);
}
if (!prompt || !img || !name) fail('Need: "prompt" --img file --name base');
if (!fs.existsSync(img)) fail('Image not found: ' + img);

let key = process.env.GEMINI_API_KEY;
if (!key) {
  const envPath = path.join(os.homedir(), '.gemini', '.env');
  if (fs.existsSync(envPath)) {
    const m = fs.readFileSync(envPath, 'utf8').match(/GEMINI_API_KEY=([^\r\n]+)/);
    if (m) key = m[1].trim();
  }
}
if (!key) fail('GEMINI_API_KEY not found');

const mime = img.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
const body = JSON.stringify({
  instances: [{
    prompt,
    image: { bytesBase64Encoded: fs.readFileSync(img).toString('base64'), mimeType: mime },
  }],
  parameters: { aspectRatio: '16:9', resolution: res, durationSeconds: seconds },
});

const base = 'https://generativelanguage.googleapis.com/v1beta/';
const hdr = { 'Content-Type': 'application/json', 'x-goog-api-key': key };

console.log('Veo submit: ' + model + ' ' + seconds + 's ' + res + ' <- ' + path.basename(img));
const t0 = Date.now();
let res1 = await fetch(base + 'models/' + model + ':predictLongRunning', {
  method: 'POST', headers: hdr, body, signal: AbortSignal.timeout(60000),
});
let op = await res1.json();
if (!res1.ok) fail('submit ' + res1.status + ': ' + JSON.stringify(op.error || op).slice(0, 400));
if (!op.name) fail('no operation name: ' + JSON.stringify(op).slice(0, 300));

while (!op.done) {
  if ((Date.now() - t0) / 1000 > timeoutS) fail('poll timeout after ' + timeoutS + 's (op: ' + op.name + ')');
  await new Promise(r => setTimeout(r, 8000));
  const pr = await fetch(base + op.name, { headers: { 'x-goog-api-key': key }, signal: AbortSignal.timeout(30000) });
  op = await pr.json();
  process.stderr.write('.');
}
process.stderr.write('\n');
if (op.error) fail('operation error: ' + JSON.stringify(op.error).slice(0, 400));

const resp = op.response || {};
const gvr = resp.generateVideoResponse || resp;
const sample = (gvr.generatedSamples && gvr.generatedSamples[0]) || (gvr.videos && gvr.videos[0]);
if (!sample) fail('no video in response: ' + JSON.stringify(resp).slice(0, 500));
const uri = (sample.video && sample.video.uri) || sample.uri || null;

fs.mkdirSync(outDir, { recursive: true });
const outFile = path.join(outDir, name + '.mp4');
if (uri) {
  const dl = await fetch(uri, { headers: { 'x-goog-api-key': key }, signal: AbortSignal.timeout(120000) });
  if (!dl.ok) fail('download ' + dl.status);
  fs.writeFileSync(outFile, Buffer.from(await dl.arrayBuffer()));
} else if (sample.video && sample.video.bytesBase64Encoded) {
  fs.writeFileSync(outFile, Buffer.from(sample.video.bytesBase64Encoded, 'base64'));
} else {
  fail('no uri or bytes in sample: ' + JSON.stringify(sample).slice(0, 300));
}
console.log('SAVED: ' + outFile + ' (' + ((Date.now() - t0) / 1000).toFixed(0) + 's)');
