"""Unit tests for Python and JS/TS environment variable extractors."""
import tempfile
import unittest
from pathlib import Path

from envsieve.extractors.python_extractor import extract_python_env_vars
from envsieve.extractors.js_extractor import extract_js_env_vars


class TestExtractors(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_python_ast_extractor(self):
        py_file = self.root / "sample.py"
        py_file.write_text(
            """import os
from os import environ, getenv

# Subscript access (required)
api_key = os.environ["API_KEY"]
secret = environ['CLIENT_SECRET']

# .get() access with and without default
db_url = os.environ.get("DATABASE_URL")
cache_ttl = os.getenv("CACHE_TTL", "3600")
host = getenv("HOST", "localhost")
port = environ.get("PORT", 8080)
""",
            encoding="utf-8"
        )

        lookups = extract_python_env_vars(py_file)
        self.assertEqual(len(lookups), 6)

        keys = {lk.key for lk in lookups}
        self.assertIn("API_KEY", keys)
        self.assertIn("CLIENT_SECRET", keys)
        self.assertIn("DATABASE_URL", keys)
        self.assertIn("CACHE_TTL", keys)
        self.assertIn("HOST", keys)
        self.assertIn("PORT", keys)

        # Check required flags
        req_keys = {lk.key for lk in lookups if lk.is_required}
        self.assertIn("API_KEY", req_keys)
        self.assertIn("CLIENT_SECRET", req_keys)
        self.assertIn("DATABASE_URL", req_keys)

        opt_keys = {lk.key for lk in lookups if not lk.is_required}
        self.assertIn("CACHE_TTL", opt_keys)
        self.assertIn("HOST", opt_keys)
        self.assertIn("PORT", opt_keys)

    def test_js_extractor(self):
        js_file = self.root / "sample.js"
        js_file.write_text(
            """
const token = process.env.AUTH_TOKEN;
const port = process.env['SERVER_PORT'] || 3000;
const apiUrl = import.meta.env.VITE_API_URL;
const mode = import.meta.env['MODE'] ?? 'development';
""",
            encoding="utf-8"
        )

        lookups = extract_js_env_vars(js_file)
        self.assertEqual(len(lookups), 4)

        keys = {lk.key for lk in lookups}
        self.assertIn("AUTH_TOKEN", keys)
        self.assertIn("SERVER_PORT", keys)
        self.assertIn("VITE_API_URL", keys)
        self.assertIn("MODE", keys)


if __name__ == "__main__":
    unittest.main()
