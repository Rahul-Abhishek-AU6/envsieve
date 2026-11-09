"""Reporters for EnvSieve: Terminal output, JSON serialization, and Markdown cards."""
import json
import os
import sys
from typing import Optional, TextIO
from .core import EnvSieveReport


def use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


class Color:
    RED = "\033[91m" if use_color() else ""
    GREEN = "\033[92m" if use_color() else ""
    YELLOW = "\033[93m" if use_color() else ""
    BLUE = "\033[94m" if use_color() else ""
    MAGENTA = "\033[95m" if use_color() else ""
    CYAN = "\033[96m" if use_color() else ""
    BOLD = "\033[1m" if use_color() else ""
    DIM = "\033[2m" if use_color() else ""
    RESET = "\033[0m" if use_color() else ""


def print_terminal_summary(report: EnvSieveReport, stream: Optional[TextIO] = None) -> None:
    if stream is None:
        stream = sys.stdout

    print(f"\n{Color.BOLD}{Color.CYAN}EnvSieve Configuration & Environment Audit{Color.RESET}", file=stream)
    print(f"{Color.DIM}Root: {report.root_dir} | Mode: {'Git Diff' if report.is_diff_mode else 'Full Workspace'}{Color.RESET}", file=stream)
    templates_str = ", ".join(report.template_files_found) if report.template_files_found else "None found"
    print(f"{Color.DIM}Templates detected: {templates_str} | Scanned {report.scanned_files_count} files ({report.total_env_lookups} env accesses){Color.RESET}\n", file=stream)

    # 1. Missing variables
    if report.missing_variables:
        print(f"{Color.BOLD}{Color.RED}🚨 MISSING ENVIRONMENT VARIABLES IN TEMPLATE ({len(report.missing_variables)}){Color.RESET}", file=stream)
        print(f"{Color.DIM}These keys are read in code but missing from .env.example. Risk of production crash on startup!{Color.RESET}\n", file=stream)
        for idx, m in enumerate(report.missing_variables, start=1):
            req_str = f"{Color.RED}[REQUIRED]{Color.RESET}" if m.is_required else f"{Color.YELLOW}[HAS DEFAULT]{Color.RESET}"
            print(f"  {Color.BOLD}{idx}. {Color.RED}'{m.key}'{Color.RESET} {req_str} at {Color.BOLD}{m.file_path}:{m.line_number}{Color.RESET}", file=stream)
            print(f"     {Color.DIM}Code:{Color.RESET} {m.raw_statement}", file=stream)
            print(f"     {Color.YELLOW}Action:{Color.RESET} Add '{m.key}=...' to .env.example", file=stream)
            print("", file=stream)
    else:
        print(f"{Color.BOLD}{Color.GREEN}✅ All referenced environment variables are documented.{Color.RESET}\n", file=stream)

    # 2. Secret leaks
    if report.secret_leaks:
        print(f"{Color.BOLD}{Color.MAGENTA}🔒 EXPOSED SECRETS IN TEMPLATE ({len(report.secret_leaks)}){Color.RESET}", file=stream)
        for s in report.secret_leaks:
            print(f"  - Key '{s.key}' at {s.template_file}:{s.line_number} -> {s.warning}", file=stream)
        print("", file=stream)

    # 3. Zombie variables
    if report.zombie_variables and not report.is_diff_mode:
        print(f"{Color.BOLD}{Color.YELLOW}⚠️  ZOMBIE TEMPLATE VARIABLES ({len(report.zombie_variables)}){Color.RESET}", file=stream)
        print(f"{Color.DIM}These keys exist in template files but are never referenced anywhere in code.{Color.RESET}\n", file=stream)
        for z in report.zombie_variables:
            print(f"  - {Color.YELLOW}{z.key}{Color.RESET} in {z.template_file}:{z.line_number}", file=stream)
        print("", file=stream)

    # Verdict
    if report.has_critical_violations:
        print(f"{Color.BOLD}{Color.RED}Result: FAILED{Color.RESET} — Found {len(report.missing_variables)} missing variable(s) or secret leaks.\n", file=stream)
    else:
        print(f"{Color.BOLD}{Color.GREEN}Result: PASSED{Color.RESET} — Environment variable hygiene verified.\n", file=stream)


def to_dict(report: EnvSieveReport) -> dict:
    return {
        "status": "failed" if report.has_critical_violations else "passed",
        "root_dir": report.root_dir,
        "is_diff_mode": report.is_diff_mode,
        "template_files_found": report.template_files_found,
        "scanned_files_count": report.scanned_files_count,
        "total_env_lookups": report.total_env_lookups,
        "missing_variables": [
            {
                "key": m.key,
                "file_path": m.file_path,
                "line_number": m.line_number,
                "raw_statement": m.raw_statement,
                "is_required": m.is_required,
            }
            for m in report.missing_variables
        ],
        "zombie_variables": [
            {
                "key": z.key,
                "template_file": z.template_file,
                "line_number": z.line_number,
            }
            for z in report.zombie_variables
        ],
        "secret_leaks": [
            {
                "key": s.key,
                "template_file": s.template_file,
                "line_number": s.line_number,
                "warning": s.warning,
            }
            for s in report.secret_leaks
        ],
    }


def to_json(report: EnvSieveReport, indent: int = 2) -> str:
    return json.dumps(to_dict(report), indent=indent)


def to_markdown(report: EnvSieveReport) -> str:
    lines = [
        "# EnvSieve Verification Report",
        "",
        f"- **Status**: {'🔴 **FAILED**' if report.has_critical_violations else '🟢 **PASSED**'}",
        f"- **Mode**: `{'git-diff' if report.is_diff_mode else 'full-workspace'}`",
        f"- **Scanned Files**: `{report.scanned_files_count}`",
        f"- **Environment Accesses**: `{report.total_env_lookups}`",
        f"- **Templates Detected**: `{', '.join(report.template_files_found) if report.template_files_found else 'None'}`",
        "",
    ]

    if report.missing_variables:
        lines.append("### 🚨 Missing Environment Variables in Templates")
        lines.append("")
        lines.append("| Variable Key | Status | File Location | Code Statement |")
        lines.append("|---|---|---|---|")
        for m in report.missing_variables:
            status_str = "**Required** (No default)" if m.is_required else "Optional (Has fallback)"
            lines.append(f"| `{m.key}` | {status_str} | `{m.file_path}:{m.line_number}` | `{m.raw_statement}` |")
        lines.append("")

    if report.secret_leaks:
        lines.append("### 🔒 Leaked Secrets in Template Files")
        lines.append("")
        for s in report.secret_leaks:
            lines.append(f"- **`{s.key}`** at `{s.template_file}:{s.line_number}`: {s.warning}")
        lines.append("")

    if report.zombie_variables and not report.is_diff_mode:
        lines.append("### ⚠️ Zombie Template Variables (Declared but Unused)")
        lines.append("")
        for z in report.zombie_variables:
            lines.append(f"- `{z.key}` in `{z.template_file}:{z.line_number}`")
        lines.append("")

    if not report.missing_variables and not report.secret_leaks and not report.zombie_variables:
        lines.append("✨ **All environment variables in code match template declarations. Ready to deploy!**")
        lines.append("")

    return "\n".join(lines)
