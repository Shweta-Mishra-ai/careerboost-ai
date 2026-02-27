"""
llm_utils.py — Real AI brain for CareerBoost AI
Uses Groq (LLaMA 3.1 8B Instant) for all LLM tasks.
Falls back gracefully when API key is not configured.
"""

import os
import json
import re
import time
import streamlit as st
from typing import Dict, List, Optional

# ─────────────────────────────────────────────
# CLIENT SETUP
# ─────────────────────────────────────────────

def _get_groq_client():
    """Return a configured Groq client or raise a clear error."""
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("groq package not installed. Run: pip install groq")

    # Check Streamlit Secrets first (for cloud/HF Spaces), then env var
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

    if not api_key:
        # Try .env or environment variable
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Add it to .streamlit/secrets.toml (cloud) or a .env file (local)."
        )

    return Groq(api_key=api_key)


def ask_llm(
    prompt: str,
    system: str = "You are a helpful AI career assistant. Always respond with valid JSON when asked.",
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 2048,
    retries: int = 2,
) -> str:
    """
    Core LLM call with retry logic.
    Returns the raw text response.
    """
    client = _get_groq_client()
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise e


def _parse_json_response(text: str) -> dict:
    """Robustly extract JSON from LLM response (handles markdown code blocks)."""
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    # Find first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # Fallback
    try:
        return json.loads(cleaned)
    except Exception:
        return {}


# ─────────────────────────────────────────────
# CV EXTRACTION
# ─────────────────────────────────────────────

def extract_cv_data_llm(raw_text: str) -> Dict:
    """
    Use LLM to intelligently extract structured data from raw CV text.
    Returns a dict with: name, email, phone, skills, experience, education, summary_hint
    """
    # Truncate very long CVs to avoid token limits (keep most important top section)
    truncated = raw_text[:6000] if len(raw_text) > 6000 else raw_text

    prompt = f"""Extract structured information from this CV/Resume text.

CV TEXT:
---
{truncated}
---

Return a JSON object with exactly these fields:
{{
  "name": "Full name of the candidate (string)",
  "email": "Email address (string, empty string if not found)",
  "phone": "Phone number (string, empty string if not found)",
  "linkedin": "LinkedIn URL if present (string, empty string if not found)",
  "github": "GitHub URL if present (string, empty string if not found)",
  "location": "City, Country or similar (string, empty string if not found)",
  "current_title": "Current or most recent job title (string)",
  "years_experience": "Estimated years of experience as integer (0 if unknown)",
  "skills": ["array", "of", "technical", "and", "soft", "skills", "found"],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "duration": "Date range e.g. Jan 2022 - Present",
      "description": "Key responsibilities and achievements (2-3 sentences)"
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University/College name",
      "year": "Graduation year or date range"
    }}
  ],
  "certifications": ["list", "of", "certifications"],
  "projects": [
    {{
      "name": "Project name",
      "description": "Brief description"
    }}
  ]
}}

Rules:
- Extract ONLY what is actually in the CV — do not invent anything
- Skills should be specific (e.g. "Python", "React", "AWS") not vague
- If a field is not found, use empty string or empty array
- Return ONLY the JSON, no explanation"""

    try:
        response = ask_llm(prompt, max_tokens=2500)
        data = _parse_json_response(response)
        if data and data.get("name"):
            return data
    except Exception:
        pass

    # Return empty structure if LLM fails
    return {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "location": "", "current_title": "", "years_experience": 0,
        "skills": [], "experience": [], "education": [],
        "certifications": [], "projects": [],
    }


# ─────────────────────────────────────────────
# ATS ANALYSIS
# ─────────────────────────────────────────────

def analyze_ats_llm(cv_text: str, job_description: str) -> Dict:
    """
    Semantic ATS analysis using LLM.
    Far more accurate than simple keyword matching.
    """
    cv_truncated = cv_text[:4000] if len(cv_text) > 4000 else cv_text
    jd_truncated = job_description[:3000] if len(job_description) > 3000 else job_description

    prompt = f"""You are an expert ATS (Applicant Tracking System) analyst. Analyze how well this CV matches the job description.

JOB DESCRIPTION:
---
{jd_truncated}
---

CANDIDATE CV:
---
{cv_truncated}
---

Provide a detailed ATS analysis. Return a JSON object:
{{
  "score": <integer 0-100, overall ATS match percentage>,
  "matched_skills": ["skills/keywords from JD that ARE present in CV"],
  "missing_skills": ["important skills/keywords from JD that are MISSING from CV"],
  "semantic_gaps": ["high-level gaps e.g. 'No cloud experience', 'Missing leadership examples'"],
  "strengths": ["2-3 specific strong points of this CV for this role"],
  "tips": [
    "Specific, actionable tip 1 with detail",
    "Specific, actionable tip 2 with detail",
    "Specific, actionable tip 3 with detail",
    "Specific, actionable tip 4 with detail",
    "Specific, actionable tip 5 with detail"
  ],
  "experience_match": <integer 0-100, how well experience level matches>,
  "keyword_density": "<low|medium|high> — how keyword-rich the CV is overall"
}}

Scoring guide:
- 85-100: Excellent match, likely to pass ATS
- 70-84: Good match, minor gaps
- 50-69: Moderate match, significant gaps to address
- Below 50: Poor match, major rework needed

Be specific and actionable in tips. Reference actual content from the CV and JD.
Return ONLY the JSON."""

    try:
        response = ask_llm(prompt, max_tokens=1500)
        data = _parse_json_response(response)
        if data and "score" in data:
            data["score"] = max(0, min(100, int(data["score"])))
            return data
    except Exception:
        pass

    # Fallback to basic analysis if LLM fails
    return {
        "score": 50,
        "matched_skills": [],
        "missing_skills": [],
        "semantic_gaps": ["Could not complete AI analysis — check your Groq API key"],
        "strengths": [],
        "tips": ["Please check your GROQ_API_KEY is set correctly and try again."],
        "experience_match": 50,
        "keyword_density": "unknown",
    }


# ─────────────────────────────────────────────
# PROFESSIONAL SUMMARY
# ─────────────────────────────────────────────

def generate_summary_llm(cv_data: Dict, job_description: Optional[str] = None) -> str:
    """
    Generate a tailored, compelling professional summary.
    """
    name = cv_data.get("name", "the candidate")
    title = cv_data.get("current_title", "Professional")
    years = cv_data.get("years_experience", 0)
    skills = ", ".join(cv_data.get("skills", [])[:8]) or "various technologies"

    job_context = ""
    if job_description:
        job_context = f"\n\nTarget Job Description (first 800 chars):\n{job_description[:800]}"

    prompt = f"""Write a compelling, ATS-optimized professional summary for a CV.

Candidate Details:
- Name: {name}
- Current/Recent Title: {title}
- Years of Experience: {years}
- Key Skills: {skills}{job_context}

Requirements:
- 3-4 sentences maximum
- Start with a strong opener (NOT "I am" or "Results-driven professional")
- Include 2-3 specific skills relevant to the role
- Mention the value they bring (quantify if possible)
- Sound human and genuine, not like a template
- Be tailored to the target job if provided
- No fluff, every word must earn its place

Return ONLY the summary text, no JSON, no quotes."""

    try:
        return ask_llm(prompt, system="You are an expert CV writer with 15 years of experience.", max_tokens=300)
    except Exception:
        skills_preview = ", ".join(cv_data.get("skills", [])[:4]) or "diverse technologies"
        return (
            f"Experienced {title} with {years}+ years of hands-on expertise in {skills_preview}. "
            f"Proven track record of delivering scalable solutions and driving measurable impact "
            f"in fast-paced environments."
        )


# ─────────────────────────────────────────────
# SKILLS ROADMAP
# ─────────────────────────────────────────────

def generate_roadmap_llm(missing_skills: List[str], target_role: str = "") -> str:
    """
    Generate a dynamic, personalized learning roadmap using LLM.
    """
    skills_list = ", ".join(missing_skills[:8]) if missing_skills else "general career skills"
    role_context = f" for a {target_role} role" if target_role else ""

    prompt = f"""Create a detailed, actionable learning roadmap{role_context} for someone who needs to develop these skills: {skills_list}.

For each skill, provide:
1. Why it matters for the target role
2. Estimated time to reach job-ready proficiency
3. The BEST free resources (be specific — actual course names, websites)
4. A concrete mini-project to build to prove the skill

Format as clean Markdown with sections, bullet points, and a priority order (learn highest-impact skills first).
Start with a brief intro paragraph, then the skill sections.
End with a "30-Day Action Plan" section with week-by-week tasks.

Be specific and practical — no generic advice. Real course names, real websites."""

    try:
        return ask_llm(
            prompt,
            system="You are a senior engineering mentor who creates practical learning roadmaps.",
            max_tokens=2000,
        )
    except Exception:
        # Fallback to static roadmap
        md = "# 📚 Skills Roadmap\n\n"
        for skill in missing_skills[:6]:
            md += f"## {skill}\n- Search YouTube for '{skill} tutorial for beginners'\n- Practice on freeCodeCamp.org\n\n"
        return md


# ─────────────────────────────────────────────
# COVER LETTER
# ─────────────────────────────────────────────

def generate_cover_letter_llm(cv_data: Dict, job_description: str) -> str:
    """
    Generate a tailored, professional cover letter.
    """
    name = cv_data.get("name", "Applicant")
    title = cv_data.get("current_title", "Professional")
    years = cv_data.get("years_experience", 0)
    skills = ", ".join(cv_data.get("skills", [])[:6]) or "various technologies"

    # Pull first experience for context
    experiences = cv_data.get("experience", [])
    recent_exp = ""
    if experiences:
        exp = experiences[0]
        recent_exp = f"{exp.get('title', '')} at {exp.get('company', '')} — {exp.get('description', '')}"

    jd_truncated = job_description[:2000] if len(job_description) > 2000 else job_description

    prompt = f"""Write a compelling, personalized cover letter for this job application.

CANDIDATE:
- Name: {name}
- Title: {title}
- Years Experience: {years}
- Key Skills: {skills}
- Recent Role: {recent_exp if recent_exp else 'Not specified'}

JOB DESCRIPTION:
{jd_truncated}

Cover Letter Requirements:
- Professional but warm tone — not stiff or robotic
- Opening paragraph: hook that connects their background to this specific role (NOT "I am writing to apply for...")
- Middle paragraph 1: most relevant experience/achievement with a specific example
- Middle paragraph 2: key skills that match the role's needs, show company knowledge
- Closing: confident call to action
- Length: 4 paragraphs, ~300 words total
- Use the candidate's name and reference specific details from the JD

Return ONLY the cover letter text. No subject line, no "Dear Hiring Manager" at top (the user will add that)."""

    try:
        return ask_llm(
            prompt,
            system="You are an expert career coach who writes compelling, personalized cover letters.",
            max_tokens=800,
        )
    except Exception:
        return (
            f"Dear Hiring Manager,\n\n"
            f"I am excited to apply for this position. With {years} years of experience in {skills}, "
            f"I am confident I would be a strong addition to your team.\n\n"
            f"[Cover letter generation failed — check your GROQ_API_KEY and try again.]\n\n"
            f"Sincerely,\n{name}"
        )


# ─────────────────────────────────────────────
# INTERVIEW PREP
# ─────────────────────────────────────────────

def generate_interview_prep_llm(cv_data: Dict, job_description: str) -> List[Dict]:
    """
    Generate likely interview questions + ideal answers based on CV + JD.
    """
    name = cv_data.get("name", "the candidate")
    title = cv_data.get("current_title", "Professional")
    skills = ", ".join(cv_data.get("skills", [])[:8]) or "various skills"
    jd_truncated = job_description[:2000] if len(job_description) > 2000 else job_description

    prompt = f"""Generate 6 realistic interview questions for this candidate applying to this job, with model answers.

CANDIDATE: {title} with skills: {skills}
JOB DESCRIPTION: {jd_truncated}

Return a JSON array of 6 objects:
[
  {{
    "question": "Interview question text",
    "category": "Technical|Behavioural|Situational|Cultural",
    "why_asked": "Why interviewers ask this (1 sentence)",
    "model_answer": "A strong, specific model answer using STAR method where relevant (3-5 sentences)"
  }}
]

Mix of question types: 2-3 technical, 2 behavioural, 1-2 situational.
Questions should be specific to this role and the candidate's background.
Model answers should sound genuine, not scripted.
Return ONLY the JSON array."""

    try:
        response = ask_llm(prompt, max_tokens=2000)
        # Handle array response
        cleaned = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(cleaned)
    except Exception:
        return [
            {
                "question": "Tell me about yourself.",
                "category": "Behavioural",
                "why_asked": "Interviewers use this to assess communication and self-awareness.",
                "model_answer": f"As a {title} with experience in {skills}, I've focused on delivering high-quality work. [LLM not available — set GROQ_API_KEY to get personalized answers]",
            }
        ]

# ─────────────────────────────────────────────
# JOB SEARCH STRATEGY
# ─────────────────────────────────────────────

def generate_job_search_strategy_llm(cv_data: Dict, job_description: str, missing_skills: List[str]) -> str:
    """
    Generate a tailored job search strategy bridging the gap between CV and JD.
    """
    name = cv_data.get("name", "the candidate")
    title = cv_data.get("current_title", "Professional")
    skills = ", ".join(cv_data.get("skills", [])[:8]) or "general tech skills"
    missing = ", ".join(missing_skills[:5]) if missing_skills else "advanced domain concepts"
    jd_truncated = job_description[:2000] if len(job_description) > 2000 else job_description

    if not job_description:
        return "Please provide a valid Job Description to generate a tailored job search strategy!"

    prompt = f"""You are an expert career strategist. This candidate wants to formulate a job search strategy based on their current profile and a target job description.

CANDIDATE TITLE: {title}
CANDIDATE CURRENT SKILLS: {skills}
JD SKILLS LACKING (TO UPSKILL/HIGHLIGHT): {missing}
TARGET JOB DESCRIPTION: {jd_truncated}

Create a highly actionable Job Search Strategy in clean Markdown.

Include:
### 🎯 Ideal Roles to Target
(Suggest 3-4 specific job titles that fit this profile)
### 🔑 Keywords to use in Job Portals
(List 5-8 highly relevant search keywords to find similar roles)
### 🚀 Networking & Outreach
(Give a short strategy on how to reach out to recruiters for this kind of role, including a 2-sentence cold message template)
### 🛠️ Skill Gap Action Plan
(A brief 1-week plan to bridge the gap with the missing skills: {missing})

Return ONLY the markdown text."""

    try:
        return ask_llm(
            prompt,
            system="You are an expert career strategist and recruiter.",
            max_tokens=1500,
        )
    except Exception:
        return f"### 🚀 Job Search Strategy\n\nTarget roles based on your skills: {skills}. Focus on upskilling in: {missing}.\n\n[LLM not available — set GROQ_API_KEY to get a detailed strategy]"
