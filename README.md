# 📄 AI Resume Analyzer Agent

An AI-powered resume analysis tool that compares your resume against a job description and provides actionable feedback. Built with Python, Streamlit, and **Google Gemini AI** (free tier available).

> ⚠️ **Disclaimer**: All scores and analysis are AI-generated estimates. They do not represent actual ATS scores or guarantee interview outcomes.

---

## 🚀 Features

- **Resume Parsing** — Upload a PDF resume and extract text automatically
- **Job Description Analysis** — Paste or upload a job description
- **AI Resume Analysis** — Extract skills, experience, education, projects, and more
- **Job Matching** — Get a match score with detailed skill-by-skill comparison
- **ATS Compatibility Check** — Identify common ATS issues in your resume
- **Improvement Suggestions** — Get specific, actionable recommendations
- **Bullet Point Improvement** — Transform weak bullet points into strong ones
- **Downloadable Report** — Export the full analysis as a text file

---

## 🏗️ Architecture

This project uses an **agentic architecture** where a central orchestrator (the `ResumeAnalyzerAgent`) manages multiple specialized tools:

```
User Input (Resume PDF + Job Description)
         │
         ▼
    ┌─────────────────────┐
    │   Streamlit UI      │
    │     (app.py)        │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  ResumeAnalyzerAgent│   ← The Agentic Orchestrator
    │  (resume_agent.py)  │
    └─────────┬───────────┘
              │
     ┌────────┼────────┬──────────┐
     ▼        ▼        ▼          ▼
  ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐
  │PDF   │ │Resume│ │Job   │ │ATS     │
  │Parser│ │Analyz│ │Analyz│ │Checker │
  └──────┘ └──────┘ └──────┘ └────────┘
     │        │        │          │
     └────────┼────────┴──────────┘
              │
              ▼
    ┌─────────────────────┐
    │   Analysis Report   │
    │ (Structured Output) │
    └─────────────────────┘
```

### Why This Is an Agentic AI Project

| Agentic Trait | Implementation |
|---|---|
| **Tool Use** | The agent has 4 distinct tools: `parse_pdf`, `analyze_resume`, `analyze_job`, `check_ats` |
| **Decision Making** | The agent decides which tools to invoke and adapts when tools fail |
| **Multi-Step Reasoning** | Each step builds on previous results (parse → analyze → match → report) |
| **Graceful Degradation** | If one tool fails, the agent continues with partial data |
| **Structured Output** | All data flows through Pydantic schemas for type-safe reasoning |
| **Orchestration** | The agent coordinates multiple LLM calls, each with a specialized role |

---

## 📁 Project Structure

```
resume-analyzer-agent/
│
├── app.py                    # Streamlit UI — main entry point
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules
│
├── agents/
│   └── resume_agent.py       # Agentic orchestrator — coordinates all tools
│
├── tools/
│   ├── pdf_parser.py         # PDF text extraction (PyMuPDF)
│   ├── resume_analyzer.py    # Resume content analysis (LLM)
│   ├── job_analyzer.py       # Job description analysis (LLM)
│   └── ats_checker.py        # ATS compatibility check (LLM)
│
├── models/
│   └── schemas.py            # Pydantic data models
│
└── utils/
    └── helpers.py            # Gemini LLM client, utilities
```

---

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.10 or later
- A **free** Google Gemini API key → [Get one here](https://aistudio.google.com/app/apikey)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/resume-analyzer-agent.git
cd resume-analyzer-agent
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Your API Key

```bash
# Copy the example env file
cp .env.example .env
```

Then open `.env` and replace the placeholder with your actual Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
```

> ⚠️ **Never commit your `.env` file** — it's already listed in `.gitignore`.

### Step 5: Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 📖 How to Use

1. **Upload your resume** — Click the file uploader in the sidebar and select your resume PDF
2. **Add a job description** — Either paste the text or upload a PDF
3. **Click "Analyze Resume"** — The agent will run its full analysis pipeline
4. **Review results** — Check scores, strengths, missing skills, and recommendations
5. **Download the report** — Click the download button for a text version

---

## 📝 Example Inputs

### Sample Job Description (paste this to test)

```
Senior Python Developer - TechCorp Inc.

We are looking for a Senior Python Developer to join our backend team.

Requirements:
- 5+ years of experience in Python development
- Strong knowledge of Django or FastAPI
- Experience with PostgreSQL and Redis
- Familiarity with Docker and Kubernetes
- Understanding of CI/CD pipelines
- Experience with RESTful API design
- Strong problem-solving skills
- Excellent communication skills

Nice to have:
- Experience with AWS or GCP
- Knowledge of machine learning libraries
- Experience with microservices architecture
- Familiarity with GraphQL

Responsibilities:
- Design and develop scalable backend services
- Write clean, maintainable, and well-tested code
- Participate in code reviews
- Mentor junior developers
- Collaborate with frontend and DevOps teams

Education:
- Bachelor's degree in Computer Science or related field
```

For the resume, use any text-based PDF resume you have.

---

## 🔧 Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | **(required)** | Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | LLM model to use |

**Available models:**
- `gemini-2.0-flash` — Fast, capable, free tier available ✅ (recommended)
- `gemini-1.5-flash` — Slightly older but also free tier
- `gemini-1.5-pro` — More powerful, higher quota usage

---

## ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core programming language |
| **Streamlit** | Web UI framework |
| **Google Gemini API** | LLM for intelligent analysis (free tier available) |
| **PyMuPDF (fitz)** | PDF text extraction |
| **Pydantic** | Data validation and schemas |
| **python-dotenv** | Environment variable management |

---

## 🔒 Security Notes

- API keys are stored in `.env` (never committed to git)
- Uploaded resumes are processed in memory and not permanently stored
- No user data is saved to disk

---

## 📄 License

This project is for educational and personal use. Feel free to modify and extend it for your own needs.
