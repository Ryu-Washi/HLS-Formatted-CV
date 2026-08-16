# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Operating framework: WAT (Workflows, Agents, Tools)

You're working inside the WAT framework (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

### The WAT architecture

**Layer 1: Workflows (the instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (the decision-maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (the execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

### How to operate

1. **Look for existing tools first.** Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.
2. **Learn and adapt when things fail.** When you hit an error:
   - Read the full error message and trace
   - Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
   - Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
   - Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again
3. **Keep workflows current.** Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

### The self-improvement loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

### File structure

What goes where:
- **Deliverables:** Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates:** Temporary processing files that can be regenerated

Directory layout:
```
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
```

Core principle: local files are just for processing. Anything I need to see or use lives in cloud services. Everything in `.tmp/` is disposable.

### Bottom line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.

## What this repository is

This is **not a software project** — there is no source code, build system, linter, or test suite, and none should be assumed or invented. It is HLS Bridge Advisory Co., Ltd's document repository: brand assets, business collateral, and candidate CVs reformatted to the company's brand for sharing with clients.

## Repository structure

- `Brand CI update/` — the brand system. `hlsbridge_brand-handbook_v3.pdf` is the full spec (colors, type, logo rules, voice/tone); `qa_guideline/page-1.png` and `page-2.png` are a two-page quick-reference (which logo file to use, colors, do/don't). The rest of the folder is the actual logo asset files (PNG + matching vector PDF per variant).
- `New CVs/` — drop folder for new raw candidate CVs (PDF) to be formatted, plus a single batch text note (see Executive Summary rule below and Candidate Emails section) carrying both the Executive Summary for each candidate's Formatted CV and the client-email-only fields (Position, Company, Compensation, Note, Key Highlights). This is the active intake folder going forward.
- `Sample CV/` — raw, unedited candidate CVs (PDF) from the initial batch. Historical/test material only — not the intake folder for new candidates, and never shared directly with a client.
- `Formatted CVs/` — client-facing candidate CVs (`.docx`) rebuilt onto the HLS template, plus `HLS_CV_Template.docx`, the blank master to start any new candidate from.
- `HLS_Bridge_Advisory_Pitch_Deck.pptx`, `HLS_Bridge_Advisory_Service_Agreement.docx` — existing branded collateral at the top level. The Service Agreement is the working precedent for page setup (A4, ~1in margins, centered header logo) since it was already produced with the font substitution below. The pitch deck's PowerPoint theme is the generic Office default (not the brand palette) — don't treat it as a color/font source.

## Brand system

Read `Brand CI update/hlsbridge_brand-handbook_v3.pdf` (or the two-page quick reference in `qa_guideline/`) before creating or restyling any document. Key tokens, so they don't need re-deriving from the PDF each time:

**Colors**
- Deep Navy `#0D1B2A` — primary: monogram, headlines, body text on light backgrounds
- Warm Gold `#C8A45E` — accent only (bridge line, pylon, taglines, CTAs) — use sparingly
- Warm Ivory `#F4F2EE` — primary light background
- Slate Gray `#6B7280` — captions, dividers, secondary text
- White `#FFFFFF` / Charcoal `#2E3440` — supporting

**Typography** — brand spec is Cormorant Garamond (headlines/H1/H2/pull quotes/tagline) + Montserrat (body/UI/captions/tables). **Neither font is installed on this machine.** The established substitute — used in the Service Agreement and every Formatted CV — is **Georgia (headlines) + Calibri (body)**. Keep using that pairing for consistency unless the real fonts are installed.

**Logo files** (`Brand CI update/`) — pick by placement, not by preference:
- `HLSBridgeAdvisory_Logo-Full-Navy_transparent.png` — primary lockup with tagline, default on light backgrounds
- `HLSBridgeAdvisory_Logo-Full-Reversed_transparent.png` — ivory version, dark backgrounds only
- `HLSBridgeAdvisory_Logo-NoTagline-Navy_transparent.png` / `-Reversed` — small placements or tight space (e.g. document headers)
- `HLSBridgeAdvisory_Icon-Gold_transparent.png` — bare arc+pylon mark, transparent, for favicon/watermark use
- `logo-icon-badge-navy-1.png` — arc+pylon enclosed in a navy circle, on an **opaque Warm Ivory square canvas** (not transparent) — for app icons/avatars, not for inline placement on a white background (shows a faint square edge)
- Each PNG has a matching vector `.pdf` in the same folder

Never recreate the mark from scratch, recolor it outside this palette, or round the pylon's corners / arc's line caps.

## Formatted CVs

`Formatted CVs/` holds client-facing versions of candidate CVs. The format (see `HLS_CV_Template.docx`): centered header logo → candidate name/title with headshot photo top-right → Executive Summary → Core Skills → Professional Experience → Education → Certifications & Awards → centered footer (company name/address, then "Confidential · page"). No References section, no logo icon in the footer.

Rules that apply to every candidate CV, not just the ones already done:
- Strip all personal data: date of birth, home address, phone number, personal email, and status fields like nationality/religion/marital status/health/age.
- Executive Summary is authored by the user, not pulled from the original CV and never fabricated by the agent. For new candidates, the user drops a single batch text note in `New CVs/` (see Candidate Emails section for the full format) containing an `Executive Summary:` field per candidate. Match each entry to its candidate by name before filling the template. If a candidate has no entry in the batch note, leave the section blank rather than inferring one.
- Condense dense/long originals (bullet lists, internal-only data, embedded screenshots) to a clean, quantified 1–3 pages; don't just re-paste everything into the new styling.

`tools/extract_photo.py` and `tools/generate_cv.py` automate the mechanical parts of producing a new Formatted CV — see the Operating framework section and each script's `--help` for usage. They handle photo extraction and template-filling only; PII scrubbing, condensing, and executive-summary matching remain judgment calls made before building the candidate JSON fed to `generate_cv.py`.

## Candidate Emails

After a batch of Formatted CVs is done, candidates are shared with the client by email, bundled per client + open position (one email covers every candidate the client is being sent for that role — see `Position` on each candidate). The email is never auto-sent: a draft is created in Outlook for the user to attach the matching Formatted CV file(s) and send themselves.

The batch text note dropped in `New CVs/` (any filename) drives both the CV and the email, split by field: `Executive Summary` feeds the Formatted CV; `Position`, `Company`, `Compensation`, `Note`, and `Key Highlights` are email-only and never appear in the CV docx. Format — one `=== CLIENT: ... ===` header per client/position, candidate blocks separated by a blank line, no blank lines within a candidate's own fields:

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

=== END ===
```

`Executive Summary`, `Position`, and `Company` are required per candidate, plus at least one `Key Highlights` bullet; `Compensation`/`Note` are optional. `tools/build_email_drafts.py --note "New CVs/<file>"` parses the note and renders one HTML email body + a `manifest.json` (recipient, subject, candidate list) per client group into `.tmp/email_drafts/` — see `--help`. It does not touch a mailbox; the agent reads its output and creates the actual Outlook draft.

## Repo state note

- `.gitignore` is in place. `tools/` now exists with `extract_photo.py`, `generate_cv.py`, and `build_email_drafts.py`. `workflows/` and `.env` still don't exist — treat those parts of the WAT framework section as intended structure, not current contents. `.tmp/` is created on demand by `build_email_drafts.py`.
