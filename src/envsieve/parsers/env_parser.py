"""Parser for .env template files (.env.example, .env.template, etc.)."""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Secret detection patterns (high-confidence actual live secret indicators)
SECRET_PATTERNS = [
    re.compile(r"sk_live_[0-9a-zA-Z]{24,}"),
    re.compile(r"ghp_[0-9a-zA-Z]{36}"),
    re.compile(r"AKIA[0-9A-Z_]{16,}"),
    re.compile(r"xox[baprs]-[0-9a-zA-Z_\-]{10,}"),
    re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
]


@dataclass
class EnvTemplateEntry:
    key: str
    value: str
    file_path: str
    line_number: int
    is_suspicious_secret: bool = False
    secret_warning: Optional[str] = None


def parse_env_template_file(path: Path | str) -> Dict[str, EnvTemplateEntry]:
    """Parse a .env.example / .env.template file into a dict of {KEY: EnvTemplateEntry}."""
    file_path = Path(path)
    entries: Dict[str, EnvTemplateEntry] = {}

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return entries

    for line_idx, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Handle 'export KEY=VAL'
        if stripped.startswith("export "):
            stripped = stripped[7:].strip()

        if "=" not in stripped:
            # Bare key declaration (e.g. KEY)
            key = stripped.strip()
            val = ""
        else:
            key, val = stripped.split("=", 1)
            key = key.strip()
            val = val.strip()

        # Remove surrounding quotes from value
        if len(val) >= 2 and ((val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'"))):
            val = val[1:-1]

        # Scan for secret patterns
        is_suspicious = False
        warning = None
        for pat in SECRET_PATTERNS:
            if pat.search(val):
                is_suspicious = True
                warning = f"Value in template matches known live secret signature: '{val[:8]}...'"
                break

        if key:
            entries[key] = EnvTemplateEntry(
                key=key,
                value=val,
                file_path=str(file_path),
                line_number=line_idx,
                is_suspicious_secret=is_suspicious,
                secret_warning=warning,
            )

    return entries
