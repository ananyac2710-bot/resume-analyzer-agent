"""
resume_agent.py - The Agentic Orchestrator for Resume Analysis.

This is the CORE of the agentic architecture. The ResumeAnalyzerAgent:

1. Maintains a registry of available tools
2. Decides which tools to call based on available inputs
3. Chains tool outputs together (resume parsing → analysis → matching → report)
4. Handles failures gracefully — if one tool fails, it continues with partial data
5. Produces a structured AnalysisReport as the final output

WHY THIS IS AGENTIC:
- The agent has autonomous decision-making: it decides which tools to invoke
- It performs multi-step reasoning: each step builds on previous results
- It uses tool outputs to inform later tool calls
- It adapts to failures (e.g., if ATS check fails, it still produces a report)
- It orchestrates multiple specialized tools rather than being a single prompt
"""

import logging
from typing import Callable, Optional

from models.schemas import (
    AnalysisReport,
    ATSIssue,
    BulletImprovement,
    JobRequirements,
    ResumeData,
    SkillMatch,
)
from tools.resume_analyzer import analyze_resume
from tools.job_analyzer import analyze_job_description
from tools.ats_checker import check_ats_compatibility
from utils.helpers import call_llm, truncate_text

logger = logging.getLogger("resume_analyzer")


class ResumeAnalyzerAgent:
    """
    The main AI agent that orchestrates the resume analysis workflow.

    The agent follows this pipeline:
        1. Analyze the resume text → ResumeData
        2. Analyze the job description → JobRequirements
        3. Check ATS compatibility → list[ATSIssue]
        4. Generate final comprehensive report → AnalysisReport

    Each step is a separate tool call. The agent decides which tools
    to use and handles errors at each step independently.

    Attributes:
        tools: A dictionary mapping tool names to their functions.
        status_callback: An optional function to report progress to the UI.
    """

    def __init__(self, status_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the agent with its available tools.

        Args:
            status_callback: Optional function that receives status messages.
                           Used by the Streamlit UI to show progress updates.
        """
        # Register available tools — the agent can call any of these
        self.tools = {
            "analyze_resume": analyze_resume,
            "analyze_job_description": analyze_job_description,
            "check_ats_compatibility": check_ats_compatibility,
        }

        # Status callback for progress reporting
        self._status_callback = status_callback or (lambda msg: None)

    def _update_status(self, message: str):
        """Send a status update to the UI."""
        logger.info(message)
        self._status_callback(message)

    # ─────────────────────────────────────────────────────────────────────────
    # Main Agent Loop
    # ─────────────────────────────────────────────────────────────────────────

    def run(self, resume_text: str, job_text: str) -> AnalysisReport:
        """
        Run the full analysis pipeline.

        This is the agent's main entrypoint. It orchestrates all tools
        and produces the final AnalysisReport.

        Args:
            resume_text: Plain text extracted from the resume PDF.
            job_text: Plain text of the job description.

        Returns:
            A complete AnalysisReport with scores, analysis, and recommendations.
        """
        self._update_status("🤖 Agent initialized. Planning analysis steps...")

        # The agent will collect results from each tool
        resume_data: Optional[ResumeData] = None
        job_requirements: Optional[JobRequirements] = None
        ats_issues: list[ATSIssue] = []

        # ── Step 1: Analyze the resume ──────────────────────────────────────
        self._update_status("📄 Step 1/4: Analyzing resume content...")
        try:
            resume_data = self.tools["analyze_resume"](resume_text)
            self._update_status(
                f"✅ Resume analyzed: {len(resume_data.technical_skills)} technical skills, "
                f"{len(resume_data.work_experience)} work experiences found"
            )
        except Exception as e:
            err_msg = str(e)
            self._update_status(f"⚠️ Resume analysis failed: {err_msg}")
            logger.error(f"Resume analysis failed: {err_msg}", exc_info=True)
            resume_data = ResumeData()

        # ── Step 2: Analyze the job description ─────────────────────────────
        self._update_status("💼 Step 2/4: Analyzing job description...")
        try:
            job_requirements = self.tools["analyze_job_description"](job_text)
            self._update_status(
                f"✅ Job description analyzed: {len(job_requirements.required_skills)} "
                f"required skills, {len(job_requirements.keywords)} keywords identified"
            )
        except Exception as e:
            err_msg = str(e)
            self._update_status(f"⚠️ Job analysis failed: {err_msg}")
            logger.error(f"Job analysis failed: {err_msg}", exc_info=True)
            job_requirements = JobRequirements()

        # ── Step 3: Check ATS compatibility ─────────────────────────────────
        self._update_status("🤖 Step 3/4: Checking ATS compatibility...")
        try:
            ats_issues = self.tools["check_ats_compatibility"](
                resume_text, job_requirements
            )
            self._update_status(
                f"✅ ATS check complete: {len(ats_issues)} issues found"
            )
        except Exception as e:
            err_msg = str(e)
            self._update_status(f"⚠️ ATS check failed: {err_msg}")
            logger.error(f"ATS check failed: {err_msg}", exc_info=True)
            ats_issues = []

        # ── Step 4: Generate the final comprehensive report ─────────────────
        self._update_status("📊 Step 4/4: Generating comprehensive analysis report...")
        try:
            report = self._generate_final_report(
                resume_text=resume_text,
                job_text=job_text,
                resume_data=resume_data,
                job_requirements=job_requirements,
                ats_issues=ats_issues,
            )
            self._update_status("✅ Analysis complete!")
        except Exception as e:
            err_msg = str(e)
            self._update_status(f"⚠️ Report generation failed: {err_msg}")
            logger.error(f"Report generation failed: {err_msg}", exc_info=True)
            report = self._build_fallback_report(resume_data, job_requirements, ats_issues)

        return report

    # ─────────────────────────────────────────────────────────────────────────
    # Final Report Generation
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_final_report(
        self,
        resume_text: str,
        job_text: str,
        resume_data: ResumeData,
        job_requirements: JobRequirements,
        ats_issues: list[ATSIssue],
    ) -> AnalysisReport:
        """
        Generate the final comprehensive analysis report using the LLM.

        This step takes ALL the data gathered by previous tools and asks
        the LLM to produce a complete analysis with scoring, matching,
        and recommendations.

        Args:
            resume_text: Original resume text.
            job_text: Original job description text.
            resume_data: Structured resume data from Step 1.
            job_requirements: Structured job requirements from Step 2.
            ats_issues: ATS issues from Step 3.

        Returns:
            A complete AnalysisReport.
        """
        # Prepare summaries of what we've gathered so far
        resume_summary = self._format_resume_summary(resume_data)
        job_summary = self._format_job_summary(job_requirements)
        ats_summary = self._format_ats_summary(ats_issues)

        # Get some bullet points for improvement suggestions
        bullets_text = ""
        if resume_data.bullet_points:
            # Take up to 10 bullet points to keep the prompt reasonable
            sample_bullets = resume_data.bullet_points[:10]
            bullets_text = "\n".join(f"- {b}" for b in sample_bullets)

        system_message = """You are an expert career advisor and resume analyst. 
Generate a comprehensive, honest analysis comparing a resume against a job description.

CRITICAL RULES:
- Do NOT fabricate information about the candidate. Only reference what is in the resume.
- Provide SPECIFIC suggestions, not generic advice.
- When suggesting bullet point improvements, only add details that are reasonably 
  supported by the original resume content. If information is missing, use [placeholder] 
  notation and explain what the candidate should fill in.
- Scores should be fair and based on the actual content. Do NOT inflate scores.
- Clearly distinguish between information FROM the resume vs. your RECOMMENDATIONS.
- Label all scores as AI-generated estimates, not actual ATS scores."""

        prompt = f"""Based on the analysis below, generate a comprehensive resume analysis report.

EXTRACTED RESUME DATA:
{resume_summary}

JOB REQUIREMENTS:
{job_summary}

ATS ISSUES FOUND:
{ats_summary}

SAMPLE BULLET POINTS FROM RESUME (for improvement suggestions):
{bullets_text if bullets_text else "No bullet points extracted."}

ORIGINAL RESUME TEXT (for reference):
{truncate_text(resume_text, 5000)}

ORIGINAL JOB DESCRIPTION (for reference):
{truncate_text(job_text, 3000)}

Return a JSON object with this EXACT structure:
{{
    "overall_score": <0-100 integer, AI-estimated resume quality>,
    "job_match_score": <0-100 integer, AI-estimated match to this specific job>,
    "strengths": ["specific strength 1", "specific strength 2", ...],
    "missing_skills": ["skill required by job but not in resume", ...],
    "matching_skills": [
        {{
            "skill": "skill name",
            "found_in_resume": true/false,
            "strength": "strong" or "weak" or "missing",
            "details": "brief explanation"
        }}
    ],
    "experience_analysis": "detailed paragraph about experience relevance",
    "project_analysis": "detailed paragraph about projects relevance",
    "keyword_analysis": "detailed paragraph about keyword coverage",
    "recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2"
    ],
    "bullet_improvements": [
        {{
            "original": "original bullet text",
            "improved": "improved version with specific details",
            "explanation": "why this is better"
        }}
    ],
    "final_recommendation": "overall summary paragraph with next steps"
}}

IMPORTANT for matching_skills: Check ALL required AND preferred skills from the job.
IMPORTANT for recommendations: Be SPECIFIC. Reference actual content from the resume.
IMPORTANT for bullet_improvements: Only improve bullets that are actually weak. 
  Add details only if supported by the resume. Use [placeholder] for missing info."""

        result = call_llm(prompt, system_message=system_message, temperature=0.3)

        # Parse matching_skills
        matching_skills = [
            SkillMatch(**sm) for sm in result.get("matching_skills", [])
        ]

        # Parse bullet_improvements
        bullet_improvements = [
            BulletImprovement(**bi) for bi in result.get("bullet_improvements", [])
        ]

        # Build the final report, combining LLM output with our ATS issues
        report = AnalysisReport(
            overall_score=result.get("overall_score", 0),
            job_match_score=result.get("job_match_score", 0),
            strengths=result.get("strengths", []),
            missing_skills=result.get("missing_skills", []),
            matching_skills=matching_skills,
            ats_issues=ats_issues,  # Use the ATS issues from Step 3
            experience_analysis=result.get("experience_analysis", "No analysis available."),
            project_analysis=result.get("project_analysis", "No analysis available."),
            keyword_analysis=result.get("keyword_analysis", "No analysis available."),
            recommendations=result.get("recommendations", []),
            bullet_improvements=bullet_improvements,
            final_recommendation=result.get("final_recommendation", "No recommendation available."),
        )

        return report

    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods for Formatting
    # ─────────────────────────────────────────────────────────────────────────

    def _format_resume_summary(self, data: ResumeData) -> str:
        """Format ResumeData into a readable summary for the LLM prompt."""
        sections = [
            f"Name: {data.name}",
            f"Email: {data.email}",
            f"Phone: {data.phone}",
            f"Location: {data.location}",
            f"Years of Experience: {data.years_of_experience}",
            f"Technical Skills: {', '.join(data.technical_skills) if data.technical_skills else 'None found'}",
            f"Soft Skills: {', '.join(data.soft_skills) if data.soft_skills else 'None found'}",
        ]

        if data.work_experience:
            sections.append("Work Experience:")
            for exp in data.work_experience:
                title = exp.get("title", "Unknown")
                company = exp.get("company", "Unknown")
                duration = exp.get("duration", "Unknown")
                sections.append(f"  - {title} at {company} ({duration})")

        if data.education:
            sections.append("Education:")
            for edu in data.education:
                degree = edu.get("degree", "Unknown")
                institution = edu.get("institution", "Unknown")
                sections.append(f"  - {degree} from {institution}")

        if data.projects:
            sections.append("Projects:")
            for proj in data.projects:
                name = proj.get("name", "Unknown")
                techs = ", ".join(proj.get("technologies", []))
                sections.append(f"  - {name} ({techs})")

        if data.certifications:
            sections.append(f"Certifications: {', '.join(data.certifications)}")

        if data.achievements:
            sections.append(f"Achievements: {', '.join(data.achievements)}")

        sections.append(
            f"Has Quantifiable Achievements: {'Yes' if data.has_quantifiable_achievements else 'No'}"
        )

        return "\n".join(sections)

    def _format_job_summary(self, reqs: JobRequirements) -> str:
        """Format JobRequirements into a readable summary for the LLM prompt."""
        return (
            f"Job Title: {reqs.job_title}\n"
            f"Company: {reqs.company}\n"
            f"Required Skills: {', '.join(reqs.required_skills) if reqs.required_skills else 'None specified'}\n"
            f"Preferred Skills: {', '.join(reqs.preferred_skills) if reqs.preferred_skills else 'None specified'}\n"
            f"Experience Level: {reqs.experience_level}\n"
            f"Education: {', '.join(reqs.education_requirements) if reqs.education_requirements else 'None specified'}\n"
            f"Keywords: {', '.join(reqs.keywords) if reqs.keywords else 'None identified'}"
        )

    def _format_ats_summary(self, issues: list[ATSIssue]) -> str:
        """Format ATS issues into a readable summary for the LLM prompt."""
        if not issues:
            return "No ATS issues were found."

        lines = []
        for issue in issues:
            lines.append(
                f"- [{issue.severity.upper()}] {issue.issue_type}: {issue.description}"
            )
        return "\n".join(lines)

    def _build_fallback_report(
        self,
        resume_data: ResumeData,
        job_requirements: JobRequirements,
        ats_issues: list[ATSIssue],
    ) -> AnalysisReport:
        """
        Build a minimal report when the final LLM call fails.

        This ensures the user still gets some useful output even if
        the comprehensive analysis step encounters an error.
        """
        return AnalysisReport(
            overall_score=0,
            job_match_score=0,
            strengths=[
                f"Found {len(resume_data.technical_skills)} technical skills"
            ] if resume_data.technical_skills else [],
            missing_skills=[],
            matching_skills=[],
            ats_issues=ats_issues,
            experience_analysis=(
                f"Found {len(resume_data.work_experience)} work experience entries."
                if resume_data.work_experience
                else "No work experience found."
            ),
            project_analysis=(
                f"Found {len(resume_data.projects)} projects."
                if resume_data.projects
                else "No projects found."
            ),
            keyword_analysis="Full keyword analysis could not be completed due to an error.",
            recommendations=[
                "The full analysis could not be completed. Please try again.",
                "If the issue persists, check your API key and internet connection.",
            ],
            bullet_improvements=[],
            final_recommendation=(
                "The analysis encountered an error during report generation. "
                "The partial results above are based on the data that was successfully extracted. "
                "Please try running the analysis again."
            ),
        )
