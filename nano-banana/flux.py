#!/usr/bin/env python
# flux.py - Black Forest Labs FLUX.2 driver (same shape as nano-banana.mjs / gpt-image.py).
# Usage: python flux.py "prompt" --ref a.png --ref b.png --name mardin --seed 42 [--width 1638 --height 2048]
# Up to 8 reference images (input_image..input_image_8). Prompt upsampling DISABLED by
# default (--pup to enable) so locked prompts are never rewritten by BFL.
# Auth: BFL_API_KEY env var, else council-config.json api_keys/bfl
import sys, os, json, base64, argparse, datetime, time
import urllib.request

API = "https://api.bfl.ai/v1"

ap = argparse.ArgumentParser()
ap.add_argument("prompt")
ap.add_argument("--ref", action="append", default=[], help="reference image path (max 8)")
ap.add_argument("--name", default=None)
ap.add_argument("--seed", type=int, default=None)
ap.add_argument("--width", type=int, default=1664)
ap.add_argument("--height", type=int, default=2048)
ap.add_argument("--model", default="flux-2-pro")
ap.add_argument("--pup", action="store_true", help="enable BFL prompt upsampling (default off)")
ap.add_argument("--out", default="./out")
ap.add_argument("--timeout", type=int, default=180)
a = ap.parse_args()

if len(a.ref) > 8:
    sys.exit("ERROR: max 8 reference images")

key = os.environ.get("BFL_API_KEY")
if not key:
    cfg = json.load(open("council-config.json"))
    key = cfg["api_keys"]["bfl"]

body = {
    "prompt": a.prompt,
    "width": a.width,
    "height": a.height,
    "output_format": "png",
    "disable_pup": (not a.pup),
    "safety_tolerance": 4,
}
if a.seed is not None:
    body["seed"] = a.seed
for i, r in enumerate(a.ref):
    field = "input_image" if i == 0 else "input_image_%d" % (i + 1)
    body[field] = base64.b64encode(open(r, "rb").read()).decode()

req = urllib.request.Request(API + "/" + a.model,
                             data=json.dumps(body).encode(),
                             headers={"x-key": key, "Content-Type": "application/json"})
try:
    resp = json.load(urllib.request.urlopen(req, timeout=60))
except urllib.error.HTTPError as e:
    sys.exit("ERROR %d: %s" % (e.code, e.read().decode()[:500]))

poll = resp.get("polling_url")
print("job:", resp.get("id"), "| cost:", resp.get("cost"),
      "| in_mp:", resp.get("input_mp"), "| out_mp:", resp.get("output_mp"))
if not poll:
    sys.exit("ERROR: no polling_url in response: %s" % json.dumps(resp)[:300])

os.makedirs(a.out, exist_ok=True)
base = a.name or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

deadline = time.time() + a.timeout
status = None
while time.time() < deadline:
    time.sleep(1.5)
    q = urllib.request.Request(poll, headers={"x-key": key})
    r = json.load(urllib.request.urlopen(q, timeout=30))
    status = r.get("status")
    if status == "Ready":
        url = r["result"]["sample"]
        p = os.path.join(a.out, base + ".png")
        urllib.request.urlretrieve(url, p)
        print("SAVED:", p)
        sys.exit(0)
    if status in ("Error", "Content Moderated", "Request Moderated", "Failed"):
        sys.exit("ERROR: status=%s detail=%s" % (status, json.dumps(r)[:400]))
sys.exit("ERROR: timed out after %ds (last status: %s)" % (a.timeout, status))
