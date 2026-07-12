import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\w)"
)
URL_RE = re.compile(r"\b(?:https?://)?(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?", re.IGNORECASE)


def extract_contact(text: str) -> dict[str, list[str]]:
    emails = sorted({match.group(0).strip() for match in EMAIL_RE.finditer(text)})
    phones = sorted({_normalize_phone(match.group(0)) for match in PHONE_RE.finditer(text)})
    links = sorted(
        {
            _normalize_url(match.group(0))
            for match in URL_RE.finditer(text)
            if "@" not in match.group(0) and not _is_email_domain_match(text, match.start())
        }
    )
    return {"emails": emails, "phones": phones, "links": links}


def _normalize_phone(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _normalize_url(value: str) -> str:
    cleaned = value.strip().rstrip(".,;)")
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    return f"https://{cleaned}"


def _is_email_domain_match(text: str, start: int) -> bool:
    return start > 0 and text[start - 1] == "@"
