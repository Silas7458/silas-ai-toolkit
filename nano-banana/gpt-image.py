#!/usr/bin/env python
# gpt-image.py - OpenAI image driver with reference images (same shape as nano-banana.mjs).
# Default model: gpt-image-2 (S#323). Others: gpt-image-2-2026-04-21, chatgpt-image-latest, gpt-image-1.5, gpt-image-1.
# Usage: python gpt-image.py "prompt" --ref a.png --ref b.png --name valerius --n 2 [--size 1024x1536] [--quality high]
# Auth: OPENAI_API_KEY env var, else council-config.json api_keys/openai
import sys, os, json, base64, argparse, datetime
from openai import OpenAI

ap = argparse.ArgumentParser()
ap.add_argument("prompt")
ap.add_argument("--ref", action="append", default=[])
ap.add_argument("--name", default=None)
ap.add_argument("--n", type=int, default=1)
ap.add_argument("--size", default="1024x1536")
ap.add_argument("--quality", default="high")
ap.add_argument("--out", default="./out")
ap.add_argument("--model", default="gpt-image-2")
a = ap.parse_args()

key = os.environ.get("OPENAI_API_KEY")
if not key:
    cfg = json.load(open("council-config.json"))
    key = cfg["api_keys"]["openai"]
client = OpenAI(api_key=key)

os.makedirs(a.out, exist_ok=True)
base = a.name or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

if a.ref:
    files = [open(r, "rb") for r in a.ref]
    resp = client.images.edit(model=a.model, image=files, prompt=a.prompt,
                              n=a.n, size=a.size, quality=a.quality)
else:
    resp = client.images.generate(model=a.model, prompt=a.prompt,
                                  n=a.n, size=a.size, quality=a.quality)

for i, d in enumerate(resp.data, 1):
    p = os.path.join(a.out, "%s-%d.png" % (base, i))
    open(p, "wb").write(base64.b64decode(d.b64_json))
    print("SAVED:", p)
