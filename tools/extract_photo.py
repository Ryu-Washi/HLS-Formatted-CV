#!/usr/bin/env python3
"""Extract a candidate headshot from a CV PDF's embedded images.

No pdftoppm/poppler on this machine, so this pulls embedded raster images
directly via PyMuPDF and scores them to guess which one is the headshot
(vs. a full-page scan, a company logo, or a divider icon). Automatic
selection is a best guess, not a guarantee -- use --list to inspect
candidates and --page/--xref to override.
"""
import argparse
import io
import json
import os
import sys

import fitz  # PyMuPDF
from PIL import Image


def find_photo_candidates(pdf_path):
    doc = fitz.open(pdf_path)
    best_by_xref = {}

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_area = page.rect.width * page.rect.height
        if page_area <= 0:
            continue

        for order, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            width, height = img[2], img[3]
            if width < 40 or height < 40:
                continue

            rects = page.get_image_rects(xref)
            if not rects:
                continue
            rect = max(rects, key=lambda r: r.width * r.height)
            coverage = (rect.width * rect.height) / page_area
            if coverage > 0.5:
                continue

            aspect = width / height if height else 0
            aspect_score = max(0.0, 1 - abs(aspect - 0.85) / 0.85)
            size_score = min(1.0, (width * height) / (400 * 400))
            coverage_score = 1.0 if 0.01 <= coverage <= 0.35 else 0.3
            page_score = {0: 1.0, 1: 0.5}.get(page_idx, 0.2)
            order_score = 1.0 / (1 + order)
            score = (
                0.35 * aspect_score
                + 0.25 * size_score
                + 0.2 * page_score
                + 0.15 * coverage_score
                + 0.05 * order_score
            )

            candidate = {
                "page": page_idx,
                "xref": xref,
                "width": width,
                "height": height,
                "aspect": round(aspect, 3),
                "coverage": round(coverage, 4),
                "score": round(score, 4),
            }
            existing = best_by_xref.get(xref)
            if existing is None or score > existing["score"]:
                best_by_xref[xref] = candidate

    ranked = sorted(best_by_xref.values(), key=lambda c: c["score"], reverse=True)
    return ranked, doc


def crop_to_square(image, max_side=800):
    if image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        image = background
    else:
        image = image.convert("RGB")

    w, h = image.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    image = image.crop((left, top, left + side, top + side))

    if side > max_side:
        image = image.resize((max_side, max_side), Image.Resampling.LANCZOS)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, help="Source CV PDF")
    parser.add_argument("--output", help="Where to save the cropped square JPEG")
    parser.add_argument(
        "--list", action="store_true",
        help="Print ranked candidate images as JSON and exit; writes no file",
    )
    parser.add_argument("--page", type=int, help="Manual override: 0-indexed page number")
    parser.add_argument("--xref", type=int, help="Manual override: image xref (from --list)")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: PDF not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    candidates, fitz_doc = find_photo_candidates(args.pdf)

    if args.list:
        print(json.dumps(candidates, indent=2))
        return

    if args.page is not None and args.xref is not None:
        target = next(
            (c for c in candidates if c["page"] == args.page and c["xref"] == args.xref),
            {"page": args.page, "xref": args.xref},
        )
    elif not candidates:
        print(
            "Error: no candidate headshot survived filtering (no embedded "
            "image on a page with a plausible headshot shape/size). Ask "
            "the user for a photo file directly.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        target = candidates[0]

    if not args.output:
        print("Error: --output is required unless --list is used.", file=sys.stderr)
        sys.exit(1)

    base_image = fitz_doc.extract_image(target["xref"])
    im = Image.open(io.BytesIO(base_image["image"]))
    im = crop_to_square(im)
    im.save(args.output, format="JPEG", quality=90)

    print(os.path.abspath(args.output))


if __name__ == "__main__":
    main()
