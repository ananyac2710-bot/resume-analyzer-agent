"""
app.py - Streamlit UI for the AI Resume Analyzer Agent.

This is the main entry point of the application. Run with:
    streamlit run app.py

The UI provides:
- Resume PDF upload
- Job description input (text or PDF)
- An "Analyze Resume" button
- Progress indicators during analysis
- Expandable result sections with scores, analysis, and recommendations
"""

import streamlit as st
import logging

from tools.pdf_parser import extract_text_from_pdf
from agents.resume_agent import ResumeAnalyzerAgent
from utils.helpers import format_score_color

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume_analyzer")


# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Resume Analyzer Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS for a polished look
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    .main-header h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
    }
    .main-header p {
        color: #888;
        font-size: 1.1rem;
    }

    /* Score card styling */
    .score-card {
        text-align: center;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333;
        background: #1a1a2e;
        margin-bottom: 1rem;
    }
    .score-card h2 {
        margin: 0;
        font-size: 3rem;
        font-weight: 800;
    }
    .score-card p {
        margin: 0.3rem 0 0 0;
        color: #aaa;
        font-size: 0.9rem;
    }
    .score-green h2 { color: #00c853; }
    .score-orange h2 { color: #ff9100; }
    .score-red h2 { color: #ff1744; }

    /* Severity badges */
    .severity-high {
        background: #ff1744;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .severity-medium {
        background: #ff9100;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .severity-low {
        background: #00c853;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Skill match indicators */
    .skill-strong { color: #00c853; }
    .skill-weak { color: #ff9100; }
    .skill-missing { color: #ff1744; }

    /* Disclaimer banner */
    .disclaimer {
        background: #2a2a3e;
        border-left: 4px solid #667eea;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin: 1rem 0;
        font-size: 0.85rem;
        color: #bbb;
    }

    /* Bullet improvement card */
    .bullet-card {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>📄 AI Resume Analyzer Agent</h1>
    <p>Upload your resume and a job description to get AI-powered feedback</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Input Controls
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("📤 Upload Your Documents")

    # Resume upload
    st.subheader("1. Resume (PDF)")
    resume_file = st.file_uploader(
        "Upload your resume",
        type=["pdf"],
        help="Upload a text-based PDF resume. Scanned images are not supported.",
        key="resume_uploader",
    )

    st.divider()

    # Job description input
    st.subheader("2. Job Description")

    jd_input_method = st.radio(
        "How would you like to provide the job description?",
        ["Paste text", "Upload PDF"],
        key="jd_method",
    )

    job_description_text = ""

    if jd_input_method == "Paste text":
        job_description_text = st.text_area(
            "Paste the job description here",
            height=200,
            placeholder="Paste the full job description text here...",
            key="jd_textarea",
        )
    else:
        jd_file = st.file_uploader(
            "Upload job description PDF",
            type=["pdf"],
            help="Upload the job description as a PDF.",
            key="jd_uploader",
        )
        if jd_file is not None:
            try:
                job_description_text = extract_text_from_pdf(jd_file.read())
                st.success("✅ Job description PDF loaded successfully!")
            except ValueError as e:
                st.error(f"❌ {str(e)}")

    st.divider()

    # Analyze button
    analyze_button = st.button(
        "🚀 Analyze Resume",
        type="primary",
        use_container_width=True,
        key="analyze_btn",
    )

    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        ⚠️ <strong>Disclaimer:</strong> All scores and analysis are AI-generated estimates. 
        They do not represent actual ATS scores or guarantee interview outcomes.
        The AI will not fabricate information about your qualifications.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main Content — Analysis Results
# ─────────────────────────────────────────────────────────────────────────────

def display_score_cards(report):
    """Display the overall and job match score cards."""
    col1, col2 = st.columns(2)

    overall_color = format_score_color(report.overall_score)
    match_color = format_score_color(report.job_match_score)

    with col1:
        st.markdown(f"""
        <div class="score-card score-{overall_color}">
            <h2>{report.overall_score}/100</h2>
            <p>Overall Resume Score</p>
            <p style="font-size: 0.75rem; color: #666;">(AI-generated estimate)</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="score-card score-{match_color}">
            <h2>{report.job_match_score}/100</h2>
            <p>Job Match Score</p>
            <p style="font-size: 0.75rem; color: #666;">(AI-generated estimate)</p>
        </div>
        """, unsafe_allow_html=True)


def display_strengths(report):
    """Display the strengths section."""
    with st.expander("✅ Strengths", expanded=True):
        if report.strengths:
            for strength in report.strengths:
                st.markdown(f"- {strength}")
        else:
            st.info("No specific strengths identified.")


def display_missing_skills(report):
    """Display missing skills section."""
    with st.expander("❌ Missing Skills", expanded=True):
        if report.missing_skills:
            for skill in report.missing_skills:
                st.markdown(f"- 🔴 {skill}")
        else:
            st.success("No critical missing skills identified!")


def display_matching_skills(report):
    """Display the detailed skill matching section."""
    with st.expander("🎯 Skill Matching Details", expanded=False):
        if report.matching_skills:
            for match in report.matching_skills:
                # Choose icon and color based on strength
                if match.strength == "strong":
                    icon = "🟢"
                    css_class = "skill-strong"
                elif match.strength == "weak":
                    icon = "🟡"
                    css_class = "skill-weak"
                else:
                    icon = "🔴"
                    css_class = "skill-missing"

                st.markdown(
                    f"{icon} **<span class='{css_class}'>{match.skill}</span>** — "
                    f"{match.details}",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No skill matching data available.")


def display_ats_issues(report):
    """Display ATS compatibility issues."""
    with st.expander(f"🤖 ATS Issues ({len(report.ats_issues)} found)", expanded=False):
        if report.ats_issues:
            for issue in report.ats_issues:
                severity_class = f"severity-{issue.severity}"
                st.markdown(
                    f"<span class='{severity_class}'>{issue.severity.upper()}</span> "
                    f"**{issue.issue_type.replace('_', ' ').title()}**: {issue.description}",
                    unsafe_allow_html=True,
                )
                st.markdown(f"  💡 *{issue.suggestion}*")
                st.markdown("---")
        else:
            st.success("No ATS issues found!")


def display_analysis_sections(report):
    """Display experience, project, and keyword analysis."""
    with st.expander("💼 Experience Analysis", expanded=False):
        st.markdown(report.experience_analysis)

    with st.expander("📂 Project Analysis", expanded=False):
        st.markdown(report.project_analysis)

    with st.expander("🔑 Keyword Analysis", expanded=False):
        st.markdown(report.keyword_analysis)


def display_recommendations(report):
    """Display specific improvement recommendations."""
    with st.expander("💡 Recommended Improvements", expanded=True):
        if report.recommendations:
            for i, rec in enumerate(report.recommendations, 1):
                st.markdown(f"**{i}.** {rec}")
        else:
            st.info("No specific recommendations at this time.")


def display_bullet_improvements(report):
    """Display improved bullet point suggestions."""
    with st.expander("✍️ Improved Bullet Points", expanded=False):
        if report.bullet_improvements:
            for i, bullet in enumerate(report.bullet_improvements, 1):
                st.markdown(f"**Bullet {i}:**")

                st.markdown(f"""
<div class="bullet-card">
    <strong>Original:</strong><br>
    <span style="color: #ff9100;">"{bullet.original}"</span><br><br>
    <strong>Improved:</strong><br>
    <span style="color: #00c853;">"{bullet.improved}"</span><br><br>
    <em style="color: #888;">💡 {bullet.explanation}</em>
</div>
                """, unsafe_allow_html=True)
        else:
            st.info("No bullet point improvements suggested.")


def display_final_recommendation(report):
    """Display the final overall recommendation."""
    with st.expander("📋 Final Recommendation", expanded=True):
        st.markdown(report.final_recommendation)


def generate_text_report(report) -> str:
    """Generate a plain-text version of the report for download."""
    lines = [
        "=" * 60,
        "RESUME ANALYSIS REPORT",
        "(AI-Generated — Not an actual ATS score)",
        "=" * 60,
        "",
        f"Overall Score: {report.overall_score}/100",
        f"Job Match Score: {report.job_match_score}/100",
        "",
        "STRENGTHS",
        "-" * 40,
    ]
    for s in report.strengths:
        lines.append(f"  • {s}")

    lines.extend(["", "MISSING SKILLS", "-" * 40])
    for s in report.missing_skills:
        lines.append(f"  • {s}")

    lines.extend(["", "MATCHING SKILLS", "-" * 40])
    for m in report.matching_skills:
        status = "✓" if m.found_in_resume else "✗"
        lines.append(f"  [{status}] {m.skill} ({m.strength}) — {m.details}")

    lines.extend(["", "ATS ISSUES", "-" * 40])
    for issue in report.ats_issues:
        lines.append(f"  [{issue.severity.upper()}] {issue.issue_type}: {issue.description}")
        lines.append(f"          Suggestion: {issue.suggestion}")

    lines.extend(["", "EXPERIENCE ANALYSIS", "-" * 40, report.experience_analysis])
    lines.extend(["", "PROJECT ANALYSIS", "-" * 40, report.project_analysis])
    lines.extend(["", "KEYWORD ANALYSIS", "-" * 40, report.keyword_analysis])

    lines.extend(["", "RECOMMENDED IMPROVEMENTS", "-" * 40])
    for i, r in enumerate(report.recommendations, 1):
        lines.append(f"  {i}. {r}")

    lines.extend(["", "IMPROVED BULLET POINTS", "-" * 40])
    for i, b in enumerate(report.bullet_improvements, 1):
        lines.append(f"  {i}. Original: {b.original}")
        lines.append(f"     Improved: {b.improved}")
        lines.append(f"     Why: {b.explanation}")
        lines.append("")

    lines.extend(["", "FINAL RECOMMENDATION", "-" * 40, report.final_recommendation])
    lines.extend(["", "=" * 60, "End of Report", "=" * 60])

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Analysis Execution
# ─────────────────────────────────────────────────────────────────────────────

if analyze_button:
    # ── Validate inputs ─────────────────────────────────────────────────────
    if resume_file is None:
        st.error("❌ Please upload a resume PDF.")
        st.stop()

    if not job_description_text.strip():
        st.error("❌ Please provide a job description (paste text or upload PDF).")
        st.stop()

    # ── Extract resume text ─────────────────────────────────────────────────
    with st.spinner("Extracting text from resume PDF..."):
        try:
            resume_text = extract_text_from_pdf(resume_file.read())
        except ValueError as e:
            st.error(f"❌ Resume PDF Error: {str(e)}")
            st.stop()

    # ── Run the Agent ───────────────────────────────────────────────────────
    # Create a status container to show real-time progress
    status_container = st.empty()
    progress_bar = st.progress(0)

    # Track progress steps
    step_count = [0]

    def status_callback(message: str):
        """Update the UI with the agent's progress."""
        status_container.info(message)
        step_count[0] += 1
        # We have roughly 8-10 status updates, so each is ~10-12%
        progress_bar.progress(min(step_count[0] * 12, 100))

    # ── Check API key before running ───────────────────────────────────
    import os
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True) or find_dotenv())
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        st.error(
            "❌ **GEMINI_API_KEY is not configured.**\n\n"
            "Please create a `.env` file in the `resume-analyzer-agent/` folder with:\n\n"
            "```\nGEMINI_API_KEY=your_actual_gemini_key_here\n```\n\n"
            "💡 Get a **FREE** Gemini API key from: https://aistudio.google.com/app/apikey"
        )
        st.stop()

    try:
        # Create the agent with our status callback
        agent = ResumeAnalyzerAgent(status_callback=status_callback)

        # Run the full analysis pipeline
        report = agent.run(resume_text, job_description_text)

        # Clear progress indicators
        progress_bar.progress(100)
        status_container.success("✅ Analysis complete!")

    except ValueError as e:
        err = str(e)
        st.error(f"❌ **Configuration Error:** {err}")
        if "GEMINI_API_KEY" in err:
            st.info(
                "💡 **How to fix:** Create a `.env` file in the `resume-analyzer-agent/` "
                "folder containing:\n```\nGEMINI_API_KEY=your_gemini_key_here\n```\n"
                "Get a FREE key from: https://aistudio.google.com/app/apikey"
            )
        st.stop()
    except RuntimeError as e:
        # LLM call failures
        st.error(f"❌ **Analysis Error:** {str(e)}")
        st.stop()
    except Exception as e:
        # Unexpected errors
        st.error(f"❌ **Unexpected Error:** {str(e)}")
        logger.exception("Unexpected error during analysis")
        st.stop()

    # ── Display Results ─────────────────────────────────────────────────────
    st.markdown("---")

    # Score cards at the top
    display_score_cards(report)

    # Expandable analysis sections
    display_strengths(report)
    display_missing_skills(report)
    display_matching_skills(report)
    display_ats_issues(report)
    display_analysis_sections(report)
    display_recommendations(report)
    display_bullet_improvements(report)
    display_final_recommendation(report)

    # Download button for the full report
    st.markdown("---")
    text_report = generate_text_report(report)
    st.download_button(
        label="📥 Download Full Report (Text)",
        data=text_report,
        file_name="resume_analysis_report.txt",
        mime="text/plain",
        use_container_width=True,
        key="download_report",
    )

else:
    # Show instructions when no analysis has been run yet
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📤 Step 1")
        st.markdown("Upload your resume as a **PDF** file using the sidebar.")

    with col2:
        st.markdown("### 📝 Step 2")
        st.markdown("Paste a **job description** or upload it as a PDF.")

    with col3:
        st.markdown("### 🚀 Step 3")
        st.markdown("Click **Analyze Resume** to get your AI-powered feedback.")

    st.markdown("---")
    st.markdown("""
    <div class="disclaimer">
        <strong>How it works:</strong> This AI agent analyzes your resume against a job description 
        using multiple specialized tools — resume parser, job analyzer, ATS checker, and improvement 
        advisor — to provide comprehensive, actionable feedback. All analysis is AI-generated and 
        should be used as guidance, not as definitive assessment.
    </div>
    """, unsafe_allow_html=True)
