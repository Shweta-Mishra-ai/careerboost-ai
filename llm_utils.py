"""
llm_utils.py — CareerBoost AI (UPDATED)
All Groq LLaMA 3 powered functions including HR emails.
Free API key: https://console.groq.com
"""

import os
import json
import re
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_groq_key() -> Optional[str]:
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key: return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY")


def _groq_call(messages: list, max_tokens: int = 1200, temperature: float = 0.4) -> str:
    key = _get_groq_key()
    if not key:
        raise Exception("GROQ_API_KEY not configured")
    from groq import Groq
    client = Groq(api_key=key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str):
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())
    raw = re.sub(r'^```\s*', '', raw.strip())
    return json.loads(raw)


def extract_cv_data_llm(text: str) -> Dict:
    prompt = f"""Extract structured data from this CV. Return ONLY valid JSON, no markdown, no explanation.

CV TEXT:
{text[:3500]}

JSON structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "location": "City, Country",
  "linkedin": "https://linkedin.com/in/...",
  "github": "https://github.com/...",
  "current_title": "Software Engineer",
  "years_experience": 3,
  "skills": ["Python", "React", "SQL"],
  "experience": [
    {{"title": "Role", "company": "Company Name", "duration": "Jan 2022 - Present", "description": "Key achievement with metrics if available"}}
  ],
  "education": [
    {{"degree": "B.Tech Computer Science", "institution": "University", "year": "2021"}}
  ],
  "projects": [
    {{"name": "Project Name", "description": "What it does, tech used, impact"}}
  ],
  "certifications": ["AWS Certified Solutions Architect"]
}}

Return ONLY JSON."""
    try:
        raw = _groq_call([{"role":"user","content":prompt}], max_tokens=1800)
        return _parse_json(raw)
    except Exception as e:
        raise Exception(f"CV extraction failed: {e}")


def analyze_ats_llm(cv_text: str, job_description: str) -> Dict:
    prompt = f"""You are an expert ATS analyzer. Analyze this CV against the job description.

CV (first 2000 chars):
{cv_text[:2000]}

JOB DESCRIPTION (first 1500 chars):
{job_description[:1500]}

Return ONLY valid JSON:
{{
  "score": 78,
  "matched_skills": ["Python", "React"],
  "missing_skills": ["Docker", "Kubernetes"],
  "semantic_gaps": ["No team leadership mentioned", "Missing cloud experience"],
  "strengths": ["Strong Python background", "Good project portfolio"],
  "tips": ["Add Docker — learn via Play With Docker (free)", "Quantify achievements with metrics"],
  "experience_match": 72,
  "keyword_density": "medium"
}}

Score 0-100 based on keyword match + semantic relevance. Return ONLY JSON."""
    try:
        raw = _groq_call([{"role":"user","content":prompt}], max_tokens=900)
        return _parse_json(raw)
    except Exception as e:
        raise Exception(f"ATS analysis failed: {e}")


def generate_summary_llm(cv_data: Dict, job_description: str = None) -> str:
    name   = cv_data.get('name', 'Professional')
    title  = cv_data.get('current_title', 'Professional')
    skills = ', '.join(cv_data.get('skills', [])[:8])
    years  = cv_data.get('years_experience', '')
    exp_n  = len(cv_data.get('experience', []))
    # Use real bio data if available
    extra  = cv_data.get('linkedin_about', '') or cv_data.get('github_bio', '')
    jd_ctx = f"\nTarget JD: {job_description[:400]}" if job_description else ""

    prompt = f"""Write a professional CV summary (2-3 sentences, 60-80 words max) for:

Name: {name}
Title: {title}
Skills: {skills}
Experience: {years or exp_n} years/roles
Real bio data: {extra[:200] if extra else 'N/A'}
{jd_ctx}

Rules:
- Start with "{title}" or "Results-driven {title}"
- Include 2-3 specific skills
- Mention 1 concrete value/impact
- NO first-person pronouns (no I/my/me)
- ATS-optimized keywords
- Professional tone

Return ONLY the summary text, no quotes."""
    try:
        return _groq_call([{"role":"user","content":prompt}], max_tokens=200, temperature=0.6)
    except Exception:
        s = ', '.join(cv_data.get('skills',[])[:4]) or 'various technologies'
        t = cv_data.get('current_title','professional')
        if extra: return extra[:250]
        return f"Results-driven {t} with expertise in {s}. Proven track record of delivering high-quality, scalable solutions with measurable business impact."


def generate_cover_letter_llm(cv_data: Dict, job_description: str) -> str:
    name        = cv_data.get('name', 'Applicant')
    title       = cv_data.get('current_title', 'Professional')
    skills      = ', '.join(cv_data.get('skills', [])[:6])
    recent_role = (cv_data.get('experience') or [{}])[0].get('title', '')
    exp_desc    = (cv_data.get('experience') or [{}])[0].get('description', '')

    prompt = f"""Write a compelling cover letter body (3 paragraphs, 280-340 words) for:

Candidate: {name}
Title: {title}
Top Skills: {skills}
Recent Role: {recent_role}
Recent Achievement: {exp_desc[:200] if exp_desc else 'N/A'}

Job Description:
{job_description[:1000]}

Structure:
Para 1 (4-5 sentences): Hook — why THIS company/role excites you. Reference specific details from JD.
Para 2 (4-5 sentences): Most relevant experience + 1-2 specific quantified achievements. Connect to job needs.
Para 3 (3-4 sentences): Cultural fit + enthusiasm + clear call to action.

Tone: Confident, personable, NOT generic. Avoid clichés like "I am writing to apply..."
Start directly with something specific and compelling.
Return ONLY the 3 paragraphs."""
    try:
        return _groq_call([{"role":"user","content":prompt}], max_tokens=700, temperature=0.7)
    except Exception as e:
        raise Exception(f"Cover letter failed: {e}")


def generate_interview_prep_llm(cv_data: Dict, job_description: str) -> List[Dict]:
    title  = cv_data.get('current_title', 'Professional')
    skills = ', '.join(cv_data.get('skills', [])[:8])

    prompt = f"""Generate 8 targeted interview questions for:
Candidate title: {title}
Skills: {skills}
Job Description: {job_description[:600]}

Return ONLY valid JSON array:
[
  {{
    "category": "Technical",
    "question": "Specific technical question from JD...",
    "why_asked": "What this tests",
    "model_answer": "Strong answer covers: [points]. Example: [concrete example from candidate's likely background]."
  }}
]

Mix: 3 Technical, 2 Behavioural, 2 Situational, 1 Cultural
Make questions SPECIFIC to the JD tech stack and candidate background.
Return ONLY the JSON array."""
    try:
        raw = _groq_call([{"role":"user","content":prompt}], max_tokens=2000, temperature=0.5)
        data = _parse_json(raw)
        return data if isinstance(data, list) else []
    except Exception as e:
        raise Exception(f"Interview prep failed: {e}")


def generate_roadmap_llm(missing_skills: List[str], target_role: str = "") -> str:
    skills_str = ', '.join(missing_skills[:8])
    prompt = f"""Create a practical learning roadmap for missing skills: {skills_str}
{f"Target role: {target_role}" if target_role else ""}

Format as clean Markdown. For each skill include:
- Estimated weeks to learn
- 2-3 SPECIFIC free resources (freeCodeCamp, official docs, YouTube channels)
- 3-step action plan

Keep it motivating, practical, under 600 words.
Return only Markdown."""
    try:
        return _groq_call([{"role":"user","content":prompt}], max_tokens=900, temperature=0.5)
    except Exception as e:
        raise Exception(f"Roadmap failed: {e}")


def generate_job_search_strategy_llm(cv_data: Dict, job_description: str, missing_skills: List[str]) -> str:
    title  = cv_data.get('current_title','Professional')
    skills = ', '.join(cv_data.get('skills',[])[:10])
    gaps   = ', '.join(missing_skills[:5]) if missing_skills else 'none significant'

    prompt = f"""Create a targeted job search strategy as Markdown:

Candidate: {title}
Skills: {skills}
Skill gaps: {gaps}
Target JD: {job_description[:400]}

Include:
1. **Target Roles** — 4-5 exact job titles to search
2. **Best Platforms** — LinkedIn, Indeed, remote boards, niche sites
3. **Search Queries** — 5 exact strings to paste into search
4. **Networking** — 3 actionable moves (LinkedIn DM templates, communities)
5. **30-Day Plan** — Week-by-week checklist

Practical and specific. Max 500 words. Return only Markdown."""
    try:
        return _groq_call([{"role":"user","content":prompt}], max_tokens=800, temperature=0.5)
    except Exception as e:
        raise Exception(f"Strategy failed: {e}")


def generate_hr_emails_llm(cv_data: Dict, company: str, role: str, hr_name: str = "Hiring Manager") -> Dict:
    """Generate all 4 email templates using LLM."""
    name   = cv_data.get('name','Candidate')
    title  = cv_data.get('current_title','Professional')
    skills = ', '.join(cv_data.get('skills',[])[:6])
    email  = cv_data.get('email','')
    exp    = cv_data.get('experience',[])
    achievement = exp[0].get('description','') if exp else ''

    prompt = f"""Generate 4 professional email templates as JSON for job outreach.

Candidate: {name} ({title})
Skills: {skills}
Recent Achievement: {achievement[:150] if achievement else 'N/A'}
Target Company: {company}
Target Role: {role}
HR Name: {hr_name}
Candidate Email: {email}

Return ONLY valid JSON:
{{
  "cold_email": {{
    "subject": "subject line here",
    "body": "full email body here"
  }},
  "follow_up_1": {{
    "subject": "subject line",
    "body": "body — 7 days after cold email"
  }},
  "follow_up_2": {{
    "subject": "subject line",
    "body": "body — 14 days after, final follow-up"
  }},
  "thank_you": {{
    "subject": "subject line",
    "body": "post-interview thank you"
  }}
}}

Email guidelines:
- Cold: Hook + specific value prop + CTA. Start with something specific about the company. NOT generic.
- Follow-up 1: Brief, professional, add new value point. 
- Follow-up 2: Concise final check-in, open door for future.
- Thank you: Specific reference to interview conversation + reinforce fit.
- All emails: Professional, confident, NOT sycophantic.
- Sign off with name and email.
Return ONLY JSON."""

    try:
        raw = _groq_call([{"role":"user","content":prompt}], max_tokens=2000, temperature=0.6)
        data = _parse_json(raw)
        # Flatten subject+body into single string for each
        result = {}
        for key in ['cold_email','follow_up_1','follow_up_2','thank_you']:
            if key in data and isinstance(data[key], dict):
                subject = data[key].get('subject','')
                body    = data[key].get('body','')
                result[key] = f"Subject: {subject}\n\n{body}"
            elif key in data:
                result[key] = data[key]
        return result
    except Exception as e:
        raise Exception(f"HR email generation failed: {e}")
