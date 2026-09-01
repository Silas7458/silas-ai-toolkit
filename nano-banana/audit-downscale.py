"""Downscale render candidates for audit reads.

Usage:
  python audit-downscale.py <image-or-dir> [more images...]

For each input image, writes an ~800px-wide copy to an `_audit/` folder
next to the source, named `<stem>_audit.png`. Existing audit copies are
overwritten so re-runs after re-renders stay fresh.

Rule (S#322 token burn): Claude audits candidates ONLY from these
downscaled copies. Full-res is read once, for the single finalist.
"""
import sys
from pathlib import Path

from PIL import Image

TARGET_WIDTH = 800
EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def downscale(src: Path) -> Path:
    out_dir = src.parent / "_audit"
    out_dir.mkdir(exist_ok=True)
    dst = out_dir / (src.stem + "_audit.jpg")
    with Image.open(src) as im:
        if im.width > TARGET_WIDTH:
            h = round(im.height * TARGET_WIDTH / im.width)
            im = im.resize((TARGET_WIDTH, h), Image.LANCZOS)
        im.convert("RGB").save(dst, "JPEG", quality=88)
    return dst


def main(args):
    if not args:
        print(__doc__)
        return 1
    targets = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            targets += [f for f in sorted(p.iterdir())
                        if f.suffix.lower() in EXTS and f.parent.name != "_audit"]
        elif p.is_file():
            targets.append(p)
        else:
            print(f"SKIP (not found): {p}")
    if not targets:
        print("No images found.")
        return 1
    for t in targets:
        dst = downscale(t)
        kb = dst.stat().st_size // 1024
        print(f"OK {t.name} -> {dst} ({kb} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
