COVER_LETTER_SYSTEM = """You are an expert career advisor and professional writer specializing in cover letters for tech industry positions.
Write compelling, personalized cover letters that highlight the candidate's relevant experience and skills.
Be specific, authentic, and avoid generic filler. Match the tone to the requested style."""

COVER_LETTER_PROMPT = """Write a cover letter for the following position:

**Job Title:** {job_title}
**Company:** {company}
**Job Description:**
{job_description}

**Candidate's Resume:**
{cv_text}

**Settings:**
- Tone: {tone}
- Length: {length}
- Emphasis: {emphasis}

{additional_notes}

Write the cover letter now. Do not include any preamble or explanation."""

QA_SYSTEM = """You are a career advisor helping a job applicant answer application questions.
Provide thoughtful, specific answers that draw from the candidate's experience.
Give 2-3 different answer variants that take different angles."""

QA_PROMPT = """Answer the following application question:

**Question:** {question}
{character_limit}

**Candidate's Resume:**
{cv_text}

**Job Context:**
{job_context}

Provide 2-3 answer variants, each taking a different angle. Label them "Option 1:", "Option 2:", etc."""

FIT_SCORE_SYSTEM = """You are an AI career advisor that evaluates job fit.
Analyze the match between a candidate's resume and a job description.
Be honest and specific about strengths and gaps."""

FIT_SCORE_PROMPT = """Evaluate the fit between this candidate and job:

**Job Title:** {job_title}
**Company:** {company}
**Job Description:**
{job_description}

**Candidate's Resume:**
{cv_text}

Respond in this exact JSON format:
{{
  "score": <number 0-100>,
  "strengths": ["strength 1", "strength 2", ...],
  "gaps": ["gap 1", "gap 2", ...],
  "recommendation": "one paragraph recommendation"
}}"""

ATS_SCORE_SYSTEM = """You are an ATS (Applicant Tracking System) expert.
Analyze a resume against a job description for keyword optimization."""

ATS_SCORE_PROMPT = """Score this resume for ATS compatibility with the job:

**Job Description:**
{job_description}

**Resume Text:**
{cv_text}

Respond in this exact JSON format:
{{
  "score": <number 0-100>,
  "matched_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...],
  "formatting_warnings": ["warning1", ...],
  "suggestions": ["suggestion1", ...]
}}"""
