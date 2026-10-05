"""Local pre-publication scan. Reports paths/categories, never credential values."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".venv", "node_modules", ".runtime", ".backups", ".git", "__pycache__",
            ".pytest_cache", ".ruff_cache", "test-results", "playwright-report"}
PATTERNS = [re.compile(rb"gsk_[A-Za-z0-9]{20,}"), re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
            re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")]


def main():
    issues = []
    checked = 0
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDED for part in relative.parts):
            continue
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            continue
        if path.suffix in {".db", ".log", ".png", ".pyc"} or ".db-" in path.name:
            continue
        data = path.read_bytes()
        checked += 1
        if any(pattern.search(data) for pattern in PATTERNS):
            issues.append(f"Possible credential in {relative.as_posix()}")
        if "frontend/dist/" in relative.as_posix() and b"GROQ_API_KEY" in data:
            issues.append(f"Provider secret identifier in browser asset {relative.as_posix()}")
    rules = set((ROOT / ".gitignore").read_text().splitlines())
    required = {".env", ".env.*", "!.env.example", ".venv/", "node_modules/", "dist/", ".backups/", ".runtime/", "*.db", "*.db-*"}
    if not required.issubset(rules):
        issues.append("Required secret/generated-file ignore rules are missing")
    if issues:
        print("SECRET / PUBLICATION REVIEW REQUIRED")
        for issue in issues:
            print(issue)
        raise SystemExit(1)
    print(f"PASS: {checked} eligible files scanned; required ignore rules present; no matching credentials in publishable files or frontend assets.")
    print("Local .env intentionally excluded. Pattern scan is not a guarantee against every secret format.")
    print("Git history review: " + ("separate history scan required before push" if (ROOT / ".git").exists() else "no Git repository/history exists yet"))


if __name__ == "__main__":
    main()
