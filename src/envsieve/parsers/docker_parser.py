"""Parser for Dockerfiles and docker-compose files."""
import re
from pathlib import Path
from typing import Dict, Set

DOCKER_ENV_RE = re.compile(r"""^\s*ENV\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:=|\s+)""", re.IGNORECASE)
DOCKER_ARG_RE = re.compile(r"""^\s*ARG\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:=|\s+|$)""", re.IGNORECASE)


def parse_dockerfile(path: Path | str) -> Set[str]:
    """Extract environment variable keys declared in Dockerfile."""
    file_path = Path(path)
    keys: Set[str] = set()

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return keys

    for line in content.splitlines():
        line = line.strip()
        m_env = DOCKER_ENV_RE.match(line)
        if m_env:
            keys.add(m_env.group(1))
            continue
        m_arg = DOCKER_ARG_RE.match(line)
        if m_arg:
            keys.add(m_arg.group(1))

    return keys
