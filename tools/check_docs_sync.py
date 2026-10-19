"""Require documentation alongside runtime changes and check local doc links."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def git(*arguments, input=None):
    return subprocess.check_output(["git", *arguments], input=input, text=True).strip()


def needs_documentation(paths):
    return any(
        (path.startswith(("fps_blocker/", "tools/")) and path.endswith(".py"))
        or ("/" not in path and path.endswith(".bat"))
        or (path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")))
        for path in paths
    )


def documentation_changed(paths):
    return any(path == "README.md" or (path.startswith("docs/") and path.endswith(".md")) for path in paths)


def broken_links(root):
    errors = []
    files = [root / "README.md", root / "CONTRIBUTING.md", *sorted((root / "docs").rglob("*.md"))]
    for file in files:
        if not file.is_file():
            errors.append(f"Missing documentation: {file.relative_to(root)}")
            continue
        content = file.read_text(encoding="utf-8")
        targets = re.findall(r"\]\(([^)]+)\)", content)
        targets += re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', content)
        for target in targets:
            if "://" in target or target.startswith(("#", "mailto:", "data:")):
                continue
            path = target.split("#", 1)[0]
            if path and not (file.parent / path).exists():
                errors.append(f"{file.relative_to(root)}: missing link target {target}")
    return errors


def event_base(event):
    if "pull_request" in event:
        return event["pull_request"]["base"]["sha"]
    before = event.get("before")
    return before if before and set(before) != {"0"} else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Base commit; defaults to the GitHub event base, or HEAD~1 locally")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    root = Path(git("rev-parse", "--show-toplevel"))
    base = args.base
    if base is None:
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if event_path:
            base = event_base(json.loads(Path(event_path).read_text(encoding="utf-8")))
            if base is None:
                base = git("hash-object", "-t", "tree", "--stdin", input="")
        else:
            base = "HEAD~1"
    paths = git("diff", "--name-only", base, args.head).splitlines()
    errors = broken_links(root)
    if needs_documentation(paths) and not documentation_changed(paths):
        errors.append("Runtime or workflow code changed without a README.md or docs/*.md update. Document behavior, setup, limitations or validation in the same change.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation check passed: code/docs change policy and local link targets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
