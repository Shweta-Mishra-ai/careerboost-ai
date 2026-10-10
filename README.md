# CareerBoost AI: archived

**This project has been merged into [CareerForge AI](https://github.com/Shweta-Mishra-ai/CareerForge_AI).**
Please use and contribute to that repository. This one is kept only so old links and the history still work, and
will receive no further changes.

## Where the features went

| CareerBoost feature | In CareerForge AI |
|---|---|
| GitHub profile → portfolio | **Start → GitHub**, then **CV & portfolio → Portfolio website** (3 themes, one `index.html`, deploy guide) |
| ATS score and gap analysis | **ATS check** (published weights, evidence-aware, optional PDF parse check, compare up to 5 postings) |
| CV builder | **CV & portfolio** (4 templates → PDF, Word, text, HTML; blocked until the CV is ready to submit) |
| Job search | **Jobs & tracker** (ranked by how well your CV matches) |
| HR outreach emails | **Letters & interviews → Outreach emails** (no guessed email addresses) |
| Interview prep, cover letter | **Letters & interviews** (every claim is checked against your CV) |
| Learning roadmap | **Insights → Learning roadmap** |
| Application tracker | **Jobs & tracker → Application tracker** (follow-ups at day 7, 14, 21) |

## What changed on purpose

* It no longer invents experience or "likely backgrounds". AI output is verified against your own text.
* PyMuPDF (AGPL) was replaced by permissively licensed libraries.
* `google-generativeai` (end of life) was replaced by the current SDK; free model names are discovered at runtime.
* API keys are never put in error messages or logs.

The audit that led to the merge, and every finding with its resolution, is in
[docs/MERGE_PLAN.md](https://github.com/Shweta-Mishra-ai/CareerForge_AI/blob/main/docs/MERGE_PLAN.md).
