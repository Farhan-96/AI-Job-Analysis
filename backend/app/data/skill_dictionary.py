"""Extensible skill dictionary and alias normalization."""

from __future__ import annotations

# Canonical skill → accepted aliases (lowercase).
SKILL_ALIASES: dict[str, list[str]] = {
    "React Native": ["react native", "react-native", "reactnative", "rn"],
    "React": ["react", "react.js", "reactjs"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "Expo": ["expo", "expo go"],
    "Redux": ["redux"],
    "Redux Toolkit": ["redux toolkit", "rtk"],
    "React Query": ["react query", "tanstack query", "@tanstack/react-query"],
    "Node.js": ["node.js", "nodejs", "node js", "node"],
    "Express": ["express", "express.js", "expressjs"],
    "MongoDB": ["mongodb", "mongo"],
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "FastAPI": ["fastapi", "fast api"],
    "Python": ["python", "python3"],
    "Docker": ["docker"],
    "AWS": ["aws", "amazon web services"],
    "Firebase": ["firebase"],
    "REST API": ["rest api", "rest apis", "restful", "rest"],
    "GraphQL": ["graphql"],
    "Git": ["git"],
    "CI/CD": ["ci/cd", "ci cd", "cicd", "continuous integration"],
    "n8n": ["n8n"],
    "Zapier": ["zapier"],
    "SQL": ["sql"],
    "Networking": ["networking", "network"],
    "TCP/IP": ["tcp/ip", "tcpip", "tcp ip"],
    "DNS": ["dns"],
    "DHCP": ["dhcp"],
    "Active Directory": ["active directory", "ad"],
    "Windows": ["windows", "windows 10", "windows 11"],
    "macOS": ["macos", "mac os", "osx"],
    "Android": ["android"],
    "iOS": ["ios"],
    "Mathematics": ["mathematics", "maths", "math"],
    "Computer Science": ["computer science", "cs", "comp sci"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "Next.js": ["next.js", "nextjs", "next js"],
    "Tailwind CSS": ["tailwind", "tailwind css", "tailwindcss"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Machine Learning": ["machine learning", "ml"],
    "LLM": ["llm", "large language model", "large language models"],
    "OpenAI": ["openai", "gpt"],
    "Gemini": ["gemini", "google gemini"],
    "Automation": ["automation", "workflow automation"],
    "IT Support": ["it support", "technical support", "help desk", "helpdesk"],
    "Teaching": ["teaching", "instructor", "lecturer"],
}


def build_alias_lookup() -> dict[str, str]:
    """Map normalized alias → canonical skill name."""
    lookup: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        lookup[canonical.lower()] = canonical
        for alias in aliases:
            lookup[alias.lower()] = canonical
    return lookup


ALIAS_TO_CANONICAL = build_alias_lookup()


# Lightweight title aliases for normalization (do not change meaning).
TITLE_ALIASES: dict[str, str] = {
    "react native eng.": "React Native Engineer",
    "react native eng": "React Native Engineer",
    "rn developer": "React Native Developer",
    "rn engineer": "React Native Engineer",
    "fullstack developer": "Full Stack Developer",
    "full-stack developer": "Full Stack Developer",
    "full stack eng": "Full Stack Engineer",
    "swe": "Software Engineer",
    "sde": "Software Developer",
    "it support eng": "IT Support Engineer",
    "app support": "Application Support",
    "maths teacher": "Mathematics Teacher",
    "math teacher": "Mathematics Teacher",
    "cs teacher": "Computer Science Teacher",
}


DEFAULT_MATCH_WEIGHTS: dict[str, float] = {
    "role": 0.30,
    "skills": 0.35,
    "experience": 0.15,
    "education": 0.10,
    "location": 0.10,
}
