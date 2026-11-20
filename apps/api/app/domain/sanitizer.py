"""PromptSanitizationService — SDD §2.5.3 "Zero-PoC to AI" guardrail; EC-13.

Two independent defenses before any data reaches an external LLM:
1. `whitelist_finding_metadata`: strict column whitelist — only abstract
   taxonomy (title/cwe_id/cvss_score/severity) ever leaves the DB boundary.
2. `sanitize_text`: strips concrete target data (IPs, URLs, hostnames,
   ports) and control characters from any free text that still needs to be
   included (e.g. scanner banners), as defense-in-depth against indirect
   prompt injection and residual PII leakage.
"""

import re

_WHITELISTED_FIELDS = ("title", "cwe_id", "cvss_score", "severity")

_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_BREAK_PATTERN = re.compile(r"[\r\n\t]+")
_URL_PATTERN = re.compile(r"\b\w+://\S+")
_IP_PATTERN = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b|"
    r"\b[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b|"
    r"\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b|"
    r"::1\b|"
    r"::ffff:(?:\d{1,3}\.){3}\d{1,3}\b"
)
_AWS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
_GITHUB_TOKEN_PATTERN = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}\b")

# Flat, single quantifier (no nesting) — a prior version used
# r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b", a nested-quantifier pattern that
# suffers catastrophic/quadratic backtracking on adversarial dotted input
# (measured: ~8-34s on a 40k-char "a." payload). EC-13's threat model is
# attacker-controlled scanner banner text, so this must stay linear.
# Candidate matching is O(n); hostname-shape validation happens in Python.
_HOSTNAME_CANDIDATE_PATTERN = re.compile(r"\b[a-zA-Z0-9.-]+\b")
_PORT_SUFFIX_PATTERN = re.compile(r":\d{2,5}\b")

_NON_HOST_EXTENSIONS = {
    "py",
    "js",
    "ts",
    "tsx",
    "jsx",
    "go",
    "rb",
    "rs",
    "java",
    "cs",
    "php",
    "json",
    "yaml",
    "yml",
    "toml",
    "xml",
    "tf",
    "hcl",
    "sql",
    "md",
    "txt",
    "sh",
    "lock",
    "env",
    "conf",
    "cfg",
    "ini",
    "vue",
    "css",
    "html",
    "png",
    "jpg",
    "jpeg",
    "svg",
}
_TECH_DOTTED_NAMES = {"node.js", "next.js", "nuxt.js", "vue.js", "asp.net", "socket.io"}

_SCRIPT_BLOCK_PATTERN = re.compile(r"<\s*script\b[^>]*>[\s\S]*?<\s*/\s*script\s*>", re.IGNORECASE)
_IFRAME_BLOCK_PATTERN = re.compile(r"<\s*iframe\b[^>]*>[\s\S]*?<\s*/\s*iframe\s*>", re.IGNORECASE)
_DANGEROUS_TAG_PATTERN = re.compile(
    r"<\s*/?\s*(?:script|iframe|object|embed)\b[^>]*>", re.IGNORECASE
)
_EVENT_HANDLER_PATTERN = re.compile(r"\bon[a-z]+\s*=", re.IGNORECASE)
_JS_URI_PATTERN = re.compile(r"javascript\s*:", re.IGNORECASE)


def whitelist_finding_metadata(finding: dict[str, object]) -> dict[str, object]:
    return {field: finding[field] for field in _WHITELISTED_FIELDS if field in finding}


def _looks_like_hostname(candidate: str) -> bool:
    lowered = candidate.lower()
    if lowered in _TECH_DOTTED_NAMES:
        return False
    labels = lowered.split(".")
    if len(labels) < 2 or any(not label for label in labels):
        return False
    tld = labels[-1]
    if not tld.isalpha() or len(tld) < 2:
        return False
    return not (len(labels) == 2 and tld in _NON_HOST_EXTENSIONS)


def _redact_hostname(match: re.Match[str]) -> str:
    candidate = match.group(0)
    return "[REDACTED_HOST]" if _looks_like_hostname(candidate) else candidate


def sanitize_text(text: str) -> str:
    text = _CONTROL_CHAR_PATTERN.sub(" ", text)
    text = _WHITESPACE_BREAK_PATTERN.sub(" ", text)
    text = _URL_PATTERN.sub("[REDACTED_URL]", text)
    text = _IP_PATTERN.sub("[REDACTED_IP]", text)
    text = _AWS_KEY_PATTERN.sub("[REDACTED_SECRET]", text)
    text = _GITHUB_TOKEN_PATTERN.sub("[REDACTED_SECRET]", text)
    text = _JWT_PATTERN.sub("[REDACTED_SECRET]", text)
    text = _HOSTNAME_CANDIDATE_PATTERN.sub(_redact_hostname, text)
    text = _PORT_SUFFIX_PATTERN.sub("", text)
    return text


def sanitize_html_text(text: str) -> str:
    """UC-12 E1: strip active XSS tags/handlers from human-edited AI narrative text."""
    cleaned = _CONTROL_CHAR_PATTERN.sub(" ", text)
    cleaned = _SCRIPT_BLOCK_PATTERN.sub("", cleaned)
    cleaned = _IFRAME_BLOCK_PATTERN.sub("", cleaned)
    cleaned = _DANGEROUS_TAG_PATTERN.sub("", cleaned)
    cleaned = _EVENT_HANDLER_PATTERN.sub("data-blocked-event=", cleaned)
    cleaned = _JS_URI_PATTERN.sub("blocked:", cleaned)
    return cleaned.strip()
