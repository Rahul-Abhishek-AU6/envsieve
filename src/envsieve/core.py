"""Core audit and reconciliation engine for EnvSieve."""
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from .extractors.js_extractor import extract_js_env_vars
from .extractors.python_extractor import EnvVarLookup, extract_python_env_vars
from .parsers.docker_parser import parse_dockerfile
from .parsers.env_parser import EnvTemplateEntry, parse_env_template_file

DEFAULT_IGNORE_DIRS = {
    ".git", ".hg", ".svn", "venv", ".venv", "env", ".env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", "assets",
    "logs", "prompts", "reports"
}

STANDARD_SYSTEM_ENV_VARS = {
    "PATH", "HOME", "USER", "SHELL", "PWD", "TERM", "LANG", "LC_ALL",
    "NODE_ENV", "PYTHONPATH", "PYTHONUNBUFFERED", "CI", "DEBUG", "NO_COLOR"
}


@dataclass
class MissingEnvFinding:
    key: str
    file_path: str
    line_number: int
    raw_statement: str
    is_required: bool


@dataclass
class ZombieEnvFinding:
    key: str
    template_file: str
    line_number: int


@dataclass
class SecretLeakFinding:
    key: str
    template_file: str
    line_number: int
    warning: str


@dataclass
class EnvSieveReport:
    root_dir: str
    is_diff_mode: bool
    template_files_found: List[str]
    scanned_files_count: int
    total_env_lookups: int
    missing_variables: List[MissingEnvFinding] = field(default_factory=list)
    zombie_variables: List[ZombieEnvFinding] = field(default_factory=list)
    secret_leaks: List[SecretLeakFinding] = field(default_factory=list)
    declared_keys: Set[str] = field(default_factory=set)

    @property
    def has_critical_violations(self) -> bool:
        return len(self.missing_variables) > 0 or len(self.secret_leaks) > 0


class EnvSieveAuditor:
    def __init__(self, root_dir: Path | str, diff_mode: bool = False, base_ref: Optional[str] = None):
        self.root_dir = Path(root_dir).resolve()
        self.diff_mode = diff_mode
        self.base_ref = base_ref

    def _discover_templates(self) -> Dict[str, EnvTemplateEntry]:
        """Find and parse template files in repository root."""
        templates: Dict[str, EnvTemplateEntry] = {}
        candidate_names = [".env.example", ".env.template", ".env.sample", "example.env"]

        for c in candidate_names:
            p = self.root_dir / c
            if p.is_file():
                entries = parse_env_template_file(p)
                templates.update(entries)

        # Dockerfile
        docker_p = self.root_dir / "Dockerfile"
        if docker_p.is_file():
            docker_keys = parse_dockerfile(docker_p)
            for k in docker_keys:
                if k not in templates:
                    templates[k] = EnvTemplateEntry(key=k, value="", file_path="Dockerfile", line_number=1)

        return templates

    def _get_target_files(self) -> List[Path]:
        if self.diff_mode:
            return self._get_git_diff_files()
        return self._crawl_directory()

    def _get_git_diff_files(self) -> List[Path]:
        cmd = ["git", "diff", "--name-only"]
        if self.base_ref:
            cmd.append(self.base_ref)
        else:
            cmd.append("HEAD")

        try:
            res = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                res = subprocess.run(["git", "diff", "--name-only"], cwd=self.root_dir, capture_output=True, text=True, check=False)

            output = res.stdout.strip().splitlines()
            files = []
            for line in output:
                p = (self.root_dir / line.strip()).resolve()
                if p.is_file() and self._is_scannable(p):
                    files.append(p)
            if not files:
                status_res = subprocess.run(["git", "status", "--porcelain"], cwd=self.root_dir, capture_output=True, text=True, check=False)
                for line in status_res.stdout.splitlines():
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        p = (self.root_dir / parts[1].strip()).resolve()
                        if p.is_file() and self._is_scannable(p):
                            files.append(p)
            return files
        except Exception:
            return self._crawl_directory()

    def _crawl_directory(self) -> List[Path]:
        files = []
        for root, dirs, filenames in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS and not d.startswith(".")]
            for fname in filenames:
                p = Path(root) / fname
                if self._is_scannable(p):
                    files.append(p)
        return sorted(files)

    def _is_scannable(self, path: Path) -> bool:
        ext = path.suffix.lower()
        return ext in {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

    def audit(self) -> EnvSieveReport:
        template_entries = self._discover_templates()
        declared_keys = set(template_entries.keys())
        target_files = self._get_target_files()

        template_file_names = sorted(list({Path(e.file_path).name for e in template_entries.values()}))

        report = EnvSieveReport(
            root_dir=str(self.root_dir),
            is_diff_mode=self.diff_mode,
            template_files_found=template_file_names,
            scanned_files_count=len(target_files),
            total_env_lookups=0,
            declared_keys=declared_keys,
        )

        # 1. Check template entries for secret leaks
        for key, entry in template_entries.items():
            if entry.is_suspicious_secret:
                report.secret_leaks.append(
                    SecretLeakFinding(
                        key=key,
                        template_file=str(Path(entry.file_path).relative_to(self.root_dir)) if Path(entry.file_path).is_relative_to(self.root_dir) else entry.file_path,
                        line_number=entry.line_number,
                        warning=entry.secret_warning or "Exposed sensitive credential in template",
                    )
                )

        referenced_keys_in_code: Set[str] = set()

        # 2. Extract code lookups
        for file_path in target_files:
            ext = file_path.suffix.lower()
            is_py = ext in {".py"}
            lookups = extract_python_env_vars(file_path) if is_py else extract_js_env_vars(file_path)
            report.total_env_lookups += len(lookups)

            rel_path = str(file_path.relative_to(self.root_dir))

            for lk in lookups:
                referenced_keys_in_code.add(lk.key)

                # Skip common system variables unless explicitly desired
                if lk.key in STANDARD_SYSTEM_ENV_VARS:
                    continue

                if lk.key not in declared_keys:
                    report.missing_variables.append(
                        MissingEnvFinding(
                            key=lk.key,
                            file_path=rel_path,
                            line_number=lk.line_number,
                            raw_statement=lk.raw_statement,
                            is_required=lk.is_required,
                        )
                    )

        # 3. Check for zombie variables (only during full scan)
        if not self.diff_mode and template_entries:
            for key, entry in template_entries.items():
                if key in STANDARD_SYSTEM_ENV_VARS:
                    continue
                if key not in referenced_keys_in_code:
                    rel_p = str(Path(entry.file_path).relative_to(self.root_dir)) if Path(entry.file_path).is_relative_to(self.root_dir) else entry.file_path
                    report.zombie_variables.append(
                        ZombieEnvFinding(
                            key=key,
                            template_file=rel_p,
                            line_number=entry.line_number,
                        )
                    )

        return report


def analyze_env_drift(root_dir: Path | str, diff_mode: bool = False, base_ref: Optional[str] = None) -> EnvSieveReport:
    auditor = EnvSieveAuditor(root_dir, diff_mode=diff_mode, base_ref=base_ref)
    return auditor.audit()
