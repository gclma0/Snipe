import re

TECHNICAL_SKILLS = {
    "api",
    "api testing",
    "automation",
    "backend",
    "c#",
    "ci/cd",
    "cloud",
    "css",
    "data analysis",
    "data engineering",
    "data visualization",
    "django",
    "fastapi",
    "frontend",
    "html",
    "java",
    "javascript",
    "machine learning",
    "node.js",
    "python",
    "qa testing",
    "react",
    "rest api",
    "software testing",
    "sql",
    "typescript",
    "ui design",
    "ux",
    "web development",
}

BUSINESS_SKILLS = {
    "account management",
    "administration",
    "analytics",
    "budgeting",
    "business analysis",
    "business development",
    "client relations",
    "customer service",
    "customer success",
    "financial modeling",
    "inventory management",
    "operations",
    "process improvement",
    "procurement",
    "project coordination",
    "project management",
    "reporting",
    "risk management",
    "sales",
    "scheduling",
    "stakeholder management",
    "strategy",
    "vendor management",
}

MARKETING_SKILLS = {
    "brand strategy",
    "campaign management",
    "content marketing",
    "content strategy",
    "copywriting",
    "digital marketing",
    "email marketing",
    "market research",
    "marketing",
    "seo",
    "social media",
}

FINANCE_SKILLS = {
    "accounting",
    "accounts payable",
    "accounts receivable",
    "auditing",
    "bookkeeping",
    "forecasting",
    "payroll",
    "tax preparation",
}

DOMAIN_SKILLS = {
    "case management",
    "classroom management",
    "compliance",
    "curriculum development",
    "data entry",
    "documentation",
    "event planning",
    "healthcare administration",
    "legal research",
    "lesson planning",
    "medical billing",
    "patient care",
    "recruiting",
    "training",
}

SOFT_SKILLS = {
    "adaptability",
    "attention to detail",
    "collaboration",
    "communication",
    "conflict resolution",
    "critical thinking",
    "leadership",
    "negotiation",
    "organization",
    "problem solving",
    "teamwork",
    "time management",
    "writing",
}

TOOL_SKILLS = {
    "adobe photoshop",
    "asana",
    "aws",
    "azure",
    "docker",
    "excel",
    "figma",
    "git",
    "github",
    "google analytics",
    "google sheets",
    "hubspot",
    "jira",
    "looker",
    "microsoft office",
    "notion",
    "power bi",
    "quickbooks",
    "salesforce",
    "slack",
    "tableau",
    "trello",
    "word",
    "zendesk",
}

SKILL_TERMS = (
    TECHNICAL_SKILLS
    | BUSINESS_SKILLS
    | MARKETING_SKILLS
    | FINANCE_SKILLS
    | DOMAIN_SKILLS
    | SOFT_SKILLS
    | TOOL_SKILLS
)

SKILL_ALIASES = {
    "amazon web services": "aws",
    "administrative": "administration",
    "administrative coordinator": "administration",
    "ci cd": "ci/cd",
    "customer support": "customer service",
    "excel": "excel",
    "github actions": "ci/cd",
    "google sheet": "google sheets",
    "js": "javascript",
    "microsoft excel": "excel",
    "ms excel": "excel",
    "ms office": "microsoft office",
    "postgres": "sql",
    "postgresql": "sql",
    "powerbi": "power bi",
    "program management": "project management",
    "quality assurance": "qa testing",
    "stakeholders": "stakeholder management",
    "ts": "typescript",
}

TRANSFERABLE_SKILLS = SOFT_SKILLS | {
    "administration",
    "client relations",
    "customer service",
    "documentation",
    "operations",
    "process improvement",
    "project coordination",
    "project management",
    "reporting",
    "stakeholder management",
    "training",
}


def canonical_skill(value: str) -> str:
    normalized = " ".join(value.lower().strip().split())
    return SKILL_ALIASES.get(normalized, normalized)


def extract_known_skills(text: str, *, extra_terms: set[str] | None = None) -> list[str]:
    haystack = text.lower()
    terms = set(SKILL_TERMS) | set(SKILL_ALIASES)
    if extra_terms:
        terms.update(extra_terms)
    found = {
        canonical_skill(term)
        for term in terms
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", haystack)
    }
    return sorted(found)


def skill_excerpt(skill: str, text: str, *, limit: int = 500) -> str:
    terms = {skill} | {alias for alias, canonical in SKILL_ALIASES.items() if canonical == skill}
    for line in text.splitlines():
        if any(
            re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", line, re.IGNORECASE)
            for term in terms
        ):
            normalized = re.sub(r"\s+", " ", line).strip()
            if len(normalized) <= limit:
                return normalized
            return f"{normalized[: limit - 3].rstrip()}..."
    return skill
