# Workflow: Candidate Profile Email (Outlook Draft)

## Objective

After a batch of Formatted CVs is ready, share the candidates with the client by email — bundled per client + open position, one email covers every candidate being submitted for that role. The email is always created as an **Outlook draft**, never auto-sent. The user attaches the matching Formatted CV file(s) and sends it themselves.

## Required inputs

- A batch text note in `New CVs/` (any filename) — the same note used for the Formatted CV Executive Summary, extended with email-only fields. See format below.
- The Microsoft 365 connector authorized and signed in as the mailbox the drafts should land in. Verify with `mcp__claude_ai_Microsoft_365__get_me` before creating anything — if it returns the wrong account, the drafts will land in the wrong Drafts folder. Reconnecting to a different account is done by the user via claude.ai → Settings → Connectors (disconnect Microsoft 365, reconnect, sign in as the right account); the agent cannot drive that OAuth flow.

## Batch note format

One `=== CLIENT: ... ===` header per client/position group. Candidate blocks are separated by a blank line; no blank lines within a single candidate's own fields.

```
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
```

Required per candidate: `Executive Summary`, `Position`, `Company`, at least one `Key Highlights` bullet. Optional: `Compensation`, `Note` (render as `-` if omitted).

`Executive Summary` feeds the Formatted CV (see the CV-formatting steps in CLAUDE.md's Formatted CVs section). `Position`, `Company`, `Compensation`, `Note`, `Key Highlights` are email-only and never touch the CV docx.

## Steps

1. Confirm the signed-in Microsoft 365 account with `get_me` before doing anything else.
2. Run `python3 tools/build_email_drafts.py --note "New CVs/<file>"`. It parses the note, groups candidates by client/position, and writes one rendered HTML body per group plus `manifest.json` into `.tmp/email_drafts/` (auto-created). Malformed notes fail loudly with a line number — fix the note and rerun rather than guessing at the intent.
3. Read `manifest.json` and each group's HTML file.
4. For each group, call `outlook_create_draft` with `to: [client_email]`, `subject` from the manifest, `bodyType: "html"`, `body` = the rendered HTML. Never call `outlook_send_mail` / `outlook_send_draft` for this workflow — drafts only.
5. Report the `webLink` for each created draft to the user, and remind them which Formatted CV file(s) (from `Formatted CVs/`) need to be attached before sending — match by the candidate names listed in the manifest entry.

## Expected output

One Outlook draft per `CLIENT` group, sitting in the signed-in account's Drafts folder, ready for the user to attach CV(s) and send.

## Edge cases / gotchas

- **Outlook's HTML sanitizer strips every attribute on every tag** — no `style=`, `border=`, `class=`, nothing except `href`/`name`/`target` on `<a>`. A plain `<table>` renders with no visible gridlines because of this; there is no HTML that produces a bordered `<table>` through this API. `build_email_drafts.py` works around it by rendering the candidate detail block as a framed, monospace `<pre>` table (dash/pipe borders) — don't try to reintroduce a real `<table>` with styling, it will be rejected outright (`VALIDATION_ERROR: html_sanitize_rejected`).
- Allowed tags: `p, br, a[href|name|target], b/strong, i/em, ul/ol/li, h1-h6, table/thead/tbody/tr/th/td, code, pre, hr, div, strike`. Anything else in the body (images, spans, inline styles) gets the draft rejected, not silently stripped.
- If a candidate has no entry in the batch note, they simply don't appear in any email — this workflow never infers or fabricates the email-only fields.
- Draft/delete operations only reach the currently signed-in account's mailbox. A draft created before switching accounts (via `get_me`) is not reachable after switching — it has to be cleaned up manually in that other account.
