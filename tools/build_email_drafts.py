#!/usr/bin/env python3
"""Parse a batch candidate-submission note into per-client email bodies.

Does no sending -- it only turns the batch text note (dropped in New CVs/
alongside the CV PDFs) into one rendered HTML email body per CLIENT group,
plus a manifest describing recipient/subject/candidates for each. The agent
reads the manifest and calls the Outlook draft-creation tool itself; this
script never touches a mailbox.

Batch note format (one text file, any filename):

    === CLIENT: Client Contact Name <client@email.com> - Position: Marketing Manager ===

    Candidate Full Name
    Executive Summary: same text used in their Formatted CV...
    Position: Marketing Manager
    Company: target company name
    Compensation: 80,000 THB
    Note: Available to start within 30 days
    Key Highlights:
    - 5+ years in digital marketing
    - Led rebrand for X company

    Another Candidate Name
    Executive Summary: ...
    Position: ...
    Company: ...
    Key Highlights:
    - ...

    === END ===

Rules:
- One CLIENT header starts a group; every candidate block until the next
  CLIENT header (or === END ===, or end of file) is bundled into that
  client's single email.
- Candidate blocks are separated by a blank line. No blank lines *within*
  a candidate's own fields.
- Executive Summary, Position, Company are required per candidate; at least
  one Key Highlights bullet is required. Compensation and Note are optional.

Usage:
    python3 tools/build_email_drafts.py --note "New CVs/batch_note.txt"
"""
import argparse
import json
import os
import re
import sys
from html import escape

HEADER_RE = re.compile(
    r"^===\s*CLIENT\s*:\s*(?P<name>.+?)\s*<(?P<email>[^>]+)>\s*[-—]\s*"
    r"Position\s*:\s*(?P<position>.+?)\s*===\s*$",
    re.IGNORECASE,
)
END_RE = re.compile(r"^===\s*END\s*===\s*$", re.IGNORECASE)
FIELD_RE = re.compile(
    r"^(Executive Summary|Position|Company|Compensation|Note|Key Highlights)\s*:\s*(.*)$",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^[-•*]\s*(.+)$")

FIELD_KEY = {
    "executive summary": "executive_summary",
    "position": "position",
    "company": "company",
    "compensation": "compensation",
    "note": "note",
}
REQUIRED_FIELDS = ("executive_summary", "position", "company")


def split_candidate_blocks(body_lines):
    blocks, current = [], []
    for ln, line in body_lines:
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append((ln, line))
    if current:
        blocks.append(current)
    return blocks


def parse_candidate_block(block):
    name_line_no, name_line = block[0]
    name = name_line.strip()
    if FIELD_RE.match(name) or HEADER_RE.match(name) or BULLET_RE.match(name):
        raise ValueError(
            f"Line {name_line_no}: expected a candidate name here, found: {name_line!r}"
        )

    data = {
        "full_name": name,
        "executive_summary": "",
        "position": "",
        "company": "",
        "compensation": "",
        "note": "",
        "key_highlights": [],
    }
    current_field = None

    for line_no, raw_line in block[1:]:
        line = raw_line.rstrip("\n")
        m = FIELD_RE.match(line.strip())
        if m:
            label = m.group(1).strip().lower()
            value = m.group(2).strip()
            current_field = label
            if label == "key highlights":
                if value:
                    raise ValueError(
                        f"Line {line_no}: 'Key Highlights:' must be followed by "
                        f"'- ' bullet lines on their own lines, not inline text."
                    )
            else:
                data[FIELD_KEY[label]] = value
            continue

        bm = BULLET_RE.match(line.strip())
        if bm and current_field == "key highlights":
            data["key_highlights"].append(bm.group(1).strip())
            continue

        if current_field is None:
            raise ValueError(
                f"Line {line_no}: unexpected text before any field label: {line!r}"
            )
        if current_field == "key highlights":
            raise ValueError(
                f"Line {line_no}: expected a '- ' bullet under Key Highlights, got: {line!r}"
            )
        key = FIELD_KEY[current_field]
        data[key] = (data[key] + " " + line.strip()).strip()

    missing = [f for f in REQUIRED_FIELDS if not data[f]]
    if missing:
        raise ValueError(
            f"Candidate {name!r} (starting line {name_line_no}) missing required "
            f"field(s): {', '.join(missing)}"
        )
    if not data["key_highlights"]:
        raise ValueError(
            f"Candidate {name!r} (starting line {name_line_no}) has no Key Highlights bullets."
        )
    return data


def parse_batch_note(text):
    lines = list(enumerate(text.splitlines(), start=1))
    groups = []
    i, n = 0, len(lines)

    while i < n:
        line_no, line = lines[i]
        m = HEADER_RE.match(line.strip())
        if not m:
            i += 1
            continue

        client_name = m.group("name").strip()
        client_email = m.group("email").strip()
        position = m.group("position").strip()
        i += 1

        body = []
        while i < n:
            ln2, l2 = lines[i]
            if HEADER_RE.match(l2.strip()) or END_RE.match(l2.strip()):
                break
            body.append((ln2, l2))
            i += 1

        candidates = [parse_candidate_block(b) for b in split_candidate_blocks(body)]
        if not candidates:
            raise ValueError(
                f"Line {line_no}: CLIENT group for {client_name!r} has no candidates."
            )
        groups.append(
            {
                "client_name": client_name,
                "client_email": client_email,
                "position": position,
                "candidates": candidates,
            }
        )

    if not groups:
        raise ValueError(
            "No '=== CLIENT: Name <email> - Position: ... ===' group headers found."
        )
    return groups


def render_candidate_table(c):
    # The Outlook draft/send tools strip every HTML attribute (no border=,
    # no style=), so a real <table> renders with no visible gridlines, and a
    # <pre>-framed table (tried and rejected -- see workflows/candidate_email.md)
    # reads as an odd monospace block against the rest of the message. A
    # plain bold-labeled list survives the sanitizer and matches the rest
    # of the email's formatting.
    fields = [
        ("Candidate", c["full_name"]),
        ("Position", c["position"]),
        ("Company", c["company"]),
        ("Compensation", c["compensation"] or "-"),
        ("Note", c["note"] or "-"),
    ]
    lines = [f"<strong>{label}:</strong> {escape(value)}" for label, value in fields]
    return "<p>" + "<br>".join(lines) + "</p>"


def render_group_html(group):
    candidates = group["candidates"]
    plural = "profile" if len(candidates) == 1 else "profiles"
    parts = [
        f"<p>Dear {escape(group['client_name'])},</p>",
        "<p>I hope this email finds you well.</p>",
        f"<p>I would like to share you {len(candidates)} potential {plural} "
        f"for your review. Please see as below;</p>",
    ]

    for idx, c in enumerate(candidates, start=1):
        parts.append(f"<p>{idx}. {escape(c['full_name'])}</p>")
        parts.append(render_candidate_table(c))
        parts.append("<p><strong>Executive Summary</strong></p>")
        parts.append(f"<p>{escape(c['executive_summary'])}</p>")
        parts.append("<p><strong>Key highlights</strong></p>")
        parts.append(
            "<ul>" + "".join(f"<li>{escape(h)}</li>" for h in c["key_highlights"]) + "</ul>"
        )

    parts.append("<p>If you have any questions regarding profiles. Please feel free to let me know.</p>")
    parts.append("<p>Look forward to hearing from you soon</p>")
    parts.append("<p>Best regards,<br>Ryu</p>")
    return "\n".join(parts)


def slugify(text):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "client"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--note", required=True, help="Path to the batch candidate-submission text note")
    parser.add_argument(
        "--output-dir", default=os.path.join(".tmp", "email_drafts"),
        help="Directory to write rendered HTML bodies + manifest.json (default: .tmp/email_drafts)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.note):
        print(f"Error: note file not found: {args.note}", file=sys.stderr)
        sys.exit(1)

    with open(args.note, "r", encoding="utf-8") as f:
        text = f.read()

    try:
        groups = parse_batch_note(text)
    except ValueError as e:
        print(f"Error: could not parse batch note -- {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    manifest = []
    used_slugs = set()

    for group in groups:
        base_slug = slugify(f"{group['client_name']}-{group['position']}")
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(slug)

        html_filename = f"{slug}.html"
        html_path = os.path.join(args.output_dir, html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(render_group_html(group))

        manifest.append(
            {
                "client_name": group["client_name"],
                "client_email": group["client_email"],
                "position": group["position"],
                "subject": f"Candidate Profiles – {group['position']}",
                "html_file": html_path,
                "candidates": [c["full_name"] for c in group["candidates"]],
            }
        )

    manifest_path = os.path.join(args.output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(os.path.abspath(manifest_path))
    for entry in manifest:
        names = ", ".join(entry["candidates"])
        print(f"  - {entry['client_name']} <{entry['client_email']}> [{entry['position']}]: {names}")


if __name__ == "__main__":
    main()
