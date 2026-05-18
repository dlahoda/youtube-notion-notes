## Project goal

Build a small Python CLI tool that turns a YouTube URL into a local transcript and a markdown note.

Later milestones may export to Notion and be wrapped by n8n, but do not implement those unless explicitly requested.

## Current working mode

Use `./design-doc.md` as the source of truth for the current milestone, slice boundaries, constraints, and durable decisions.

## Engineering rules

- Keep changes small and reviewable.
- Prefer boring, simple Python.
- Do not add a web UI.
- Do not add new Notion or n8n behavior unless the current task explicitly asks for it.
- Keep Notion export logic inside Python.
- Keep n8n as orchestration only.
- Do not add unnecessary dependencies.
- Keep secrets out of git.
- Use `.env.example` for required environment variables.
- Add README instructions for setup and usage.

## Design document maintenance

- Treat explicit user-request constraints as active task boundaries, even when they are not repeated in `./design-doc.md`.
- In `./design-doc.md`, milestone-level `Out of scope` and non-goals sections apply to every slice within that milestone.
- Do not copy the same `Out of scope` block into each slice when it is already defined at the milestone level.
- Use slice-level `Out of scope` only for constraints, exceptions, or clarifications specific to that slice.
- When a later slice changes milestone state, update stale milestone-level or earlier-slice wording where practical, especially `yet` and `not yet` statements.
- Keep each slice focused on status, scope, decisions, and slice-specific notes.

## Verification

After changes, explain:

- what files were created or changed;
- how to install dependencies;
- how to run the CLI;
- how to test it manually with one YouTube URL;
- what limitations remain.

## Communication and file references

When describing files, always include the project-relative path from the repository root.

Good examples:
- `./review`
- `./README.md`
- `./services/transcript.py`
- `./prompts/comprehensive_note.md`

Avoid vague references like:
- "the review file"
- "the script"
- "the prompt file"

When showing file contents, put the project-relative path directly above the code block.
