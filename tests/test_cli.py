"""Tests for EnvSieve CLI interface."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from envsieve.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_clean_returns_zero(self):
        (self.root / ".env.example").write_text("HOST=localhost\n", encoding="utf-8")
        (self.root / "app.py").write_text("import os; h = os.getenv('HOST')\n", encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("PASSED", buf.getvalue())

    def test_cli_missing_returns_one(self):
        (self.root / ".env.example").write_text("HOST=localhost\n", encoding="utf-8")
        (self.root / "app.py").write_text("import os; secret = os.environ['SECRET_KEY']\n", encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--path", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("FAILED", buf.getvalue())
        self.assertIn("SECRET_KEY", buf.getvalue())

    def test_cli_json_and_markdown_output_files(self):
        (self.root / ".env.example").write_text("PORT=3000\n", encoding="utf-8")
        (self.root / "app.py").write_text("import os; p = os.getenv('PORT')\n", encoding="utf-8")

        json_out = self.root / "report.json"
        md_out = self.root / "report.md"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main([
                "--path", str(self.root),
                "--json",
                "--output-json", str(json_out),
                "--output-md", str(md_out)
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], "passed")
        self.assertTrue(json_out.is_file())
        self.assertTrue(md_out.is_file())


if __name__ == "__main__":
    unittest.main()
