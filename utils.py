"""
utils.py — CareerBoost AI (TOP 1% VERSION)
Fixes:
  1. CV PDF — proper ATS format, no layout bugs, Table for alignment
  2. LinkedIn public data fetch
  3. GitHub repos + bio + languages fetch
  4. Portfolio — top 1% professional with categorized skills
  5. HR Finder + Email templates
"""

import fitz
import docx
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import re
import io
import zipfile
import datetime
from typing import Dict, List, Optional


# ─────────────────────────────────────────────
# FILE PARSING
# ─────────────────────────────────────────────

def parse_pdf(file) -> str:
    try:
        pdf_bytes = file.read() if hasattr(file, 'read') else file
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF parse error: {e}")


def parse_docx(file) -> str:
    try:
        d = docx.Document(file)
        return "\n".join(p.text for p in d.paragraphs).strip()
    except Exception as e:
        raise Exception(f"DOCX parse error: {e}")


def parse_txt(file) -> str:
    try:
        raw = file.read()
        return (raw.decode('utf-8') if isinstance(raw, bytes) else raw).strip()
    except Exception as e:
        raise Exception(f"TXT parse error: {e}")


def parse_cv(file) -> Dict:
    fname = file.name.lower()
    if fname.endswith('.pdf'):
        text = parse_pdf(file)
    elif fname.endswith(('.docx', '.doc')):
        text = parse_docx(file)
    elif fname.endswith('.txt'):
        text = parse_txt(file)
    else:
        raise Exception("Unsupported format. Use PDF, DOCX or TXT.")

    if not text.strip():
        raise Exception("File appears empty or unreadable.")

    try:
        from llm_utils import extract_cv_data_llm
        data = extract_cv_data_llm(text)
        if data and data.get("name"):
            data["raw_text"] = text
            data.setdefault("skills", [])
            edu = data.get("education", [])
            if edu and isinstance(edu[0], dict):
                data["education_structured"] = edu
                data["education"] = [
                    f"{e.get('degree','')} — {e.get('institution','')} ({e.get('year','')})".strip(" —()")
                    for e in edu
                ]
            return data
    except Exception:
        pass

    return {
        'raw_text': text,
        'name': _extract_name(text),
        'email': _extract_email(text),
        'phone': _extract_phone(text),
        'linkedin': _extract_linkedin(text),
        'github': _extract_github(text),
        'skills': _extract_skills(text),
        'experience': _extract_experience(text),
        'education': _extract_education(text),
        'certifications': [],
        'projects': [],
        'current_title': _extract_title(text),
        'years_experience': 0,
        'location': '',
        'summary': '',
    }


# ─────────────────────────────────────────────
# REGEX HELPERS
# ─────────────────────────────────────────────

def _extract_name(text):
    for line in (l.strip() for l in text.split('\n') if l.strip()):
        if 2 <= len(line.split()) <= 4 and '@' not in line and len(line) > 3:
            if not re.match(r'(?i)(experience|education|skills|summary|objective|contact|profile|about|resume|cv)', line):
                return line
    return "Professional"


def _extract_email(text):
    m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    return m.group(0) if m else ""


def _extract_phone(text):
    m = re.search(r'(\+?\d{1,3}[\-.\s]?)?(\(?\d{2,4}\)?[\-.\s]?)?\d{3,4}[\-.\s]?\d{4}', text)
    return m.group(0).strip() if m else ""


def _extract_linkedin(text):
    m = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    return f"https://{m.group(0)}" if m else ""


def _extract_github(text):
    m = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)
    return f"https://{m.group(0)}" if m else ""


def _extract_title(text):
    titles = ['software engineer','software developer','frontend developer',
              'backend developer','full stack developer','data scientist',
              'data analyst','ml engineer','devops engineer','product manager',
              'web developer','mobile developer']
    lower = text.lower()
    for t in titles:
        if t in lower:
            return t.title()
    return ""


SKILL_KEYWORDS = [
    'python','java','javascript','typescript','go','golang','rust','swift','kotlin',
    'c++','c#','.net','ruby','php','scala','r','matlab',
    'react','angular','vue.js','next.js','nuxt','svelte','html','css','sass',
    'bootstrap','tailwind css','material ui','figma','adobe xd','ui/ux',
    'node.js','express','django','flask','fastapi','spring boot','laravel',
    'graphql','rest api','websocket','grpc','microservices',
    'sql','postgresql','mysql','sqlite','mongodb','redis','elasticsearch',
    'cassandra','dynamodb','snowflake','bigquery',
    'pandas','numpy','matplotlib','seaborn','plotly',
    'machine learning','deep learning','nlp','computer vision','llm',
    'tensorflow','pytorch','scikit-learn','keras','hugging face',
    'langchain','openai','generative ai','rag',
    'aws','azure','gcp','google cloud','ec2','lambda','s3',
    'docker','kubernetes','terraform','ansible','helm',
    'ci/cd','jenkins','github actions','gitlab ci',
    'linux','bash','shell scripting',
    'git','github','gitlab','jira','confluence',
    'power bi','tableau','excel',
    'agile','scrum','kanban',
    'react native','flutter','ios','android',
    'kafka','rabbitmq','celery',
]


def _extract_skills(text):
    lower = text.lower()
    seen, result = set(), []
    for kw in SKILL_KEYWORDS:
        if kw in lower and kw not in seen:
            seen.add(kw)
            result.append(kw.title())
    return sorted(result)


def _extract_experience(text):
    header = re.search(r'(?i)(work\s*experience|professional\s*experience|employment|experience)', text)
    if not header:
        return []
    start = header.end()
    next_sec = re.search(r'(?i)\n(education|skills|certifications|projects|awards)', text[start:])
    chunk = text[start: start + next_sec.start() if next_sec else len(text)]
    entries = []
    for line in (l.strip() for l in chunk.split('\n') if l.strip()):
        if len(line) > 8:
            entries.append({'title': line[:120], 'company': '', 'duration': '', 'description': ''})
        if len(entries) >= 5:
            break
    return entries


def _extract_education(text):
    edu = []
    for kw in [r"bachelor", r"master", r"phd", r"b\.?tech", r"m\.?tech", r"mba", r"b\.?s", r"m\.?s"]:
        for m in re.finditer(kw, text, re.IGNORECASE):
            ctx = text[max(0, m.start()-20): min(len(text), m.end()+100)].strip()
            if ctx not in edu:
                edu.append(ctx)
    return edu or []


# ─────────────────────────────────────────────
# GITHUB DATA FETCH
# ─────────────────────────────────────────────

def get_github_data(github_url: str) -> Dict:
    """Fetch GitHub profile: bio, repos, languages, stars."""
    if not github_url:
        return {}
    match = re.search(r'github\.com/([^/\s]+)', github_url)
    if not match:
        return {}
    username = match.group(1).strip()
    headers = {'Accept': 'application/vnd.github.v3+json'}
    data = {'username': username, 'projects': [], 'bio': '', 'languages': [], 'total_stars': 0}

    try:
        r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=8)
        if r.status_code == 200:
            u = r.json()
            data['bio']          = u.get('bio') or ''
            data['location']     = u.get('location') or ''
            data['blog']         = u.get('blog') or ''
            data['followers']    = u.get('followers', 0)
            data['public_repos'] = u.get('public_repos', 0)
            data['company']      = u.get('company') or ''

        r2 = requests.get(
            f"https://api.github.com/users/{username}/repos?sort=stars&per_page=20",
            headers=headers, timeout=8
        )
        if r2.status_code == 200:
            repos = r2.json()
            lang_count = {}
            total_stars = 0
            for repo in repos:
                if repo.get('fork'):
                    continue
                stars = repo.get('stargazers_count', 0)
                lang  = repo.get('language') or ''
                total_stars += stars
                if lang:
                    lang_count[lang] = lang_count.get(lang, 0) + 1
                desc = repo.get('description') or (f"A {lang} project" if lang else "GitHub repository")
                data['projects'].append({
                    'name': repo.get('name', ''),
                    'description': desc,
                    'language': lang,
                    'stars': stars,
                    'url': repo.get('html_url', ''),
                    'topics': repo.get('topics', []),
                    'updated': repo.get('updated_at', '')[:10],
                })
            data['projects']    = sorted(data['projects'], key=lambda x: x['stars'], reverse=True)[:6]
            data['total_stars'] = total_stars
            data['languages']   = sorted(lang_count, key=lang_count.get, reverse=True)[:6]
    except Exception:
        pass
    return data


def get_github_projects(github_url: str) -> List[Dict]:
    return get_github_data(github_url).get('projects', [])


# ─────────────────────────────────────────────
# LINKEDIN PUBLIC DATA FETCH
# ─────────────────────────────────────────────

def get_linkedin_data(linkedin_url: str) -> Dict:
    """Scrape LinkedIn public profile meta tags. No login needed."""
    if not linkedin_url or 'linkedin.com' not in linkedin_url:
        return {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    data = {}
    try:
        r = requests.get(linkedin_url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            og_title = soup.find('meta', property='og:title')
            og_desc  = soup.find('meta', property='og:description')
            if og_title:
                t = og_title.get('content', '')
                if ' - ' in t:
                    parts = t.split(' - ')
                    data['name']     = parts[0].strip()
                    data['headline'] = parts[1].replace(' | LinkedIn','').strip()
                elif ' | ' in t:
                    data['name'] = t.split(' | ')[0].strip()
            if og_desc:
                data['about'] = og_desc.get('content', '')[:500]
    except Exception:
        pass
    return data


# ─────────────────────────────────────────────
# ENRICH CV WITH GITHUB + LINKEDIN
# ─────────────────────────────────────────────

def enrich_cv_with_external_data(cv_data: Dict, github_url: str = '', linkedin_url: str = '') -> Dict:
    """Merge GitHub + LinkedIn data into cv_data for top 1% output."""
    enriched = cv_data.copy()

    if github_url:
        gh = get_github_data(github_url)
        enriched['github'] = github_url
        if gh.get('bio') and not enriched.get('summary'):
            enriched['github_bio'] = gh['bio']
        if gh.get('location') and not enriched.get('location'):
            enriched['location'] = gh['location']
        existing_skills = set(s.lower() for s in enriched.get('skills', []))
        for lang in gh.get('languages', []):
            if lang.lower() not in existing_skills:
                enriched.setdefault('skills', []).append(lang)
                existing_skills.add(lang.lower())
        existing_proj = {p.get('name','').lower() for p in enriched.get('projects', [])}
        for gp in gh.get('projects', []):
            if gp['name'].lower() not in existing_proj:
                enriched.setdefault('projects', []).append({
                    'name': gp['name'], 'description': gp['description'],
                    'url': gp['url'], 'language': gp.get('language',''),
                    'stars': gp.get('stars',0), 'topics': gp.get('topics',[]),
                })
                existing_proj.add(gp['name'].lower())
        enriched['github_stats'] = {
            'followers': gh.get('followers',0),
            'repos': gh.get('public_repos',0),
            'stars': gh.get('total_stars',0),
            'languages': gh.get('languages',[]),
        }

    if linkedin_url:
        li = get_linkedin_data(linkedin_url)
        enriched['linkedin'] = linkedin_url
        if li.get('name') and enriched.get('name') in ['Professional','',None]:
            enriched['name'] = li['name']
        if li.get('headline') and not enriched.get('current_title'):
            enriched['current_title'] = li['headline']
        if li.get('location') and not enriched.get('location'):
            enriched['location'] = li['location']
        if li.get('about') and not enriched.get('summary'):
            enriched['linkedin_about'] = li['about']

    return enriched


# ─────────────────────────────────────────────
# ATS ANALYSIS
# ─────────────────────────────────────────────

def analyze_ats(cv_data: Dict, job_description: str) -> Dict:
    try:
        from llm_utils import analyze_ats_llm
        result = analyze_ats_llm(cv_data.get('raw_text',''), job_description)
        if result and result.get('score') is not None:
            return result
    except Exception:
        pass

    cv_lower  = cv_data.get('raw_text','').lower()
    job_lower = job_description.lower()
    job_kws   = [kw for kw in SKILL_KEYWORDS if kw in job_lower]
    matched   = [kw for kw in job_kws if kw in cv_lower]
    missing   = [kw for kw in job_kws if kw not in cv_lower]

    score = round((len(matched)/len(job_kws))*100) if job_kws else 65
    if not job_kws:
        if 'project' in cv_lower: score += 5
        if '%' in cv_lower: score += 10
        if len(cv_data.get('skills',[])) > 5: score += 10
    score = max(0, min(100, score))

    strengths = []
    if len(matched) > 5: strengths.append("Strong keyword alignment with job requirements.")
    if 'project' in cv_lower: strengths.append("Projects section detected — great credibility signal.")
    if any(v in cv_lower for v in ['%','increased','reduced','improved']):
        strengths.append("Quantified achievements present — excellent for recruiters.")
    if cv_data.get('github'): strengths.append("GitHub linked — shows real technical portfolio.")

    return {
        'score': score,
        'matched_skills': [s.title() for s in matched],
        'missing_skills': [s.title() for s in missing[:10]],
        'semantic_gaps': [],
        'strengths': strengths,
        'tips': _generate_tips(cv_data, missing, cv_lower),
        'experience_match': score,
        'keyword_density': 'high' if score>75 else 'medium' if score>50 else 'low',
    }


def _generate_tips(cv_data, missing, cv_lower):
    resources = {
        'docker': 'Play With Docker (free)', 'aws': 'AWS Free Tier + freeCodeCamp',
        'kubernetes': 'Kubernetes.io tutorial', 'python': 'Python.org + freeCodeCamp',
        'javascript': 'JavaScript.info (free)', 'react': 'react.dev official',
        'sql': 'SQLBolt (free)', 'machine learning': 'Andrew Ng Coursera (audit)',
    }
    tips = []
    for skill in missing[:4]:
        res = resources.get(skill.lower(), 'YouTube + freeCodeCamp')
        tips.append(f"Add <strong>{skill.title()}</strong> — Learn: {res}")
    if 'project' not in cv_lower:
        tips.append("Add a <strong>Projects section</strong> with GitHub links")
    if not any(v in cv_lower for v in ['%','increased','reduced','grew']):
        tips.append("<strong>Quantify achievements</strong> — e.g. 'Reduced load time by 40%'")
    if 'certification' not in cv_lower:
        tips.append("Add <strong>free certifications</strong> — Google, AWS, Meta on Coursera")
    return tips[:8]


def generate_skills_roadmap(missing_skills, target_role=""):
    try:
        from llm_utils import generate_roadmap_llm
        return generate_roadmap_llm(missing_skills, target_role)
    except Exception:
        pass
    db = {
        'python': {'weeks':'3-5','r':['Python.org','freeCodeCamp']},
        'react':  {'weeks':'3-4','r':['react.dev','freeCodeCamp React']},
        'docker': {'weeks':'2-3','r':['Docker Docs','Play With Docker']},
        'aws':    {'weeks':'6-8','r':['AWS Free Tier','freeCodeCamp AWS']},
        'sql':    {'weeks':'2-3','r':['SQLBolt','W3Schools SQL']},
    }
    md = f"# Roadmap\n*{datetime.datetime.now().strftime('%B %d, %Y')}*\n\n"
    for i, skill in enumerate(missing_skills[:8], 1):
        info = db.get(skill.lower(), {'weeks':'2-4','r':['YouTube','freeCodeCamp']})
        md += f"## {i}. {skill.title()}\n⏱️ {info['weeks']} weeks\n"
        for r in info['r']: md += f"  - {r}\n"
        md += "\n"
    return md


# ─────────────────────────────────────────────
# CV PDF — TOP 1% ATS FORMAT (FIXED)
# ─────────────────────────────────────────────

def generate_optimized_cv(cv_data: Dict, job_description: str = None, template: str = "Modern") -> bytes:
    buf = io.BytesIO()
    is_harvard = template.lower() == "harvard"

    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.55*inch, bottomMargin=0.55*inch,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
    )
    styles = getSampleStyleSheet()

    # Colors
    if is_harvard:
        CA = HexColor('#A51C30')  # Harvard Crimson
        CN = HexColor('#000000')
        CB = HexColor('#1a1a1a')
        CM = HexColor('#555555')
        FH = 'Times-Bold'
        FB = 'Times-Roman'
        FI = 'Times-Italic'
        NS = 22; NA = TA_CENTER
    else:
        CA = HexColor('#1a56db')  # Blue
        CN = HexColor('#0d1117')
        CB = HexColor('#24292f')
        CM = HexColor('#57606a')
        FH = 'Helvetica-Bold'
        FB = 'Helvetica'
        FI = 'Helvetica-Oblique'
        NS = 24; NA = TA_LEFT

    def sty(name, **kwargs):
        return ParagraphStyle(name, parent=styles['Normal'], **kwargs)

    s_name    = sty('nm',  fontSize=NS, leading=NS+4, textColor=CN, alignment=NA, fontName=FH, spaceAfter=2)
    s_title   = sty('jt',  fontSize=11, leading=14, textColor=CA, alignment=TA_CENTER, fontName=FH, spaceAfter=2)
    s_contact = sty('ct',  fontSize=8.5, leading=12, textColor=CM, alignment=TA_CENTER, fontName=FB, spaceAfter=3)
    s_section = sty('sec', fontSize=10, leading=13, textColor=CA, alignment=TA_CENTER if is_harvard else TA_LEFT,
                    fontName=FH, spaceBefore=9, spaceAfter=1)
    s_body    = sty('bd',  fontSize=9.5, leading=13.5, textColor=CB, fontName=FB, spaceAfter=2)
    s_role    = sty('rl',  fontSize=10, leading=13, textColor=CB, fontName=FH, spaceAfter=1)
    s_company = sty('co',  fontSize=9, leading=12, textColor=CA, fontName=FB, spaceAfter=1)
    s_date    = sty('dt',  fontSize=8.5, leading=11, textColor=CM, fontName=FI, spaceAfter=2)
    s_bullet  = sty('bu',  fontSize=9, leading=13, textColor=CB, fontName=FB, leftIndent=10, spaceAfter=1.5)
    s_date_r  = sty('dtr', fontSize=8.5, leading=11, textColor=CM, fontName=FI, alignment=2)  # right align

    def rule(thick=0.6):
        return HRFlowable(width='100%', color=CA, thickness=thick, spaceAfter=4, spaceBefore=0)

    def section(title):
        return [Paragraph(title.upper(), s_section), rule()]

    story = []

    # ─ HEADER ─
    name = (cv_data.get('name') or 'Professional').strip()
    jtitle = (cv_data.get('current_title') or '').strip()
    story.append(Paragraph(name.upper() if is_harvard else name, s_name))
    if jtitle:
        story.append(Paragraph(jtitle, s_title))

    # Contact row 1: email | phone | location
    r1 = [x for x in [
        cv_data.get('email'), cv_data.get('phone'), cv_data.get('location')
    ] if x]
    if r1:
        story.append(Paragraph('  |  '.join(r1), s_contact))

    # Contact row 2: linkedin | github
    r2_parts = []
    if cv_data.get('linkedin'):
        r2_parts.append(cv_data['linkedin'].replace('https://','').replace('http://',''))
    if cv_data.get('github'):
        r2_parts.append(cv_data['github'].replace('https://','').replace('http://',''))
    if r2_parts:
        story.append(Paragraph('  |  '.join(r2_parts), s_contact))

    story.append(HRFlowable(width='100%', color=CA, thickness=1.5, spaceAfter=5, spaceBefore=4))

    # ─ SUMMARY ─
    story.extend(section("PROFESSIONAL SUMMARY"))
    try:
        from llm_utils import generate_summary_llm
        summary = generate_summary_llm(cv_data, job_description)
    except Exception:
        skills_str = ', '.join(cv_data.get('skills',[])[:5]) or 'various technologies'
        t = cv_data.get('current_title','professional')
        fallback_text = cv_data.get('linkedin_about','') or cv_data.get('github_bio','')
        summary = fallback_text[:250] if fallback_text else (
            f"Results-driven {t} with expertise in {skills_str}. "
            "Passionate about building scalable solutions and delivering measurable impact."
        )
    story.append(Paragraph(summary, s_body))

    # ─ SKILLS ─
    skills = cv_data.get('skills', [])
    if skills:
        story.extend(section("TECHNICAL SKILLS"))
        if job_description:
            jd_l = job_description.lower()
            matched = [s for s in skills if s.lower() in jd_l]
            rest    = [s for s in skills if s.lower() not in jd_l]
            ordered = matched + rest
        else:
            ordered = skills
        # Rows of 6
        for i in range(0, min(len(ordered), 24), 6):
            chunk = ordered[i:i+6]
            story.append(Paragraph('  •  '.join(chunk), s_body))

    # ─ EXPERIENCE ─
    experience = cv_data.get('experience', [])
    if experience:
        story.extend(section("PROFESSIONAL EXPERIENCE"))
        for exp in experience[:5]:
            role    = (exp.get('title') or '').strip()
            company = (exp.get('company') or '').strip()
            dur     = (exp.get('duration') or '').strip()
            desc    = (exp.get('description') or '').strip()
            if not role:
                continue

            # Role + date on same line using Table
            if dur:
                tbl = Table(
                    [[Paragraph(f"<b>{role}</b>", s_role), Paragraph(dur, s_date_r)]],
                    colWidths=[4.4*inch, 2.3*inch]
                )
                tbl.setStyle(TableStyle([
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
                    ('TOPPADDING',(0,0),(-1,-1),0),  ('BOTTOMPADDING',(0,0),(-1,-1),1),
                ]))
                story.append(tbl)
            else:
                story.append(Paragraph(f"<b>{role}</b>", s_role))

            if company:
                story.append(Paragraph(company, s_company))

            if desc:
                bullets = [b.strip() for b in re.split(r'[\n;•\-]', desc) if len(b.strip()) > 10]
                if bullets:
                    for b in bullets[:4]:
                        story.append(Paragraph(f"• {b}", s_bullet))
                else:
                    story.append(Paragraph(f"• {desc[:300]}", s_bullet))
            story.append(Spacer(1, 3))

    # ─ PROJECTS ─
    projects = cv_data.get('projects', [])
    if projects:
        story.extend(section("PROJECTS"))
        for proj in projects[:5]:
            pname  = (proj.get('name') or '').strip()
            pdesc  = (proj.get('description') or '').strip()
            plang  = (proj.get('language') or '').strip()
            purl   = (proj.get('url') or '').strip()
            pstars = proj.get('stars', 0) or 0
            if not pname:
                continue
            meta = []
            if plang:  meta.append(plang)
            if pstars: meta.append(f"★ {pstars}")
            name_line = f"<b>{pname}</b>" + (f"  <font size='8' color='#{CM.hexval()[2:]}'>[{', '.join(meta)}]</font>" if meta else "")
            story.append(Paragraph(name_line, s_role))
            if pdesc:
                story.append(Paragraph(f"• {pdesc[:200]}", s_bullet))
            if purl:
                story.append(Paragraph(f"<font size='8' color='#{CA.hexval()[2:]}'>{purl.replace('https://','')}</font>", s_date))
            story.append(Spacer(1, 3))

    # ─ EDUCATION ─
    education = cv_data.get('education', [])
    if education:
        story.extend(section("EDUCATION"))
        edu_structured = cv_data.get('education_structured', [])
        if edu_structured:
            for e in edu_structured[:3]:
                degree = (e.get('degree') or '').strip()
                inst   = (e.get('institution') or '').strip()
                year   = (e.get('year') or '').strip()
                if degree or inst:
                    if year:
                        tbl = Table(
                            [[Paragraph(f"<b>{degree}</b>", s_role), Paragraph(year, s_date_r)]],
                            colWidths=[4.8*inch, 1.9*inch]
                        )
                        tbl.setStyle(TableStyle([
                            ('VALIGN',(0,0),(-1,-1),'TOP'),
                            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1),
                        ]))
                        story.append(tbl)
                    else:
                        story.append(Paragraph(f"<b>{degree}</b>", s_role))
                    if inst:
                        story.append(Paragraph(inst, s_company))
                    story.append(Spacer(1, 2))
        else:
            for e in education[:3]:
                story.append(Paragraph(f"• {str(e)[:120]}", s_body))

    # ─ CERTIFICATIONS ─
    certs = cv_data.get('certifications', [])
    if certs:
        story.extend(section("CERTIFICATIONS"))
        story.append(Paragraph('  |  '.join(str(c) for c in certs[:6]), s_body))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────
# HR FINDER
# ─────────────────────────────────────────────

def find_hr_contacts(company_name: str, role: str = "") -> List[Dict]:
    """Find HR/Recruiter contacts at a company using free public methods."""
    if not company_name:
        return []
    company_slug   = re.sub(r'[^a-z0-9]', '', company_name.lower())
    company_domain = f"{company_slug}.com"
    contacts = []

    # LinkedIn search URLs
    hr_titles = ["Technical Recruiter", "HR Manager", "Talent Acquisition", "People Operations", "Hiring Manager"]
    for title in hr_titles[:4]:
        q = f"{title} {company_name}".replace(' ', '%20')
        contacts.append({
            'type': 'linkedin_search',
            'name': f"{title} at {company_name}",
            'title': title,
            'company': company_name,
            'linkedin_search_url': f"https://www.linkedin.com/search/results/people/?keywords={q}&origin=GLOBAL_SEARCH_HEADER",
            'action': 'Open link → connect + message',
        })

    # Common email patterns
    email_patterns = [
        f"hr@{company_domain}", f"careers@{company_domain}",
        f"talent@{company_domain}", f"recruiting@{company_domain}",
        f"jobs@{company_domain}", f"hiring@{company_domain}",
    ]
    for ep in email_patterns:
        contacts.append({
            'type': 'email_pattern',
            'email': ep,
            'company': company_name,
            'note': 'Common HR email pattern — verify with tools like Hunter.io (free)',
        })

    return contacts


def generate_hr_email_templates(cv_data: Dict, company: str, role: str, hr_name: str = "Hiring Manager") -> Dict:
    """Generate cold outreach, follow-up x2, and thank you email templates."""
    name   = cv_data.get('name', 'Candidate')
    title  = cv_data.get('current_title', 'Professional')
    skills = ', '.join(cv_data.get('skills', [])[:5])
    email  = cv_data.get('email', '')
    today  = datetime.date.today().strftime("%B %d, %Y")

    try:
        from llm_utils import generate_hr_emails_llm
        return generate_hr_emails_llm(cv_data, company, role, hr_name)
    except Exception:
        pass

    cold = f"""Subject: {role} — {name} ({title})

Dear {hr_name},

I hope this finds you well. I'm a {title} with expertise in {skills}, and I'm very interested in the {role} position at {company}.

What draws me specifically to {company} is your reputation for technical excellence and innovation. I believe my background aligns strongly with what your team needs — I've been building [mention a specific relevant achievement] and would love to bring that experience to your team.

My CV is attached for your review. I'd welcome a 15-minute call at your convenience.

Thank you for your time.

Best regards,
{name}
{email} | {today}"""

    followup_1 = f"""Subject: Following Up — {role} Application — {name}

Dear {hr_name},

I'm following up on my application for the {role} position I sent last week.

I remain genuinely excited about the opportunity to join {company}. My experience with {skills} maps closely to what you're building, and I'd love to discuss further.

Happy to provide any additional information you might need.

Thank you,
{name}
{email}"""

    followup_2 = f"""Subject: Quick Follow-Up — {role} — {name}

Hi {hr_name},

I wanted to reach out one more time about the {role} role at {company}.

I'm still very interested and believe I could add immediate value. If this isn't the right timing, I'd also be glad to be considered for future openings.

Thanks for your consideration either way.

{name}
{email}"""

    thank_you = f"""Subject: Thank You — {role} Interview — {name}

Dear {hr_name},

Thank you for taking the time to interview me today for the {role} position.

I really enjoyed our conversation — especially learning about [specific topic from interview]. It reinforced my excitement about joining {company}.

I'm confident my experience in {skills} will help me contribute meaningfully from day one. Please feel free to reach out if you need anything else from my side.

Looking forward to next steps!

Warm regards,
{name}
{email}"""

    return {
        'cold_email':  cold,
        'follow_up_1': followup_1,
        'follow_up_2': followup_2,
        'thank_you':   thank_you,
    }


# ─────────────────────────────────────────────
# PORTFOLIO HTML — TOP 1%
# ─────────────────────────────────────────────

def generate_portfolio(cv_data: Dict) -> bytes:
    name     = (cv_data.get('name') or 'Professional').strip()
    email    = (cv_data.get('email') or '').strip()
    phone    = (cv_data.get('phone') or '').strip()
    linkedin = (cv_data.get('linkedin') or '').strip()
    github   = (cv_data.get('github') or '').strip()
    title    = (cv_data.get('current_title') or 'Software Developer').strip()
    skills   = cv_data.get('skills', [])
    exp      = cv_data.get('experience', [])
    edu      = cv_data.get('education', [])
    projects = cv_data.get('projects', [])
    certs    = cv_data.get('certifications', [])
    years    = cv_data.get('years_experience', 0) or 0
    gh_stats = cv_data.get('github_stats', {})
    gh_bio   = (cv_data.get('github_bio') or '').strip()
    li_about = (cv_data.get('linkedin_about') or '').strip()
    about    = li_about or gh_bio or (
        f"I'm a {title} passionate about building clean, scalable software. "
        f"I specialize in {', '.join(skills[:3]) if skills else 'modern technologies'} "
        "and thrive in collaborative environments."
    )

    initials = ''.join(w[0].upper() for w in name.split()[:2]) if name else 'CB'
    yr = datetime.datetime.now().year
    stat_num = f"{years}+" if years else str(len(exp))
    stat_lbl = "Years Exp" if years else "Roles"

    # ── Categorized skill grid ──
    skill_cats = {
        'Languages':  ['Python','Java','Javascript','Typescript','Go','Golang','Rust','Swift','Kotlin','C++','C#','Ruby','Php','Scala'],
        'Frontend':   ['React','Angular','Vue.Js','Next.Js','Svelte','Html','Css','Tailwind Css','Bootstrap','Figma','Adobe Xd'],
        'Backend':    ['Node.Js','Express','Django','Flask','Fastapi','Spring Boot','Graphql','Rest Api','Microservices'],
        'Data & AI':  ['Machine Learning','Pandas','Numpy','Tensorflow','Pytorch','Nlp','Sql','Mongodb','Postgresql'],
        'Cloud/DevOps':['Docker','Kubernetes','Aws','Azure','Gcp','Terraform','Ci/Cd','Jenkins','Github Actions','Linux'],
        'Tools':      ['Git','Github','Jira','Agile','Scrum','Confluence','Tableau','Power Bi'],
    }
    user_skill_set = set(s.lower() for s in skills)
    skill_grid = ""
    for cat, cat_skills in skill_cats.items():
        matched = [s for s in cat_skills if s.lower() in user_skill_set]
        if matched:
            pills = "".join(f'<span class="sp">{s}</span>' for s in matched)
            skill_grid += f'<div class="sc"><div class="sc-lbl">{cat}</div><div class="sc-pills">{pills}</div></div>'
    if not skill_grid:
        pills = "".join(f'<span class="sp">{s}</span>' for s in skills[:20])
        skill_grid = f'<div class="sc"><div class="sc-lbl">Skills</div><div class="sc-pills">{pills}</div></div>'

    # ── Experience timeline ──
    exp_html = ""
    for i, e in enumerate(exp[:6]):
        role    = (e.get('title') or '').strip()
        company = (e.get('company') or '').strip()
        dur     = (e.get('duration') or '').strip()
        desc    = (e.get('description') or '').strip()
        active  = 'active' if i == 0 else ''
        if not role: continue
        exp_html += f"""
      <div class="tl {active}">
        <div class="tl-left"><div class="tl-dot"></div></div>
        <div class="tl-card">
          <div class="tl-top">
            <div><div class="tl-role">{role}</div>{"<div class='tl-co'>"+company+"</div>" if company else ""}</div>
            {"<div class='tl-dur'>"+dur+"</div>" if dur else ""}
          </div>
          {"<p class='tl-desc'>"+desc[:200]+"</p>" if desc else ""}
        </div>
      </div>"""

    # ── Project cards ──
    proj_html = ""
    for p in projects[:6]:
        pn = (p.get('name') or '').strip()
        pd = (p.get('description') or '').strip()
        pl = (p.get('language') or '').strip()
        pu = (p.get('url') or '').strip()
        ps = p.get('stars', 0) or 0
        pt = p.get('topics', []) or []
        if not pn: continue
        topics = "".join(f'<span class="tp">{t}</span>' for t in pt[:4])
        proj_html += f"""
      <div class="pc">
        <div class="pc-top">
          <div class="pc-icon">{pn[0].upper()}</div>
          <div class="pc-meta">{"<span class='lang'>"+pl+"</span>" if pl else ""}{"<span class='stars'>★ "+str(ps)+"</span>" if ps else ""}</div>
        </div>
        <div class="pc-name">{pn}</div>
        <p class="pc-desc">{pd[:180]}</p>
        {"<div class='pc-topics'>"+topics+"</div>" if topics else ""}
        {"<a href='"+pu+"' target='_blank' class='pc-link'>View →</a>" if pu else ""}
      </div>"""

    # ── Education ──
    edu_html = ""
    edu_str  = cv_data.get('education_structured', [])
    if edu_str:
        for e in edu_str[:3]:
            dg = (e.get('degree') or '').strip()
            inst = (e.get('institution') or '').strip()
            yr2  = (e.get('year') or '').strip()
            edu_html += f'<div class="edu"><span class="edu-i">🎓</span><div><strong>{dg}</strong>{"<br/><span class=\\'edu-inst\\'>" + inst + " · " + yr2 + "</span>" if inst else ""}</div></div>'
    else:
        for e in edu[:3]:
            edu_html += f'<div class="edu"><span class="edu-i">🎓</span><div>{str(e)[:100]}</div></div>'

    certs_html = "".join(f'<span class="cert">{c}</span>' for c in certs[:8])

    # ── GitHub stats ──
    ghbox = ""
    if gh_stats:
        ghbox = f"""<div class="gh-box">
      <div class="gh-s"><span class="gh-n">{gh_stats.get('repos',0)}</span><span class="gh-l">Repos</span></div>
      <div class="gh-s"><span class="gh-n">{gh_stats.get('stars',0)}</span><span class="gh-l">Stars</span></div>
      <div class="gh-s"><span class="gh-n">{gh_stats.get('followers',0)}</span><span class="gh-l">Followers</span></div>
    </div>"""

    # ── Social buttons ──
    socials = ""
    if linkedin: socials += f'<a href="{linkedin}" target="_blank" class="sb li">LinkedIn</a>'
    if github:   socials += f'<a href="{github}" target="_blank" class="sb gh">GitHub</a>'
    if email:    socials += f'<a href="mailto:{email}" class="sb em">Email</a>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="description" content="{name} — {title}"/>
<title>{name} · {title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--bg:#07070e;--s1:#0c0c18;--card:#131325;--bd:rgba(255,255,255,.06);
  --a:#5b6af9;--a2:#f95b8d;--a3:#5bf9c0;--t:#eeeef8;--m:#6060a0;
  --fh:'Plus Jakarta Sans',sans-serif;--fi:'Instrument Serif',serif;}}
html{{scroll-behavior:smooth;}}
body{{font-family:var(--fh);background:var(--bg);color:var(--t);line-height:1.65;overflow-x:hidden;}}
.blob{{position:fixed;border-radius:50%;filter:blur(110px);opacity:.07;pointer-events:none;}}
.b1{{width:700px;height:700px;background:var(--a);top:-200px;left:-150px;animation:d 28s infinite alternate;}}
.b2{{width:600px;height:600px;background:var(--a2);bottom:-200px;right:-150px;animation:d 22s infinite alternate-reverse;}}
@keyframes d{{to{{transform:translate(40px,30px) scale(1.06);}}}}
nav{{position:fixed;top:0;width:100%;z-index:100;padding:.9rem 0;background:rgba(7,7,14,.75);backdrop-filter:blur(24px);border-bottom:1px solid var(--bd);}}
.ni{{max-width:1120px;margin:0 auto;padding:0 2rem;display:flex;justify-content:space-between;align-items:center;}}
.nl a{{color:#fff;text-decoration:none;font-weight:800;font-size:1.1rem;}}
.nr a{{color:var(--m);text-decoration:none;font-size:.84rem;font-weight:500;margin-left:1.8rem;transition:color .2s;}}
.nr a:hover{{color:#fff;}}
.hero{{min-height:100vh;display:flex;align-items:center;padding:8rem 2rem 5rem;}}
.hi{{max-width:1120px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 380px;gap:5rem;align-items:center;}}
.badge{{display:inline-flex;align-items:center;gap:.4rem;padding:5px 14px;background:rgba(91,106,249,.1);border:1px solid rgba(91,106,249,.2);border-radius:20px;color:#9aa3fc;font-size:.77rem;font-weight:700;letter-spacing:.8px;text-transform:uppercase;margin-bottom:1.4rem;}}
.badge::before{{content:'';width:6px;height:6px;border-radius:50%;background:var(--a);box-shadow:0 0 8px var(--a);}}
h1{{font-family:var(--fh);font-size:clamp(3rem,5.5vw,5rem);font-weight:800;line-height:1.08;letter-spacing:-2px;color:#fff;margin-bottom:1.2rem;}}
h1 em{{font-family:var(--fi);font-style:italic;background:linear-gradient(135deg,var(--a),var(--a2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.bio{{color:var(--m);font-size:1.05rem;line-height:1.8;margin-bottom:2.5rem;max-width:520px;}}
.btns{{display:flex;gap:.9rem;flex-wrap:wrap;}}
.b-cta{{padding:.85rem 2rem;background:linear-gradient(135deg,var(--a),#7c55f9);color:#fff;border-radius:10px;text-decoration:none;font-weight:700;font-size:.9rem;transition:all .25s;box-shadow:0 4px 20px rgba(91,106,249,.25);}}
.b-cta:hover{{transform:translateY(-2px);box-shadow:0 8px 30px rgba(91,106,249,.4);}}
.b-ghost{{padding:.85rem 2rem;background:var(--card);border:1px solid var(--bd);color:var(--t);border-radius:10px;text-decoration:none;font-weight:600;font-size:.9rem;transition:all .25s;}}
.b-ghost:hover{{border-color:rgba(255,255,255,.15);transform:translateY(-2px);}}
.hcard{{background:var(--card);border:1px solid var(--bd);border-radius:20px;padding:2rem;}}
.hc-av{{width:68px;height:68px;border-radius:50%;background:linear-gradient(135deg,var(--a),var(--a2));display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:800;color:#fff;margin-bottom:1.2rem;}}
.hc-name{{font-weight:700;font-size:1.05rem;color:#fff;}}
.hc-title{{font-size:.84rem;color:var(--a);font-weight:600;margin-bottom:1.3rem;}}
.hc-grid{{display:grid;grid-template-columns:1fr 1fr;gap:.7rem;}}
.hstat{{background:rgba(255,255,255,.03);border:1px solid var(--bd);border-radius:10px;padding:.9rem;text-align:center;}}
.hn{{font-size:1.5rem;font-weight:800;color:#fff;line-height:1;}}
.hl{{font-size:.68rem;color:var(--m);margin-top:2px;text-transform:uppercase;letter-spacing:.5px;}}
.gh-box{{display:flex;gap:.6rem;margin-top:.7rem;}}
.gh-s{{flex:1;background:rgba(255,255,255,.03);border:1px solid var(--bd);border-radius:8px;padding:.6rem;text-align:center;}}
.gh-n{{display:block;font-weight:700;font-size:1rem;color:#fff;}}
.gh-l{{font-size:.65rem;color:var(--m);}}
section{{padding:6rem 2rem;}}
.si{{max-width:1120px;margin:0 auto;}}
.eyebrow{{font-size:.74rem;color:var(--a);letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:.4rem;}}
.sh{{font-family:var(--fh);font-size:clamp(1.8rem,3.5vw,2.6rem);font-weight:800;color:#fff;letter-spacing:-1px;margin-bottom:2.5rem;}}
#skills{{background:var(--s1);}}
.sc{{margin-bottom:1.6rem;}}
.sc-lbl{{font-size:.74rem;color:var(--m);text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:.6rem;}}
.sc-pills{{display:flex;flex-wrap:wrap;gap:.45rem;}}
.sp{{padding:4px 13px;background:var(--card);border:1px solid var(--bd);border-radius:6px;font-size:.82rem;color:#d0d0ee;font-weight:500;transition:all .2s;}}
.sp:hover{{border-color:rgba(91,106,249,.4);color:#fff;}}
.tl{{display:grid;grid-template-columns:28px 1fr;gap:0;margin-bottom:1.8rem;}}
.tl-left{{display:flex;flex-direction:column;align-items:center;padding-top:4px;}}
.tl-dot{{width:11px;height:11px;border-radius:50%;background:var(--s1);border:2px solid var(--m);flex-shrink:0;transition:all .3s;}}
.tl.active .tl-dot{{background:var(--a);border-color:var(--a);box-shadow:0 0 12px rgba(91,106,249,.6);}}
.tl-left::after{{content:'';flex:1;width:2px;background:linear-gradient(var(--bd),transparent);margin-top:5px;}}
.tl-card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1.3rem 1.5rem;margin-left:.9rem;transition:all .25s;}}
.tl-card:hover{{border-color:rgba(91,106,249,.25);}}
.tl-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:.8rem;margin-bottom:.4rem;}}
.tl-role{{font-weight:700;font-size:.98rem;color:#fff;}}
.tl-co{{color:var(--a);font-size:.83rem;font-weight:600;margin-top:2px;}}
.tl-dur{{font-size:.75rem;color:var(--m);white-space:nowrap;padding-top:2px;}}
.tl-desc{{font-size:.86rem;color:var(--m);line-height:1.65;}}
#projects{{background:var(--s1);}}
.pg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.4rem;}}
.pc{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:1.7rem;display:flex;flex-direction:column;gap:.7rem;transition:all .3s;}}
.pc:hover{{border-color:rgba(91,106,249,.3);transform:translateY(-4px);box-shadow:0 12px 30px rgba(0,0,0,.5);}}
.pc-top{{display:flex;justify-content:space-between;align-items:center;}}
.pc-icon{{width:40px;height:40px;border-radius:9px;background:linear-gradient(135deg,rgba(91,106,249,.2),rgba(249,91,141,.2));display:flex;align-items:center;justify-content:center;font-size:1.05rem;font-weight:800;color:#fff;border:1px solid var(--bd);}}
.pc-meta{{display:flex;gap:.4rem;align-items:center;}}
.lang{{padding:3px 8px;background:rgba(91,249,192,.07);border:1px solid rgba(91,249,192,.18);border-radius:4px;color:var(--a3);font-size:.7rem;font-weight:600;}}
.stars{{color:#f9c85b;font-size:.78rem;}}
.pc-name{{font-weight:700;font-size:.97rem;color:#fff;}}
.pc-desc{{font-size:.85rem;color:var(--m);line-height:1.65;flex:1;}}
.pc-topics{{display:flex;flex-wrap:wrap;gap:.35rem;}}
.tp{{padding:2px 8px;background:rgba(91,106,249,.07);border:1px solid rgba(91,106,249,.15);border-radius:4px;color:#9aa3fc;font-size:.68rem;}}
.pc-link{{color:var(--a);text-decoration:none;font-size:.82rem;font-weight:700;align-self:flex-start;transition:color .2s;}}
.pc-link:hover{{color:#9aa3fc;}}
.edu{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:1.1rem 1.4rem;display:flex;align-items:center;gap:.9rem;margin-bottom:.7rem;transition:all .25s;}}
.edu:hover{{border-color:rgba(91,106,249,.25);}}
.edu-i{{font-size:1.3rem;}}
.edu strong{{color:#fff;font-size:.93rem;}}
.edu-inst{{color:var(--m);font-size:.82rem;}}
.cert{{display:inline-block;padding:5px 13px;margin:3px;background:rgba(91,106,249,.07);border:1px solid rgba(91,106,249,.17);border-radius:20px;color:#9aa3fc;font-size:.78rem;font-weight:600;}}
#contact{{background:var(--s1);text-align:center;}}
.cw{{max-width:560px;margin:0 auto;}}
.cav{{width:88px;height:88px;border-radius:50%;background:linear-gradient(135deg,var(--a),var(--a2));display:flex;align-items:center;justify-content:center;font-size:1.9rem;font-weight:800;color:#fff;margin:0 auto 1.4rem;}}
.cw h2{{font-family:var(--fh);font-size:2rem;font-weight:800;color:#fff;margin-bottom:.5rem;letter-spacing:-1px;}}
.cw p{{color:var(--m);margin-bottom:2rem;line-height:1.7;}}
.socs{{display:flex;justify-content:center;flex-wrap:wrap;gap:.7rem;}}
.sb{{padding:.72rem 1.7rem;border-radius:9px;text-decoration:none;font-weight:700;font-size:.86rem;transition:all .25s;border:1px solid var(--bd);}}
.sb.li{{background:rgba(10,102,194,.12);color:#7abfff;border-color:rgba(10,102,194,.25);}}
.sb.li:hover{{background:rgba(10,102,194,.22);transform:translateY(-2px);}}
.sb.gh{{background:rgba(255,255,255,.05);color:#fff;}}
.sb.gh:hover{{background:rgba(255,255,255,.1);transform:translateY(-2px);}}
.sb.em{{background:rgba(249,91,141,.08);color:#f997ba;border-color:rgba(249,91,141,.2);}}
.sb.em:hover{{background:rgba(249,91,141,.16);transform:translateY(-2px);}}
footer{{text-align:center;padding:1.8rem;font-size:.78rem;color:var(--m);border-top:1px solid var(--bd);}}
@keyframes fu{{from{{opacity:0;transform:translateY(26px);}}to{{opacity:1;transform:none;}}}}
.f{{animation:fu .8s cubic-bezier(.16,1,.3,1) both;}}
.d1{{animation-delay:.1s;}}.d2{{animation-delay:.22s;}}.d3{{animation-delay:.34s;}}.d4{{animation-delay:.46s;}}
.rv{{opacity:0;transform:translateY(20px);transition:opacity .7s cubic-bezier(.16,1,.3,1),transform .7s cubic-bezier(.16,1,.3,1);}}
.rv.in{{opacity:1;transform:none;}}
@media(max-width:860px){{.hi{{grid-template-columns:1fr;gap:3rem;}} h1{{font-size:2.8rem;}} .nr{{display:none;}}}}
::-webkit-scrollbar{{width:4px;}}::-webkit-scrollbar-track{{background:var(--bg);}}::-webkit-scrollbar-thumb{{background:#1f1f3a;border-radius:3px;}}
</style>
</head>
<body>
<div class="blob b1"></div><div class="blob b2"></div>
<nav>
  <div class="ni">
    <div class="nl"><a href="#">{initials}</a></div>
    <div class="nr">
      <a href="#about">About</a><a href="#skills">Skills</a><a href="#experience">Experience</a>
      {"<a href='#projects'>Projects</a>" if projects else ""}<a href="#education">Education</a><a href="#contact">Contact</a>
    </div>
  </div>
</nav>

<section class="hero" id="home">
  <div class="hi">
    <div>
      <div class="badge f d1">{title}</div>
      <h1 class="f d2">Hi, I'm<br/><em>{name}</em></h1>
      <p class="bio f d3">{about[:200]}</p>
      <div class="btns f d4">
        <a href="#contact" class="b-cta">Get In Touch →</a>
        <a href="{"#projects" if projects else "#skills"}" class="b-ghost">{"View Projects" if projects else "View Skills"}</a>
      </div>
    </div>
    <div class="hcard f d3">
      <div class="hc-av">{initials}</div>
      <div class="hc-name">{name}</div>
      <div class="hc-title">{title}</div>
      <div class="hc-grid">
        <div class="hstat"><div class="hn">{stat_num}</div><div class="hl">{stat_lbl}</div></div>
        <div class="hstat"><div class="hn">{len(skills)}</div><div class="hl">Skills</div></div>
        <div class="hstat"><div class="hn">{len(projects) or len(exp)}</div><div class="hl">{"Projects" if projects else "Companies"}</div></div>
        <div class="hstat"><div class="hn">{len(certs) or len(edu)}</div><div class="hl">{"Certs" if certs else "Degrees"}</div></div>
      </div>
      {ghbox}
    </div>
  </div>
</section>

<section id="about" class="rv">
  <div class="si">
    <div class="eyebrow">About</div>
    <div class="sh">The story so far.</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:3rem;">
      <p style="color:var(--m);font-size:1.05rem;line-height:1.85;">{about}</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:.9rem;">
        <div class="hstat"><div class="hn">{stat_num}</div><div class="hl">{stat_lbl}</div></div>
        <div class="hstat"><div class="hn">{len(skills)}</div><div class="hl">Technologies</div></div>
        <div class="hstat"><div class="hn">{len(projects) or len(exp)}</div><div class="hl">{"Projects" if projects else "Roles"}</div></div>
        <div class="hstat"><div class="hn">{len(edu)}</div><div class="hl">Degrees</div></div>
      </div>
    </div>
  </div>
</section>

<section id="skills" class="rv">
  <div class="si">
    <div class="eyebrow">Expertise</div>
    <div class="sh">Technical Skills</div>
    {skill_grid}
  </div>
</section>

<section id="experience" class="rv">
  <div class="si">
    <div class="eyebrow">Career</div>
    <div class="sh">Experience</div>
    {exp_html or '<p style="color:var(--m)">Experience details on request.</p>'}
  </div>
</section>

{"<section id='projects' class='rv'><div class='si'><div class='eyebrow'>Work</div><div class='sh'>Projects</div><div class='pg'>"+proj_html+"</div></div></section>" if projects else ""}

<section id="education" class="rv">
  <div class="si">
    <div class="eyebrow">Background</div>
    <div class="sh">Education</div>
    {edu_html or '<p style="color:var(--m)">Education details on request.</p>'}
    {f"<div style='margin-top:1.8rem;'><div style='font-size:.72rem;color:var(--m);text-transform:uppercase;letter-spacing:1px;margin-bottom:.7rem;'>Certifications</div>{certs_html}</div>" if certs else ""}
  </div>
</section>

<section id="contact" class="rv">
  <div class="si">
    <div class="cw">
      <div class="eyebrow" style="text-align:center;">Contact</div>
      <div class="sh" style="text-align:center;">Let's work together.</div>
      <div class="cav">{initials}</div>
      <h2>{name}</h2>
      <p>Open to new opportunities and collaborations.{"<br/>"+email if email else ""}</p>
      <div class="socs">{socials}</div>
    </div>
  </div>
</section>

<footer>Built with CareerBoost AI · {name} · {yr}</footer>

<script>
  const o=new IntersectionObserver(e=>e.forEach(x=>{{if(x.isIntersecting)x.target.classList.add('in')}}),{{threshold:.1}});
  document.querySelectorAll('.rv').forEach(el=>o.observe(el));
</script>
</body>
</html>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', html)
    buf.seek(0)
    return buf.getvalue()
