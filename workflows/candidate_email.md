# Workflow: Candidate Profile Email (Outlook Draft)

## Objective

After a batch of Formatted CVs is ready, share the candidates with the client by email — bundled per client + open position, one email covers every candidate being submitted for that role. The email is always created as an **Outlook draft**, never auto-sent. The user attaches the matching Formatted CV file(s) and sends it themselves.

## Before drafting — always ask the user

Never draft from memory or assumption. Every time, ask the user for and confirm:

1. **Formatted CV link / path** — the file(s) in `Formatted CVs/`. Open and read each one; pull the candidate name, current role + employer, and Executive Summary from it (do not fabricate or pull from the raw CV if a Formatted CV exists).
2. **Client name** — for the `Dear <name>,` greeting.
3. **Vacancy** — one value, used *both* as the subject (`HLS Bridge: <Vacancy>`) and the `Vacancy:` line in the body.

Then build the draft. After creating it, **remind the user of every blank field** they still need to fill: `To:` recipient, Compensation, Notice period, Consultant comments, plus signature paste and CV attachment.

## Email template (use every time)

Model every draft on the **Janista Pinthong** email sent 2026-09-01 (subject `HLS Bridge: Key Account Manager`). Structure:

- **Subject:** `HLS Bridge: <Vacancy>` — same value as the `Vacancy:` line below.
- `Dear <Client name>,`
- `I would like to send you a profile for your review.` — "profiles" if more than one candidate.
- `Vacancy: <Vacancy>` — bold.
- Numbered list, one entry per candidate. Each: **bold candidate name**, then a sub-bullet list:
  - `Current Position / Company:` — bold value; the candidate's *current* role + employer (from the Formatted CV, not the vacancy).
  - `Compensation:`
  - `Notice period:`
  - `Consultant comments:`
  - `Executive Summary:` — bold label; same text as the candidate's Formatted CV.
- `If you have any questions regarding her/his profile, please feel free to let me know krub.`
- `Best regards,` / `Ryu`
- Signature block (see below).

Leave `Compensation` / `Notice period` / `Consultant comments` as empty labels if the batch note / user has not supplied them — the user fills them in.

**Recipient: leave `To:` blank.** The user inserts the client email address themselves. Create the draft anyway (0 recipients is accepted).

### Signature block

The Outlook draft API strips every inline style, so the branded gold-rule signature table in `config/signature.html` **cannot** be reproduced through the API. Render it as plain tags:

```
Washirawish (Ryu) Raweerojthakul
Founder & Consulting Partner
M: +66 81-135-7286
Connect with me on LinkedIn   (link: https://www.linkedin.com/in/washirawish-ryu-raweerojthakul-a8716b86/)
```

The user pastes the styled version from `config/signature.html` (or relies on the server-side signature) after opening the draft.

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
2. Gather each candidate's fields — from the batch note if present, otherwise from the user's message plus the raw/Formatted CV: current role + employer, Executive Summary (verbatim from the Formatted CV), and any Compensation / Notice period / Consultant comments the user supplied.
3. For each client/position group, call `outlook_create_draft` with **`to` omitted** (blank recipient), `subject` = `HLS Bridge: <Position>`, `bodyType: "html"`, `body` = the template above rendered with allowed tags only (`p, b/strong, i/em, ul/ol/li, div, br, a[href]`). Never call `outlook_send_mail` / `outlook_send_draft` — drafts only.
4. Report the `webLink` for each created draft, and remind the user to (a) insert the client email address, (b) paste the styled signature from `config/signature.html` if the server signature does not apply, and (c) attach the matching Formatted CV file(s) from `Formatted CVs/`.

`tools/build_email_drafts.py` predates the Janista template (it emits a "Key Highlights" section and requires a client email in the header). Until it is updated, build the draft body directly rather than from its output.

## Expected output

One Outlook draft per client/position group, in the signed-in account's Drafts folder, with a blank `To:`, ready for the user to fill the recipient, paste the signature, attach CV(s), and send.

## Edge cases / gotchas

- **Outlook's HTML sanitizer strips every attribute on every tag** — no `style=`, `border=`, `class=`, nothing except `href`/`name`/`target` on `<a>`. A plain `<table>` renders with no visible gridlines because of this; there is no HTML that produces a bordered `<table>` through this API. Two workarounds were tried and rejected by the user during review (a borderless `<table>`, then a framed monospace `<pre>` table that read as an odd block against the rest of the message) before landing on the current approach: `build_email_drafts.py` renders the candidate detail block as a plain bold-labeled list (`<strong>Candidate:</strong> ...<br>`), which matches the rest of the email's formatting. Don't reintroduce a styled `<table>` — it will be rejected outright (`VALIDATION_ERROR: html_sanitize_rejected`).
- Allowed tags: `p, br, a[href|name|target], b/strong, i/em, ul/ol/li, h1-h6, table/thead/tbody/tr/th/td, code, pre, hr, div, strike`. Anything else in the body (images, spans, inline styles) gets the draft rejected, not silently stripped.
- If a candidate has no entry in the batch note, they simply don't appear in any email — this workflow never infers or fabricates the email-only fields.
- Draft/delete operations only reach the currently signed-in account's mailbox. A draft created before switching accounts (via `get_me`) is not reachable after switching — it has to be cleaned up manually in that other account.
