import streamlit as st
from utils import (
    parse_cv,
    analyze_ats,
    generate_optimized_cv,
    generate_portfolio,
    generate_skills_roadmap,
    parse_pdf,
    parse_txt,
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CareerBoost AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'CareerBoost AI — Real AI-powered ATS optimization, CV generation & more.',
    }
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* hide default streamlit chrome */
  #MainMenu, footer { display:none !important; }

  /* ── gradient header ── */
  .cb-header { text-align:center; padding:1.6rem 0 .4rem; }
  .cb-header h1 {
      font-size:2.8rem; font-weight:800;
      background:linear-gradient(90deg,#e94560,#c23152,#764ba2);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent;
      margin:0; line-height:1.15;
  }
  .cb-header p { color:#7a7f8e; font-size:.95rem; margin-top:.35rem; }

  /* ── sidebar tweaks ── */
  .stSidebar { background:#13151f !important; }
  .stSidebar .stMarkdown h3 { color:#fff !important; }

  /* ── score ring ── */
  .score-ring {
      width:140px; height:140px; margin:0 auto;
      border-radius:50%; display:flex; align-items:center;
      justify-content:center; flex-direction:column;
      font-family:'Segoe UI',sans-serif;
  }
  .score-ring .num { font-size:2.2rem; font-weight:800; color:#fff; }
  .score-ring .lbl { font-size:.72rem; color:#aaa; text-transform:uppercase; letter-spacing:1px; }

  /* ── tag pills ── */
  .pill { display:inline-block; padding:4px 12px; border-radius:20px; font-size:.78rem; font-weight:600; margin:3px; }
  .pill-green { background:#1a3a2a; color:#4ade80; }
  .pill-red   { background:#3a1a1f; color:#f87171; }
  .pill-blue  { background:#1a2a3a; color:#60a5fa; }

  /* ── tip card ── */
  .tip-card {
      background:#161923; border-left:3px solid #e94560;
      border-radius:6px; padding:.85rem 1rem;
      margin:.45rem 0; font-size:.88rem; color:#c8cad0;
  }
  .tip-card strong { color:#fff; }

  /* ── strength card ── */
  .strength-card {
      background:#161923; border-left:3px solid #22c55e;
      border-radius:6px; padding:.85rem 1rem;
      margin:.45rem 0; font-size:.88rem; color:#c8cad0;
  }

  /* ── download strip ── */
  .dl-strip {
      background:#1a1d27; border:1px solid #2a2d38;
      border-radius:10px; padding:1rem 1.3rem;
      display:flex; align-items:center; gap:1rem; margin-top:1rem;
  }
  .dl-strip .dl-icon { font-size:1.6rem; }
  .dl-strip .dl-text { font-size:.82rem; color:#7a7f8e; }
  .dl-strip .dl-text strong { color:#e2e4e9; font-size:.9rem; }

  /* ── interview card ── */
  .q-card {
      background:#1a1d27; border:1px solid #2a2d38;
      border-radius:10px; padding:1.2rem 1.3rem; margin-bottom:1rem;
  }
  .q-card .q-cat {
      display:inline-block; padding:2px 10px; border-radius:12px;
      font-size:.72rem; font-weight:700; margin-bottom:.5rem; text-transform:uppercase;
  }
  .q-cat-technical  { background:#1a2a3a; color:#60a5fa; }
  .q-cat-behavioural{ background:#2a1a3a; color:#c084fc; }
  .q-cat-situational{ background:#1a3a2a; color:#4ade80; }
  .q-cat-cultural   { background:#3a2a1a; color:#fb923c; }
  .q-card .q-text   { color:#e2e4e9; font-weight:600; font-size:.95rem; margin-bottom:.5rem; }
  .q-card .q-why    { color:#7a7f8e; font-size:.8rem; font-style:italic; margin-bottom:.6rem; }
  .q-card .q-answer { color:#c8cad0; font-size:.88rem; line-height:1.6; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _fetch_job_from_url(url: str) -> str:
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return '\n'.join(text.split('\n')[:200])
    except Exception as e:
        raise Exception(f"Could not fetch URL: {e}")


def _score_color(score: int) -> str:
    if score >= 75: return "linear-gradient(135deg,#16a34a,#22c55e)"
    if score >= 50: return "linear-gradient(135deg,#ca8a04,#eab308)"
    return "linear-gradient(135deg,#dc2626,#ef4444)"


def _score_label(score: int) -> str:
    if score >= 85: return "🟢 Excellent"
    if score >= 70: return "🟡 Good"
    if score >= 50: return "🟠 Moderate"
    return "🔴 Needs Work"


def _llm_available() -> bool:
    """Check if Groq API key is configured."""
    import os
    try:
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return True
    except Exception:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return bool(os.environ.get("GROQ_API_KEY"))


# ─────────────────────────────────────────────
# WELCOME / LANDING STATE
# ─────────────────────────────────────────────

def _show_welcome():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;">
      <p style="color:#7a7f8e;font-size:.9rem;">Powered by Groq LLaMA 3 · 100% Free · No data stored</p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, title, icon, desc in [
        (c1, "ATS Scoring",       "📊", "Semantic AI analysis vs any job description. Not just keyword grep."),
        (c2, "CV Generation",     "📄", "LLM-written tailored summary + ATS-optimized PDF with your data."),
        (c3, "Cover Letter",      "✍️", "Personalized cover letter crafted from your CV + the job posting."),
        (c4, "Interview Prep",    "🎤", "Predicted interview questions + model answers for your exact role."),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:#1a1d27;border:1px solid #2a2d38;border-radius:12px;padding:1.6rem 1.2rem;height:100%;">
              <div style="font-size:2rem;margin-bottom:.5rem;">{icon}</div>
              <h4 style="color:#fff;margin-bottom:.4rem;">{title}</h4>
              <p style="color:#7a7f8e;font-size:.82rem;line-height:1.5;">{desc}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Show API key warning if not configured
    if not _llm_available():
        st.warning(
            "⚠️ **Groq API key not configured** — AI features will use basic fallback logic. "
            "Add `GROQ_API_KEY` to `.streamlit/secrets.toml` (cloud) or a `.env` file (local)."
        )
    else:
        st.success("✅ AI engine connected (Groq LLaMA 3)")

    st.info("👈  Upload your CV in the sidebar, add an optional job description, then hit **Analyze & Generate**.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    # ── Header ──
    st.markdown(
        '<div class="cb-header"><h1>🚀 CareerBoost AI</h1>'
        '<p>ATS optimization • AI-powered CV • Cover letter • Interview prep</p></div>',
        unsafe_allow_html=True
    )

    # ── Session State Init ──
    for key in ['cv_data', 'ats_results', 'cv_pdf', 'port_zip',
                'roadmap_md', 'cover_letter', 'interview_qa', 'job_search_strategy',
                'last_cv_name', 'last_job_hash', 'last_template']:
        if key not in st.session_state:
            st.session_state[key] = None

    # ─── SIDEBAR ───────────────────────────────
    with st.sidebar:
        st.markdown("### 📄 Your Documents")
        cv_file = st.file_uploader(
            "Upload CV / Resume",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="PDF, DOCX or TXT — your data is never stored"
        )
        
        cv_template = st.selectbox(
            "CV Format Template",
            ["Modern", "Harvard"],
            help="Choose between a modern colorful CV or a classic Harvard-style CV format."
        )
        
        linkedin_input = st.text_input("LinkedIn Profile URL (Optional)", placeholder="https://linkedin.com/in/...")
        github_input = st.text_input("GitHub Profile URL (Optional)", placeholder="https://github.com/...", help="Allows AI to auto-fetch your top repositories.")

        st.markdown("---")
        st.markdown("### 🎯 Job Description *(optional)*")

        job_mode = st.radio(
            "Input method", ["Paste text", "Upload PDF", "Paste URL"],
            label_visibility="collapsed"
        )

        job_text_input = ""
        job_file_input = None
        job_url_input  = ""

        if job_mode == "Paste text":
            job_text_input = st.text_area(
                "Job description", height=200,
                placeholder="Paste the full job description here…",
                label_visibility="collapsed"
            )
        elif job_mode == "Upload PDF":
            job_file_input = st.file_uploader(
                "Job desc PDF", type=['pdf', 'txt'], key="job_pdf",
                label_visibility="collapsed"
            )
        else:
            job_url_input = st.text_input(
                "Job posting URL", placeholder="https://…",
                label_visibility="collapsed"
            )

        st.markdown("---")
        go = st.button("🚀  Analyze & Generate", type="primary", use_container_width=True)

        # Clear button
        if st.session_state.cv_data:
            if st.button("🗑️  Clear & Start Over", use_container_width=True):
                for key in ['cv_data', 'ats_results', 'cv_pdf', 'port_zip',
                            'roadmap_md', 'cover_letter', 'interview_qa', 'job_search_strategy',
                            'last_cv_name', 'last_job_hash', 'last_template']:
                    st.session_state[key] = None
                st.rerun()

        st.markdown("---")
        st.markdown("""
        <div style="font-size:.75rem;color:#555;line-height:1.6;">
        <strong style="color:#888">Supported formats:</strong><br/>
        PDF, DOCX, DOC, TXT<br/><br/>
        <strong style="color:#888">Powered by:</strong><br/>
        Groq LLaMA 3.1 · ReportLab · PyMuPDF
        </div>
        """, unsafe_allow_html=True)

    # ─── WELCOME STATE ────────────────────────
    if not go and not st.session_state.cv_data:
        _show_welcome()
        return

    # ─── VALIDATION ───────────────────────────
    if go:
        if not cv_file:
            st.error("⚠️ Please upload your CV (PDF, DOCX or TXT).")
            return

        # ─── PROCESSING ───────────────────────
        # Detect if inputs changed (avoid re-running LLM unnecessarily)
        import hashlib
        cv_name = cv_file.name if cv_file else ""
        job_combined = job_text_input + job_url_input + (job_file_input.name if job_file_input else "")
        job_hash = hashlib.md5(job_combined.encode()).hexdigest()

        needs_reparse  = (cv_name != st.session_state.last_cv_name)
        needs_reanalyze = (job_hash != st.session_state.last_job_hash)

        with st.status("🔍 Processing your documents…", expanded=True) as status:

            # ── Parse CV ──
            if needs_reparse:
                st.write("📄 Parsing CV with AI…")
                try:
                    cv_data = parse_cv(cv_file)
                    
                    # Update fields based on manual input
                    if linkedin_input: cv_data['linkedin'] = linkedin_input.strip()
                    if github_input: 
                        cv_data['github'] = github_input.strip()
                        st.write("Fetching GitHub repositories...")
                        import utils
                        import importlib
                        importlib.reload(utils)
                        github_projects = utils.get_github_projects(github_input.strip())
                        if github_projects:
                            existing_projects = cv_data.get('projects', [])
                            # Append but try to avoid obvious precise duplicates if both match by name
                            existing_names = [p.get('name', '').lower() for p in existing_projects]
                            for gp in github_projects:
                                if gp['name'].lower() not in existing_names:
                                    existing_projects.append(gp)
                            cv_data['projects'] = existing_projects

                    st.session_state.cv_data = cv_data
                    st.session_state.last_cv_name = cv_name
                    # Clear downstream cached results when CV changes
                    for k in ['cv_pdf', 'port_zip', 'cover_letter', 'interview_qa', 'ats_results', 'roadmap_md', 'job_search_strategy']:
                        st.session_state[k] = None
                except Exception as e:
                    st.error(f"CV parse failed: {e}")
                    return
            else:
                cv_data = st.session_state.cv_data
                st.write("✅ CV already parsed (using cached result)")

            # ── Job description ──
            job_text = None
            if job_text_input.strip():
                job_text = job_text_input.strip()
            elif job_file_input:
                st.write("📑 Parsing job description PDF…")
                try:
                    if job_file_input.name.endswith('.pdf'):
                        job_text = parse_pdf(job_file_input)
                    else:
                        job_text = parse_txt(job_file_input)
                except Exception as e:
                    st.error(f"Job PDF parse failed: {e}")
                    return
            elif job_url_input.strip():
                st.write("🌐 Fetching job posting from URL…")
                try:
                    job_text = _fetch_job_from_url(job_url_input.strip())
                except Exception as e:
                    st.error(str(e))
                    return

            # ── ATS Analysis ──
            if needs_reanalyze or st.session_state.ats_results is None:
                st.write("🤖 Running AI ATS analysis…")
                eval_text = job_text if job_text else "General Resume Quality Evaluation: Assess clarity, presentation, metrics, and professional phrasing."
                try:
                    ats_results = analyze_ats(cv_data, eval_text)
                    st.session_state.ats_results = ats_results
                    st.session_state.last_job_hash = job_hash
                    # Clear roadmap/cover-letter/interview if job changes
                    for k in ['roadmap_md', 'cover_letter', 'interview_qa', 'job_search_strategy']:
                        st.session_state[k] = None
                except Exception as e:
                    st.warning(f"ATS analysis failed: {e}")

            # Re-render CV PDF if template changed
            if st.session_state.last_template != cv_template:
                st.session_state.cv_pdf = None
                st.session_state.last_template = cv_template

            status.update(label="✅ Done!", state="complete", expanded=False)

    # Use cached data for display
    cv_data = st.session_state.cv_data
    ats_results = st.session_state.ats_results

    if not cv_data:
        _show_welcome()
        return

    # Rebuild job_text for tabs that need it (cover letter, interview)
    job_text = None
    if job_text_input.strip():
        job_text = job_text_input.strip()
    elif 'last_job_hash' in st.session_state:
        pass  # job_text will be None — cover letter/interview prep will skip

    # ─── BUILD TABS ───────────────────────────
    tab_labels = ["📄 Optimized CV", "🌐 Portfolio", "✍️ Cover Letter", "🎤 Interview Prep", "📋 Parsed Data"]
    if ats_results:
        tab_labels = ["📊 ATS Analysis"] + tab_labels + ["📚 Roadmap", "💼 Job Search"]
        t_ats, t_cv, t_port, t_cover, t_interview, t_data, t_road, t_projects = st.tabs(tab_labels)
    else:
        t_cv, t_port, t_cover, t_interview, t_data = st.tabs(tab_labels)
        t_ats = t_road = t_projects = None

    # ═══════════════════════════════════════════
    # TAB — ATS ANALYSIS
    # ═══════════════════════════════════════════
    if t_ats and ats_results:
        with t_ats:
            score         = ats_results.get('score', 0)
            matched       = ats_results.get('matched_skills', [])
            missing       = ats_results.get('missing_skills', [])
            semantic_gaps = ats_results.get('semantic_gaps', [])
            strengths     = ats_results.get('strengths', [])
            tips          = ats_results.get('tips', [])
            exp_match     = ats_results.get('experience_match', score)
            kw_density    = ats_results.get('keyword_density', 'medium')

            # Score row
            c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
            with c1:
                st.markdown(f"""
                <div class="score-ring" style="background:{_score_color(score)};">
                  <div class="num">{score}%</div>
                  <div class="lbl">ATS Score</div>
                </div>
                <div style="text-align:center;margin-top:.5rem;font-size:.85rem;color:#aaa">{_score_label(score)}</div>""",
                unsafe_allow_html=True)
            with c2:
                st.metric("✅ Matched Skills", len(matched))
            with c3:
                st.metric("❌ Missing Skills", len(missing))
            with c4:
                st.metric("🎯 Exp. Match", f"{exp_match}%")

            st.markdown("---")

            col_l, col_r = st.columns(2)

            with col_l:
                # Matched
                if matched:
                    st.markdown("**✅ Matched Keywords**")
                    st.markdown(" ".join(
                        f'<span class="pill pill-green">{s.title()}</span>' for s in matched
                    ), unsafe_allow_html=True)
                    st.markdown("")

                # Missing
                if missing:
                    st.markdown("**❌ Missing Keywords**")
                    st.markdown(" ".join(
                        f'<span class="pill pill-red">{s.title()}</span>' for s in missing
                    ), unsafe_allow_html=True)
                    st.markdown("")

                # Semantic gaps
                if semantic_gaps:
                    st.markdown("**🔍 Strategic Gaps**")
                    for g in semantic_gaps:
                        st.markdown(f'<span class="pill pill-blue">{g}</span>', unsafe_allow_html=True)
                    st.markdown("")

            with col_r:
                # Strengths
                if strengths:
                    st.markdown("**💪 Your Strengths**")
                    for s in strengths:
                        st.markdown(f'<div class="strength-card">{s}</div>', unsafe_allow_html=True)
                    st.markdown("")

                # Keyword density
                st.markdown(f"**📈 Keyword Density:** `{kw_density}`")
                st.caption("High density = better ATS readability")

            st.markdown("---")
            st.markdown("### 💡 Improvement Tips")
            for i, tip in enumerate(tips, 1):
                st.markdown(f'<div class="tip-card"><strong>{i}.</strong> {tip}</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════
    # TAB — OPTIMIZED CV
    # ═══════════════════════════════════════════
    with t_cv:
        if st.session_state.cv_pdf is None:
            with st.spinner("✍️ Generating AI-optimized CV…"):
                try:
                    template_choice = st.session_state.get('last_template', 'Modern')
                    st.session_state.cv_pdf = generate_optimized_cv(cv_data, job_text, template=template_choice)
                except Exception as e:
                    st.error(f"CV generation failed: {e}")

        if st.session_state.cv_pdf:
            st.markdown("""
            <div class="dl-strip">
              <div class="dl-icon">📄</div>
              <div class="dl-text">
                <strong>ATS-Optimized CV Ready</strong><br/>
                AI-written summary tailored to your skills. Professional layout, keyword-rich.
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("")
            st.download_button(
                "⬇️  Download CV (PDF)",
                data=st.session_state.cv_pdf,
                file_name=f"{cv_data.get('name','CV').replace(' ','_')}_optimized.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.markdown("---")
            st.markdown("""
            **What's in your generated CV:**
            - 🤖 AI-written professional summary (tailored to job if provided)
            - 🎯 Skills section — matched keywords prioritized first
            - 💼 Experience with company names, dates & descriptions
            - 🚀 Projects section (if found in your CV)
            - 🎓 Education & Certifications
            """)

    # ═══════════════════════════════════════════
    # TAB — PORTFOLIO
    # ═══════════════════════════════════════════
    with t_port:
        if st.session_state.port_zip is None:
            with st.spinner("🌐 Building your portfolio website…"):
                try:
                    st.session_state.port_zip = generate_portfolio(cv_data)
                except Exception as e:
                    st.error(f"Portfolio generation failed: {e}")

        if st.session_state.port_zip:
            st.markdown("""
            <div class="dl-strip">
              <div class="dl-icon">🌐</div>
              <div class="dl-text">
                <strong>Portfolio Website Ready</strong><br/>
                Single-file HTML with hero, skills grid, timeline, projects & contact.
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("")
            st.download_button(
                "⬇️  Download Portfolio (ZIP)",
                data=st.session_state.port_zip,
                file_name="portfolio.zip",
                mime="application/zip",
                use_container_width=True,
            )
            st.markdown("---")
            st.markdown("""
            **Sections included:** Hero · About · Skills Grid · Experience Timeline · Projects · Education · Contact

            **Deploy free in 2 minutes:**
            1. **GitHub Pages** — push `index.html`, enable Pages → live URL
            2. **Netlify** — drag & drop the folder on netlify.app
            3. **Vercel** — connect GitHub repo in one click
            """)

    # ═══════════════════════════════════════════
    # TAB — COVER LETTER
    # ═══════════════════════════════════════════
    with t_cover:
        if not job_text:
            st.info("📋 **Add a job description** in the sidebar to generate a tailored cover letter.")
        else:
            if st.session_state.cover_letter is None:
                with st.spinner("✍️ Writing your cover letter with AI…"):
                    try:
                        from llm_utils import generate_cover_letter_llm
                        st.session_state.cover_letter = generate_cover_letter_llm(cv_data, job_text)
                    except Exception as e:
                        st.session_state.cover_letter = f"[Cover letter generation failed: {e}]"

            if st.session_state.cover_letter:
                name = cv_data.get('name', 'Applicant')
                email = cv_data.get('email', '')
                today = __import__('datetime').date.today().strftime("%B %d, %Y")

                full_letter = f"""Dear Hiring Manager,

{st.session_state.cover_letter}

Best regards,
{name}
{email}
{today}"""

                st.markdown("### ✍️ Your Cover Letter")
                st.text_area(
                    "Cover Letter (editable)",
                    value=full_letter,
                    height=400,
                    label_visibility="collapsed"
                )
                st.download_button(
                    "⬇️  Download Cover Letter (.txt)",
                    data=full_letter,
                    file_name="cover_letter.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
                if st.button("🔄 Regenerate Cover Letter"):
                    st.session_state.cover_letter = None
                    st.rerun()

    # ═══════════════════════════════════════════
    # TAB — INTERVIEW PREP
    # ═══════════════════════════════════════════
    with t_interview:
        if not job_text:
            st.info("📋 **Add a job description** in the sidebar to generate tailored interview questions.")
        else:
            if st.session_state.interview_qa is None:
                with st.spinner("🎤 Generating interview questions with AI…"):
                    try:
                        from llm_utils import generate_interview_prep_llm
                        st.session_state.interview_qa = generate_interview_prep_llm(cv_data, job_text)
                    except Exception as e:
                        st.session_state.interview_qa = []
                        st.error(f"Interview prep failed: {e}")

            qa_list = st.session_state.interview_qa or []
            if qa_list:
                st.markdown("### 🎤 Likely Interview Questions")
                st.caption("Based on your CV + the job description. Use these to prepare!")
                for i, qa in enumerate(qa_list, 1):
                    cat = qa.get('category', 'General').lower()
                    cat_class = f"q-cat-{cat}"
                    with st.expander(f"Q{i}: {qa.get('question', 'Question')}", expanded=(i == 1)):
                        st.markdown(f"""
                        <div class="q-card">
                          <div class="q-cat {cat_class}">{qa.get('category','General')}</div>
                          <div class="q-text">{qa.get('question','')}</div>
                          <div class="q-why">💡 {qa.get('why_asked','')}</div>
                          <div class="q-answer"><strong>Model Answer:</strong><br/>{qa.get('model_answer','')}</div>
                        </div>""", unsafe_allow_html=True)

                if st.button("🔄 Regenerate Questions"):
                    st.session_state.interview_qa = None
                    st.rerun()

    # ═══════════════════════════════════════════
    # TAB — ROADMAP
    # ═══════════════════════════════════════════
    if t_road and ats_results:
        with t_road:
            missing = ats_results.get('missing_skills', [])
            if missing:
                if st.session_state.roadmap_md is None:
                    with st.spinner("📚 Building AI-powered learning roadmap…"):
                        try:
                            target_role = cv_data.get('current_title', '')
                            st.session_state.roadmap_md = generate_skills_roadmap(missing, target_role)
                        except Exception as e:
                            st.session_state.roadmap_md = f"**Roadmap generation failed:** {e}"

                if st.session_state.roadmap_md:
                    st.markdown(st.session_state.roadmap_md)
                    st.markdown("---")
                    st.download_button(
                        "⬇️  Download Roadmap (Markdown)",
                        data=st.session_state.roadmap_md,
                        file_name="skills_roadmap.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
            else:
                st.success("🎉 Your skills are a strong match for this role — no major gaps detected!")

    # ═══════════════════════════════════════════
    # TAB — PARSED DATA
    # ═══════════════════════════════════════════
    with t_data:
        st.markdown("#### 👤 Profile")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Name:** {cv_data.get('name','—')}")
            st.write(f"**Email:** {cv_data.get('email','—')}")
            st.write(f"**Phone:** {cv_data.get('phone','—')}")
        with c2:
            st.write(f"**Title:** {cv_data.get('current_title','—')}")
            st.write(f"**Location:** {cv_data.get('location','—')}")
            st.write(f"**Experience:** {cv_data.get('years_experience', '—')} yrs")
        with c3:
            st.metric("Skills", len(cv_data.get('skills', [])))
            st.metric("Experience entries", len(cv_data.get('experience', [])))
            st.metric("Education entries", len(cv_data.get('education', [])))

        if cv_data.get('linkedin') or cv_data.get('github'):
            st.markdown("")
            if cv_data.get('linkedin'):
                st.write(f"🔗 **LinkedIn:** {cv_data['linkedin']}")
            if cv_data.get('github'):
                st.write(f"💻 **GitHub:** {cv_data['github']}")

        st.markdown("---")

        if cv_data.get('skills'):
            st.markdown("#### 💼 Detected Skills")
            cols = st.columns(5)
            for i, s in enumerate(cv_data['skills']):
                cols[i % 5].markdown(f"✓ {s}")

        st.markdown("---")

        if cv_data.get('experience'):
            st.markdown("#### 🏢 Experience")
            for exp in cv_data['experience']:
                title = exp.get('title', 'Entry')
                if exp.get('company'):
                    title = f"{title} @ {exp['company']}"
                with st.expander(title, expanded=False):
                    if exp.get('duration'):
                        st.caption(exp['duration'])
                    st.write(exp.get('description', 'No detail available.'))

        if cv_data.get('projects'):
            st.markdown("---")
            st.markdown("#### 🚀 Projects")
            for p in cv_data['projects']:
                with st.expander(p.get('name', 'Project'), expanded=False):
                    st.write(p.get('description', ''))

        if cv_data.get('certifications'):
            st.markdown("---")
            st.markdown("#### 🏆 Certifications")
            for cert in cv_data['certifications']:
                st.write(f"• {cert}")

        if cv_data.get('education'):
            st.markdown("---")
            st.markdown("#### 🎓 Education")
            for e in cv_data['education']:
                if isinstance(e, dict):
                    st.write(f"• **{e.get('degree','')}** — {e.get('institution','')} ({e.get('year','')})")
                else:
                    st.write(f"• {e}")

    # ═══════════════════════════════════════════
    # TAB — JOB SEARCH STRATEGY
    # ═══════════════════════════════════════════
    if t_projects:
        with t_projects:
            if not job_text:
                st.info("📋 **Add a target job description** in the sidebar to generate a custom job search strategy.")
            else:
                missing = ats_results.get('missing_skills', []) if ats_results else []
                if st.session_state.job_search_strategy is None:
                    with st.spinner("💼 Generating a targeted job search strategy…"):
                        import importlib
                        import llm_utils
                        importlib.reload(llm_utils)
                        try:
                            from llm_utils import generate_job_search_strategy_llm
                            st.session_state.job_search_strategy = generate_job_search_strategy_llm(cv_data, job_text, missing)
                        except Exception as e:
                            st.error(f"Strategy generation failed: {e}")
                            st.session_state.job_search_strategy = None
                
                if st.session_state.job_search_strategy:
                    st.markdown("""
                    <div style="background:rgba(99, 102, 241, 0.1); border-left:4px solid #6366f1; padding:1.2rem; border-radius:4px; margin-bottom:1.5rem;">
                        <strong>🚀 Turbocharge your Job Hunt!</strong><br/>
                        Based on your profile and this JD, here are the target roles, search queries, and networking templates you should use.
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(st.session_state.job_search_strategy)
                    if st.button("🔄 Regenerate Strategy"):
                        st.session_state.job_search_strategy = None
                        st.rerun()


if __name__ == "__main__":
    main()
    
