<div align="center">

<img src="https://img.shields.io/badge/CareerBoost_AI-🚀-7c6af7?style=for-the-badge&labelColor=0a0a0f" alt="CareerBoost AI"/>

# CareerBoost AI

### From GitHub profile to employed — in one session.

**ATS Score · CV Builder · Portfolio Generator · Job Search · HR Outreach · Interview Prep**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit-ff4b4b?style=flat-square&logo=streamlit)](https://careerboost-ai-deyohkhprupf4kfsfe8ypx.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-Shweta--Mishra--ai-181717?style=flat-square&logo=github)](https://github.com/Shweta-Mishra-ai/careerboost-ai)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/AI-Groq_LLaMA_3-f55036?style=flat-square)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-22d3a0?style=flat-square)](LICENSE)

<img width="100%" src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png"/>

</div>

---

## 🎯 What Is CareerBoost AI?

CareerBoost AI is an **open-source developer career OS** — not just a resume builder. It turns your GitHub profile and CV into a complete job-seeking toolkit using free AI (Groq LLaMA 3).

**Two ways to use it:**
- **Mode 1 — Upload CV:** Parse existing PDF/DOCX + optionally enrich with GitHub/LinkedIn
- **Mode 2 — URLs only:** Just paste your GitHub URL — CV + Portfolio built automatically

---

## ✨ Features

| Feature | What It Does |
|---------|-------------|
| **📊 ATS Analyzer** | Compares your CV vs any job description. Score, matched keywords, gaps, improvement tips |
| **📄 CV Builder** | AI-generated ATS-optimized PDF. Two templates: Modern + Harvard |
| **🌐 Portfolio Generator** | Stunning single-page HTML portfolio — dark glassmorphism, animated, deploy-ready |
| **✍️ Cover Letter** | Job-tailored cover letter generated in seconds |
| **🎤 Interview Prep** | 10 role-specific questions with model answers + why they're asked |
| **🔍 Job Search** | Live jobs from Remotive + Jobicy matched to your CV skills |
| **📧 HR Finder** | Find recruiters at any company + 4 email templates (cold → follow-up → thank you) |
| **📚 Skills Roadmap** | Personalized learning plan to close skill gaps found by ATS |

---

## 🏗️ Architecture

```
careerboost-ai/
│
├── streamlit_app.py          # Main app — UI, routing, session state, all tabs
│   ├── show_welcome()        # Landing page with feature cards
│   ├── main()                # Sidebar inputs, processing flow, tab rendering
│   ├── search_jobs_remotive()# Remotive API integration
│   ├── search_jobs_jobicy()  # Jobicy API integration
│   └── match_score()         # CV-to-job skill matching algorithm
│
├── utils.py                  # Core logic — no UI code here
│   ├── parse_cv()            # PDF/DOCX/TXT → structured cv_data dict
│   ├── parse_pdf()           # Raw PDF text extraction (PyMuPDF)
│   ├── parse_txt()           # Plain text CV parsing
│   ├── analyze_ats()         # Keyword + semantic ATS scoring
│   ├── generate_optimized_cv()  # ReportLab PDF generation (4 templates)
│   ├── generate_portfolio()  # Self-contained HTML portfolio generation
│   ├── generate_skills_roadmap() # Markdown learning roadmap
│   ├── get_github_data()     # GitHub API — repos, languages, bio, stars
│   ├── get_linkedin_data()   # LinkedIn (stub — platform blocks scraping)
│   ├── enrich_cv_with_external_data() # Merge GitHub/LinkedIn into cv_data
│   ├── find_hr_contacts()    # Email pattern generation + LinkedIn search URLs
│   ├── generate_hr_email_templates() # 4 email templates (cold/follow-up/thank you)
│   ├── _extract_experience() # Regex experience parser (fallback when no LLM)
│   ├── _extract_education()  # Education section parser
│   └── SKILL_KEYWORDS        # 100+ technology keywords for skill detection
│
├── llm_utils.py              # All Groq LLM calls — isolated here
│   ├── _get_groq_key()       # Key resolution (secrets → env → None)
│   ├── _groq_call()          # Base Groq call (fast model / smart model)
│   ├── _parse_json()         # LLM JSON parser with truncation repair
│   ├── extract_cv_data_llm() # CV text → structured JSON (smart model)
│   ├── analyze_ats_llm()     # ATS analysis via LLM (smart model)
│   ├── generate_summary_llm()# Professional summary writer (fast model)
│   ├── generate_cover_letter_llm() # Tailored cover letter (fast model)
│   ├── generate_interview_prep_llm() # 10 interview Q&As (smart model)
│   ├── generate_roadmap_llm()# Skill gap learning plan (fast model)
│   ├── enrich_from_github_llm() # GitHub → experience + title inference (smart model)
│   └── generate_hr_emails_llm()  # 4 email templates via AI (smart model)
│
├── requirements.txt          # All Python dependencies
├── .env.example              # Environment variable template
├── .streamlit/
│   └── secrets.toml.example  # Streamlit Cloud secrets template
└── test_st.py                # Basic smoke test
```

### Data Flow

```
User Input (CV / GitHub URL / LinkedIn URL)
          │
          ▼
    streamlit_app.py
    ├── parse_cv() ──────────────────────────► cv_data dict
    ├── get_github_data() ────────────────────► gh_data dict  ──► merge ──► cv_data
    ├── get_linkedin_data() ──────────────────► li_data dict  ──► merge ──► cv_data
    │
    ▼
  cv_data (structured dict)
    ├── analyze_ats(cv_data, job_description) ──► ATS tab
    ├── generate_optimized_cv(cv_data) ──────────► CV tab (PDF)
    ├── generate_portfolio(cv_data) ─────────────► Portfolio tab (ZIP)
    ├── generate_cover_letter_llm(cv_data, jd) ──► Cover Letter tab
    ├── generate_interview_prep_llm(cv_data, jd) ► Interview tab
    ├── search_jobs_remotive/jobicy() ───────────► Jobs tab
    └── find_hr_contacts() + emails ─────────────► HR Finder tab
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Free Groq API key → [console.groq.com](https://console.groq.com) (takes 60 seconds)

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/Shweta-Mishra-ai/careerboost-ai.git
cd careerboost-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your Groq API key
mkdir -p .streamlit
echo 'GROQ_API_KEY = "gsk_your_key_here"' > .streamlit/secrets.toml

# 4. Run
streamlit run streamlit_app.py
```

App opens at `http://localhost:8501`

### Environment Variables

```bash
# .streamlit/secrets.toml (Streamlit Cloud)
GROQ_API_KEY = "gsk_..."

# OR .env (local development)
GROQ_API_KEY=gsk_...
```

### Streamlit Cloud Deployment

```
1. Fork this repo
2. Go to share.streamlit.io → New app → select this repo
3. Add GROQ_API_KEY in App Settings → Secrets
4. Deploy
```

---

## 🤖 AI Models Used

| Task | Model | Why |
|------|-------|-----|
| CV data extraction | `llama-3.3-70b-versatile` | Needs structured JSON — 70b more reliable |
| ATS analysis | `llama-3.3-70b-versatile` | Complex scoring logic requires larger model |
| HR emails | `llama-3.3-70b-versatile` | Structured JSON output needed |
| GitHub enrichment | `llama-3.3-70b-versatile` | Inference from sparse data |
| Cover letter | `llama-3.1-8b-instant` | Freetext — fast model sufficient |
| Summary | `llama-3.1-8b-instant` | Freetext — fast model sufficient |
| Interview prep | `llama-3.1-8b-instant` | Freetext — fast model sufficient |
| Roadmap | `llama-3.1-8b-instant` | Markdown output — fast model fine |

All models via **Groq** — free tier, no credit card required.

---

## 📦 Dependencies

```
streamlit>=1.31.0      # UI framework
PyMuPDF>=1.23.8        # PDF parsing
python-docx>=1.0.0     # DOCX parsing
requests>=2.31.0       # HTTP requests (GitHub API, job search)
httpx>=0.27.0          # Async HTTP (job search)
beautifulsoup4>=4.12.0 # HTML parsing
reportlab>=4.0.9       # PDF generation
lxml>=5.0.0            # XML/HTML processing
groq>=0.9.0            # Groq AI SDK
python-dotenv>=1.0.0   # Environment variable loading
```

---

## 🔑 Key Design Decisions

**Why Groq (not OpenAI)?**
Free tier is extremely generous (thousands of requests/day), fast (400+ tokens/sec), and no credit card required. Perfect for an open-source tool.

**Why two LLM models?**
`llama-3.3-70b-versatile` produces reliable JSON. `llama-3.1-8b-instant` is 3x faster for text output. Using the right model for each task improves quality and speed.

**Why Streamlit?**
Fastest path from Python logic to working UI. The entire frontend is ~400 lines of Python. Tradeoff: not suitable for production SaaS (no real auth, mobile UX limited).

**Why single HTML portfolio?**
Zero dependencies, deploys anywhere (Netlify drag-drop, GitHub Pages, Vercel), works offline. Users can host it for free in 30 seconds.

**Why not scrape LinkedIn?**
LinkedIn has blocked all automated scraping since 2022 (returns HTTP 999 or login redirect with no data). We display an honest message instead of silently returning empty data. For production LinkedIn integration, use their OAuth API or Apify.

---

## 🐛 Known Limitations

| Limitation | Reason | Workaround |
|-----------|--------|------------|
| LinkedIn import doesn't work | Platform blocks scraping | Paste your About section manually |
| Job search is remote/global only | Using Remotive + Jobicy APIs (free) | India-specific jobs coming (Naukri integration) |
| Mobile sidebar hidden | Streamlit limitation on small screens | Tap ☰ hamburger icon (top left) |
| PDF generation slow sometimes | Groq API latency | ~5-10s is normal; free tier has no SLA |
| CV parsing quality varies | Depends on CV formatting | Use standard single-column PDF for best results |

---

## 🗺️ Roadmap

- [ ] Naukri.com job search integration (India-specific)
- [ ] LinkedIn OAuth import (official API)
- [ ] Application tracker (kanban board)
- [ ] Multiple portfolio themes
- [ ] Chrome extension for one-click ATS analysis
- [ ] Resume scoring history

**Rebuilding as full SaaS:** [Caria](https://github.com/Shweta-Mishra-ai) — Next.js + FastAPI + Supabase (coming soon)

---

## 🤝 Contributing

```bash
# Fork → clone → create branch
git checkout -b feature/your-feature

# Make changes
# Test locally: streamlit run streamlit_app.py

# Commit with conventional commit message
git commit -m "feat: add Naukri job search integration"

# Push + open PR
git push origin feature/your-feature
```

**Commit message format:**
- `feat:` — new feature
- `fix:` — bug fix
- `chore:` — dependencies, config
- `docs:` — README, comments
- `refactor:` — code restructure, no behavior change

---

## 👩‍💻 Built By

**Shweta Mishra** — Python Developer & AI/ML Engineer

[![GitHub](https://img.shields.io/badge/GitHub-Shweta--Mishra--ai-181717?style=flat-square&logo=github)](https://github.com/Shweta-Mishra-ai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-shweta--mishra--ai-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/shweta-mishra-ai)

---

## 📄 License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

<div align="center">

**If this helped you land a job, give it a ⭐**

Made with ❤️ in India · Powered by Groq LLaMA 3

</div>
