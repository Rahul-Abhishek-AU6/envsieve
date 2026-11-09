#!/usr/bin/env python3
"""EnvSieve Interactive Simulation Demo.

Simulates a modern team / AI agent workflow:
1. Standard codebase with .env.example template.
2. AI-assisted feature introduces new environment variables.
3. EnvSieve catches missing keys and blocks pre-commit / CI gate.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from envsieve.cli import main


def run_demo():
    temp_dir = tempfile.TemporaryDirectory()
    demo_root = Path(temp_dir.name)

    print("=" * 60)
    print(" ENVSIEVE INTERACTIVE DEMO")
    print("=" * 60)

    try:
        # Step 1: Create template
        print("\n[Step 1] Creating repository template (.env.example):")
        (demo_root / ".env.example").write_text(
            """# Server configuration
PORT=8080
DATABASE_URL=postgres://user:pass@localhost:5432/app
OLD_UNUSED_METRIC=1
""",
            encoding="utf-8"
        )
        print("  -> Declared keys: PORT, DATABASE_URL, OLD_UNUSED_METRIC")

        # Step 2: Authoring standard code
        print("\n[Step 2] Authoring baseline application code:")
        src = demo_root / "src"
        src.mkdir()
        (src / "server.py").write_text(
            """import os
port = int(os.getenv("PORT", "8080"))
db_url = os.environ["DATABASE_URL"]
""",
            encoding="utf-8"
        )
        print("  -> server.py reads PORT and DATABASE_URL")

        # Step 3: Run baseline audit
        print("\n[Step 3] Running EnvSieve on baseline project:")
        main(["--path", str(demo_root)])

        # Step 4: Simulate AI Agent adding new payment service
        print("\n[Step 4] Simulating AI coding agent adding new payment service:")
        print("  -> Agent adds payments.py requiring STRIPE_SECRET_KEY and WEBHOOK_SIGNING_SECRET")
        print("  -> (Agent neglects to update .env.example)")
        (src / "payments.py").write_text(
            """import os

def process_charge():
    # Required secret lookups without defaults
    stripe_key = os.environ["STRIPE_SECRET_KEY"]
    signing_secret = os.environ["WEBHOOK_SIGNING_SECRET"]
    retry_limit = os.getenv("PAYMENT_RETRY_MAX", "3")
    return stripe_key
""",
            encoding="utf-8"
        )

        # Step 5: Run EnvSieve catching missing variables
        print("\n[Step 5] Running EnvSieve before commit / CI push:")
        exit_code = main([
            "--path", str(demo_root),
            "--output-json", str(demo_root / "env-report.json"),
            "--output-md", str(demo_root / "env-report.md")
        ])
        print(f"  -> EnvSieve exited with code: {exit_code} (1 indicates blocked CI gate)")

        # Step 6: Review generated Markdown card
        print("\n[Step 6] Generated Markdown review card (env-report.md):")
        print("-" * 50)
        print((demo_root / "env-report.md").read_text(encoding="utf-8"))
        print("-" * 50)

    finally:
        temp_dir.cleanup()

    print("\nDemo completed successfully!")


if __name__ == "__main__":
    run_demo()
