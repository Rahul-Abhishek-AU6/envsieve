"""Integration tests for EnvSieve core reconciliation engine."""
import tempfile
import unittest
from pathlib import Path

from envsieve.core import EnvSieveAuditor


class TestCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_environment_variable_detected(self):
        # Template only has PORT
        (self.root / ".env.example").write_text("PORT=8000\n", encoding="utf-8")

        # Code requires DATABASE_URL and STRIPE_KEY
        (self.root / "app.py").write_text(
            """import os
port = os.getenv("PORT", "8000")
db_url = os.environ["DATABASE_URL"]
stripe = os.environ["STRIPE_KEY"]
""",
            encoding="utf-8"
        )

        auditor = EnvSieveAuditor(self.root)
        report = auditor.audit()

        self.assertTrue(report.has_critical_violations)
        self.assertEqual(len(report.missing_variables), 2)
        missing_keys = {m.key for m in report.missing_variables}
        self.assertIn("DATABASE_URL", missing_keys)
        self.assertIn("STRIPE_KEY", missing_keys)

    def test_clean_workspace_passes(self):
        (self.root / ".env.example").write_text(
            "API_KEY=your_key\nDATABASE_URL=postgres://...\n", encoding="utf-8"
        )
        (self.root / "main.py").write_text(
            """import os
api = os.getenv("API_KEY")
db = os.environ["DATABASE_URL"]
""",
            encoding="utf-8"
        )

        auditor = EnvSieveAuditor(self.root)
        report = auditor.audit()

        self.assertFalse(report.has_critical_violations)
        self.assertEqual(len(report.missing_variables), 0)
        self.assertEqual(len(report.zombie_variables), 0)

    def test_zombie_template_variable_detected(self):
        # Template declares DEPRECATED_FLAG and ACTIVE_VAR
        (self.root / ".env.example").write_text(
            "ACTIVE_VAR=true\nDEPRECATED_FLAG=old_setting\n", encoding="utf-8"
        )
        # Code only accesses ACTIVE_VAR
        (self.root / "index.js").write_text(
            "const val = process.env.ACTIVE_VAR;\n", encoding="utf-8"
        )

        auditor = EnvSieveAuditor(self.root)
        report = auditor.audit()

        self.assertFalse(report.has_critical_violations)
        self.assertEqual(len(report.zombie_variables), 1)
        self.assertEqual(report.zombie_variables[0].key, "DEPRECATED_FLAG")


if __name__ == "__main__":
    unittest.main()
