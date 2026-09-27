#!/usr/bin/env python3
"""Report local Git health without reading working files or changing refs."""
import argparse
import json
import subprocess
from pathlib import Path


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def inspect(repo):
    head = git(repo, 'rev-parse', 'HEAD')
    upstream = git(repo, 'rev-parse', '--abbrev-ref', '@{upstream}')
    default = git(repo, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD')
    divergence = git(repo, 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}') if upstream else None
    counts = [int(n) for n in divergence.split()] if divergence else [None, None]
    changes = git(repo, 'status', '--porcelain=v1', '--untracked-files=normal')
    records = changes.splitlines() if changes else []
    worktrees = git(repo, 'worktree', 'list', '--porcelain') or ''
    return dict(repository=repo.name, branch=git(repo, 'branch', '--show-current') or '(detached)',
                head=head, upstream=upstream, ahead=counts[0], behind=counts[1],
                tracked_changes=sum(not line.startswith('??') for line in records),
                untracked_entries=sum(line.startswith('??') for line in records),
                default=default, base_commit=git(repo, 'merge-base', 'HEAD', default) if default else None,
                worktree_count=sum(line.startswith('worktree ') for line in worktrees.splitlines()),
                remote_state='last fetched; no network refresh')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps([inspect(p) for p in sorted(args.root.iterdir()) if (p / '.git').exists()], indent=2))


if __name__ == '__main__':
    main()
