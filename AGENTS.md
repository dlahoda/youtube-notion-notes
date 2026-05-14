## Project goal

Build a small Python CLI tool that turns a YouTube URL into a local transcript and a markdown note.

Later milestones may export to Notion and be wrapped by n8n, but do not implement those unless explicitly requested.

## Current milestone

Implement Milestone 1 only:

- parse a YouTube URL;
- fetch a transcript;
- save raw transcript locally;
- create a ready-to-paste GPT prompt;
- optionally generate a markdown note if OpenAI API config is present.

## Engineering rules

- Keep changes small and reviewable.
- Prefer boring, simple Python.
- Do not add a web UI.
- Do not implement Notion yet.
- Do not implement n8n yet.
- Do not add unnecessary dependencies.
- Keep secrets out of git.
- Use `.env.example` for required environment variables.
- Add README instructions for setup and usage.

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