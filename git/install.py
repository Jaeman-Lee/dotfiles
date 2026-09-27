#!/usr/bin/env python3
"""Install a managed Git profile and non-destructive per-repository push guards."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def git(*args, cwd=None):
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    return result.returncode, result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    target = Path.home() / ".config/git/managed-workflow.inc"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != (source / "workflow.inc").read_bytes():
        raise SystemExit("Existing managed profile differs; review before replacing.")
    shutil.copyfile(source / "workflow.inc", target)
    _, includes = git("config", "--global", "--get-all", "include.path")
    if str(target) not in includes.splitlines():
        code, _ = git("config", "--global", "--add", "include.path", str(target))
        if code:
            raise SystemExit("Cannot install global include")
    results = []
    for repo in sorted(args.root.iterdir()):
        if not (repo / ".git").exists():
            continue
        _, override = git("config", "--get", "core.hooksPath", cwd=repo)
        if override:
            results.append({"repo": repo.name, "guard": "existing hooksPath preserved"})
            continue
        _, common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=repo)
        _, default = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", cwd=repo)
        if not default.startswith("origin/"):
            results.append({"repo": repo.name, "guard": "default branch unknown"})
            continue
        hook = Path(common) / "hooks/pre-push"
        if hook.exists() and hook.read_bytes() != (source / "pre-push").read_bytes():
            results.append({"repo": repo.name, "guard": "existing pre-push preserved"})
            continue
        hook.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "pre-push", hook)
        hook.chmod(0o755)
        git("config", "workflow.defaultBranch", default.removeprefix("origin/"), cwd=repo)
        results.append({"repo": repo.name, "guard": "installed"})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
