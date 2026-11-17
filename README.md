# SkillBridge.AI: AI-Powered Resume Job Matcher and Career Agent

SkillBridge.AI is a full-stack prototype based on the paper "AI-Powered Resume Job Matcher & Career Agent." It analyzes resume text, extracts normalized technical skills, ranks job roles with skill overlap and market-demand weighting, identifies skill gaps, recommends suitable jobs, creates learning plans, and drafts cover letters.

## Features

- Resume ingestion through pasted text or PDF/TXT upload
- Rule-based skill extraction and normalization
- Job-role scoring with the paper's weighted formula:
  `final = 0.6 * skill_match + 0.4 * normalized_market_demand`
- Skill gap analysis using set difference
- Suitable job recommendations with title, company, location, salary, apply links, and job-specific cover letters
- Up to 50 recommended jobs across official career sites and major job portals
- Login, signup, logout, real SMTP OTP password reset, and saved jobs
- Saved-job collection with filters for salary, match score, and role
- Separate same-tab pages for login, signup, forget password, saved jobs, and direct job application
- Contact-us section with centered mail, WhatsApp, phone, LinkedIn, Instagram, and GitHub icons
- Tool-style learning plan generation with verified resource links
- Context-aware cover letter generation from matched skills and role responsibilities
- Professional responsive frontend
- Python backend API with no required package installation

## Run

```bash
python server.py
```

Open:

```text
http://127.0.0.1:8000
```

If port 8000 is busy:

```bash
$env:PORT=8010; python server.py
```

## Real OTP Email Setup

Forget-password OTP uses real SMTP email. Set these environment variables before publishing or testing OTP:

```bash
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="your_email@gmail.com"
$env:SMTP_PASSWORD="your_app_password"
$env:SMTP_FROM="your_email@gmail.com"
python server.py
```

For Gmail, use an app password from your Google account security settings. If SMTP is not configured, the app blocks the reset request and asks for server email setup.

## API Endpoints

- `GET /api/roles` returns the supported role catalog.
- `GET /api/sample-resume` returns a demo resume.
- `GET /api/jobs/{job_id}` returns one exact recommended job for direct application.
- `POST /api/analyze` extracts skills and ranks roles.
- `POST /api/learning-plan` creates a resource-backed plan for missing skills.
- `POST /api/cover-letter` generates a role-specific cover letter draft.
- `POST /api/signup` creates a local user account.
- `POST /api/login` validates credentials and returns a session token.
- `POST /api/password/otp` sends a real OTP email when SMTP is configured.
- `POST /api/password/verify` checks the OTP before unlocking the password update fields.
- `POST /api/password/update` verifies OTP and updates password.
- `GET /api/saved-jobs` returns saved jobs for a logged-in user.

## Notes

PDF upload uses `PyPDF2` when available and falls back to a lightweight text extraction heuristic. For best results, paste resume text into the textarea if the PDF is scanned or image-only.
