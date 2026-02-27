"""
CareerBoost AI — streamlit_app.py (TOP 1% VERSION)
New features:
  - LinkedIn + GitHub enrichment before CV/Portfolio generation
  - HR Finder — find recruiters at any company
  - Email templates: cold, follow-up x2, thank you
  - Job search with AI match scoring
  - Proper CV + Portfolio from enriched data
"""

import streamlit as st
import hashlib
import datetime

st.set_page_config(
    page_title="CareerBoost AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;}
#MainMenu,footer,header{display:none!important;}
.block-container{padding-top:1.5rem!important;}
:root{
  --bg:#0a0a0f; --surface:#111118; --card:#16161f;
  --border:rgba(255,255,255,0.07); --accent:#7c6af7; --accent2:#f74f6a;
  --green:#22d3a0; --text:#f0f0f5; --muted:#6b6b80;
  --fh:'Syne',sans-serif; --fb:'DM Sans',sans-serif;
}
html,body,.stApp{background:var(--bg)!important;color:var(--text)!important;font-family:var(--fb)!important;}

/* Header */
.cb-logo{text-align:center;padding:2rem 0 .8rem;}
.cb-logo h1{font-family:var(--fh);font-size:2.8rem;font-weight:800;letter-spacing:-2px;
  background:linear-gradient(135deg,#fff 30%,var(--accent) 70%,var(--accent2) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  line-height:1;margin-bottom:.4rem;}
.cb-logo p{color:var(--muted);font-size:.88rem;}

/* Sidebar */
section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label{color:#9090a8!important;font-size:.82rem!important;}
section[data-testid="stSidebar"] h3{color:#fff!important;font-family:var(--fh)!important;font-size:.9rem!important;}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:var(--surface)!important;border-radius:10px!important;padding:4px!important;border:1px solid var(--border)!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;border-radius:8px!important;font-family:var(--fb)!important;font-size:.8rem!important;font-weight:500!important;padding:5px 12px!important;transition:all .2s!important;}
.stTabs [aria-selected="true"]{background:var(--card)!important;color:#fff!important;border:1px solid var(--border)!important;}

/* Buttons */
.stButton>button{background:linear-gradient(135deg,var(--accent),#9d55f7)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:var(--fh)!important;font-weight:600!important;font-size:.87rem!important;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(124,106,247,.3)!important;}
.stDownloadButton>button{background:var(--card)!important;border:1px solid var(--accent)!important;color:var(--accent)!important;font-family:var(--fh)!important;font-weight:600!important;border-radius:8px!important;}
.stDownloadButton>button:hover{background:rgba(124,106,247,.1)!important;transform:translateY(-1px)!important;}

/* Inputs */
.stTextInput input,.stTextArea textarea{background:var(--card)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:8px!important;font-family:var(--fb)!important;font-size:.87rem!important;}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(124,106,247,.15)!important;}
[data-testid="stFileUploader"]{background:var(--card)!important;border:1px dashed rgba(124,106,247,.3)!important;border-radius:10px!important;}
[data-testid="stMetric"]{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:10px!important;padding:1rem!important;}
[data-testid="stMetricValue"]{color:#fff!important;font-family:var(--fh)!important;}
.streamlit-expanderHeader{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text)!important;}
.streamlit-expanderContent{background:var(--surface)!important;border:1px solid var(--border)!important;border-top:none!important;}
.stAlert{background:var(--card)!important;border-radius:8px!important;}

/* Custom cards */
.stat-box{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.3rem 1.1rem;text-align:center;transition:all .25s;}
.stat-box:hover{border-color:rgba(124,106,247,.3);transform:translateY(-2px);}
.stat-box .num{font-family:var(--fh);font-size:1.9rem;font-weight:800;color:#fff;}
.stat-box .lbl{font-size:.72rem;color:var(--muted);margin-top:3px;text-transform:uppercase;letter-spacing:.8px;}

.score-ring{width:128px;height:128px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;margin:0 auto;}
.score-ring .num{font-family:var(--fh);font-size:1.9rem;font-weight:800;color:#fff;}
.score-ring .lbl{font-size:.62rem;color:rgba(255,255,255,.6);text-transform:uppercase;letter-spacing:1px;}

.pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:600;margin:2px;font-family:var(--fb);}
.pill-green{background:rgba(34,211,160,.1);color:var(--green);border:1px solid rgba(34,211,160,.2);}
.pill-red{background:rgba(247,79,106,.1);color:#f87171;border:1px solid rgba(247,79,106,.2);}
.pill-purple{background:rgba(124,106,247,.1);color:#a78bfa;border:1px solid rgba(124,106,247,.2);}

.tip-card{background:var(--card);border-left:3px solid var(--accent2);border-radius:0 8px 8px 0;padding:.85rem 1rem;margin:.35rem 0;font-size:.85rem;color:#c0c0d0;line-height:1.6;}
.tip-card strong{color:#fff;}
.strength-card{background:var(--card);border-left:3px solid var(--green);border-radius:0 8px 8px 0;padding:.85rem 1rem;margin:.35rem 0;font-size:.85rem;color:#c0c0d0;}

/* Job cards */
.job-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.3rem 1.4rem;margin-bottom:.9rem;transition:all .25s;position:relative;}
.job-card:hover{border-color:rgba(124,106,247,.3);transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3);}
.job-card .jt{font-family:var(--fh);font-size:.97rem;font-weight:700;color:#fff;margin-bottom:.2rem;}
.job-card .jco{font-size:.83rem;color:var(--accent);font-weight:600;margin-bottom:.5rem;}
.job-card .jm{font-size:.76rem;color:var(--muted);display:flex;gap:.9rem;flex-wrap:wrap;margin-bottom:.6rem;}
.job-card .jd{font-size:.82rem;color:#8888a0;line-height:1.6;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.mbadge{position:absolute;top:.9rem;right:.9rem;padding:2px 9px;border-radius:20px;font-size:.7rem;font-weight:700;font-family:var(--fh);}
.mh{background:rgba(34,211,160,.12);color:var(--green);border:1px solid rgba(34,211,160,.25);}
.mm{background:rgba(250,204,21,.1);color:#fbbf24;border:1px solid rgba(250,204,21,.2);}
.ml{background:rgba(247,79,106,.1);color:#f87171;border:1px solid rgba(247,79,106,.2);}
.apply-btn{display:inline-block;padding:6px 16px;background:linear-gradient(135deg,var(--accent),#9d55f7);color:#fff!important;border-radius:7px;font-size:.78rem;font-weight:700;text-decoration:none!important;font-family:var(--fh);transition:all .2s;margin-top:.5rem;}
.apply-btn:hover{transform:translateY(-1px);box-shadow:0 4px 14px rgba(124,106,247,.3);}

/* HR finder */
.hr-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:.8rem;transition:all .25s;}
.hr-card:hover{border-color:rgba(124,106,247,.25);}
.hr-card .hr-title{font-family:var(--fh);font-size:.92rem;font-weight:700;color:#fff;margin-bottom:.3rem;}
.hr-card .hr-sub{font-size:.8rem;color:var(--accent);margin-bottom:.5rem;}
.hr-card .hr-note{font-size:.75rem;color:var(--muted);}
.open-btn{display:inline-block;padding:6px 14px;background:rgba(124,106,247,.12);border:1px solid rgba(124,106,247,.25);color:#a78bfa;border-radius:7px;font-size:.78rem;font-weight:700;text-decoration:none!important;font-family:var(--fh);transition:all .2s;}
.open-btn:hover{background:rgba(124,106,247,.2);}
.email-copy-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:.8rem 1rem;margin-bottom:.5rem;font-size:.8rem;color:var(--muted);font-family:monospace;}

/* Feature cards */
.feat-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.5rem 1.2rem;text-align:center;height:100%;transition:all .3s;}
.feat-card:hover{border-color:rgba(124,106,247,.25);transform:translateY(-3px);}
.feat-card .icon{font-size:1.9rem;margin-bottom:.6rem;}
.feat-card h4{font-family:var(--fh);font-size:.9rem;color:#fff;margin-bottom:.35rem;}
.feat-card p{font-size:.78rem;color:var(--muted);line-height:1.5;}

/* Enrichment banner */
.enrich-banner{background:rgba(34,211,160,.07);border:1px solid rgba(34,211,160,.2);border-radius:10px;padding:.9rem 1.2rem;margin-bottom:1rem;font-size:.84rem;color:#7af5d5;}

.sec-title{font-family:var(--fh);font-size:1.3rem;font-weight:700;color:#fff;margin-bottom:.2rem;}
.sec-sub{font-size:.81rem;color:var(--muted);margin-bottom:1.4rem;}

/* Q cards */
.q-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.1rem 1.3rem;margin-bottom:.9rem;}
.q-cat{display:inline-block;padding:2px 9px;border-radius:12px;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:.4rem;font-family:var(--fh);}
.q-technical{background:rgba(96,165,250,.1);color:#60a5fa;}
.q-behavioural{background:rgba(192,132,252,.1);color:#c084fc;}
.q-situational{background:rgba(34,211,160,.1);color:var(--green);}
.q-cultural{background:rgba(251,146,60,.1);color:#fb923c;}
.q-text{font-size:.93rem;font-weight:600;color:#fff;margin-bottom:.35rem;}
.q-why{font-size:.76rem;color:var(--muted);font-style:italic;margin-bottom:.5rem;}
.q-answer{font-size:.82rem;color:#b0b0c0;line-height:1.65;}

::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:#2a2a40;border-radius:3px;}
</style>
""", unsafe_allow_html=True)

from utils import (
    parse_cv, analyze_ats, generate_optimized_cv, generate_portfolio,
    generate_skills_roadmap, parse_pdf, parse_txt,
)

try:
    from utils import enrich_cv_with_external_data
except ImportError:
    def enrich_cv_with_external_data(cv_data, github_url='', linkedin_url=''):
        if github_url: cv_data['github'] = github_url
        if linkedin_url: cv_data['linkedin'] = linkedin_url
        return cv_data

try:
    from utils import find_hr_contacts
except ImportError:
    def find_hr_contacts(company, role=''):
        slug = company.lower().replace(' ','')
        return [
            {'type':'email_pattern','email':f'hr@{slug}.com','company':company,'note':'Common pattern'},
            {'type':'email_pattern','email':f'careers@{slug}.com','company':company,'note':'Common pattern'},
            {'type':'email_pattern','email':f'talent@{slug}.com','company':company,'note':'Common pattern'},
            {'type':'linkedin_search','title':'Technical Recruiter','company':company,
             'linkedin_search_url':f'https://www.linkedin.com/search/results/people/?keywords=Technical+Recruiter+{company.replace(" ","+")}',
             'action':'Search on LinkedIn'},
        ]

try:
    from utils import generate_hr_email_templates
except ImportError:
    def generate_hr_email_templates(cv_data, company, role, hr_name='Hiring Manager'):
        name = cv_data.get('name','Candidate')
        email = cv_data.get('email','')
        title = cv_data.get('current_title','Professional')
        skills = ', '.join(cv_data.get('skills',[])[:5])
        return {
            'cold_email': f"Subject: {role} Application — {name}\n\nDear {hr_name},\n\nI'm a {title} with expertise in {skills} and I'm very interested in the {role} role at {company}.\n\nI'd love to discuss how my background aligns with your team's needs. My CV is attached.\n\nBest regards,\n{name}\n{email}",
            'follow_up_1': f"Subject: Following Up — {role} — {name}\n\nDear {hr_name},\n\nFollowing up on my application for {role} at {company} sent last week. Still very interested — happy to provide any additional info.\n\nBest,\n{name}\n{email}",
            'follow_up_2': f"Subject: Final Follow-Up — {role} — {name}\n\nHi {hr_name},\n\nOne last follow-up on the {role} position. If timing isn't right, I'd love to be considered for future openings.\n\nThank you,\n{name}",
            'thank_you': f"Subject: Thank You — {role} Interview — {name}\n\nDear {hr_name},\n\nThank you for the interview today. I'm very excited about joining {company} and confident my skills in {skills} will add real value.\n\nLooking forward to next steps!\n\n{name}\n{email}",
        }


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _fetch_job_url(url):
    import requests
    from bs4 import BeautifulSoup
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=12)
        soup = BeautifulSoup(r.text,'html.parser')
        for t in soup(['script','style','nav','header','footer']): t.decompose()
        return '\n'.join(soup.get_text(separator='\n',strip=True).split('\n')[:200])
    except Exception as e:
        raise Exception(f"Could not fetch URL: {e}")


def _score_color(s):
    if s>=75: return "linear-gradient(135deg,#059669,#22d3a0)"
    if s>=50: return "linear-gradient(135deg,#b45309,#f59e0b)"
    return "linear-gradient(135deg,#dc2626,#f87171)"


def _mclass(s):
    if s>=70: return "mh"
    if s>=40: return "mm"
    return "ml"


def _llm_ok():
    import os
    try:
        k = st.secrets.get("GROQ_API_KEY")
        if k: return True
    except: pass
    try:
        from dotenv import load_dotenv; load_dotenv()
    except: pass
    return bool(os.environ.get("GROQ_API_KEY"))


# ─────────────────────────────────────────────
# JOB SEARCH APIS
# ─────────────────────────────────────────────

def search_jobs_remotive(query, limit=12):
    import requests
    try:
        r = requests.get(f"https://remotive.com/api/remote-jobs?search={query.replace(' ','%20')}&limit={limit}", timeout=10)
        if r.status_code == 200:
            return [{
                'title': j.get('title',''), 'company': j.get('company_name',''),
                'location': j.get('candidate_required_location','Remote'),
                'type': j.get('job_type',''), 'salary': j.get('salary',''),
                'tags': j.get('tags',[]),
                'description': re.sub(r'<[^>]+>','',j.get('description',''))[:400],
                'url': j.get('url',''), 'posted': j.get('publication_date','')[:10],
                'source': 'Remotive',
            } for j in r.json().get('jobs',[])]
    except: pass
    return []


def search_jobs_jobicy(query, limit=8):
    import requests
    try:
        r = requests.get(f"https://jobicy.com/api/v2/remote-jobs?count={limit}&tag={query.replace(' ','+')}", timeout=10)
        if r.status_code == 200:
            return [{
                'title': j.get('jobTitle',''), 'company': j.get('companyName',''),
                'location': 'Remote — ' + j.get('jobGeo','Worldwide'),
                'type': j.get('jobType',''), 'salary': str(j.get('annualSalaryMin','') or ''),
                'tags': j.get('jobIndustry',[]),
                'description': re.sub(r'<[^>]+>','',j.get('jobDescription',''))[:400],
                'url': j.get('url',''), 'posted': j.get('pubDate','')[:10],
                'source': 'Jobicy',
            } for j in r.json().get('jobs',[])]
    except: pass
    return []


def match_score(cv_skills, tags, jt, jd):
    import re
    if not cv_skills: return 50
    cv = set(s.lower() for s in cv_skills)
    s = sum(2 for t in (tags or []) if any(t.lower() in x or x in t.lower() for x in cv))
    s += sum(1 for w in jt.lower().split() if len(w)>3 and any(w in x for x in cv))
    jd_l = jd.lower()
    s += sum(1 for x in list(cv)[:20] if x in jd_l)
    total = len(tags)*2 + len(jt.split()) + 20
    return max(10, min(99, int((s/max(total,1))*100)))


def smart_queries(cv_data):
    title = cv_data.get('current_title','')
    sl = [s.lower() for s in cv_data.get('skills',[])[:15]]
    q = [title] if title else []
    if any(s in sl for s in ['react','vue','angular','javascript','typescript','next.js']): q.append('Frontend Developer')
    if any(s in sl for s in ['node.js','python','django','fastapi','express']): q.append('Backend Developer')
    if any(s in sl for s in ['react','node.js','full stack','python']): q.append('Full Stack Developer')
    if any(s in sl for s in ['machine learning','pytorch','tensorflow','nlp','deep learning']): q.append('ML Engineer')
    if any(s in sl for s in ['python','pandas','sql','data science']): q.append('Data Scientist')
    if any(s in sl for s in ['aws','docker','kubernetes','terraform','devops']): q.append('DevOps Engineer')
    if any(s in sl for s in ['flutter','react native','android','ios']): q.append('Mobile Developer')
    seen, uniq = set(), []
    for x in q:
        if x and x.lower() not in seen:
            seen.add(x.lower()); uniq.append(x)
    return uniq[:6] or ['Software Developer']


import re

# ─────────────────────────────────────────────
# WELCOME
# ─────────────────────────────────────────────

def show_welcome():
    st.markdown("""<div style="text-align:center;padding:.5rem 0 1.5rem;">
      <span style="background:rgba(124,106,247,.1);border:1px solid rgba(124,106,247,.25);color:#a78bfa;
        font-size:.76rem;padding:4px 14px;border-radius:20px;font-family:'Syne',sans-serif;
        letter-spacing:1px;text-transform:uppercase;">100% Free · Groq LLaMA 3 Powered</span>
    </div>""", unsafe_allow_html=True)

    cols = st.columns(6)
    feats = [
        ("📊","ATS Score","AI semantic analysis vs job description"),
        ("📄","CV Builder","ATS-optimized PDF — Harvard or Modern"),
        ("🌐","Portfolio","Professional site from your data"),
        ("✍️","Cover Letter","Tailored for every job"),
        ("🔍","Job Search","Live jobs matched to your skills"),
        ("📧","HR Finder","Find recruiters + email templates"),
    ]
    for col,(icon,title,desc) in zip(cols,feats):
        with col:
            st.markdown(f"""<div class="feat-card">
              <div class="icon">{icon}</div><h4>{title}</h4><p>{desc}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    if not _llm_ok():
        st.warning("⚠️ **Groq API key not set** — AI features use basic fallback. Add `GROQ_API_KEY` to `.streamlit/secrets.toml`")
    else:
        st.success("✅ AI engine ready (Groq LLaMA 3)")
    st.info("👈 **Two ways to start:**  \n1️⃣ Upload CV + optionally add GitHub/LinkedIn  \n2️⃣ Only paste GitHub/LinkedIn URL — CV will be generated automatically!")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    st.markdown("""<div class="cb-logo">
      <h1>🚀 CareerBoost AI</h1>
      <p>ATS · CV · Portfolio · Job Search · HR Outreach</p>
    </div>""", unsafe_allow_html=True)

    # Session state
    for k in ['cv_data','ats_results','cv_pdf','port_zip','roadmap_md',
              'cover_letter','interview_qa','job_results','job_query',
              'job_search_strategy','last_cv_name','last_job_hash','last_template',
              'hr_contacts','hr_emails','enrichment_done',
              '_prefetch_key','_prefetch_data']:
        if k not in st.session_state:
            st.session_state[k] = None

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("### 🚀 Input Method")

        input_mode = st.radio(
            "How do you want to start?",
            ["📄 Upload CV", "🔗 GitHub / LinkedIn only"],
            label_visibility="collapsed",
            key="input_mode_radio"
        )
        st.session_state['_input_mode'] = input_mode

        cv_file = None
        github_input = ""
        linkedin_input = ""
        manual_info = {}

        if input_mode == "📄 Upload CV":
            st.markdown("**Upload CV** *(PDF/DOCX/TXT)*")
            cv_file = st.file_uploader("CV", type=['pdf','docx','doc','txt'],
                                       help="Never stored", label_visibility="collapsed")
            st.markdown("**Enrich with external data** *(optional)*")
            github_input   = st.text_input("GitHub URL", placeholder="https://github.com/username", key="gh1")
            linkedin_input = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...", key="li1")

        else:
            github_input   = st.text_input("🐙 GitHub URL", placeholder="https://github.com/username", key="gh2")
            linkedin_input = st.text_input("🔗 LinkedIn URL", placeholder="https://linkedin.com/in/...", key="li2")

            if not github_input.strip() and not linkedin_input.strip():
                st.info("Enter GitHub and/or LinkedIn URL — everything else fetched automatically")
            else:
                st.caption("✅ URLs entered — data will be fetched when you click Generate")

            st.markdown("---")
            # Only ask what can NEVER be on public profiles
            st.markdown("**3 things we can't fetch:**")
            manual_info['email']     = st.text_input("📧 Email", placeholder="you@email.com")
            manual_info['phone']     = st.text_input("📞 Phone *(optional)*", placeholder="+91 98765 43210")
            manual_info['years_exp'] = st.number_input("🗓 Years Experience *(optional)*", min_value=0, max_value=40, value=0)
            # Everything else (name, title, location, bio, skills, projects) — fetched silently

        cv_template = st.selectbox("CV Template", ["Modern", "Harvard"])

        st.markdown("---")
        st.markdown("### 🎯 Job Description *(optional)*")
        job_mode = st.radio("Method", ["Paste text", "Upload PDF", "Paste URL"], label_visibility="collapsed")
        job_text_input = job_url_input = ""
        job_file_input = None
        if job_mode == "Paste text":
            job_text_input = st.text_area("JD", height=130, placeholder="Paste job description…", label_visibility="collapsed")
        elif job_mode == "Upload PDF":
            job_file_input = st.file_uploader("JD PDF", type=['pdf','txt'], key="jdpdf", label_visibility="collapsed")
        else:
            job_url_input = st.text_input("Job URL", placeholder="https://…", label_visibility="collapsed")

        st.markdown("---")
        go = st.button("🚀 Generate", type="primary", use_container_width=True)
        if st.session_state.cv_data:
            if st.button("🗑️ Clear & Start Over", use_container_width=True):
                for k in list(st.session_state.keys()):
                    st.session_state[k] = None
                st.rerun()

        st.markdown("---")
        st.markdown("""<div style="font-size:.7rem;color:#444;line-height:1.8;">
        <b style="color:#666">Mode 1:</b> Upload CV + enrich<br/>
        <b style="color:#666">Mode 2:</b> GitHub/LinkedIn only<br/>
        <b style="color:#666">AI:</b> Groq LLaMA 3.1 (free)<br/>
        <b style="color:#666">Storage:</b> None
        </div>""", unsafe_allow_html=True)

    # ── WELCOME ──
    if not go and not st.session_state.cv_data:
        show_welcome(); return

    # ── PROCESSING ──
    if go:
        input_mode_val = st.session_state.get('_input_mode', '📄 Upload CV')
        using_urls_only = (input_mode_val == "🔗 GitHub / LinkedIn only")

        # Validation
        if not using_urls_only and not cv_file:
            st.error("⚠️ Please upload your CV first, or switch to 'GitHub / LinkedIn only' mode.")
            return
        if using_urls_only and not github_input.strip() and not linkedin_input.strip():
            st.error("⚠️ Please enter at least a GitHub or LinkedIn URL.")
            return

        # Build cache key
        if using_urls_only:
            cache_key = (github_input.strip() + linkedin_input.strip() +
                         manual_info.get('name','') + manual_info.get('title',''))
        else:
            cache_key = cv_file.name if cv_file else ""

        jd_combined  = job_text_input + job_url_input + (job_file_input.name if job_file_input else "")
        job_hash     = hashlib.md5(jd_combined.encode()).hexdigest()
        needs_reparse   = (cache_key != st.session_state.last_cv_name)
        needs_reanalyze = (job_hash != st.session_state.last_job_hash)

        with st.status("🔍 Processing…", expanded=True) as status:

            # ── MODE 1: URL-only (no CV) ──
            if using_urls_only and needs_reparse:
                gh_data, li_data = {}, {}

                # Step 1: Fetch GitHub silently
                if github_input.strip():
                    st.write("🐙 Fetching GitHub profile + repos…")
                    try:
                        from utils import get_github_data
                        gh_data = get_github_data(github_input.strip())
                        repos_n = len(gh_data.get('projects', []))
                        langs   = ', '.join(gh_data.get('languages', [])[:4])
                        st.write(f"   ✅ GitHub: {repos_n} repos · {langs}")
                    except Exception as e:
                        st.write(f"   ⚠️ GitHub fetch failed: {e}")

                # Step 2: Fetch LinkedIn silently
                if linkedin_input.strip():
                    st.write("🔗 Fetching LinkedIn profile…")
                    try:
                        from utils import get_linkedin_data
                        li_data = get_linkedin_data(linkedin_input.strip())
                        li_got  = [k for k in ['name','headline','location','about'] if li_data.get(k)]
                        st.write(f"   ✅ LinkedIn: found {', '.join(li_got) if li_got else 'limited data (public profile only)'}")
                    except Exception as e:
                        st.write(f"   ⚠️ LinkedIn fetch failed: {e}")

                # Step 3: Build cv_data by merging all sources — priority: LinkedIn > GitHub > manual
                st.write("🤖 Building CV from fetched data + AI…")
                try:
                    # Name: LinkedIn > GitHub username > manual > ask
                    name = (li_data.get('name') or
                            (gh_data.get('username','').replace('-',' ').replace('_',' ').title() if gh_data.get('username') else '') or
                            manual_info.get('name','') or
                            'Professional')

                    # Title: LinkedIn headline > GitHub bio inferred > manual
                    title = (li_data.get('headline') or
                             manual_info.get('title','') or '')

                    # Location: LinkedIn > GitHub > manual
                    location = (li_data.get('location') or
                                gh_data.get('location','') or
                                manual_info.get('location',''))

                    # Bio/About: LinkedIn > GitHub bio
                    bio = (li_data.get('about','') or gh_data.get('bio','') or '')

                    # Skills from GitHub languages + project topics
                    from utils import SKILL_KEYWORDS
                    skills = list(gh_data.get('languages', []))
                    all_proj_text = ' '.join(
                        p.get('description','') + ' ' + ' '.join(p.get('topics',[]))
                        for p in gh_data.get('projects', [])
                    ).lower()
                    # Also scan LinkedIn about
                    all_proj_text += ' ' + bio.lower()
                    for kw in SKILL_KEYWORDS:
                        if kw in all_proj_text and kw.title() not in skills:
                            skills.append(kw.title())

                    cv_data = {
                        'name':             name,
                        'email':            manual_info.get('email','').strip(),
                        'phone':            manual_info.get('phone','').strip(),
                        'location':         location,
                        'current_title':    title,
                        'years_experience': int(manual_info.get('years_exp', 0) or 0),
                        'linkedin':         linkedin_input.strip(),
                        'github':           github_input.strip(),
                        'skills':           skills[:30],
                        'experience':       [],
                        'education':        [],
                        'projects':         gh_data.get('projects', []),
                        'certifications':   [],
                        'github_bio':       gh_data.get('bio',''),
                        'linkedin_about':   li_data.get('about',''),
                        'github_stats': {
                            'followers':  gh_data.get('followers', 0),
                            'repos':      gh_data.get('public_repos', 0),
                            'stars':      gh_data.get('total_stars', 0),
                            'languages':  gh_data.get('languages', []),
                        },
                        'raw_text': f"Name: {name}\nTitle: {title}\nBio: {bio[:300]}\nSkills: {', '.join(skills[:15])}\nProjects: {', '.join(p['name'] for p in gh_data.get('projects',[])[:5])}",
                    }

                    # Step 4: LLM enrichment — generate experience, better title, summary
                    st.write("✨ AI enriching experience + summary…")
                    try:
                        from llm_utils import enrich_from_github_llm
                        enriched = enrich_from_github_llm(cv_data)
                        if enriched:
                            if enriched.get('current_title') and not cv_data['current_title']:
                                cv_data['current_title'] = enriched['current_title']
                            if enriched.get('experience'):
                                cv_data['experience'] = enriched['experience']
                            if enriched.get('skills'):
                                merged = list({s.lower(): s for s in cv_data['skills'] + enriched['skills']}.values())
                                cv_data['skills'] = merged[:30]
                            if enriched.get('summary'):
                                cv_data['summary'] = enriched['summary']
                            if enriched.get('education'):
                                cv_data['education'] = enriched['education']
                    except Exception as e:
                        st.write(f"   ℹ️ AI enrichment skipped: {e}")

                    # Step 5: Report what we got vs what's missing
                    got, missing_fields = [], []
                    if cv_data['name'] != 'Professional': got.append(f"👤 {cv_data['name']}")
                    else: missing_fields.append("name")
                    if cv_data['current_title']: got.append(f"💼 {cv_data['current_title']}")
                    else: missing_fields.append("job title")
                    if cv_data['location']:  got.append(f"📍 {cv_data['location']}")
                    if cv_data['email']:     got.append(f"📧 email")
                    if cv_data['skills']:    got.append(f"🛠 {len(cv_data['skills'])} skills")
                    if cv_data['projects']:  got.append(f"💻 {len(cv_data['projects'])} projects")
                    if cv_data['experience']:got.append(f"🏢 {len(cv_data['experience'])} experience entries")

                    st.write("✅ Built: " + " · ".join(got))
                    if missing_fields:
                        st.warning(f"⚠️ Could not find: {', '.join(missing_fields)} — add manually in sidebar if needed")

                except Exception as e:
                    st.error(f"Build failed: {e}"); return

                st.session_state.enrichment_done = [
                    x for x in [
                        'GitHub' if github_input.strip() else '',
                        'LinkedIn' if linkedin_input.strip() else ''
                    ] if x
                ]
                st.session_state.cv_data         = cv_data
                st.session_state.last_cv_name    = cache_key
                for k in ['cv_pdf','port_zip','cover_letter','interview_qa',
                          'ats_results','roadmap_md','job_search_strategy','hr_contacts','hr_emails']:
                    st.session_state[k] = None

            # ── MODE 2: CV upload ──
            elif not using_urls_only and needs_reparse:
                st.write("📄 Parsing CV…")
                try:
                    cv_data = parse_cv(cv_file)
                    st.session_state.last_cv_name = cache_key
                    enrich_msgs = []
                    if github_input.strip():
                        st.write("🐙 Fetching GitHub data…")
                        enrich_msgs.append("GitHub")
                    if linkedin_input.strip():
                        st.write("🔗 Fetching LinkedIn data…")
                        enrich_msgs.append("LinkedIn")
                    if github_input.strip() or linkedin_input.strip():
                        cv_data = enrich_cv_with_external_data(
                            cv_data,
                            github_url=github_input.strip(),
                            linkedin_url=linkedin_input.strip(),
                        )
                        st.session_state.enrichment_done = enrich_msgs
                    else:
                        st.session_state.enrichment_done = None
                    st.session_state.cv_data = cv_data
                    for k in ['cv_pdf','port_zip','cover_letter','interview_qa',
                              'ats_results','roadmap_md','job_search_strategy','hr_contacts','hr_emails']:
                        st.session_state[k] = None
                except Exception as e:
                    st.error(f"CV parse failed: {e}"); return

            else:
                cv_data = st.session_state.cv_data
                st.write("✅ Data cached")

            # Job description
            job_text = None
            if job_text_input.strip():
                job_text = job_text_input.strip()
            elif job_file_input:
                try:
                    job_text = parse_pdf(job_file_input) if job_file_input.name.endswith('.pdf') else parse_txt(job_file_input)
                except Exception as e:
                    st.error(str(e)); return
            elif job_url_input.strip():
                st.write("🌐 Fetching job posting…")
                try:
                    job_text = _fetch_job_url(job_url_input.strip())
                except Exception as e:
                    st.error(str(e)); return

            # ATS
            if needs_reanalyze or not st.session_state.ats_results:
                st.write("🤖 ATS analysis…")
                eval_text = job_text or "General Resume Quality: clarity, skills depth, project portfolio, quantified achievements."
                try:
                    st.session_state.ats_results = analyze_ats(st.session_state.cv_data, eval_text)
                    st.session_state.last_job_hash = job_hash
                    for k in ['roadmap_md','cover_letter','interview_qa','job_search_strategy']:
                        st.session_state[k] = None
                except Exception as e:
                    st.warning(f"ATS issue: {e}")

            if st.session_state.last_template != cv_template:
                st.session_state.cv_pdf = None
                st.session_state.last_template = cv_template

            status.update(label="✅ Ready!", state="complete", expanded=False)

    cv_data     = st.session_state.cv_data
    ats_results = st.session_state.ats_results
    if not cv_data:
        show_welcome(); return

    # Enrichment banner
    enrich_done = st.session_state.get('enrichment_done')
    if enrich_done:
        st.markdown(f"""<div class="enrich-banner">
          ✅ <strong>Enriched with external data:</strong> {' + '.join(enrich_done)} data successfully integrated into your CV and Portfolio
        </div>""", unsafe_allow_html=True)

    # Job text for tabs
    job_text = None
    if job_text_input.strip():
        job_text = job_text_input.strip()

    # ── TABS ──
    has_ats = bool(ats_results)
    if has_ats:
        tabs = st.tabs(["📊 ATS","📄 CV","🌐 Portfolio","✍️ Cover Letter",
                        "🎤 Interview","🔍 Jobs","📧 HR Finder","📚 Roadmap","🗂️ Data"])
        t_ats,t_cv,t_port,t_cover,t_interview,t_jobs,t_hr,t_road,t_data = tabs
    else:
        tabs = st.tabs(["📄 CV","🌐 Portfolio","✍️ Cover Letter",
                        "🎤 Interview","🔍 Jobs","📧 HR Finder","🗂️ Data"])
        t_cv,t_port,t_cover,t_interview,t_jobs,t_hr,t_data = tabs
        t_ats = t_road = None

    # ════ ATS ════
    if t_ats and ats_results:
        with t_ats:
            score    = ats_results.get('score',0)
            matched  = ats_results.get('matched_skills',[])
            missing  = ats_results.get('missing_skills',[])
            strengths = ats_results.get('strengths',[])
            tips     = ats_results.get('tips',[])

            c1,c2,c3,c4 = st.columns([1.3,1,1,1])
            with c1:
                st.markdown(f"""<div class="score-ring" style="background:{_score_color(score)};">
                  <div class="num">{score}%</div><div class="lbl">ATS Score</div>
                </div>
                <div style="text-align:center;margin-top:.5rem;font-size:.8rem;color:#888;">
                {"🟢 Excellent" if score>=85 else "🟡 Good" if score>=70 else "🟠 Moderate" if score>=50 else "🔴 Needs Work"}
                </div>""", unsafe_allow_html=True)
            with c2: st.metric("✅ Matched", len(matched))
            with c3: st.metric("❌ Missing", len(missing))
            with c4: st.metric("💡 Tips", len(tips))

            st.markdown("---")
            cl,cr = st.columns(2)
            with cl:
                if matched:
                    st.markdown("**✅ Matched**")
                    st.markdown(" ".join(f'<span class="pill pill-green">{s}</span>' for s in matched), unsafe_allow_html=True)
                    st.markdown("")
                if missing:
                    st.markdown("**❌ Missing**")
                    st.markdown(" ".join(f'<span class="pill pill-red">{s}</span>' for s in missing), unsafe_allow_html=True)
            with cr:
                if strengths:
                    st.markdown("**💪 Strengths**")
                    for s in strengths:
                        st.markdown(f'<div class="strength-card">{s}</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 💡 Tips")
            for i,tip in enumerate(tips,1):
                st.markdown(f'<div class="tip-card"><strong>{i}.</strong> {tip}</div>', unsafe_allow_html=True)

    # ════ CV ════
    with t_cv:
        st.markdown('<div class="sec-title">📄 Optimized CV</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">ATS-optimized PDF — enriched with GitHub + LinkedIn data</div>', unsafe_allow_html=True)

        if st.session_state.cv_pdf is None:
            with st.spinner("Generating CV…"):
                try:
                    tmpl = st.session_state.get('last_template','Modern')
                    st.session_state.cv_pdf = generate_optimized_cv(cv_data, job_text, template=tmpl)
                except Exception as e:
                    st.error(f"CV error: {e}")

        if st.session_state.cv_pdf:
            col1,col2 = st.columns([2,1])
            with col1:
                st.download_button(
                    "⬇️ Download CV (PDF)",
                    data=st.session_state.cv_pdf,
                    file_name=f"{cv_data.get('name','CV').replace(' ','_')}_optimized.pdf",
                    mime="application/pdf", use_container_width=True,
                )
            with col2:
                st.markdown(f"**Template:** {st.session_state.get('last_template','Modern')}")

            st.markdown("---")
            c1,c2,c3,c4 = st.columns(4)
            for col,(icon,t,d) in zip([c1,c2,c3,c4],[
                ("🤖","AI Summary","Tailored to job if provided"),
                ("🐙","GitHub Data","Projects + languages from repos"),
                ("🔗","LinkedIn","Bio + headline integrated"),
                ("✅","ATS Ready","Clean format, no tables"),
            ]):
                with col:
                    st.markdown(f"""<div class="stat-box">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div style="font-size:.83rem;font-weight:600;color:#fff;margin-top:.3rem;">{t}</div>
                    <div style="font-size:.72rem;color:#555;margin-top:.2rem;">{d}</div>
                    </div>""", unsafe_allow_html=True)

    # ════ PORTFOLIO ════
    with t_port:
        st.markdown('<div class="sec-title">🌐 Portfolio Website</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Deploy-ready HTML — enriched with GitHub repos + stats + LinkedIn bio</div>', unsafe_allow_html=True)

        if st.session_state.port_zip is None:
            with st.spinner("Building portfolio…"):
                try:
                    st.session_state.port_zip = generate_portfolio(cv_data)
                except Exception as e:
                    st.error(f"Portfolio error: {e}")

        if st.session_state.port_zip:
            st.download_button("⬇️ Download Portfolio (ZIP)", data=st.session_state.port_zip,
                               file_name="portfolio.zip", mime="application/zip", use_container_width=True)
            st.markdown("---")
            st.markdown("**Portfolio includes:** Hero · GitHub Stats · Skills Grid (categorized) · Experience Timeline · Projects (from GitHub) · Education · Contact")
            st.markdown("""
**Deploy FREE:**
- **Netlify** — drag & drop folder on netlify.app/drop (fastest)
- **GitHub Pages** — push `index.html`, enable Pages in repo settings
- **Vercel** — `vercel deploy` from folder
            """)

    # ════ COVER LETTER ════
    with t_cover:
        st.markdown('<div class="sec-title">✍️ Cover Letter</div>', unsafe_allow_html=True)
        if not job_text:
            st.info("📋 Add a job description in the sidebar to generate a tailored cover letter.")
        else:
            if st.session_state.cover_letter is None:
                with st.spinner("Writing cover letter…"):
                    try:
                        from llm_utils import generate_cover_letter_llm
                        st.session_state.cover_letter = generate_cover_letter_llm(cv_data, job_text)
                    except Exception as e:
                        st.session_state.cover_letter = f"[Failed: {e}]\n\nCheck GROQ_API_KEY."

            if st.session_state.cover_letter:
                today = datetime.date.today().strftime("%B %d, %Y")
                full = f"""Dear Hiring Manager,

{st.session_state.cover_letter}

Sincerely,
{cv_data.get('name','Applicant')}
{cv_data.get('email','')}
{today}"""
                st.text_area("Cover Letter (editable)", value=full, height=400, label_visibility="collapsed")
                c1,c2 = st.columns(2)
                with c1: st.download_button("⬇️ Download (.txt)", data=full, file_name="cover_letter.txt", mime="text/plain", use_container_width=True)
                with c2:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.session_state.cover_letter = None; st.rerun()

    # ════ INTERVIEW ════
    with t_interview:
        st.markdown('<div class="sec-title">🎤 Interview Prep</div>', unsafe_allow_html=True)
        if not job_text:
            st.info("📋 Add a job description to get tailored interview questions.")
        else:
            if st.session_state.interview_qa is None:
                with st.spinner("Generating questions…"):
                    try:
                        from llm_utils import generate_interview_prep_llm
                        st.session_state.interview_qa = generate_interview_prep_llm(cv_data, job_text)
                    except Exception as e:
                        st.session_state.interview_qa = []; st.error(str(e))

            for i,qa in enumerate(st.session_state.interview_qa or [],1):
                cat = qa.get('category','general').lower().replace(' ','')
                with st.expander(f"**Q{i}:** {qa.get('question','')}",expanded=(i==1)):
                    st.markdown(f"""<div class="q-card">
                    <div class="q-cat q-{cat}">{qa.get('category','General')}</div>
                    <div class="q-text">{qa.get('question','')}</div>
                    <div class="q-why">💡 {qa.get('why_asked','')}</div>
                    <div class="q-answer"><strong>Model Answer:</strong><br/>{qa.get('model_answer','')}</div>
                    </div>""", unsafe_allow_html=True)

            if st.session_state.interview_qa:
                if st.button("🔄 Regenerate"):
                    st.session_state.interview_qa = None; st.rerun()

    # ════ JOBS ════
    with t_jobs:
        st.markdown('<div class="sec-title">🔍 Job Search</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Live jobs from Remotive & Jobicy — matched to your CV skills</div>', unsafe_allow_html=True)

        sq = smart_queries(cv_data)
        cv_skills = cv_data.get('skills',[])

        jc1,jc2,jc3 = st.columns([2.5,1,1])
        with jc1: job_query = st.text_input("Search jobs", value=sq[0] if sq else "Software Developer", label_visibility="collapsed")
        with jc2: job_source = st.selectbox("Source", ["Both","Remotive","Jobicy"], label_visibility="collapsed")
        with jc3: search_btn = st.button("🔍 Search Jobs", use_container_width=True)

        if sq:
            st.markdown("**🤖 Suggested (from your CV):**")
            st.markdown(" ".join(f'<span class="pill pill-purple">🎯 {q}</span>' for q in sq), unsafe_allow_html=True)

        st.markdown("")

        if search_btn:
            with st.spinner(f"Searching '{job_query}'…"):
                results = []
                if job_source in ["Both","Remotive"]: results += search_jobs_remotive(job_query)
                if job_source in ["Both","Jobicy"]:   results += search_jobs_jobicy(job_query)
                for j in results:
                    tags = j.get('tags',[])
                    j['match'] = match_score(cv_skills, tags, j.get('title',''), j.get('description',''))
                results.sort(key=lambda x: x.get('match',0), reverse=True)
                st.session_state.job_results = results
                st.session_state.job_query = job_query

        jobs = st.session_state.job_results or []
        if jobs:
            fc1,fc2 = st.columns([1,3])
            with fc1: min_m = st.slider("Min match %", 0, 90, 30, step=10)
            filtered = [j for j in jobs if j.get('match',0) >= min_m]
            st.markdown(f"**{len(filtered)} jobs** above {min_m}% match")
            st.markdown("")

            for j in filtered:
                m = j.get('match',50)
                mc = _mclass(m)
                tags = j.get('tags',[])
                tag_pills = " ".join(f'<span class="pill pill-purple">{t}</span>' for t in (tags if isinstance(tags,list) else [])[:4])
                st.markdown(f"""<div class="job-card">
                  <div class="mbadge {mc}">{m}%</div>
                  <div class="jt">{j['title']}</div>
                  <div class="jco">🏢 {j.get('company','')}</div>
                  <div class="jm"><span>📍 {j.get('location','Remote')}</span><span>⏰ {j.get('type','')}</span>{"<span>💰 "+j['salary']+"</span>" if j.get('salary') else ""}{"<span>📅 "+j['posted']+"</span>" if j.get('posted') else ""}<span style='margin-left:auto;font-size:.7rem;color:#555'>{j.get('source','')}</span></div>
                  {"<div style='margin-bottom:.5rem;'>"+tag_pills+"</div>" if tag_pills else ""}
                  <div class="jd">{j.get('description','')[:280]}</div>
                  {"<a href='"+j['url']+"' target='_blank' class='apply-btn'>Apply Now →</a>" if j.get('url') else ""}
                </div>""", unsafe_allow_html=True)
        elif search_btn:
            st.warning("No results. Try 'Python Developer', 'React', or 'Data Scientist'.")
        else:
            st.info("👆 Click **Search Jobs** to find live opportunities.")

        st.caption("Jobs from Remotive.com + Jobicy.com — 100% free, no API key. Primarily remote/global.")

    # ════ HR FINDER ════
    with t_hr:
        st.markdown('<div class="sec-title">📧 HR Finder & Email Templates</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Find recruiters at any company + ready-to-send emails</div>', unsafe_allow_html=True)

        hc1, hc2, hc3 = st.columns([2, 2, 1])
        with hc1: target_company = st.text_input("Company Name", placeholder="e.g. Google, Infosys, Tata")
        with hc2: target_role    = st.text_input("Role Applying For", placeholder="e.g. Software Engineer", value=cv_data.get('current_title','') or '')
        with hc3: hr_name_input  = st.text_input("HR Name (optional)", placeholder="First Name")
        find_btn = st.button("🔍 Find HR Contacts + Generate Emails", use_container_width=True)

        if find_btn and target_company:
            with st.spinner(f"Finding HR contacts at {target_company}…"):
                st.session_state.hr_contacts = find_hr_contacts(target_company, target_role)
                hr_nm = hr_name_input.strip() if hr_name_input.strip() else "Hiring Manager"
                try:
                    st.session_state.hr_emails = generate_hr_email_templates(cv_data, target_company, target_role, hr_nm)
                except Exception as e:
                    st.warning(f"Email generation failed: {e}")

        if st.session_state.hr_contacts:
            contacts = st.session_state.hr_contacts

            # LinkedIn search contacts
            li_contacts = [c for c in contacts if c.get('type') == 'linkedin_search']
            email_contacts = [c for c in contacts if c.get('type') == 'email_pattern']

            col_l, col_r = st.columns(2)

            with col_l:
                st.markdown("### 🔗 LinkedIn Search (Direct)")
                st.caption("Click to search for HR people at this company on LinkedIn")
                for c in li_contacts[:4]:
                    st.markdown(f"""<div class="hr-card">
                      <div class="hr-title">{c['title']}</div>
                      <div class="hr-sub">{c['company']}</div>
                      <a href="{c['linkedin_search_url']}" target="_blank" class="open-btn">Search on LinkedIn →</a>
                      <div class="hr-note" style="margin-top:.5rem;">💡 Connect → wait 1 day → send message</div>
                    </div>""", unsafe_allow_html=True)

            with col_r:
                st.markdown("### 📧 Email Patterns to Try")
                st.caption("Verify with Hunter.io (free 25/month) before sending")
                for c in email_contacts[:4]:
                    st.markdown(f"""<div class="hr-card">
                      <div class="email-copy-box">{c['email']}</div>
                      <div class="hr-note">{c.get('note','')}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 💡 Free Tools to Verify Emails")
            st.markdown("""
- **Hunter.io** — hunter.io (25 free searches/month)
- **Apollo.io** — apollo.io (free tier)
- **Snov.io** — snov.io (50 free credits)
- **LinkedIn Sales Navigator** — try free trial
            """)

        # ── EMAIL TEMPLATES ──
        if st.session_state.hr_emails:
            st.markdown("---")
            st.markdown("### ✉️ Email Templates")
            emails = st.session_state.hr_emails

            e_tabs = st.tabs(["🥶 Cold Email","📩 Follow-Up 1 (7 days)","📩 Follow-Up 2 (14 days)","🙏 Thank You"])

            labels = ['cold_email','follow_up_1','follow_up_2','thank_you']
            for etab, key in zip(e_tabs, labels):
                with etab:
                    content = emails.get(key, '')
                    if content:
                        st.text_area("Edit before sending →", value=content, height=320, label_visibility="collapsed", key=f"email_{key}")
                        st.download_button(
                            f"⬇️ Download {key.replace('_',' ').title()}",
                            data=content,
                            file_name=f"{key}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"dl_{key}",
                        )

            st.markdown("---")
            st.markdown("### 📅 Follow-Up Schedule")
            st.markdown("""
| Action | When |
|--------|------|
| Send Cold Email | Day 1 |
| Follow-Up 1 | Day 7 (if no reply) |
| Follow-Up 2 | Day 14 (if still no reply) |
| Move on | Day 21+ |
| Thank You | Same day as interview |

**Pro tips:**
- Send cold emails **Tuesday–Thursday, 9–11am** (highest open rates)
- Keep subject line under 50 characters
- Personalize first 2 sentences — mention their recent project/news
- Never send more than 3 follow-ups to the same person
            """)

        elif not st.session_state.hr_contacts:
            st.markdown("""
            **How to use:**
            1. Enter the company name you want to apply to
            2. Enter the role
            3. Click **Find HR Contacts + Generate Emails**
            4. Get LinkedIn search links + email patterns + 4 ready-to-send email templates

            **Strategy:**
            - Find the recruiter on LinkedIn first → connect
            - Try the email patterns with Hunter.io to verify
            - Send the cold email → wait 7 days → follow up
            """)

    # ════ ROADMAP ════
    if t_road and ats_results:
        with t_road:
            missing = ats_results.get('missing_skills',[])
            if missing:
                if st.session_state.roadmap_md is None:
                    with st.spinner("Building roadmap…"):
                        try:
                            st.session_state.roadmap_md = generate_skills_roadmap(missing, cv_data.get('current_title',''))
                        except Exception as e:
                            st.session_state.roadmap_md = f"**Failed:** {e}"
                if st.session_state.roadmap_md:
                    st.markdown(st.session_state.roadmap_md)
                    st.download_button("⬇️ Download Roadmap", data=st.session_state.roadmap_md,
                                       file_name="roadmap.md", mime="text/markdown", use_container_width=True)
            else:
                st.success("🎉 Strong skills match — no major gaps!")
                st.balloons()

    # ════ DATA ════
    with t_data:
        st.markdown('<div class="sec-title">🗂️ Parsed + Enriched Data</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1:
            st.write(f"**Name:** {cv_data.get('name','—')}")
            st.write(f"**Email:** {cv_data.get('email','—')}")
            st.write(f"**Phone:** {cv_data.get('phone','—')}")
        with c2:
            st.write(f"**Title:** {cv_data.get('current_title','—')}")
            st.write(f"**Location:** {cv_data.get('location','—')}")
            st.write(f"**Years:** {cv_data.get('years_experience','—')}")
        with c3:
            sc1,sc2 = st.columns(2)
            with sc1: st.metric("Skills", len(cv_data.get('skills',[])))
            with sc2: st.metric("Roles",  len(cv_data.get('experience',[])))

        if cv_data.get('linkedin'): st.write(f"🔗 {cv_data['linkedin']}")
        if cv_data.get('github'):   st.write(f"💻 {cv_data['github']}")
        if cv_data.get('github_bio'): st.write(f"*GitHub bio: {cv_data['github_bio']}*")
        if cv_data.get('linkedin_about'): st.write(f"*LinkedIn about: {cv_data['linkedin_about'][:150]}…*")

        if cv_data.get('github_stats'):
            gs = cv_data['github_stats']
            st.markdown(f"**GitHub:** {gs.get('repos',0)} repos · {gs.get('stars',0)} stars · {gs.get('followers',0)} followers · Languages: {', '.join(gs.get('languages',[]))}")

        st.markdown("---")
        if cv_data.get('skills'):
            st.markdown("**Skills**")
            st.markdown(" ".join(f'<span class="pill pill-purple">{s}</span>' for s in cv_data['skills']), unsafe_allow_html=True)
        if cv_data.get('experience'):
            st.markdown("---\n**Experience**")
            for e in cv_data['experience']:
                t = e.get('title','') + (f" @ {e['company']}" if e.get('company') else '')
                with st.expander(t):
                    if e.get('duration'): st.caption(e['duration'])
                    st.write(e.get('description','—'))
        if cv_data.get('projects'):
            st.markdown("---\n**Projects**")
            for p in cv_data['projects']:
                with st.expander(p.get('name','Project')):
                    st.write(p.get('description','—'))
                    if p.get('url'): st.write(f"🔗 {p['url']}")
                    if p.get('stars'): st.write(f"⭐ {p['stars']} stars")
        if cv_data.get('education'):
            st.markdown("---\n**Education**")
            for e in cv_data['education']:
                if isinstance(e,dict):
                    st.write(f"• **{e.get('degree','')}** — {e.get('institution','')} ({e.get('year','')})")
                else:
                    st.write(f"• {e}")


if __name__ == "__main__":
    main()
