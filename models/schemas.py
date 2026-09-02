"""
schemas.py - Pydantic data models for the Resume Analyzer Agent.

These models define the structured data that flows between the agent's tools.
Using Pydantic ensures type safety and makes it easy to parse JSON from the LLM.
"""

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Resume Data Models
# ─────────────────────────────────────────────────────────────────────────────

class ResumeData(BaseModel):
    """Structured representation of a parsed resume."""

    # Contact information
    name: str = Field(default="Not found", description="Candidate's full name")
    email: str = Field(default="Not found", description="Email address")
    phone: str = Field(default="Not found", description="Phone number")
    linkedin: str = Field(default="Not found", description="LinkedIn profile URL")
    location: str = Field(default="Not found", description="Location/city")

    # Skills
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Programming languages, frameworks, tools, technologies"
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Communication, leadership, teamwork, etc."
    )

    # Experience
    work_experience: list[dict] = Field(
        default_factory=list,
        description="List of work experiences with title, company, duration, bullets"
    )
    years_of_experience: str = Field(
        default="Not specified",
        description="Estimated total years of experience"
    )

    # Education
    education: list[dict] = Field(
        default_factory=list,
        description="List of education entries with degree, institution, year"
    )

    # Projects
    projects: list[dict] = Field(
        default_factory=list,
        description="List of projects with name, description, technologies"
    )

    # Certifications & Achievements
    certifications: list[str] = Field(
        default_factory=list,
        description="Professional certifications"
    )
    achievements: list[str] = Field(
        default_factory=list,
        description="Awards, honors, notable accomplishments"
    )

    # Resume quality indicators
    has_quantifiable_achievements: bool = Field(
        default=False,
        description="Whether the resume contains measurable results"
    )
    bullet_points: list[str] = Field(
        default_factory=list,
        description="All bullet points from the resume for improvement analysis"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Job Description Models
# ─────────────────────────────────────────────────────────────────────────────

class JobRequirements(BaseModel):
    """Structured representation of a parsed job description."""

    job_title: str = Field(default="Not specified", description="The job title")
    company: str = Field(default="Not specified", description="Company name")

    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills explicitly listed as required"
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Skills listed as nice-to-have or preferred"
    )
    experience_level: str = Field(
        default="Not specified",
        description="Required years/level of experience (e.g., '3+ years', 'Senior')"
    )
    education_requirements: list[str] = Field(
        default_factory=list,
        description="Required or preferred education qualifications"
    )
    key_responsibilities: list[str] = Field(
        default_factory=list,
        description="Main job responsibilities"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Important keywords and phrases from the job description"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Analysis Result Models
# ─────────────────────────────────────────────────────────────────────────────

class SkillMatch(BaseModel):
    """Result of matching a single skill between resume and job description."""

    skill: str = Field(description="The skill being evaluated")
    found_in_resume: bool = Field(description="Whether this skill appears in the resume")
    strength: str = Field(
        description="How strongly demonstrated: 'strong', 'weak', or 'missing'"
    )
    details: str = Field(
        default="",
        description="Brief explanation of how this skill is demonstrated (or not)"
    )


class ATSIssue(BaseModel):
    """A single ATS compatibility issue found in the resume."""

    issue_type: str = Field(
        description="Category: 'missing_keywords', 'formatting', 'section_headings', "
                    "'contact_info', 'content_quality', 'dates', 'other'"
    )
    description: str = Field(description="What the issue is")
    severity: str = Field(description="Impact level: 'high', 'medium', or 'low'")
    suggestion: str = Field(description="How to fix this issue")


class BulletImprovement(BaseModel):
    """A suggestion to improve a specific resume bullet point."""

    original: str = Field(description="The original bullet point from the resume")
    improved: str = Field(
        description="The improved version (only adds details supported by the resume)"
    )
    explanation: str = Field(description="Why this change makes the bullet stronger")


# ─────────────────────────────────────────────────────────────────────────────
# Final Report Model
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisReport(BaseModel):
    """The complete analysis report generated by the agent."""

    # Scores (AI-estimated, not actual ATS scores)
    overall_score: int = Field(
        default=0,
        description="Overall resume quality score out of 100 (AI estimate)"
    )
    job_match_score: int = Field(
        default=0,
        description="How well the resume matches the job description, out of 100 (AI estimate)"
    )

    # Strengths & Gaps
    strengths: list[str] = Field(
        default_factory=list,
        description="Key strengths found in the resume"
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Skills required by the job but not found in the resume"
    )
    matching_skills: list[SkillMatch] = Field(
        default_factory=list,
        description="Detailed skill-by-skill matching results"
    )

    # ATS
    ats_issues: list[ATSIssue] = Field(
        default_factory=list,
        description="ATS compatibility issues found"
    )

    # Detailed analysis sections
    experience_analysis: str = Field(
        default="No analysis available.",
        description="Analysis of work experience relevance"
    )
    project_analysis: str = Field(
        default="No analysis available.",
        description="Analysis of projects relevance"
    )
    keyword_analysis: str = Field(
        default="No analysis available.",
        description="Analysis of keyword coverage"
    )

    # Improvements
    recommendations: list[str] = Field(
        default_factory=list,
        description="Specific, actionable improvement suggestions"
    )
    bullet_improvements: list[BulletImprovement] = Field(
        default_factory=list,
        description="Suggested improvements for weak bullet points"
    )

    # Final summary
    final_recommendation: str = Field(
        default="No recommendation available.",
        description="Overall summary and next steps"
    )
