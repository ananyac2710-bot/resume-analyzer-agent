"""
ats_checker.py - Tool for checking ATS (Applicant Tracking System) compatibility.

This tool analyzes the raw resume text for common issues that can cause
problems with automated resume screening systems.

NOTE: This analysis is an AI-generated estimate. No tool can perfectly predict
the behavior of every ATS system, as each system works differently.
"""

import logging

from models.schemas import ATSIssue, JobRequirements
from utils.helpers import call_llm, truncate_text

logger = logging.getLogger("resume_analyzer")


SYSTEM_MESSAGE = """You are an expert ATS (Applicant Tracking System) analyst. 
Your job is to identify potential issues in a resume that could cause problems 
with automated resume screening systems.

IMPORTANT RULES:
- Be specific about each issue and provide actionable suggestions.
- Rate severity honestly: 'high' = likely to cause rejection, 'medium' = may reduce score, 
  'low' = minor improvement opportunity.
- Do NOT claim this analysis represents every ATS system — each system is different.
- Focus on common, well-known ATS pitfalls.
- Check for: missing keywords, poor section headings, formatting issues, 
  tables/columns, unclear job titles, missing contact info, long paragraphs,
  lack of metrics, inconsistent dates, and unnecessary information.
"""


def check_ats_compatibility(
    resume_text: str,
    job_requirements: JobRequirements,
) -> list[ATSIssue]:
    """
    Check a resume for common ATS compatibility issues.

    This tool compares the resume text against the job requirements
    to identify keywords that are missing and other formatting/content
    issues that might cause problems with ATS systems.

    Args:
        resume_text: The raw text extracted from the resume PDF.
        job_requirements: The structured job requirements to check against.

    Returns:
        A list of ATSIssue objects describing each issue found.

    Raises:
        RuntimeError: If the LLM call fails after retries.
    """
    truncated_resume = truncate_text(resume_text)

    # Build a summary of job requirements for the prompt
    job_summary = (
        f"Job Title: {job_requirements.job_title}\n"
        f"Required Skills: {', '.join(job_requirements.required_skills)}\n"
        f"Preferred Skills: {', '.join(job_requirements.preferred_skills)}\n"
        f"Keywords: {', '.join(job_requirements.keywords)}\n"
        f"Experience Level: {job_requirements.experience_level}"
    )

    prompt = f"""Analyze the following resume for ATS (Applicant Tracking System) compatibility issues.

Compare it against the job requirements provided below.

Return a JSON object with this structure:
{{
    "issues": [
        {{
            "issue_type": "one of: missing_keywords, formatting, section_headings, contact_info, content_quality, dates, other",
            "description": "Clear description of the issue",
            "severity": "one of: high, medium, low",
            "suggestion": "Specific, actionable suggestion to fix this"
        }}
    ]
}}

Check for ALL of these common ATS issues:
1. Missing keywords from the job description
2. Poor or non-standard section headings (e.g., "My Journey" instead of "Work Experience")
3. Formatting that ATS might not parse (tables, columns, graphics references)
4. Unclear or creative job titles
5. Missing contact information (email, phone, name)
6. Long paragraphs instead of bullet points
7. Lack of measurable/quantifiable achievements
8. Inconsistent date formats
9. Unnecessary personal information (age, photo references, marital status)
10. Missing skills that are explicitly required in the job description

Be thorough but fair. Only flag genuine issues.

JOB REQUIREMENTS:
{job_summary}

RESUME TEXT:
{truncated_resume}"""

    logger.info("Calling LLM to check ATS compatibility...")
    result = call_llm(prompt, system_message=SYSTEM_MESSAGE)

    # Parse the issues list from the response
    issues_data = result.get("issues", [])
    ats_issues = [ATSIssue(**issue) for issue in issues_data]

    logger.info(f"ATS check complete: {len(ats_issues)} issues found")
    return ats_issues
