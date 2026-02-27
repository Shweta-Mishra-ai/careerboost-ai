"""
utils.py — CareerBoost AI core utilities (LLM-powered overhaul)

Parsing: PyMuPDF (PDF), python-docx (DOCX), plain text
AI:      Groq LLaMA 3.1 via llm_utils.py
PDF gen: ReportLab
"""

import fitz  # PyMuPDF
import docx
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
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
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF parse error: {e}")


def parse_docx(file) -> str:
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    except Exception as e:
        raise Exception(f"DOCX parse error: {e}")


def parse_txt(file) -> str:
    try:
        raw = file.read()
        return (raw.decode('utf-8') if isinstance(raw, bytes) else raw).strip()
    except Exception as e:
        raise Exception(f"TXT parse error: {e}")


def parse_cv(file) -> Dict:
    """
    Parse a CV file (PDF/DOCX/TXT) and extract structured data using LLM.
    Falls back to regex extraction if LLM is unavailable.
    """
    name = file.name.lower()
    if name.endswith('.pdf'):
        text = parse_pdf(file)
    elif name.endswith(('.docx', '.doc')):
        text = parse_docx(file)
    elif name.endswith('.txt'):
        text = parse_txt(file)
    else:
        raise Exception("Unsupported format. Use PDF, DOC, DOCX, or TXT.")

    if not text.strip():
        raise Exception("CV file appears to be empty or unreadable.")

    # Try LLM-powered extraction first
    try:
        from llm_utils import extract_cv_data_llm
        llm_data = extract_cv_data_llm(text)
        if llm_data and llm_data.get("name"):
            # Normalize experience to match expected format
            llm_data["raw_text"] = text
            llm_data["skills"] = llm_data.get("skills", [])
            # Normalize education list (could be list of dicts or strings)
            edu = llm_data.get("education", [])
            if edu and isinstance(edu[0], dict):
                llm_data["education_structured"] = edu
                llm_data["education"] = [
                    f"{e.get('degree', '')} — {e.get('institution', '')} ({e.get('year', '')})".strip(" —()")
                    for e in edu
                ]
            return llm_data
    except Exception:
        pass  # Fall back to regex

    # ── Regex fallback ──
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
        'current_title': '',
        'years_experience': 0,
        'location': '',
    }


# ─────────────────────────────────────────────
# REGEX EXTRACTION HELPERS (fallback)
# ─────────────────────────────────────────────

def _extract_name(text: str) -> str:
    """Best-effort name extraction: first non-header, 2-4 word line."""
    for line in (l.strip() for l in text.split('\n') if l.strip()):
        if 2 <= len(line.split()) <= 4 and '@' not in line and len(line) > 3:
            if not re.match(r'(?i)(experience|education|skills|summary|objective|contact|profile|about)', line):
                return line
    return "Professional"


def _extract_email(text: str) -> str:
    m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    return m.group(0) if m else ""


def _extract_phone(text: str) -> str:
    m = re.search(r'(\+?\d{1,3}[\-.\s]?)?(\(?\d{2,4}\)?[\-.\s]?)?\d{3,4}[\-.\s]?\d{4}', text)
    return m.group(0).strip() if m else ""


def _extract_linkedin(text: str) -> str:
    m = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    return f"https://{m.group(0)}" if m else ""


def _extract_github(text: str) -> str:
    m = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)
    return f"https://{m.group(0)}" if m else ""


# Expanded skill keyword list (~200 skills)
SKILL_KEYWORDS = [
    # Languages
    'python', 'java', 'javascript', 'typescript', 'go', 'golang', 'rust', 'swift',
    'kotlin', 'c++', 'c#', '.net', 'ruby', 'php', 'scala', 'r', 'matlab',
    # Frontend
    'react', 'angular', 'vue.js', 'next.js', 'nuxt', 'svelte', 'html', 'css',
    'sass', 'less', 'bootstrap', 'tailwind css', 'material ui', 'figma', 'adobe xd',
    'ui/ux', 'wireframing', 'prototyping', 'framer',
    # Backend
    'node.js', 'express', 'django', 'flask', 'fastapi', 'spring boot', 'laravel',
    'ruby on rails', 'graphql', 'rest api', 'websocket', 'grpc', 'microservices',
    # Data
    'sql', 'postgresql', 'mysql', 'sqlite', 'mongodb', 'redis', 'elasticsearch',
    'cassandra', 'dynamodb', 'snowflake', 'bigquery', 'dbt',
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
    # ML/AI
    'machine learning', 'deep learning', 'nlp', 'computer vision', 'llm',
    'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'hugging face',
    'langchain', 'openai', 'generative ai', 'rag', 'fine-tuning',
    'data science', 'data analysis', 'feature engineering', 'a/b testing',
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'google cloud', 'aws s3', 'ec2', 'lambda',
    'docker', 'kubernetes', 'terraform', 'ansible', 'helm', 'pulumi',
    'ci/cd', 'jenkins', 'github actions', 'gitlab ci', 'azure devops',
    'linux', 'bash', 'shell scripting', 'powershell',
    # Tools
    'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'notion',
    'power bi', 'tableau', 'excel', 'looker',
    # Business
    'agile', 'scrum', 'kanban', 'project management', 'product management',
    'leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking',
    # Mobile
    'react native', 'flutter', 'xamarin', 'ios', 'android',
    # Security
    'cybersecurity', 'penetration testing', 'owasp', 'soc2', 'gdpr',
    # Messaging
    'kafka', 'rabbitmq', 'celery', 'aws sqs', 'pubsub',
]


def _extract_skills(text: str) -> List[str]:
    lower = text.lower()
    found = []
    for kw in SKILL_KEYWORDS:
        if kw in lower:
            found.append(kw.title())
    seen = set()
    unique = []
    for s in found:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return sorted(unique)


def _extract_experience(text: str) -> List[Dict]:
    exp_header = re.search(
        r'(?i)(work\s*experience|professional\s*experience|employment|experience\s*&?\s*history)',
        text
    )
    if not exp_header:
        return [{'title': 'Professional Experience', 'company': '', 'duration': '', 'description': 'See CV for full details.'}]

    start = exp_header.end()
    next_sec = re.search(r'(?i)\n(education|skills|certifications|projects|awards)', text[start:])
    chunk = text[start: start + next_sec.start() if next_sec else len(text)]

    entries = []
    for line in (l.strip() for l in chunk.split('\n') if l.strip()):
        if len(line) > 8:
            entries.append({'title': line[:120], 'company': '', 'duration': '', 'description': ''})
        if len(entries) >= 5:
            break

    return entries if entries else [{'title': 'Professional Experience', 'company': '', 'duration': '', 'description': 'See CV for details.'}]


def _extract_education(text: str) -> List[str]:
    edu = []
    for kw in [r"bachelor", r"master", r"phd", r"doctorate", r"b\.?s\.?", r"m\.?s\.?", r"b\.?a\.?", r"m\.?a\.?", r"mba", r"b\.?tech", r"m\.?tech"]:
        for m in re.finditer(kw, text, re.IGNORECASE):
            ctx = text[max(0, m.start() - 20): min(len(text), m.end() + 100)].strip()
            if ctx not in edu:
                edu.append(ctx)
    return edu if edu else ["Education details in CV"]


# ─────────────────────────────────────────────
# LINKEDIN (graceful — no scraping)
# ─────────────────────────────────────────────

def parse_linkedin(url: str) -> Dict:
    """
    LinkedIn now blocks all automated scraping.
    We return a helpful error directing users to upload their LinkedIn PDF export.
    """
    raise Exception(
        "LinkedIn no longer allows automated access. "
        "Instead, go to LinkedIn → Me → Settings → Data Privacy → Get a copy of your data, "
        "download the PDF, and upload it here as your CV."
    )


# ─────────────────────────────────────────────
# ATS ANALYSIS
# ─────────────────────────────────────────────

def analyze_ats(cv_data: Dict, job_description: str) -> Dict:
    """
    LLM-powered semantic ATS analysis.
    Falls back to keyword matching if LLM unavailable.
    """
    # Try LLM first
    try:
        from llm_utils import analyze_ats_llm
        raw_text = cv_data.get('raw_text', '')
        result = analyze_ats_llm(raw_text, job_description)
        if result and result.get('score') is not None:
            return result
    except Exception:
        pass

    # ── Keyword fallback ──
    cv_lower = cv_data.get('raw_text', '').lower()
    job_lower = job_description.lower()
    job_kws = _extract_job_keywords(job_lower)
    matched, missing = [], []

    for kw in job_kws:
        if kw in cv_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    if job_kws:
        score = round((len(matched) / len(job_kws)) * 100)
    else:
        score = 65
        if 'project' in cv_lower: score += 10
        if '%' in cv_lower or 'increased' in cv_lower: score += 15
        if len(cv_data.get('skills', [])) > 5: score += 10
        
    score = max(0, min(100, score))

    return {
        'score': score,
        'matched_skills': matched,
        'missing_skills': missing[:10],
        'semantic_gaps': [],
        'strengths': ["Strong base formatting detected."] if score > 75 else [],
        'tips': _generate_tips(cv_data, missing, cv_lower),
        'experience_match': score,
        'keyword_density': 'medium',
    }


def _extract_job_keywords(job_text: str) -> List[str]:
    found = []
    for kw in SKILL_KEYWORDS:
        if kw in job_text:
            found.append(kw)
    return found


def _generate_tips(cv_data: Dict, missing: List[str], cv_lower: str) -> List[str]:
    tips = []
    resource_map = {
        'docker': 'Docker Official Docs + Play With Docker (free)',
        'aws': 'AWS Free Tier + freeCodeCamp AWS Course',
        'kubernetes': 'Kubernetes.io Interactive Tutorial (free)',
        'python': 'Python.org Tutorial + freeCodeCamp',
        'javascript': 'freeCodeCamp + JavaScript.info',
        'react': 'React.dev official tutorial (free)',
        'sql': 'SQLBolt + W3Schools SQL',
        'git': 'GitHub Learning Lab (free)',
        'typescript': 'TypeScript Handbook (official, free)',
        'machine learning': 'Andrew Ng ML Course on Coursera (audit free)',
    }
    for skill in missing[:4]:
        res = resource_map.get(skill.lower(), 'YouTube tutorials + freeCodeCamp')
        tips.append(f"Add \"{skill.title()}\" — Learn via: {res}")

    if 'project' not in cv_lower:
        tips.append("Add a 'Projects' section — concrete examples boost ATS and recruiter trust.")
    if not any(v in cv_lower for v in ['increased', 'improved', 'reduced', 'grew', '%']):
        tips.append("Include quantifiable achievements (e.g., 'Reduced load time by 40%').")
    if 'certification' not in cv_lower and 'certified' not in cv_lower:
        tips.append("Add certifications — even free ones (Google, AWS, Meta) add credibility.")
    if not any(v in cv_lower for v in ['developed', 'led', 'designed', 'built', 'implemented']):
        tips.append("Use strong action verbs: Developed, Led, Architected, Implemented.")

    return tips[:8]


# ─────────────────────────────────────────────
# SKILLS ROADMAP
# ─────────────────────────────────────────────

def generate_skills_roadmap(missing_skills: List[str], target_role: str = "") -> str:
    """LLM-powered dynamic roadmap, static fallback."""
    try:
        from llm_utils import generate_roadmap_llm
        return generate_roadmap_llm(missing_skills, target_role)
    except Exception:
        pass

    # Fallback static roadmap
    ROADMAP_DB = {
        'python':           {'weeks': '3-5', 'resources': ['Python.org Tutorial', 'freeCodeCamp Python', 'Codecademy']},
        'javascript':       {'weeks': '4-6', 'resources': ['freeCodeCamp JS', 'JavaScript.info', 'MDN Web Docs']},
        'react':            {'weeks': '3-4', 'resources': ['React.dev Tutorial', 'freeCodeCamp React', 'Scrimba (free tier)']},
        'docker':           {'weeks': '2-3', 'resources': ['Docker Docs', 'Play With Docker', 'YouTube: Docker in 1 Hr']},
        'aws':              {'weeks': '6-8', 'resources': ['AWS Free Tier', 'freeCodeCamp AWS', 'A Cloud Guru (free tier)']},
        'sql':              {'weeks': '2-3', 'resources': ['SQLBolt', 'W3Schools SQL', 'Khan Academy']},
        'machine learning': {'weeks': '8-12','resources': ['Andrew Ng ML (Coursera audit)', 'fast.ai', 'Kaggle Learn']},
    }
    md = "# 📚 Personalized Skills Roadmap\n\n"
    md += f"*Generated on {datetime.datetime.now().strftime('%B %d, %Y')}*\n\n---\n\n"
    for i, skill in enumerate(missing_skills[:8], 1):
        info = ROADMAP_DB.get(skill.lower(), {'weeks': '2-4', 'resources': ['YouTube Tutorials', 'freeCodeCamp', 'Udemy']})
        md += f"## {i}. {skill.title()}\n\n"
        md += f"⏱️ **Estimated Time:** {info['weeks']} weeks\n\n"
        md += "📖 **Free Resources:**\n"
        for r in info['resources']:
            md += f"  - {r}\n"
        md += "\n✅ **Action Plan:**\n"
        md += f"  1. **Week 1** — Complete a beginner tutorial on {skill.title()}\n"
        md += f"  2. **Week 2** — Build a small hands-on project\n"
        md += f"  3. **Week 3+** — Add the project to GitHub & update CV\n\n---\n\n"
    return md


# ─────────────────────────────────────────────
# GITHUB SCRAPING
# ─────────────────────────────────────────────

def get_github_projects(github_url: str) -> List[Dict]:
    """Fetch top 3 public repositories for a GitHub user."""
    if not github_url:
        return []
    
    # Try to extract username
    match = re.search(r'github\.com/([^/]+)', github_url)
    if not match:
        return []
        
    username = match.group(1).strip()
    try:
        response = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10", timeout=5)
        if response.status_code == 200:
            repos = response.json()
            # Sort by stars, take top 3
            repos = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)[:3]
            projects = []
            for r in repos:
                desc = r.get('description') or "A GitHub repository"
                if r.get('language'):
                    desc += f" (Built with {r.get('language')})"
                projects.append({
                    "name": r.get('name', 'Project'),
                    "description": desc
                })
            return projects
    except Exception:
        pass
    return []

# ─────────────────────────────────────────────
# CV PDF GENERATION (ReportLab)
# ─────────────────────────────────────────────

def generate_optimized_cv(cv_data: Dict, job_description: str = None, template: str = "Modern") -> bytes:
    """
    Generate an ATS-optimized PDF CV using LLM-powered summary.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.55 * inch, bottomMargin=0.5 * inch,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch
    )
    styles = getSampleStyleSheet()
    story = []

    is_harvard = template.lower() == "harvard"

    if is_harvard:
        dark   = HexColor('#000000')
        accent = HexColor('#000000')
        grey   = HexColor('#333333')
        light  = HexColor('#555555')
        font_main = 'Times-Roman'
        font_bold = 'Times-Bold'
        font_italic = 'Times-Italic'
        name_align = TA_CENTER
    else:
        dark   = HexColor('#1a1a2e')
        accent = HexColor('#e94560')
        grey   = HexColor('#555555')
        light  = HexColor('#888888')
        font_main = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        font_italic = 'Helvetica-Oblique'
        name_align = TA_CENTER

    name_style = ParagraphStyle('Name', parent=styles['Normal'],
                                fontSize=24 if is_harvard else 26, 
                                leading=28 if is_harvard else 30, 
                                textColor=dark, alignment=name_align,
                                fontName=font_bold, spaceAfter=4 if is_harvard else 6)
    contact_style = ParagraphStyle('Contact', parent=styles['Normal'],
                                   fontSize=10 if is_harvard else 9, 
                                   leading=14 if is_harvard else 12, 
                                   textColor=dark if is_harvard else grey, 
                                   alignment=TA_CENTER,
                                   fontName=font_main, spaceAfter=8)
    section_style = ParagraphStyle('Section', parent=styles['Normal'],
                                   fontSize=11, textColor=accent, alignment=TA_CENTER if is_harvard else TA_LEFT,
                                   fontName=font_bold, spaceBefore=12 if is_harvard else 10, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                fontSize=10 if is_harvard else 9.5, textColor=dark,
                                fontName=font_main, spaceAfter=3, leading=14 if is_harvard else 13)
    bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
                                  fontSize=10 if is_harvard else 9, textColor=dark if is_harvard else grey,
                                  fontName=font_main, leftIndent=14, spaceAfter=2, leading=13 if is_harvard else 12)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=9.5 if is_harvard else 8.5, textColor=grey if is_harvard else light,
                                fontName=font_italic, spaceAfter=2)

    # ── NAME ──
    story.append(Paragraph(cv_data.get('name', 'Professional').upper() if is_harvard else cv_data.get('name', 'Professional'), name_style))

    # ── CONTACT LINE ──
    parts = []
    if cv_data.get('email'):    parts.append(cv_data['email'])
    if cv_data.get('phone'):    parts.append(cv_data['phone'])
    if cv_data.get('linkedin'): parts.append(cv_data['linkedin'])
    if cv_data.get('github'):   parts.append(cv_data['github'])
    if cv_data.get('location'): parts.append(cv_data['location'])
    
    if parts:
        story.append(Paragraph(' | '.join(parts) if is_harvard else ' • '.join(parts), contact_style))
    story.append(HRFlowable(width="100%", color=accent, thickness=1 if is_harvard else 1.5, spaceAfter=6))

    # ── PROFESSIONAL SUMMARY (LLM-generated) ──
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    try:
        from llm_utils import generate_summary_llm
        summary = generate_summary_llm(cv_data, job_description)
    except Exception:
        skills_preview = ', '.join(cv_data.get('skills', [])[:5]) or 'diverse technologies'
        summary = (
            f"Results-driven {cv_data.get('current_title', 'professional')} with expertise in "
            f"{skills_preview}. Passionate about delivering high-quality solutions."
        )
    story.append(Paragraph(summary, body_style))

    # ── SKILLS ──
    if cv_data.get('skills'):
        story.append(Paragraph("SKILLS", section_style))
        if is_harvard: story.append(HRFlowable(width="100%", color=accent, thickness=0.8, spaceAfter=4))
        all_skills = cv_data['skills']
        # If job desc provided, put matched skills first
        if job_description:
            jd_lower = job_description.lower()
            matched = [s for s in all_skills if s.lower() in jd_lower]
            rest = [s for s in all_skills if s.lower() not in jd_lower]
            ordered = matched + rest
        else:
            ordered = all_skills
        story.append(Paragraph(' &nbsp;•&nbsp; '.join(ordered[:18]), body_style))

    # ── EXPERIENCE ──
    story.append(Paragraph("PROFESSIONAL EXPERIENCE" if is_harvard else "EXPERIENCE", section_style))
    if is_harvard: story.append(HRFlowable(width="100%", color=accent, thickness=0.8, spaceAfter=4))
    for exp in cv_data.get('experience', [])[:5]:
        title_line = exp.get('title', 'Role')
        if exp.get('company'):
            title_line = f"<b>{exp.get('title', 'Role')}</b> — {exp.get('company', '')}"
        else:
            title_line = f"<b>{title_line}</b>"
        story.append(Paragraph(title_line, body_style))
        if exp.get('duration'):
            story.append(Paragraph(exp['duration'], sub_style))
        if exp.get('description'):
            story.append(Paragraph(f"• {exp['description']}", bullet_style))
        story.append(Spacer(1, 4))

    # ── PROJECTS ──
    if cv_data.get('projects'):
        story.append(Paragraph("PROJECTS" if is_harvard else "KEY PROJECTS", section_style))
        if is_harvard: story.append(HRFlowable(width="100%", color=accent, thickness=0.8, spaceAfter=4))
        for proj in cv_data['projects'][:4]:
            story.append(Paragraph(f"<b>{proj.get('name', 'Project')}</b>", body_style))
            if proj.get('description'):
                story.append(Paragraph(f"• {proj['description']}", bullet_style))

    # ── EDUCATION ──
    if cv_data.get('education'):
        story.append(Paragraph("EDUCATION", section_style))
        if is_harvard: story.append(HRFlowable(width="100%", color=accent, thickness=0.8, spaceAfter=4))
        edu = cv_data['education']
        if edu and isinstance(edu[0], dict):
            for e in edu[:3]:
                story.append(Paragraph(
                    f"<b>{e.get('degree', '')}</b> — {e.get('institution', '')} ({e.get('year', '')})",
                    body_style
                ))
        else:
            for e in edu[:3]:
                story.append(Paragraph(str(e), body_style))

    # ── CERTIFICATIONS ──
    if cv_data.get('certifications'):
        story.append(Paragraph("CERTIFICATIONS", section_style))
        for cert in cv_data['certifications'][:5]:
            story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────
# PORTFOLIO HTML + ZIP
# ─────────────────────────────────────────────

def generate_portfolio(cv_data: Dict) -> bytes:
    name = cv_data.get('name', 'Professional')
    email = cv_data.get('email', 'contact@example.com')
    phone = cv_data.get('phone', '')
    linkedin = cv_data.get('linkedin', '')
    github = cv_data.get('github', '')
    title = cv_data.get('current_title', 'Software Developer')
    skills = cv_data.get('skills', ['Software Development', 'Problem Solving'])
    experience = cv_data.get('experience', [])
    education = cv_data.get('education', [])
    projects = cv_data.get('projects', [])
    certs = cv_data.get('certifications', [])
    years = cv_data.get('years_experience', 0)

    # ── skill grid cards ──
    skill_cards = "\n".join([
        f'''            <div class="skill-card">
              <div class="skill-icon">{s[0].upper()}</div>
              <span>{s}</span>
            </div>'''
        for s in skills[:20]
    ])

    # ── experience timeline ──
    exp_items = "\n".join([
        f'''            <div class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <h3>{e.get('title', 'Role')}{' @ ' + e['company'] if e.get('company') else ''}</h3>
                {f'<div class="timeline-date">{e["duration"]}</div>' if e.get('duration') else ''}
                <p>{e.get('description', 'Delivered impactful results in a professional setting.')}</p>
              </div>
            </div>'''
        for e in experience[:5]
    ])

    # ── projects ──
    project_cards = "\n".join([
        f'''            <div class="project-card">
              <h3>{p.get('name', 'Project')}</h3>
              <p>{p.get('description', '')}</p>
            </div>'''
        for p in projects[:4]
    ]) if projects else ""

    # ── education ──
    edu_items = ""
    for e in education[:3]:
        if isinstance(e, dict):
            edu_items += f'            <li><strong>{e.get("degree","")}</strong> — {e.get("institution","")} ({e.get("year","")})</li>\n'
        else:
            edu_items += f'            <li>{e}</li>\n'

    # ── cert pills ──
    cert_html = " ".join([f'<span class="cert-pill">{c}</span>' for c in certs[:6]]) if certs else ""

    # ── social links ──
    social_html = ""
    if linkedin:
        social_html += f'<a href="{linkedin}" target="_blank" class="social-link">🔗 LinkedIn</a>'
    if github:
        social_html += f'<a href="{github}" target="_blank" class="social-link">💻 GitHub</a>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="description" content="{name} — {title} portfolio website"/>
  <title>{name} — Portfolio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
    :root {{
      --clr-bg:      #09090b;
      --clr-surface: rgba(24, 24, 27, 0.45);
      --clr-border:  rgba(255, 255, 255, 0.08);
      --clr-accent:  #6366f1; /* Indigo */
      --clr-accent2: #a855f7; /* Purple */
      --clr-text:    #f8fafc;
      --clr-muted:   #94a3b8;
      --font-head:   'Outfit', sans-serif;
      --font-body:   'Inter', sans-serif;
    }}
    html {{ scroll-behavior:smooth; }}
    body {{
      font-family: var(--font-body);
      background: var(--clr-bg);
      color: var(--clr-text);
      line-height: 1.6;
      overflow-x: hidden;
    }}

    /* MESH GRADIENT BACKGROUND */
    .mesh-bg {{
      position: fixed; inset: 0; z-index: -1;
      background: var(--clr-bg);
      overflow: hidden;
    }}
    .mesh-bg::before, .mesh-bg::after {{
      content: ''; position: absolute;
      width: 60vw; height: 60vw;
      border-radius: 50%;
      filter: blur(120px);
      opacity: 0.15;
      animation: float 20s infinite alternate cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .mesh-bg::before {{
      background: var(--clr-accent);
      top: -20%; left: -10%;
    }}
    .mesh-bg::after {{
      background: var(--clr-accent2);
      bottom: -20%; right: -10%;
      animation-delay: -10s;
    }}
    @keyframes float {{
      0%   {{ transform: translate(0, 0) scale(1); }}
      100% {{ transform: translate(15%, 15%) scale(1.1); }}
    }}

    /* NAV */
    nav {{
      position:fixed; top:0; width:100%; z-index:100;
      background: rgba(9, 9, 11, 0.5);
      backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      border-bottom: 1px solid var(--clr-border);
      padding: 1rem 0;
      transition: all 0.3s;
    }}
    .nav-inner {{
      max-width:1100px; margin:0 auto; padding:0 1.5rem;
      display:flex; justify-content:space-between; align-items:center;
    }}
    .nav-logo {{
      font-family:var(--font-head); font-size:1.4rem; font-weight: 700;
      color:#fff; text-decoration:none;
      background: linear-gradient(135deg, #fff, #94a3b8);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .nav-links a {{
      color:var(--clr-muted); text-decoration:none;
      margin-left:2rem; font-size:.85rem; font-weight:500;
      transition:color .2s;
    }}
    .nav-links a:hover {{ color: #fff; }}

    /* HERO */
    .hero {{
      min-height:100vh; display:flex; align-items:center; justify-content:center;
      position:relative; padding:7rem 1.5rem 4rem; text-align:center;
    }}
    .hero-content {{ position:relative; z-index:1; max-width:800px; }}
    .hero-badge {{
      display:inline-block; padding:6px 18px; border-radius:30px;
      background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2);
      color:#818cf8; font-family: var(--font-head); font-size:.85rem; font-weight:500;
      letter-spacing:1px; margin-bottom:1.5rem; text-transform:uppercase;
    }}
    .hero-content h1 {{
      font-family:var(--font-head); font-size:clamp(3rem, 7vw, 5.5rem);
      font-weight:800; line-height:1.1; letter-spacing:-1.5px;
      margin-bottom:1rem;
    }}
    .hero-content h1 span {{
      background: linear-gradient(135deg, var(--clr-accent), var(--clr-accent2));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .hero-subtitle {{
      color:var(--clr-muted); font-size:1.1rem; font-weight:400;
      max-width:580px; margin:0 auto 2.5rem; line-height: 1.7;
    }}
    .btn {{
      display:inline-block; padding:.8rem 2.2rem;
      background: linear-gradient(135deg, var(--clr-accent), var(--clr-accent2));
      color:#fff; border:none; border-radius:30px; font-size:.9rem; font-family: var(--font-head);
      font-weight:600; text-decoration:none; cursor:pointer;
      transition:all .3s ease; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.2);
    }}
    .btn:hover {{ transform:translateY(-2px); box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4); }}
    
    .btn-outline {{
      display:inline-block; padding:.8rem 2.2rem; margin-left:1rem;
      background: var(--clr-surface); border:1px solid var(--clr-border);
      backdrop-filter: blur(10px);
      color:#fff; border-radius:30px; font-size:.9rem; font-family: var(--font-head);
      font-weight:600; text-decoration:none; transition:all .3s;
    }}
    .btn-outline:hover {{ border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); transform:translateY(-2px); }}

    .hero-stats {{
      display:flex; justify-content:center; gap:3.5rem; margin-top:4rem; flex-wrap:wrap;
    }}
    .hero-stat .num {{
      font-family:var(--font-head); font-size:2.4rem; font-weight:700; color:#fff;
    }}
    .hero-stat .lbl {{
      font-size:.8rem; color:var(--clr-muted); margin-top:-4px;
    }}

    /* SECTIONS */
    section {{ padding:7rem 1.5rem; }}
    .container {{ max-width:1050px; margin:0 auto; }}
    .section-label {{
      font-family: var(--font-head); font-size:.85rem; color:#818cf8;
      letter-spacing:2px; text-transform:uppercase; font-weight:600; margin-bottom:.5rem;
    }}
    .section-title {{
      font-family:var(--font-head); font-size:clamp(2rem,4vw,3rem);
      font-weight:700; color:#fff; margin-bottom:3rem; letter-spacing:-1px;
    }}

    /* GLASS CARDS */
    .glass-card {{
      background: var(--clr-surface); border: 1px solid var(--clr-border);
      backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
      border-radius: 16px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .glass-card:hover {{
      border-color: rgba(255, 255, 255, 0.15);
      background: rgba(24, 24, 27, 0.6);
      transform: translateY(-4px);
    }}

    /* ABOUT */
    #about {{ position: relative; }}
    .about-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:4rem; align-items:center; }}
    .about-text p {{ color:var(--clr-muted); font-size:1.05rem; margin-bottom:1.2rem; }}
    .about-stats {{ display:grid; grid-template-columns:1fr 1fr; gap:1.2rem; }}
    .stat-card {{ padding:1.8rem; text-align:center; }}
    .stat-card .num {{ font-family:var(--font-head); font-size:2.2rem; color:var(--clr-accent2); font-weight:700; }}
    .stat-card .label {{ color:var(--clr-muted); font-size:.85rem; margin-top:.3rem; }}

    /* SKILLS */
    .skills-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(140px,1fr)); gap:1.2rem; }}
    .skill-card {{ padding:1.5rem 1rem; text-align:center; display:flex; flex-direction:column; align-items:center; }}
    .skill-card:hover {{ box-shadow: 0 10px 30px rgba(99, 102, 241, 0.1); }}
    .skill-icon {{
      width:42px; height:42px; border-radius:10px;
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2));
      color: #fff; font-weight:700; font-size:1.1rem;
      display:flex; align-items:center; justify-content:center; margin-bottom:.8rem;
      border: 1px solid rgba(255,255,255,0.05);
    }}
    .skill-card span {{ font-size:.85rem; color:#e2e8f0; font-weight:500; }}

    /* EXPERIENCE TIMELINE */
    .timeline {{ position:relative; padding-left:2.5rem; }}
    .timeline::before {{
      content:''; position:absolute; left:0.85rem; top:0; bottom:0;
      width:2px; background: linear-gradient(to bottom, var(--clr-accent), transparent);
      opacity: 0.5;
    }}
    .timeline-item {{ position:relative; margin-bottom:2.5rem; }}
    .timeline-dot {{
      position:absolute; left:-1.95rem; top:.4rem;
      width:14px; height:14px; border-radius:50%;
      background: #09090b; border: 2px solid var(--clr-accent);
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
    }}
    .timeline-content {{ padding:1.8rem 2rem; }}
    .timeline-content h3 {{ font-family:var(--font-head); color:#fff; font-size:1.1rem; font-weight:600; margin-bottom:.3rem; }}
    .timeline-date {{ font-size:.85rem; color:#818cf8; margin-bottom:.8rem; font-family: var(--font-head); }}
    .timeline-content p {{ color:var(--clr-muted); font-size:.95rem; }}

    /* PROJECTS */
    .projects-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(320px,1fr)); gap:1.5rem; }}
    .project-card {{ padding:1.8rem; display:flex; flex-direction:column; }}
    .project-card h3 {{ font-family:var(--font-head); color:#fff; font-size:1.1rem; font-weight:600; margin-bottom:.6rem; }}
    .project-card p {{ color:var(--clr-muted); font-size:.95rem; line-height:1.6; }}

    /* EDUCATION & CERTS */
    .edu-list {{ list-style:none; padding:0; }}
    .edu-list li {{ padding:1.2rem 1.6rem; margin-bottom:.8rem; color:var(--clr-muted); font-size:.95rem; }}
    .edu-list li strong {{ color: #e2e8f0; }}
    .cert-pill {{
      display:inline-block; padding:6px 16px; border-radius:30px;
      background: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.2);
      color: #d8b4fe; font-size:.85rem; font-family: var(--font-head);
      margin:5px; transition:all .2s;
    }}
    .cert-pill:hover {{ background: rgba(168, 85, 247, 0.2); }}

    /* CONTACT */
    #contact {{ position: relative; text-align:center; padding-top: 8rem; padding-bottom: 6rem; }}
    .contact-info {{ display:flex; justify-content:center; gap:3rem; flex-wrap:wrap; margin-top:2.5rem; }}
    .contact-item {{ color:var(--clr-muted); font-size:.95rem; }}
    .contact-item strong {{ color:#fff; font-size:1.05rem; display:block; margin-top:0.3rem; }}
    .social-link {{
      display:inline-flex; align-items:center; margin:0 .6rem; padding:.8rem 1.8rem;
      background: var(--clr-surface); border:1px solid var(--clr-border); border-radius:30px;
      color:#fff; text-decoration:none; font-size:.9rem; font-weight:500;
      transition:all .3s; margin-top:1.5rem;
    }}
    .social-link:hover {{ border-color:var(--clr-accent); background:rgba(99, 102, 241, 0.1); transform:translateY(-2px); }}

    footer {{
      text-align:center; padding:2.5rem; color:var(--clr-muted);
      font-size:.85rem; border-top:1px solid var(--clr-border);
      background: #09090b; position:relative; z-index:10;
    }}

    /* RESPONSIVE */
    @media (max-width:768px) {{
      .about-grid {{ grid-template-columns:1fr; gap: 3rem; }}
      .hero-stats {{ gap:2rem; }}
      section {{ padding:5rem 1.2rem; }}
      .btn-outline {{ margin-left:0; margin-top:1rem; }}
    }}

    /* ANIMATIONS */
    @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(30px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .fade-up {{ animation:fadeUp .8s cubic-bezier(0.16, 1, 0.3, 1) both; }}
    .delay-1 {{ animation-delay:.15s; }} .delay-2 {{ animation-delay:.3s; }}
    .delay-3 {{ animation-delay:.45s; }} .delay-4 {{ animation-delay:.6s; }}
    .reveal {{ opacity:0; transform:translateY(30px); transition:all .8s cubic-bezier(0.16, 1, 0.3, 1); }}
    .reveal.visible {{ opacity:1; transform:none; }}
  </style>
</head>
<body>

<div class="mesh-bg"></div>

<!-- NAV -->
<nav>
  <div class="nav-inner">
    <a href="#" class="nav-logo">{name}</a>
    <div class="nav-links">
      <a href="#about">About</a>
      <a href="#skills">Skills</a>
      <a href="#experience">Experience</a>
      {'<a href="#projects">Projects</a>' if projects else ''}
      <a href="#contact">Contact</a>
    </div>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-content fade-up">
    <div class="hero-badge">{title}</div>
    <h1>Hi, I'm <br/><span>{name}</span></h1>
    <p class="hero-subtitle">
      A passionate professional crafting innovative solutions and delivering exceptional results through technology and design.
    </p>
    <div>
      <a href="#contact" class="btn">Get In Touch</a>
      <a href="#skills" class="btn-outline">View Skills</a>
    </div>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{years if years else len(experience)}+</div><div class="lbl">{'Years Exp' if years else 'Roles'}</div></div>
      <div class="hero-stat"><div class="num">{len(skills)}</div><div class="lbl">Skills</div></div>
      <div class="hero-stat"><div class="num">{len(projects) if projects else len(experience)}</div><div class="lbl">{'Projects' if projects else 'Companies'}</div></div>
    </div>
  </div>
</section>

<!-- ABOUT -->
<section id="about" class="reveal">
  <div class="container">
    <div class="about-grid">
      <div class="about-text">
        <p class="section-label">About Me</p>
        <h2 class="section-title">Driven by passion, <br/>powered by code.</h2>
        <p>
          Results-oriented {title} with deep expertise in {', '.join(skills[:3]) if len(skills)>=3 else 'emerging technologies'}. 
          I thrive on solving complex problems and transforming ideas into polished, scalable solutions that drive real value.
        </p>
        <p>
          Passionate about continuous learning, clean architecture, and creating experiences
          that leave a lasting impact. Always looking for the next big challenge.
        </p>
      </div>
      <div class="about-stats">
        <div class="glass-card stat-card"><div class="num">{len(skills)}</div><div class="label">Skills Assessed</div></div>
        <div class="glass-card stat-card"><div class="num">{len(experience)}</div><div class="label">Key Roles</div></div>
        <div class="glass-card stat-card"><div class="num">{years if years else '∞'}</div><div class="label">{'Yrs Experience' if years else 'Curiosity'}</div></div>
        <div class="glass-card stat-card"><div class="num">{len(projects) if projects else len(education)}</div><div class="label">{'Projects Won' if projects else 'Degrees'}</div></div>
      </div>
    </div>
  </div>
</section>

<!-- SKILLS -->
<section id="skills" class="reveal">
  <div class="container">
    <p class="section-label">Expertise</p>
    <h2 class="section-title">Software & Tools</h2>
    <div class="skills-grid">
{skill_cards.replace('skill-card', 'glass-card skill-card')}
    </div>
  </div>
</section>

<!-- EXPERIENCE -->
<section id="experience" class="reveal">
  <div class="container">
    <p class="section-label">Career</p>
    <h2 class="section-title">Experience</h2>
    <div class="timeline">
{exp_items.replace('timeline-content', 'glass-card timeline-content')}
    </div>
  </div>
</section>

{'<!-- PROJECTS --><section id="projects" class="reveal"><div class="container"><p class="section-label">Work</p><h2 class="section-title">Key Projects</h2><div class="projects-grid">' + project_cards.replace('project-card', 'glass-card project-card') + '</div></div></section>' if projects else ''}

<!-- EDUCATION -->
<section id="education" class="reveal">
  <div class="container">
    <p class="section-label">Background</p>
    <h2 class="section-title">Education & Certs</h2>
    <ul class="edu-list">
{edu_items.replace('<li>', '<li class="glass-card">')}
    </ul>
    {f'<div style="margin-top:1.5rem">{cert_html}</div>' if certs else ''}
  </div>
</section>

<!-- CONTACT -->
<section id="contact" class="reveal">
  <div class="container">
    <p class="section-label">Let's Connect</p>
    <h2 class="section-title">Get In Touch</h2>
    <p style="color:var(--clr-muted); max-width:480px; margin:0 auto 1rem; font-size:1.05rem;">
      Interested in working together or building something new? Looking forward to hearing from you.
    </p>
    <div class="contact-info">
      <div class="glass-card contact-item" style="padding: 1.5rem;">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem">📫</div>
        Email Me
        <strong>{email}</strong>
      </div>
      {f"<div class='glass-card contact-item' style='padding: 1.5rem;'><div style='font-size: 1.5rem; margin-bottom: 0.5rem'>📱</div>Call Me<strong>{phone}</strong></div>" if phone else ""}
    </div>
    <div style="margin-top:2.5rem; display: flex; justify-content: center; flex-wrap: wrap;">
      {social_html}
    </div>
  </div>
</section>

<footer>
  <p>Built with CareerBoost AI 🚀 — {datetime.datetime.now().year}</p>
</footer>

<script>
  // Smooth reveal on scroll
  const reveals = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }});
  }}, {{ threshold: 0.12 }});
  reveals.forEach(el => io.observe(el));
</script>
</body>
</html>"""

    # Zip it
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', html)
    buf.seek(0)
    return buf.getvalue()
