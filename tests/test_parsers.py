"""Unit tests for template and container configuration parsers."""
import tempfile
import unittest
from pathlib import Path

from envsieve.parsers.docker_parser import parse_dockerfile
from envsieve.parsers.env_parser import parse_env_template_file


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_env_template_file(self):
        env_file = self.root / ".env.example"
        env_file.write_text(
            """# Database settings
DATABASE_URL=postgres://user:pass@localhost:5432/db
PORT=8000
DEBUG=false
export JWT_SECRET=your_jwt_secret_here
OPTIONAL_KEY
""",
            encoding="utf-8"
        )

        entries = parse_env_template_file(env_file)
        self.assertEqual(len(entries), 5)
        self.assertIn("DATABASE_URL", entries)
        self.assertEqual(entries["DATABASE_URL"].value, "postgres://user:pass@localhost:5432/db")
        self.assertIn("PORT", entries)
        self.assertIn("JWT_SECRET", entries)
        self.assertIn("OPTIONAL_KEY", entries)

    def test_detect_suspicious_secrets_in_template(self):
        env_file = self.root / ".env.example"
        env_file.write_text(
            """
SLACK_TOKEN=xoxb-dummy-test-sample-1234567890
AWS_KEY=AKIA_MOCK_TEST_SAMPLE_KEY
SAFE_PLACEHOLDER=your_key_here
""",
            encoding="utf-8"
        )
        entries = parse_env_template_file(env_file)
        self.assertTrue(entries["SLACK_TOKEN"].is_suspicious_secret)
        self.assertTrue(entries["AWS_KEY"].is_suspicious_secret)
        self.assertFalse(entries["SAFE_PLACEHOLDER"].is_suspicious_secret)

    def test_parse_dockerfile(self):
        docker_file = self.root / "Dockerfile"
        docker_file.write_text(
            """FROM python:3.11-slim
ARG BUILD_ENV=production
ENV APP_HOME=/app
ENV PORT=8080
CMD ["python", "app.py"]
""",
            encoding="utf-8"
        )
        keys = parse_dockerfile(docker_file)
        self.assertIn("BUILD_ENV", keys)
        self.assertIn("APP_HOME", keys)
        self.assertIn("PORT", keys)


if __name__ == "__main__":
    unittest.main()
