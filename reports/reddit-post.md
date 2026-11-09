# Community Launch Announcement: EnvSieve

Status: **Ready for Submission**  
Project: **EnvSieve**  
Public Repository: https://github.com/Rahul-Abhishek-AU6/envsieve

---

## 1. Candidate Subreddits & Rules Review

| Subreddit | Recommended Flair | Rules & Self-Promotion Guidelines |
|---|---|---|
| **r/Python** (Primary) | `Showcase` / `Project` | Requires open-source code link, MIT license, and direct explanation. No direct commercial ads or affiliate links. |
| **r/programming** | `Discussion` | 9:1 participation ratio rule; frame as an architectural discussion around environment variable drift and static analysis in AI agent loops. |
| **r/devops** | `Tools` | Focus on CI/CD pipeline reliability, preventing container boot crashes, and pre-commit automation. |
| **r/ClaudeAI** / **r/Cursor** | `Discussion` | Highlight the specific failure mode where coding agents write `os.environ[...]` without updating `.env.example`. |

---

## 2. Prepared Post

### Title Options
- **Option 1 (Recommended)**: *I built EnvSieve: a zero-dependency CLI that catches missing environment variables and .env.example drift in 20ms before production crashes*
- **Option 2**: *Why AI coding agents forget .env.example, and how we caught it statically before CI/CD*

---

### Body

```markdown
Hey r/Python,

If you work with team codebases or use AI coding agents (Claude Code, Cursor, Copilot, Antigravity), you’ve probably experienced this deployment disaster:

1. A developer or agent adds a new feature that reads a new configuration key (`os.environ["PAYMENT_WEBHOOK_SECRET"]` or `process.env.REDIS_URL`).
2. Locally, the code runs fine because the key is already set in their personal `.env`.
3. They commit and push, forgetting to update `.env.example` or staging configs.
4. Unit tests pass (mocked).
5. The container deploys to production and immediately crashes on boot with `KeyError` or an unhandled exception during checkout.

To eliminate this friction, I built **EnvSieve**: a fast, zero-dependency pre-commit and CI verification check.

### What it does:
- **Zero External Dependencies**: Built with 100% Python standard library (`ast`, `re`, `pathlib`, `json`). You don't need to pip-install anything to run it.
- **Pure Static AST & Token Parsing**: Scans Python (`os.environ[...]`, `os.getenv(...)`, `environ.get(...)`) and JS/TS (`process.env.*`, `import.meta.env.*`) without executing code.
- **Template Parity**: Automatically detects and parses `.env.example`, `.env.template`, `.env.sample`, and `Dockerfile` (`ENV`/`ARG`).
- **Secret Leak Detection**: Alerts if actual live API keys (e.g. Stripe keys, personal access tokens) are accidentally left inside template files.
- **Zombie Key Detection**: Flags variables declared in `.env.example` that are no longer used anywhere in code.
- **Sub-20ms Diff Mode (`--diff`)**: Audits only uncommitted git changes for instant pre-commit feedback.

### Quick Start (No installation needed):
```bash
# Clone the repository
git clone https://github.com/Rahul-Abhishek-AU6/envsieve.git
cd envsieve

# Run interactive demo simulating an AI agent omission
python3 demo.py

# Run over your uncommitted changes
python3 run_envsieve.py --diff
```

### GitHub Actions Integration:
```yaml
- name: Audit Environment Drift
  run: python3 run_envsieve.py --strict
```

- **GitHub Repository**: https://github.com/Rahul-Abhishek-AU6/envsieve (MIT Licensed)
- **Visuals & Architecture**: Full dark-mode architectural diagram and terminal demo are in the repo README.

Would love to hear how other teams handle environment parity and template synchronization!
```

---

## 3. Submission Protocol

- Target Community: `r/Python` (Showcase)
- Visual asset embedded in README: `assets/envsieve-architecture-concept.png` & `assets/envsieve-terminal-demo.svg`
- Verification: All links verified live on GitHub.
