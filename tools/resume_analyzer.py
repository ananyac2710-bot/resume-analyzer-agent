"""
resume_analyzer.py - Tool for analyzing resume content using an LLM.

This tool sends the resume text to the LLM with a structured prompt
and returns a ResumeData object containing extracted information.
"""

import logging

from models.schemas import ResumeData
from utils.helpers import call_llm, truncate_text

logger = logging.getLogger("resume_analyzer")


# The system message tells the LLM its role and constraints
SYSTEM_MESSAGE = """You are an expert resume analyst. Your job is to carefully extract 
structured information from resumes. 

IMPORTANT RULES:
- Only extract information that is ACTUALLY PRESENT in the resume.
- Do NOT invent, assume, or fabricate any skills, experience, or qualifications.
- If information is not found, use empty lists or "Not found" / "Not specified".
- Be thorough — look for skills mentioned anywhere (in projects, experience, etc.).
- Distinguish between technical skills and soft skills.
"""


def analyze_resume(resume_text: str) -> ResumeData:
    """
    Analyze resume text and extract structured data using an LLM.

    This tool sends the full resume text to the LLM with instructions
    to extract skills, experience, education, projects, and other data.

    Args:
        resume_text: The plain text extracted from the resume PDF.

    Returns:
        A ResumeData object with all extracted information.

    Raises:
        RuntimeError: If the LLM call fails after retries.
    """
    # Truncate very long resumes to avoid token limits
    truncated_text = truncate_text(resume_text)

    prompt = f"""Analyze the following resume and extract structured information.

Return a JSON object with these exact fields:
{{
    "name": "candidate's full name or 'Not found'",
    "email": "email address or 'Not found'",
    "phone": "phone number or 'Not found'",
    "linkedin": "LinkedIn URL or 'Not found'",
    "location": "city/location or 'Not found'",
    "technical_skills": ["list", "of", "technical", "skills"],
    "soft_skills": ["list", "of", "soft", "skills"],
    "work_experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "duration": "Start - End",
            "bullets": ["responsibility 1", "responsibility 2"]
        }}
    ],
    "years_of_experience": "estimated total years or 'Not specified'",
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "School Name",
            "year": "Graduation Year or 'Not specified'"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Brief description",
            "technologies": ["tech1", "tech2"]
        }}
    ],
    "certifications": ["certification 1", "certification 2"],
    "achievements": ["achievement 1", "achievement 2"],
    "has_quantifiable_achievements": true/false,
    "bullet_points": ["all bullet points from work experience and projects"]
}}

IMPORTANT: Only include information that is ACTUALLY in the resume. 
Do not invent or assume anything.

RESUME TEXT:
{truncated_text}"""

    logger.info("Calling LLM to analyze resume...")
    result = call_llm(prompt, system_message=SYSTEM_MESSAGE)

    # Parse the LLM response into our Pydantic model
    # Pydantic will validate the data and use defaults for missing fields
    resume_data = ResumeData(**result)

    logger.info(
        f"Resume analysis complete: {len(resume_data.technical_skills)} technical skills, "
        f"{len(resume_data.work_experience)} work experiences found"
    )
    return resume_data
