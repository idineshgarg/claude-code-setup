#!/usr/bin/env python3
"""Validate the dev-workflow config: command frontmatter, skill wiring, and the
worked example. Pure stdlib so CI needs no install step.

Exit 0 if everything checks out, 1 otherwise. Pass --github to also emit
::error:: annotations that GitHub Actions renders inline on the PR.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = "--github" in sys.argv

errors: list[str] = []
checks = 0


def fail(path: Path, msg: str) -> None:
    rel = path.relative_to(ROOT)
    errors.append(f"{rel}: {msg}")
    if GITHUB:
        print(f"::error file={rel}::{msg}")


def frontmatter(text: str) -> dict[str, str] | None:
    """Parse a leading `--- ... ---` block into a flat key: value dict."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip().splitlines()
    out: dict[str, str] = {}
    for line in block:
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip()
    return out


def check(cond: bool, path: Path, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        fail(path, msg)


# --- 1. Slash commands ------------------------------------------------------
command_dir = ROOT / ".claude" / "commands"
commands = sorted(command_dir.glob("*.md"))
check(len(commands) >= 5, command_dir, f"expected >=5 commands, found {len(commands)}")

for cmd in commands:
    fm = frontmatter(cmd.read_text())
    check(fm is not None, cmd, "missing or malformed YAML frontmatter")
    if fm is not None:
        check(bool(fm.get("description")), cmd, "frontmatter needs a non-empty 'description'")

# --- 2. Skill ------------------------------------------------------------------
skill = ROOT / ".claude" / "skills" / "dev-workflow" / "SKILL.md"
check(skill.exists(), skill, "skill file is missing")
if skill.exists():
    text = skill.read_text()
    fm = frontmatter(text)
    check(fm is not None and "name" in fm and "description" in fm,
          skill, "frontmatter needs 'name' and 'description'")
    # every command is referenced from the skill table
    for cmd in commands:
        name = cmd.stem
        check(f"/{name}" in text, skill, f"skill does not reference /{name}")
    # templates named in the skill exist on disk
    tdir = skill.parent / "templates"
    for tmpl in ("spec.md", "prd.md", "pull_request.md"):
        check((tdir / tmpl).exists(), tdir / tmpl, "referenced by SKILL.md but missing")

# --- 3. PR template ----------------------------------------------------------
gh_tmpl = ROOT / ".github" / "pull_request_template.md"
check(gh_tmpl.exists(), gh_tmpl, "missing GitHub PR template")

# --- 4. Worked example -----------------------------------------------------
example = ROOT / "examples" / "API-231"
for stage_file in ("ticket.md", "spec.md", "prd.md", "progress.md", "review.md",
                   "pull_request.md"):
    f = example / stage_file
    check(f.exists() and f.stat().st_size > 200, f,
          "worked-example stage file missing or suspiciously short")

# PRD acceptance criteria in the example should all be checked off
prd = example / "prd.md"
if prd.exists():
    unchecked = prd.read_text().count("- [ ] AC")
    check(unchecked == 0, prd, f"{unchecked} acceptance criteria still unchecked")

# --- report ----------------------------------------------------------------
summary = Path(sys.argv[sys.argv.index("--summary") + 1]) if "--summary" in sys.argv else None
line = (f"{checks - len(errors)}/{checks} checks passed"
        if not errors else f"{len(errors)} of {checks} checks FAILED")
if summary:
    body = "## Workflow validation\n\n"
    body += f"**{line}**\n\n"
    if errors:
        body += "\n".join(f"- ❌ {e}" for e in errors) + "\n"
    else:
        body += "All command frontmatter, skill wiring, and the worked example are intact.\n"
    summary.write_text(body)

print(line)
for e in errors:
    print(f"  - {e}")
sys.exit(1 if errors else 0)
