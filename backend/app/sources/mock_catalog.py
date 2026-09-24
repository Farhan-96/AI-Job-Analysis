"""In-memory mock job catalog for development/testing (source=mock)."""

from __future__ import annotations

from typing import Any

# Clearly marked as mock — never present these as real postings.
MOCK_JOB_CATALOG: list[dict[str, Any]] = [
    {
        "source_job_id": "mock-rn-001",
        "title": "React Native Developer",
        "company": "Mock Mobile Labs",
        "location": "Islamabad",
        "remote_type": "hybrid",
        "url": "https://example.invalid/mock/react-native-developer",
        "description": (
            "Build cross-platform mobile apps with React Native and Expo. "
            "TypeScript, Redux, REST APIs. [MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "salary_min": 80000,
        "salary_max": 150000,
        "salary_currency": "PKR",
        "posted_at": "2026-09-20T10:00:00Z",
        "tags": ["react native", "mobile", "expo"],
    },
    {
        "source_job_id": "mock-rn-002",
        "title": "Mobile App Developer",
        "company": "Mock App Studio",
        "location": "Remote",
        "remote_type": "remote",
        "url": "https://example.invalid/mock/mobile-app-developer",
        "description": (
            "React Native Engineer for Android/iOS. Expo Developer preferred. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-21T08:00:00Z",
        "tags": ["react native", "mobile developer", "cross platform"],
    },
    {
        "source_job_id": "mock-it-001",
        "title": "IT Support Engineer",
        "company": "Mock Help Desk Co",
        "location": "Rawalpindi",
        "remote_type": "onsite",
        "url": "https://example.invalid/mock/it-support-engineer",
        "description": (
            "IT Support, Windows, Active Directory, networking, Help Desk. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-19T12:00:00Z",
        "tags": ["it support", "help desk", "desktop support"],
    },
    {
        "source_job_id": "mock-it-002",
        "title": "Application Support Engineer",
        "company": "Mock Systems",
        "location": "Islamabad",
        "remote_type": "hybrid",
        "url": "https://example.invalid/mock/application-support",
        "description": (
            "Application Support and Technical Support for internal tools. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-18T09:00:00Z",
        "tags": ["application support", "it officer", "system support"],
    },
    {
        "source_job_id": "mock-teach-001",
        "title": "Computer Teacher",
        "company": "Mock Academy",
        "location": "Islamabad",
        "remote_type": "onsite",
        "url": "https://example.invalid/mock/computer-teacher",
        "description": (
            "Computer Science Teacher / Computer Instructor for secondary school. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-17T11:00:00Z",
        "tags": ["computer teacher", "it teacher", "teaching"],
    },
    {
        "source_job_id": "mock-teach-002",
        "title": "Mathematics Teacher",
        "company": "Mock High School",
        "location": "Rawalpindi",
        "remote_type": "onsite",
        "url": "https://example.invalid/mock/math-teacher",
        "description": (
            "Math Teacher for grades 9-12. [MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-16T14:00:00Z",
        "tags": ["mathematics teacher", "math teacher"],
    },
    {
        "source_job_id": "mock-sw-001",
        "title": "Full Stack Developer",
        "company": "Mock Web Works",
        "location": "Islamabad",
        "remote_type": "hybrid",
        "url": "https://example.invalid/mock/full-stack-developer",
        "description": (
            "Software Engineer / Full Stack Developer with Node.js and React. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-22T07:00:00Z",
        "tags": ["full stack", "software developer", "web developer", "node.js"],
    },
    {
        "source_job_id": "mock-sw-002",
        "title": "Backend Developer",
        "company": "Mock API Corp",
        "location": "Remote",
        "remote_type": "remote",
        "url": "https://example.invalid/mock/backend-developer",
        "description": (
            "Backend Developer / Python Developer / Node.js Developer. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-21T15:00:00Z",
        "tags": ["backend", "software engineer", "python developer"],
    },
    {
        "source_job_id": "mock-ai-001",
        "title": "Python FastAPI Developer",
        "company": "Mock AI Labs",
        "location": "Islamabad",
        "remote_type": "remote",
        "url": "https://example.invalid/mock/python-fastapi-developer",
        "description": (
            "AI Engineer / FastAPI Developer building LLM applications with Python. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-22T09:00:00Z",
        "tags": ["ai engineer", "fastapi", "python", "llm"],
    },
    {
        "source_job_id": "mock-ai-002",
        "title": "Junior AI Engineer",
        "company": "Mock ML Hub",
        "location": "Pakistan",
        "remote_type": "hybrid",
        "url": "https://example.invalid/mock/junior-ai-engineer",
        "description": (
            "Junior AI Engineer / Machine Learning Engineer. Python, FastAPI. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-20T16:00:00Z",
        "tags": ["ai developer", "machine learning", "python engineer"],
    },
    {
        "source_job_id": "mock-auto-001",
        "title": "n8n Automation Developer",
        "company": "Mock Flow Systems",
        "location": "Remote",
        "remote_type": "remote",
        "url": "https://example.invalid/mock/n8n-automation-developer",
        "description": (
            "n8n Developer / Automation Engineer for workflow automation. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Contract",
        "posted_at": "2026-09-21T11:00:00Z",
        "tags": ["n8n", "automation", "workflow automation", "ai automation"],
    },
    {
        "source_job_id": "mock-auto-002",
        "title": "Automation Engineer",
        "company": "Mock Ops",
        "location": "Islamabad",
        "remote_type": "hybrid",
        "url": "https://example.invalid/mock/automation-engineer",
        "description": (
            "Automation Developer building AI Automation and Workflow Automation. "
            "[MOCK DATA — not a real job]"
        ),
        "employment_type": "Full-time",
        "posted_at": "2026-09-19T13:00:00Z",
        "tags": ["automation engineer", "n8n developer"],
    },
]
