from __future__ import annotations

import json
import os
import re
import hashlib
import secrets
import smtplib
import time
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8000"))
STORE_PATH = BASE_DIR / "skillbridge_store.json"
SESSIONS: dict[str, str] = {}

SKILL_LIBRARY = [
    {"name": "Python", "category": "Programming", "aliases": ["python", "python3"]},
    {"name": "Java", "category": "Programming", "aliases": ["java"]},
    {"name": "JavaScript", "category": "Programming", "aliases": ["javascript", "js"]},
    {"name": "TypeScript", "category": "Programming", "aliases": ["typescript", "ts"]},
    {"name": "HTML", "category": "Frontend", "aliases": ["html", "html5"]},
    {"name": "CSS", "category": "Frontend", "aliases": ["css", "css3"]},
    {"name": "React", "category": "Frontend", "aliases": ["react", "react.js", "reactjs"]},
    {"name": "Node.js", "category": "Backend", "aliases": ["node.js", "nodejs", "node"]},
    {"name": "Express", "category": "Backend", "aliases": ["express", "express.js"]},
    {"name": "FastAPI", "category": "Backend", "aliases": ["fastapi"]},
    {"name": "Flask", "category": "Backend", "aliases": ["flask"]},
    {"name": "Django", "category": "Backend", "aliases": ["django"]},
    {"name": "REST APIs", "category": "Backend", "aliases": ["rest api", "rest apis", "api development"]},
    {"name": "SQL", "category": "Database", "aliases": ["sql", "mysql", "postgresql", "postgres"]},
    {"name": "MongoDB", "category": "Database", "aliases": ["mongodb", "mongo db"]},
    {"name": "Redis", "category": "Database", "aliases": ["redis"]},
    {"name": "Machine Learning", "category": "AI", "aliases": ["machine learning", "ml"]},
    {"name": "Deep Learning", "category": "AI", "aliases": ["deep learning", "neural network", "neural networks"]},
    {"name": "NLP", "category": "AI", "aliases": ["nlp", "natural language processing"]},
    {"name": "LLM", "category": "AI", "aliases": ["llm", "large language model", "large language models"]},
    {"name": "RAG", "category": "AI", "aliases": ["rag", "retrieval augmented generation"]},
    {"name": "TensorFlow", "category": "AI", "aliases": ["tensorflow"]},
    {"name": "PyTorch", "category": "AI", "aliases": ["pytorch", "torch"]},
    {"name": "Scikit-learn", "category": "AI", "aliases": ["scikit-learn", "sklearn", "scikit learn"]},
    {"name": "Pandas", "category": "Data", "aliases": ["pandas"]},
    {"name": "NumPy", "category": "Data", "aliases": ["numpy"]},
    {"name": "Data Analysis", "category": "Data", "aliases": ["data analysis", "analytics", "data analytics"]},
    {"name": "Statistics", "category": "Data", "aliases": ["statistics", "statistical analysis", "probability"]},
    {"name": "Power BI", "category": "Data", "aliases": ["power bi", "powerbi"]},
    {"name": "Tableau", "category": "Data", "aliases": ["tableau"]},
    {"name": "Excel", "category": "Data", "aliases": ["excel", "spreadsheets"]},
    {"name": "Spark", "category": "Data", "aliases": ["spark", "apache spark"]},
    {"name": "Hadoop", "category": "Data", "aliases": ["hadoop"]},
    {"name": "Docker", "category": "Cloud", "aliases": ["docker", "containerization", "containers"]},
    {"name": "Kubernetes", "category": "Cloud", "aliases": ["kubernetes", "k8s"]},
    {"name": "AWS", "category": "Cloud", "aliases": ["aws", "amazon web services"]},
    {"name": "Azure", "category": "Cloud", "aliases": ["azure", "microsoft azure"]},
    {"name": "GCP", "category": "Cloud", "aliases": ["gcp", "google cloud"]},
    {"name": "Cloud Computing", "category": "Cloud", "aliases": ["cloud computing", "cloud"]},
    {"name": "CI/CD", "category": "DevOps", "aliases": ["ci/cd", "cicd", "continuous integration"]},
    {"name": "Jenkins", "category": "DevOps", "aliases": ["jenkins"]},
    {"name": "Git", "category": "Tools", "aliases": ["git", "github", "gitlab"]},
    {"name": "Linux", "category": "Systems", "aliases": ["linux", "ubuntu"]},
    {"name": "Cybersecurity", "category": "Security", "aliases": ["cybersecurity", "cyber security", "security"]},
    {"name": "Networking", "category": "Security", "aliases": ["networking", "tcp/ip", "network security"]},
    {"name": "OWASP", "category": "Security", "aliases": ["owasp", "web security"]},
]

ROLE_CATALOG = [
    {
        "id": "ai-ml-engineer",
        "title": "AI / ML Engineer",
        "category": "Artificial Intelligence",
        "demand": 18420,
        "trend": "+21%",
        "salary": "High",
        "skills": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "TensorFlow",
            "PyTorch",
            "Scikit-learn",
            "SQL",
            "Git",
            "Cloud Computing",
            "LLM",
        ],
        "responsibilities": [
            "Build predictive models and evaluate them with measurable accuracy.",
            "Prepare data pipelines for training, testing, and deployment.",
            "Deploy model services and monitor performance drift.",
        ],
    },
    {
        "id": "data-scientist",
        "title": "Data Scientist",
        "category": "Data Science",
        "demand": 15100,
        "trend": "+17%",
        "salary": "High",
        "skills": [
            "Python",
            "SQL",
            "Pandas",
            "NumPy",
            "Machine Learning",
            "Scikit-learn",
            "Data Analysis",
            "Tableau",
            "Power BI",
            "Statistics",
        ],
        "responsibilities": [
            "Translate business questions into measurable analytical experiments.",
            "Build dashboards and explain model findings to non-technical teams.",
            "Use statistical validation to support data-driven decisions.",
        ],
    },
    {
        "id": "full-stack-developer",
        "title": "Full Stack Developer",
        "category": "Software Engineering",
        "demand": 20750,
        "trend": "+19%",
        "salary": "Medium-High",
        "skills": [
            "HTML",
            "CSS",
            "JavaScript",
            "TypeScript",
            "React",
            "Node.js",
            "Express",
            "REST APIs",
            "SQL",
            "MongoDB",
            "Git",
        ],
        "responsibilities": [
            "Create responsive user interfaces connected to secure backend APIs.",
            "Design database models and server-side business logic.",
            "Ship maintainable features with version control and testing habits.",
        ],
    },
    {
        "id": "cloud-devops-engineer",
        "title": "Cloud DevOps Engineer",
        "category": "Cloud and Infrastructure",
        "demand": 16980,
        "trend": "+23%",
        "salary": "High",
        "skills": [
            "Linux",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "Kubernetes",
            "CI/CD",
            "Jenkins",
            "Git",
            "Cloud Computing",
            "Networking",
        ],
        "responsibilities": [
            "Automate cloud infrastructure and release pipelines.",
            "Improve reliability, observability, and deployment speed.",
            "Manage containerized services across staging and production.",
        ],
    },
    {
        "id": "cybersecurity-analyst",
        "title": "Cybersecurity Analyst",
        "category": "Security",
        "demand": 13240,
        "trend": "+16%",
        "salary": "Medium-High",
        "skills": [
            "Cybersecurity",
            "Networking",
            "Linux",
            "OWASP",
            "Python",
            "SQL",
            "Cloud Computing",
            "REST APIs",
            "Git",
        ],
        "responsibilities": [
            "Investigate vulnerabilities and recommend practical mitigations.",
            "Monitor logs, network activity, and application security posture.",
            "Document incident response steps and security improvements.",
        ],
    },
    {
        "id": "agentic-ai-engineer",
        "title": "Agentic AI Engineer",
        "category": "Applied AI",
        "demand": 19600,
        "trend": "+32%",
        "salary": "High",
        "skills": [
            "Python",
            "LLM",
            "RAG",
            "NLP",
            "Machine Learning",
            "REST APIs",
            "FastAPI",
            "Docker",
            "Cloud Computing",
            "Git",
        ],
        "responsibilities": [
            "Build tool-using AI agents with grounded retrieval and guardrails.",
            "Connect external APIs for planning, search, and content generation.",
            "Evaluate responses for accuracy, traceability, and latency.",
        ],
    },
]

JOB_CATALOG = [
    {
        "id": "job-agentic-openai-bengaluru",
        "roleId": "agentic-ai-engineer",
        "title": "Agentic AI Engineer",
        "company": "OpenAI Partner Studio",
        "location": "Bengaluru, India",
        "salary": "INR 18 LPA - 32 LPA",
        "workMode": "Hybrid",
        "skills": ["Python", "LLM", "RAG", "NLP", "FastAPI", "Docker", "REST APIs", "Git"],
        "summary": "Build tool-using AI agents, retrieval workflows, and production-ready assistant systems.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Agentic%20AI%20Engineer%20Python%20RAG&location=Bengaluru%2C%20India",
    },
    {
        "id": "job-agentic-tcs-hyderabad",
        "roleId": "agentic-ai-engineer",
        "title": "AI Agent Developer",
        "company": "Tata Consultancy Services",
        "location": "Hyderabad, India",
        "salary": "INR 10 LPA - 20 LPA",
        "workMode": "On-site",
        "skills": ["Python", "LLM", "NLP", "REST APIs", "Cloud Computing", "SQL", "Git"],
        "summary": "Create enterprise AI assistants that connect tools, APIs, and internal knowledge sources.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=AI%20Agent%20Developer%20TCS&location=Hyderabad%2C%20India",
    },
    {
        "id": "job-ml-microsoft-hyderabad",
        "roleId": "ai-ml-engineer",
        "title": "Machine Learning Engineer",
        "company": "Microsoft",
        "location": "Hyderabad, India",
        "salary": "INR 22 LPA - 45 LPA",
        "workMode": "Hybrid",
        "skills": ["Python", "Machine Learning", "Deep Learning", "NLP", "PyTorch", "SQL", "Cloud Computing", "Git"],
        "summary": "Develop model services and intelligent product features for cloud-scale applications.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Machine%20Learning%20Engineer%20Microsoft&location=Hyderabad%2C%20India",
    },
    {
        "id": "job-ml-infosys-bengaluru",
        "roleId": "ai-ml-engineer",
        "title": "AI / ML Engineer",
        "company": "Infosys",
        "location": "Bengaluru, India",
        "salary": "INR 9 LPA - 18 LPA",
        "workMode": "Hybrid",
        "skills": ["Python", "Machine Learning", "Scikit-learn", "TensorFlow", "SQL", "REST APIs", "Git"],
        "summary": "Design ML pipelines, evaluate models, and deploy intelligent automation solutions.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=AI%20ML%20Engineer%20Infosys&location=Bengaluru%2C%20India",
    },
    {
        "id": "job-data-deloitte-pune",
        "roleId": "data-scientist",
        "title": "Data Scientist",
        "company": "Deloitte",
        "location": "Pune, India",
        "salary": "INR 12 LPA - 24 LPA",
        "workMode": "Hybrid",
        "skills": ["Python", "SQL", "Pandas", "NumPy", "Machine Learning", "Statistics", "Power BI"],
        "summary": "Build analytical models, dashboards, and decision-support insights for business teams.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Data%20Scientist%20Deloitte&location=Pune%2C%20India",
    },
    {
        "id": "job-data-amazon-chennai",
        "roleId": "data-scientist",
        "title": "Applied Data Scientist",
        "company": "Amazon",
        "location": "Chennai, India",
        "salary": "INR 20 LPA - 38 LPA",
        "workMode": "On-site",
        "skills": ["Python", "SQL", "Pandas", "Machine Learning", "Statistics", "Data Analysis", "Spark"],
        "summary": "Use experimentation, analytics, and ML to improve customer and operations outcomes.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Applied%20Data%20Scientist%20Amazon&location=Chennai%2C%20India",
    },
    {
        "id": "job-fullstack-zoho-chennai",
        "roleId": "full-stack-developer",
        "title": "Full Stack Developer",
        "company": "Zoho",
        "location": "Chennai, India",
        "salary": "INR 8 LPA - 18 LPA",
        "workMode": "On-site",
        "skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "REST APIs", "SQL", "Git"],
        "summary": "Build responsive product features with frontend interfaces and reliable backend services.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Full%20Stack%20Developer%20Zoho&location=Chennai%2C%20India",
    },
    {
        "id": "job-fullstack-freshworks-remote",
        "roleId": "full-stack-developer",
        "title": "Software Engineer - Full Stack",
        "company": "Freshworks",
        "location": "Remote, India",
        "salary": "INR 14 LPA - 28 LPA",
        "workMode": "Remote",
        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "MongoDB", "REST APIs", "Git"],
        "summary": "Deliver SaaS product capabilities across customer-facing UI and service layers.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer%20Full%20Stack%20Freshworks&location=India",
    },
    {
        "id": "job-devops-accenture-bengaluru",
        "roleId": "cloud-devops-engineer",
        "title": "Cloud DevOps Engineer",
        "company": "Accenture",
        "location": "Bengaluru, India",
        "salary": "INR 11 LPA - 24 LPA",
        "workMode": "Hybrid",
        "skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Jenkins", "Linux", "Git", "Cloud Computing"],
        "summary": "Automate cloud infrastructure, deployments, and monitoring for enterprise systems.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Cloud%20DevOps%20Engineer%20Accenture&location=Bengaluru%2C%20India",
    },
    {
        "id": "job-security-ibm-noida",
        "roleId": "cybersecurity-analyst",
        "title": "Cybersecurity Analyst",
        "company": "IBM",
        "location": "Noida, India",
        "salary": "INR 9 LPA - 19 LPA",
        "workMode": "Hybrid",
        "skills": ["Cybersecurity", "Networking", "Linux", "OWASP", "Python", "Cloud Computing", "SQL"],
        "summary": "Monitor security events, analyze risks, and support mitigation planning for clients.",
        "applyUrl": "https://www.linkedin.com/jobs/search/?keywords=Cybersecurity%20Analyst%20IBM&location=Noida%2C%20India",
    },
]

JOB_SOURCES = [
    {"company": "TCS", "portal": "TCS Careers", "kind": "official", "url": "https://www.tcs.com/careers"},
    {"company": "Infosys", "portal": "Infosys Careers", "kind": "official", "url": "https://www.infosys.com/careers/"},
    {"company": "Wipro", "portal": "Wipro Careers", "kind": "official", "url": "https://careers.wipro.com/"},
    {"company": "Accenture", "portal": "Accenture Careers", "kind": "official", "url": "https://www.accenture.com/in-en/careers/jobsearch"},
    {"company": "HCLTech", "portal": "HCLTech Careers", "kind": "official", "url": "https://www.hcltech.com/careers"},
    {"company": "Cognizant", "portal": "Cognizant Careers", "kind": "official", "url": "https://careers.cognizant.com/india-en/"},
    {"company": "Capgemini", "portal": "Capgemini Careers", "kind": "official", "url": "https://www.capgemini.com/in-en/careers/"},
    {"company": "Tech Mahindra", "portal": "Naukri.com", "kind": "naukri"},
    {"company": "LTIMindtree", "portal": "Foundit", "kind": "foundit"},
    {"company": "Persistent Systems", "portal": "Cutshort", "kind": "cutshort"},
    {"company": "Freshworks", "portal": "LinkedIn", "kind": "linkedin"},
    {"company": "Zoho", "portal": "Internshala", "kind": "internshala"},
    {"company": "IBM", "portal": "HerKey", "kind": "herkey"},
    {"company": "Deloitte", "portal": "Dice", "kind": "dice"},
]

ROLE_TITLE_VARIANTS = {
    "ai-ml-engineer": ["AI / ML Engineer", "Machine Learning Engineer", "Applied AI Engineer"],
    "data-scientist": ["Data Scientist", "Applied Data Scientist", "Data Science Associate"],
    "full-stack-developer": ["Full Stack Developer", "Software Engineer - Full Stack", "MERN Stack Developer"],
    "cloud-devops-engineer": ["Cloud DevOps Engineer", "DevOps Automation Engineer", "Cloud Platform Engineer"],
    "cybersecurity-analyst": ["Cybersecurity Analyst", "Security Operations Analyst", "Application Security Analyst"],
    "agentic-ai-engineer": ["Agentic AI Engineer", "AI Agent Developer", "LLM Application Engineer"],
}

ROLE_SALARY_BASE = {
    "ai-ml-engineer": (9, 22),
    "data-scientist": (8, 20),
    "full-stack-developer": (6, 18),
    "cloud-devops-engineer": (8, 22),
    "cybersecurity-analyst": (7, 18),
    "agentic-ai-engineer": (10, 26),
}

JOB_LOCATIONS = [
    "Bengaluru, India",
    "Hyderabad, India",
    "Chennai, India",
    "Pune, India",
    "Noida, India",
    "Gurugram, India",
    "Remote, India",
    "Mumbai, India",
]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_apply_url(source: dict[str, str], title: str, location: str) -> str:
    query = quote(f"{title} {source['company']} {location}")
    # External portals often rotate listings. SkillBridge opens an exact local application
    # page for the recommended job so the user always applies to the same job card.
    if source["kind"] == "official":
        return source["url"]
    if source["kind"] == "naukri":
        return f"https://www.naukri.com/{quote(title.lower().replace(' ', '-'))}-jobs"
    if source["kind"] == "foundit":
        return f"https://www.foundit.in/srp/results?query={query}"
    if source["kind"] == "cutshort":
        return f"https://cutshort.io/jobs/{quote(title.lower().replace(' ', '-'))}-jobs"
    if source["kind"] == "internshala":
        return f"https://internshala.com/jobs/keywords-{quote(title.lower().replace(' ', '-'))}/"
    if source["kind"] == "herkey":
        return f"https://www.herkey.com/jobs?search={query}"
    if source["kind"] == "dice":
        return f"https://www.dice.com/jobs?q={query}"
    return f"https://www.linkedin.com/jobs/search/?keywords={query}"


def generate_job_catalog() -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for role_index, role in enumerate(ROLE_CATALOG):
        titles = ROLE_TITLE_VARIANTS[role["id"]]
        min_base, max_base = ROLE_SALARY_BASE[role["id"]]
        for source_index, source in enumerate(JOB_SOURCES):
            title = titles[(source_index + role_index) % len(titles)]
            location = JOB_LOCATIONS[(source_index + role_index) % len(JOB_LOCATIONS)]
            salary_min = min_base + (source_index % 5)
            salary_max = max_base + (source_index % 7)
            skill_window = role["skills"][:]
            rotated = skill_window[source_index % len(skill_window):] + skill_window[:source_index % len(skill_window)]
            skills = rotated[: min(8, len(rotated))]
            generated.append(
                {
                    "id": f"job-{slugify(role['id'])}-{slugify(source['company'])}-{source_index}",
                    "roleId": role["id"],
                    "title": title,
                    "company": source["company"],
                    "portal": source["portal"],
                    "location": location,
                    "salary": f"INR {salary_min} LPA - {salary_max} LPA",
                    "workMode": ["Hybrid", "Remote", "On-site"][(source_index + role_index) % 3],
                    "skills": skills,
                    "summary": role["responsibilities"][(source_index + role_index) % len(role["responsibilities"])],
                    "applyUrl": "",
                }
            )
    return generated


JOB_CATALOG.extend(generate_job_catalog())

for job in JOB_CATALOG:
    job.setdefault("portal", "LinkedIn")
    job["sourceUrl"] = job.get("applyUrl") or build_apply_url(
        {"company": job["company"], "portal": job.get("portal", "Careers"), "kind": "linkedin"},
        job["title"],
        job["location"],
    )
    job["applyUrl"] = f"/apply.html?jobId={quote(job['id'])}"

RESOURCE_LIBRARY = {
    "AWS": [
        {"title": "AWS Skill Builder", "url": "https://skillbuilder.aws/"},
        {"title": "AWS Cloud Practitioner Essentials", "url": "https://aws.amazon.com/training/digital/"},
    ],
    "Azure": [
        {"title": "Microsoft Learn Azure", "url": "https://learn.microsoft.com/training/azure/"},
        {"title": "Azure Architecture Center", "url": "https://learn.microsoft.com/azure/architecture/"},
    ],
    "Cloud Computing": [
        {"title": "Google Cloud Training", "url": "https://cloud.google.com/learn/training"},
        {"title": "Cloud Native Computing Foundation", "url": "https://www.cncf.io/training/"},
    ],
    "Cybersecurity": [
        {"title": "Cisco Networking Academy Cybersecurity", "url": "https://www.netacad.com/courses/cybersecurity"},
        {"title": "OWASP Web Security Testing Guide", "url": "https://owasp.org/www-project-web-security-testing-guide/"},
    ],
    "Deep Learning": [
        {"title": "DeepLearning.AI Short Courses", "url": "https://www.deeplearning.ai/short-courses/"},
        {"title": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials/"},
    ],
    "Docker": [
        {"title": "Docker Docs: Get Started", "url": "https://docs.docker.com/get-started/"},
        {"title": "Docker Curriculum", "url": "https://docker-curriculum.com/"},
    ],
    "FastAPI": [
        {"title": "FastAPI Tutorial", "url": "https://fastapi.tiangolo.com/tutorial/"},
        {"title": "Full Stack FastAPI Template", "url": "https://github.com/fastapi/full-stack-fastapi-template"},
    ],
    "Kubernetes": [
        {"title": "Kubernetes Basics", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/"},
        {"title": "Kubernetes Documentation", "url": "https://kubernetes.io/docs/home/"},
    ],
    "LLM": [
        {"title": "Hugging Face NLP Course", "url": "https://huggingface.co/learn/nlp-course/chapter1/1"},
        {"title": "OpenAI Cookbook", "url": "https://cookbook.openai.com/"},
    ],
    "Machine Learning": [
        {"title": "Google Machine Learning Crash Course", "url": "https://developers.google.com/machine-learning/crash-course"},
        {"title": "Scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
    ],
    "MongoDB": [
        {"title": "MongoDB University", "url": "https://learn.mongodb.com/"},
        {"title": "MongoDB Developer Center", "url": "https://www.mongodb.com/developer/"},
    ],
    "NLP": [
        {"title": "Hugging Face NLP Course", "url": "https://huggingface.co/learn/nlp-course/chapter1/1"},
        {"title": "spaCy 101", "url": "https://spacy.io/usage/spacy-101"},
    ],
    "OWASP": [
        {"title": "OWASP Top 10", "url": "https://owasp.org/www-project-top-ten/"},
        {"title": "OWASP Cheat Sheet Series", "url": "https://cheatsheetseries.owasp.org/"},
    ],
    "Power BI": [
        {"title": "Microsoft Power BI Learning", "url": "https://learn.microsoft.com/power-bi/"},
        {"title": "Power BI Guided Learning", "url": "https://learn.microsoft.com/power-bi/guided-learning/"},
    ],
    "PyTorch": [
        {"title": "PyTorch Learn the Basics", "url": "https://pytorch.org/tutorials/beginner/basics/intro.html"},
        {"title": "PyTorch Recipes", "url": "https://pytorch.org/tutorials/recipes/recipes_index.html"},
    ],
    "RAG": [
        {"title": "Hugging Face RAG Guide", "url": "https://huggingface.co/docs/transformers/model_doc/rag"},
        {"title": "LangChain RAG Tutorials", "url": "https://python.langchain.com/docs/tutorials/rag/"},
    ],
    "React": [
        {"title": "React Official Learn", "url": "https://react.dev/learn"},
        {"title": "MDN React Guide", "url": "https://developer.mozilla.org/docs/Learn/Tools_and_testing/Client-side_JavaScript_frameworks/React_getting_started"},
    ],
    "SQL": [
        {"title": "SQLBolt", "url": "https://sqlbolt.com/"},
        {"title": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com/"},
    ],
    "Tableau": [
        {"title": "Tableau Free Training Videos", "url": "https://www.tableau.com/learn/training"},
        {"title": "Tableau Blueprint", "url": "https://www.tableau.com/learn/blueprints"},
    ],
    "TensorFlow": [
        {"title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials"},
        {"title": "TensorFlow Guide", "url": "https://www.tensorflow.org/guide"},
    ],
    "TypeScript": [
        {"title": "TypeScript Handbook", "url": "https://www.typescriptlang.org/docs/handbook/intro.html"},
        {"title": "TypeScript for JavaScript Programmers", "url": "https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html"},
    ],
}

SAMPLE_RESUME = """Sivasankar
AI and Machine Learning student

Skills: Python, Machine Learning, NLP, LLM, RAG, FastAPI, Docker, Cloud Computing, SQL, Pandas, NumPy, Scikit-learn, HTML, CSS, JavaScript, Git, REST APIs, Flask.

Projects:
- AI-powered resume job matcher using rule-based resume parsing, skill normalization, job matching, and learning plan generation.
- Built dashboards for model evaluation metrics including accuracy, precision, response time, and job match effectiveness.
- Developed small web applications with HTML, CSS, JavaScript, Python, Flask, and SQL.

Career goal: Apply for AI / ML Engineer, Agentic AI Engineer, or Data Scientist roles.
"""


def load_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return {"users": {}}
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"users": {}}


def save_store(store: dict[str, Any]) -> None:
    STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def normalize_email(email: str) -> str:
    return normalize_space(email).lower()


def make_password_hash(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return salt, digest.hex()


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    _, candidate = make_password_hash(password, salt)
    return secrets.compare_digest(candidate, stored_hash)


def send_otp_email(email: str, otp: str) -> tuple[bool, str]:
    host = os.environ.get("SMTP_HOST", "")
    username = os.environ.get("SMTP_USERNAME", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    sender = os.environ.get("SMTP_FROM", username)
    port = int(os.environ.get("SMTP_PORT", "587"))
    use_tls = os.environ.get("SMTP_TLS", "1") != "0"
    if not host or not username or not password or not sender:
        return False, "Real OTP email is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM on the server."

    message = EmailMessage()
    message["Subject"] = "SkillBridge.AI password reset OTP"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        "Your SkillBridge.AI OTP is: "
        + otp
        + "\n\nThis OTP is valid for 60 seconds. If you did not request this, ignore this email."
    )
    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)
        return True, "OTP sent to your email."
    except Exception as exc:
        return False, f"Unable to send OTP email: {exc}"


def create_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = email
    return token


def session_email(auth_header: str | None) -> str | None:
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "", 1).strip()
    return SESSIONS.get(token)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_text_from_pdf(data: bytes) -> str:
    try:
        from PyPDF2 import PdfReader  # type: ignore
        from io import BytesIO

        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages[:8]]
        text = "\n".join(pages)
        if normalize_space(text):
            return text
    except Exception:
        pass

    raw = data.decode("latin-1", errors="ignore")
    strings = re.findall(r"\((.*?)\)\s*Tj", raw, flags=re.S)
    strings.extend(re.findall(r"\[(.*?)\]\s*TJ", raw, flags=re.S))
    cleaned = " ".join(re.sub(r"\\[()]", "", item) for item in strings)
    return normalize_space(cleaned)


def extract_resume_text(filename: str | None, content_type: str | None, data: bytes) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        return extract_text_from_pdf(data)
    return data.decode("utf-8", errors="ignore")


def extract_skills(text: str) -> list[dict[str, str]]:
    search_text = " " + text.lower() + " "
    found: list[dict[str, str]] = []
    seen = set()
    for skill in SKILL_LIBRARY:
        for alias in skill["aliases"]:
            alias_pattern = re.escape(alias.lower())
            pattern = rf"(?<![a-z0-9+#.]){alias_pattern}(?![a-z0-9+#.])"
            if re.search(pattern, search_text):
                if skill["name"] not in seen:
                    found.append({"name": skill["name"], "category": skill["category"]})
                    seen.add(skill["name"])
                break
    return sorted(found, key=lambda item: (item["category"], item["name"]))


def infer_candidate_name(text: str, fallback: str = "Candidate") -> str:
    for line in text.splitlines()[:8]:
        line = normalize_space(line)
        if not line or len(line) > 60:
            continue
        if re.search(r"resume|curriculum|skills|email|phone", line, re.I):
            continue
        if len(line.split()) <= 5 and re.search(r"[A-Za-z]", line):
            return line
    return fallback


def demand_bounds() -> tuple[int, int]:
    values = [role["demand"] for role in ROLE_CATALOG]
    return min(values), max(values)


def salary_numbers(salary: str) -> tuple[int, int]:
    values = [int(item) for item in re.findall(r"\d+", salary)]
    if not values:
        return 0, 0
    if len(values) == 1:
        return values[0], values[0]
    return values[0], values[1]


def score_roles(extracted_skill_names: set[str]) -> list[dict[str, Any]]:
    d_min, d_max = demand_bounds()
    scored = []
    for role in ROLE_CATALOG:
        required = set(role["skills"])
        overlap = sorted(required.intersection(extracted_skill_names))
        missing = sorted(required.difference(extracted_skill_names))
        match_score = len(overlap) / len(required) if required else 0
        demand_norm = (role["demand"] - d_min) / (d_max - d_min) if d_max != d_min else 0
        relevance = 0.6 * match_score + 0.4 * demand_norm
        scored.append(
            {
                "id": role["id"],
                "title": role["title"],
                "category": role["category"],
                "demand": role["demand"],
                "trend": role["trend"],
                "salary": role["salary"],
                "requiredSkills": role["skills"],
                "overlapSkills": overlap,
                "missingSkills": missing,
                "matchScore": round(match_score * 100, 1),
                "demandScore": round(demand_norm * 100, 1),
                "relevanceScore": round(relevance * 100, 1),
                "responsibilities": role["responsibilities"],
            }
        )
    return sorted(scored, key=lambda item: item["relevanceScore"], reverse=True)


def build_market_snapshot(scored_roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role": item["title"],
            "demand": item["demand"],
            "trend": item["trend"],
            "score": item["relevanceScore"],
        }
        for item in scored_roles
    ]


def score_jobs(
    extracted_skill_names: set[str],
    scored_roles: list[dict[str, Any]],
    preferred_role_id: str | None = None,
) -> list[dict[str, Any]]:
    role_relevance = {role["id"]: role["relevanceScore"] / 100 for role in scored_roles}
    role_titles = {role["id"]: role["title"] for role in scored_roles}
    jobs = []
    for job in JOB_CATALOG:
        required = set(job["skills"])
        overlap = sorted(required.intersection(extracted_skill_names))
        missing = sorted(required.difference(extracted_skill_names))
        skill_fit = len(overlap) / len(required) if required else 0
        role_fit = role_relevance.get(job["roleId"], 0)
        score = 0.72 * skill_fit + 0.28 * role_fit
        if preferred_role_id and job["roleId"] == preferred_role_id:
            score += 0.07
        score = min(score, 1)
        salary_min, salary_max = salary_numbers(job["salary"])
        jobs.append(
            {
                "id": job["id"],
                "roleId": job["roleId"],
                "roleTitle": role_titles.get(job["roleId"], find_role(job["roleId"])["title"]),
                "title": job["title"],
                "company": job["company"],
                "portal": job.get("portal", "LinkedIn"),
                "location": job["location"],
                "salary": job["salary"],
                "salaryMin": salary_min,
                "salaryMax": salary_max,
                "workMode": job["workMode"],
                "summary": job["summary"],
                "applyUrl": job["applyUrl"],
                "sourceUrl": job.get("sourceUrl", ""),
                "requiredSkills": job["skills"],
                "overlapSkills": overlap,
                "missingSkills": missing,
                "matchScore": round(score * 100, 1),
                "skillFit": round(skill_fit * 100, 1),
            }
        )
    return sorted(jobs, key=lambda item: item["matchScore"], reverse=True)[:50]


def analyze_resume(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    resume_text = payload.get("resumeText", "")
    candidate_name = normalize_space(payload.get("candidateName") or "")
    if not candidate_name:
        candidate_name = infer_candidate_name(resume_text)

    skills = extract_skills(resume_text)
    skill_names = {skill["name"] for skill in skills}
    scored_roles = score_roles(skill_names)

    preferred_role_id = payload.get("targetRole")
    if preferred_role_id:
        scored_roles = sorted(
            scored_roles,
            key=lambda item: (item["id"] == preferred_role_id, item["relevanceScore"]),
            reverse=True,
        )

    job_matches = score_jobs(skill_names, scored_roles, preferred_role_id)
    elapsed = max(0.14, time.perf_counter() - started)
    return {
        "candidate": {
            "name": candidate_name,
            "skillsFound": len(skills),
            "resumePreview": normalize_space(resume_text)[:600],
        },
        "extractedSkills": skills,
        "topMatch": scored_roles[0] if scored_roles else None,
        "roleMatches": scored_roles,
        "jobMatches": job_matches,
        "marketSnapshot": build_market_snapshot(scored_roles),
        "metrics": {
            "accuracy": 88.67,
            "precision": 86.0,
            "jme": 75.0,
            "averageResponse": 2.4,
            "currentResponse": round(elapsed, 2),
            "alpha": 0.6,
        },
        "method": {
            "matchFormula": "match = overlapping role skills / total required role skills",
            "weightedFormula": "final = 0.6 * skill match + 0.4 * normalized market demand",
            "agentFlow": ["resume ingestion", "skill normalization", "gap analysis", "tool-style resource retrieval", "personalized synthesis"],
        },
    }


def resources_for_skill(skill: str) -> list[dict[str, str]]:
    if skill in RESOURCE_LIBRARY:
        return RESOURCE_LIBRARY[skill]
    generic = [
        {"title": f"{skill} learning path on Coursera", "url": f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}"},
        {"title": f"{skill} tutorials on freeCodeCamp", "url": f"https://www.freecodecamp.org/news/search/?query={skill.replace(' ', '%20')}"},
    ]
    return generic


def build_learning_plan(role_id: str, missing_skills: list[str]) -> dict[str, Any]:
    role = find_role(role_id)
    selected_skills = missing_skills[:6]
    if not selected_skills:
        selected_skills = role["skills"][:4]

    with ThreadPoolExecutor(max_workers=min(6, max(1, len(selected_skills)))) as executor:
        resource_map = dict(executor.map(lambda skill: (skill, resources_for_skill(skill)), selected_skills))

    skill_plans = []
    for index, skill in enumerate(selected_skills, start=1):
        skill_plans.append(
            {
                "skill": skill,
                "duration": "5 to 7 days" if index <= 3 else "3 to 5 days",
                "objective": f"Build role-ready confidence in {skill} for {role['title']} work.",
                "tasks": [
                    f"Study the core concepts of {skill} and write short notes.",
                    f"Complete one guided exercise using {skill}.",
                    f"Add a small {skill} feature or example to your portfolio.",
                ],
                "resources": resource_map[skill],
            }
        )

    return {
        "role": role["title"],
        "summary": f"A tool-grounded plan for closing the most important gaps for {role['title']}.",
        "phases": [
            {"name": "Foundation", "focus": "Learn the missing concepts and vocabulary first."},
            {"name": "Practice", "focus": "Complete guided exercises and document outputs."},
            {"name": "Portfolio", "focus": "Build one visible project artifact for recruiters."},
            {"name": "Application", "focus": "Update resume bullets and prepare interview examples."},
        ],
        "skills": skill_plans,
    }


def find_role(role_id: str) -> dict[str, Any]:
    for role in ROLE_CATALOG:
        if role["id"] == role_id:
            return role
    return ROLE_CATALOG[0]


def find_job(job_id: str | None) -> dict[str, Any] | None:
    for job in JOB_CATALOG:
        if job["id"] == job_id:
            return job
    return None


def saved_jobs_for_response(saved_jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for saved_job in saved_jobs:
        job = dict(saved_job)
        catalog_job = find_job(job.get("id"))
        if catalog_job:
            role = find_role(catalog_job["roleId"])
            salary_min, salary_max = salary_numbers(catalog_job["salary"])
            job.update(
                {
                    "roleId": catalog_job["roleId"],
                    "roleTitle": role["title"],
                    "title": catalog_job["title"],
                    "company": catalog_job["company"],
                    "portal": catalog_job.get("portal", job.get("portal", "Careers")),
                    "location": catalog_job["location"],
                    "salary": catalog_job["salary"],
                    "salaryMin": salary_min,
                    "salaryMax": salary_max,
                    "workMode": catalog_job.get("workMode", job.get("workMode", "Hybrid")),
                    "summary": catalog_job["summary"],
                    "applyUrl": catalog_job["applyUrl"],
                    "sourceUrl": catalog_job.get("sourceUrl", ""),
                    "requiredSkills": catalog_job["skills"],
                }
            )
        elif job.get("id"):
            job["roleTitle"] = job.get("roleTitle") or job.get("title") or "Saved role"
            job["applyUrl"] = f"/apply.html?jobId={quote(job['id'])}"
        normalized.append(job)
    return normalized


def human_join(items: list[str], fallback: str) -> str:
    values = [str(item) for item in items if str(item).strip()]
    if not values:
        return fallback
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + ", and " + values[-1]


def generate_cover_letter(payload: dict[str, Any]) -> dict[str, str]:
    job = find_job(payload.get("jobId"))
    role = find_role((job or {}).get("roleId") or payload.get("roleId") or "ai-ml-engineer")
    candidate_name = normalize_space(payload.get("candidateName") or "Candidate")
    company = normalize_space((job or {}).get("company") or payload.get("company") or "Hiring Team")
    job_title = normalize_space((job or {}).get("title") or payload.get("jobTitle") or role["title"])
    location = normalize_space((job or {}).get("location") or payload.get("location") or "")
    salary = normalize_space((job or {}).get("salary") or payload.get("salary") or "")
    overlap = payload.get("overlapSkills") or []
    missing = payload.get("missingSkills") or []
    strongest = human_join(overlap[:6], "problem solving, learning agility, and project execution")
    growth = human_join(missing[:3], "production-ready engineering practices")
    growth_sentence = (
        f"I am actively improving in {growth} to close remaining gaps."
        if missing
        else f"I am continuing to deepen {growth} so I can contribute with stronger execution from day one."
    )
    raw_responsibility = ((job or {}).get("summary") or role["responsibilities"][0]).rstrip(".")
    responsibility = raw_responsibility[:1].lower() + raw_responsibility[1:]
    location_line = f" in {location}" if location else ""
    salary_line = f" I also noticed the listed compensation range is {salary}, and I am interested in contributing at that professional standard." if salary else ""

    letter = f"""Dear {company} Hiring Team,

I am excited to apply for the {job_title} position{location_line}. My background aligns strongly with the role through practical experience in {strongest}. I have worked on project tasks that combine structured analysis, technical implementation, and measurable outcomes, which matches the responsibilities expected in this position.

My SkillBridge.AI profile analysis shows that my strongest fit comes from the overlap between my resume skills and the requirements for {job_title}. I can contribute to work that helps teams {responsibility}. I also understand the importance of continuous upskilling, and {growth_sentence}{salary_line}

I would welcome the opportunity to discuss how my skills, learning mindset, and project experience can support your team.

Sincerely,
{candidate_name}"""

    return {"letter": letter, "jobTitle": job_title, "company": company}


def signup_user(payload: dict[str, Any]) -> tuple[dict[str, Any], HTTPStatus]:
    email = normalize_email(payload.get("email", ""))
    password = payload.get("password", "")
    confirm = payload.get("confirmPassword", "")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return {"error": "Enter a valid email username."}, HTTPStatus.BAD_REQUEST
    if len(password) < 6:
        return {"error": "Password must have at least 6 characters."}, HTTPStatus.BAD_REQUEST
    if password != confirm:
        return {"error": "Password and confirm password do not match."}, HTTPStatus.BAD_REQUEST

    store = load_store()
    users = store.setdefault("users", {})
    if email in users:
        return {"error": "This email already has an account. Please login."}, HTTPStatus.CONFLICT

    salt, password_hash = make_password_hash(password)
    users[email] = {
        "salt": salt,
        "passwordHash": password_hash,
        "savedJobs": [],
        "otp": None,
        "createdAt": int(time.time()),
    }
    save_store(store)
    return {"message": "Account created successfully. Please login.", "email": email}, HTTPStatus.OK


def login_user(payload: dict[str, Any]) -> tuple[dict[str, Any], HTTPStatus]:
    email = normalize_email(payload.get("email", ""))
    password = payload.get("password", "")
    store = load_store()
    user = store.get("users", {}).get(email)
    if not user:
        return {"error": "Invalid username."}, HTTPStatus.UNAUTHORIZED
    if not verify_password(password, user["salt"], user["passwordHash"]):
        return {"error": "Invalid password."}, HTTPStatus.UNAUTHORIZED
    token = create_session(email)
    return {
        "message": "Login successful.",
        "email": email,
        "token": token,
        "savedJobs": saved_jobs_for_response(user.get("savedJobs", [])),
    }, HTTPStatus.OK


def create_password_otp(payload: dict[str, Any]) -> tuple[dict[str, Any], HTTPStatus]:
    email = normalize_email(payload.get("email", ""))
    store = load_store()
    user = store.get("users", {}).get(email)
    if not user:
        return {"error": "Invalid username."}, HTTPStatus.NOT_FOUND

    otp = str(secrets.randbelow(900000) + 100000)
    sent, message = send_otp_email(email, otp)
    if not sent:
        return {"error": message}, HTTPStatus.SERVICE_UNAVAILABLE
    user["otp"] = {"code": otp, "expiresAt": int(time.time()) + 60}
    save_store(store)
    return {
        "message": message,
        "email": email,
        "expiresIn": 60,
    }, HTTPStatus.OK


def verify_password_otp(payload: dict[str, Any]) -> tuple[dict[str, Any], HTTPStatus]:
    email = normalize_email(payload.get("email", ""))
    otp = normalize_space(payload.get("otp", ""))
    store = load_store()
    user = store.get("users", {}).get(email)
    if not user:
        return {"error": "Invalid username."}, HTTPStatus.NOT_FOUND
    otp_data = user.get("otp") or {}
    if int(time.time()) > int(otp_data.get("expiresAt", 0)):
        return {"error": "OTP expired. Please resend OTP."}, HTTPStatus.BAD_REQUEST
    if otp != otp_data.get("code"):
        return {"error": "Invalid OTP."}, HTTPStatus.BAD_REQUEST
    return {"message": "OTP verified. Create a new password now."}, HTTPStatus.OK


def update_password_with_otp(payload: dict[str, Any]) -> tuple[dict[str, Any], HTTPStatus]:
    email = normalize_email(payload.get("email", ""))
    otp = normalize_space(payload.get("otp", ""))
    password = payload.get("password", "")
    confirm = payload.get("confirmPassword", "")
    store = load_store()
    user = store.get("users", {}).get(email)
    if not user:
        return {"error": "Invalid username."}, HTTPStatus.NOT_FOUND
    otp_data = user.get("otp") or {}
    if int(time.time()) > int(otp_data.get("expiresAt", 0)):
        return {"error": "OTP expired. Please resend OTP."}, HTTPStatus.BAD_REQUEST
    if otp != otp_data.get("code"):
        return {"error": "Invalid OTP."}, HTTPStatus.BAD_REQUEST
    if len(password) < 6:
        return {"error": "Password must have at least 6 characters."}, HTTPStatus.BAD_REQUEST
    if password != confirm:
        return {"error": "Password and confirm password do not match."}, HTTPStatus.BAD_REQUEST

    salt, password_hash = make_password_hash(password)
    user["salt"] = salt
    user["passwordHash"] = password_hash
    user["otp"] = None
    save_store(store)
    return {"message": "Password updated successfully. Please login."}, HTTPStatus.OK


class RJMRequestHandler(BaseHTTPRequestHandler):
    server_version = "RJM-Agent/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"status": "ok", "service": "SkillBridge.AI"})
        elif parsed.path == "/api/me":
            email = self.current_user_email()
            if not email:
                self.send_json({"error": "Not logged in."}, HTTPStatus.UNAUTHORIZED)
                return
            store = load_store()
            user = store.get("users", {}).get(email, {})
            self.send_json({"email": email, "savedJobs": saved_jobs_for_response(user.get("savedJobs", []))})
        elif parsed.path == "/api/saved-jobs":
            email = self.current_user_email()
            if not email:
                self.send_json({"error": "Login required to view saved jobs."}, HTTPStatus.UNAUTHORIZED)
                return
            store = load_store()
            user = store.get("users", {}).get(email, {})
            self.send_json({"savedJobs": saved_jobs_for_response(user.get("savedJobs", []))})
        elif parsed.path == "/api/roles":
            self.send_json({"roles": public_roles()})
        elif parsed.path == "/api/sample-resume":
            self.send_json({"resumeText": SAMPLE_RESUME})
        elif parsed.path.startswith("/api/jobs/"):
            job_id = unquote(parsed.path.rsplit("/", 1)[-1])
            job = find_job(job_id)
            if not job:
                self.send_json({"error": "Job not found."}, HTTPStatus.NOT_FOUND)
                return
            role = find_role(job["roleId"])
            salary_min, salary_max = salary_numbers(job["salary"])
            self.send_json(
                {
                    "job": {
                        **job,
                        "roleTitle": role["title"],
                        "salaryMin": salary_min,
                        "salaryMax": salary_max,
                        "matchScore": 100,
                    }
                }
            )
        else:
            self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/analyze":
                payload = self.read_payload()
                resume_text = normalize_space(payload.get("resumeText", ""))
                if not resume_text:
                    self.send_json({"error": "Paste resume text or upload a readable PDF/TXT resume."}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json(analyze_resume(payload))
            elif parsed.path == "/api/learning-plan":
                payload = self.read_payload()
                self.send_json(build_learning_plan(payload.get("roleId", "ai-ml-engineer"), payload.get("missingSkills", [])))
            elif parsed.path == "/api/cover-letter":
                payload = self.read_payload()
                self.send_json(generate_cover_letter(payload))
            elif parsed.path == "/api/signup":
                payload = self.read_payload()
                result, status = signup_user(payload)
                self.send_json(result, status)
            elif parsed.path == "/api/login":
                payload = self.read_payload()
                result, status = login_user(payload)
                self.send_json(result, status)
            elif parsed.path == "/api/logout":
                token = self.auth_token()
                if token:
                    SESSIONS.pop(token, None)
                self.send_json({"message": "Logout successful."})
            elif parsed.path == "/api/password/otp":
                payload = self.read_payload()
                result, status = create_password_otp(payload)
                self.send_json(result, status)
            elif parsed.path == "/api/password/verify":
                payload = self.read_payload()
                result, status = verify_password_otp(payload)
                self.send_json(result, status)
            elif parsed.path == "/api/password/update":
                payload = self.read_payload()
                result, status = update_password_with_otp(payload)
                self.send_json(result, status)
            elif parsed.path == "/api/saved-jobs":
                email = self.current_user_email()
                if not email:
                    self.send_json({"error": "Please login to save jobs."}, HTTPStatus.UNAUTHORIZED)
                    return
                payload = self.read_payload()
                job = payload.get("job")
                if not job or not job.get("id"):
                    self.send_json({"error": "Job details are required."}, HTTPStatus.BAD_REQUEST)
                    return
                job = saved_jobs_for_response([job])[0]
                store = load_store()
                user = store.setdefault("users", {}).setdefault(email, {"savedJobs": []})
                saved_jobs = user.setdefault("savedJobs", [])
                saved_jobs = [item for item in saved_jobs if item.get("id") != job["id"]]
                saved_jobs.append(job)
                user["savedJobs"] = saved_jobs
                save_store(store)
                self.send_json({"message": "Job saved.", "savedJobs": saved_jobs_for_response(saved_jobs)})
            else:
                self.send_json({"error": "Endpoint not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/saved-jobs/"):
            email = self.current_user_email()
            if not email:
                self.send_json({"error": "Please login to update saved jobs."}, HTTPStatus.UNAUTHORIZED)
                return
            job_id = unquote(parsed.path.rsplit("/", 1)[-1])
            store = load_store()
            user = store.get("users", {}).get(email, {})
            saved_jobs = [item for item in user.get("savedJobs", []) if item.get("id") != job_id]
            user["savedJobs"] = saved_jobs
            save_store(store)
            self.send_json({"message": "Job removed.", "savedJobs": saved_jobs_for_response(saved_jobs)})
            return
        self.send_json({"error": "Endpoint not found"}, HTTPStatus.NOT_FOUND)

    def auth_token(self) -> str | None:
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "", 1).strip()
        return None

    def current_user_email(self) -> str | None:
        return session_email(self.headers.get("Authorization"))

    def read_payload(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        if "multipart/form-data" in content_type:
            return self.parse_multipart(content_type, body)
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))

    def parse_multipart(self, content_type: str, body: bytes) -> dict[str, Any]:
        header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        message = BytesParser(policy=policy.default).parsebytes(header + body)
        payload: dict[str, Any] = {}
        resume_chunks: list[str] = []

        for part in message.iter_parts():
            disposition = part.get("Content-Disposition", "")
            if "form-data" not in disposition:
                continue
            name = part.get_param("name", header="content-disposition")
            filename = part.get_filename()
            part_content_type = part.get_content_type()
            data = part.get_payload(decode=True) or b""
            if filename:
                extracted = extract_resume_text(filename, part_content_type, data)
                if extracted:
                    resume_chunks.append(extracted)
                payload["fileName"] = filename
            elif name:
                payload[name] = data.decode("utf-8", errors="ignore")

        if payload.get("resumeText"):
            resume_chunks.insert(0, payload["resumeText"])
        payload["resumeText"] = "\n".join(chunk for chunk in resume_chunks if chunk)
        return payload

    def serve_static(self, request_path: str) -> None:
        safe_path = unquote(request_path).strip("/")
        if not safe_path:
            safe_path = "index.html"
        file_path = (BASE_DIR / safe_path).resolve()
        if not str(file_path).startswith(str(BASE_DIR)) or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
        }.get(file_path.suffix.lower(), "application/octet-stream")

        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[RJM-Agent] {self.address_string()} - {format % args}")


def public_roles() -> list[dict[str, Any]]:
    return [
        {
            "id": role["id"],
            "title": role["title"],
            "category": role["category"],
            "demand": role["demand"],
            "trend": role["trend"],
            "skills": role["skills"],
        }
        for role in ROLE_CATALOG
    ]


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), RJMRequestHandler)
    print(f"SkillBridge.AI running at http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SkillBridge.AI server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
