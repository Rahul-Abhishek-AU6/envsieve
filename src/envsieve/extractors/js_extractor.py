"""JavaScript and TypeScript environment variable access extractor."""
import re
from pathlib import Path
from typing import List
from .python_extractor import EnvVarLookup

# Regex patterns for Node.js and frontend env lookups
PROCESS_ENV_DOT_RE = re.compile(
    r"""\bprocess\.env\.([a-zA-Z_][a-zA-Z0-9_]*)\b"""
)
PROCESS_ENV_BRACKET_RE = re.compile(
    r"""\bprocess\.env\s*\[\s*['"]([a-zA-Z_][a-zA-Z0-9_]*)['"]\s*\]"""
)
IMPORT_META_DOT_RE = re.compile(
    r"""\bimport\.meta\.env\.([a-zA-Z_][a-zA-Z0-9_]*)\b"""
)
IMPORT_META_BRACKET_RE = re.compile(
    r"""\bimport\.meta\.env\s*\[\s*['"]([a-zA-Z_][a-zA-Z0-9_]*)['"]\s*\]"""
)


def extract_js_env_vars(file_path: Path | str) -> List[EnvVarLookup]:
    """Extract environment variable accesses from JS/TS source files."""
    path = Path(file_path)
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    results: List[EnvVarLookup] = []
    lines = content.splitlines()

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        found_keys = set()
        for pattern in (PROCESS_ENV_DOT_RE, PROCESS_ENV_BRACKET_RE, IMPORT_META_DOT_RE, IMPORT_META_BRACKET_RE):
            for match in pattern.finditer(line):
                found_keys.add(match.group(1))

        for k in found_keys:
            # Check if simple fallback or default present on same line (e.g. || 'default')
            has_default = "||" in line or "??" in line
            results.append(
                EnvVarLookup(
                    key=k,
                    file_path=str(path),
                    line_number=line_idx,
                    raw_statement=stripped,
                    is_required=not has_default,
                    has_default=has_default,
                )
            )

    return results
