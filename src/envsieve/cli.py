"""Command-line interface for EnvSieve."""
import argparse
import sys
from pathlib import Path
from . import __version__
from .core import EnvSieveAuditor
from .reporter import print_terminal_summary, to_json, to_markdown


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="envsieve",
        description="EnvSieve: Zero-dependency environment variable and .env.example drift detector."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--path", "-p", default=".", help="Root directory of repository to audit")
    parser.add_argument("--diff", "-d", action="store_true", help="Analyze only modified/added files in git diff")
    parser.add_argument("--base", help="Git base reference for comparison (e.g. 'main', 'HEAD~1')")
    parser.add_argument("--json", action="store_true", help="Print report as JSON to stdout")
    parser.add_argument("--output-json", metavar="FILE", help="Write JSON report to specified file path")
    parser.add_argument("--output-md", metavar="FILE", help="Write Markdown review card to specified file path")
    parser.add_argument("--strict", action="store_true", help="Fail with exit code 1 if zombie variables are found")

    args = parser.parse_args(argv)
    target_dir = Path(args.path).resolve()

    if not target_dir.exists():
        print(f"Error: Target path '{args.path}' does not exist.", file=sys.stderr)
        return 2

    auditor = EnvSieveAuditor(
        root_dir=target_dir,
        diff_mode=args.diff,
        base_ref=args.base,
    )

    report = auditor.audit()

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(to_json(report), encoding="utf-8")

    if args.output_md:
        out_p = Path(args.output_md)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(to_markdown(report), encoding="utf-8")

    if args.json:
        print(to_json(report))
    else:
        print_terminal_summary(report)

    if report.has_critical_violations:
        return 1
    if args.strict and len(report.zombie_variables) > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
