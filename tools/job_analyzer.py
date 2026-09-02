"""
job_analyzer.py - Tool for analyzing job descriptions using an LLM.

This tool parses a job description and extracts structured requirements
that can be compared against a candidate's resume.
"""

import logging

from models.schemas import JobRequirements
from utils.helpers import call_llm, truncate_text

logger = logging.getLogger("resume_analyzer")


SYSTEM_MESSAGE = """You are an expert job description analyst. Your job is to carefully 
extract structured requirements from job descriptions.

IMPORTANT RULES:
- Only extract information that is ACTUALLY stated in the job description.
- Distinguish between required and preferred/nice-to-have skills.
- Extract both explicit keywords and implied technical terms.
- If the job description is vague, note what you can determine.
"""


def analyze_job_description(job_text: str) -> JobRequirements:
    """
    Analyze a job description and extract structured requirements.

    This tool sends the job description to the LLM to identify
    required skills, qualifications, and keywords.

    Args:
        job_text: The plain text of the job description.

    Returns:
        A JobRequirements object with extracted requirements.

    Raises:
        RuntimeError: If the LLM call fails after retries.
    """
    truncated_text = truncate_text(job_text)

    prompt = f"""Analyze the following job description and extract structured requirements.

Return a JSON object with these exact fields:
{{
    "job_title": "The job title or 'Not specified'",
    "company": "The company name or 'Not specified'",
    "required_skills": ["skills explicitly listed as required"],
    "preferred_skills": ["skills listed as preferred or nice-to-have"],
    "experience_level": "required experience level (e.g., '3+ years', 'Senior') or 'Not specified'",
    "education_requirements": ["required or preferred education qualifications"],
    "key_responsibilities": ["main responsibilities of the role"],
    "keywords": ["important technical terms, tools, and keywords from the posting"]
}}

Extract ALL relevant technical terms, tools, frameworks, and methodologies mentioned.
The "keywords" field should be comprehensive — include everything an ATS might scan for.

JOB DESCRIPTION:
{truncated_text}"""

    logger.info("Calling LLM to analyze job description...")
    result = call_llm(prompt, system_message=SYSTEM_MESSAGE)

    job_requirements = JobRequirements(**result)

    logger.info(
        f"Job analysis complete: {len(job_requirements.required_skills)} required skills, "
        f"{len(job_requirements.keywords)} keywords found"
    )
    return job_requirements
