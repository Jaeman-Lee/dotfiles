"""Exercise push policy and idempotent installation with disposable repositories."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {
            'GIT_CONFIG_GLOBAL': str(self.root / 'global.config'),
            'GIT_CONFIG_NOSYSTEM': '1',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.repos = self.root / 'repos'
        self.repos.mkdir()
        self.repo = self.repos / 'example'
        self.git('init', '-q', str(self.repo), cwd=self.root)
        self.git('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')

    def git(self, *args, cwd=None):
        return subprocess.check_output(['git', *args], cwd=cwd or self.repo, text=True).strip()

    def push(self, branch):
        return subprocess.run(['sh', str(ROOT / 'git/pre-push')], cwd=self.repo,
            input=f'refs/heads/feature {"1" * 40} refs/heads/{branch} {"0" * 40}\n',
            capture_output=True, text=True).returncode

    def test_default_branch_rejected_feature_allowed(self):
        self.assertEqual(self.push('main'), 1)
        self.assertEqual(self.push('feature'), 0)
        self.git('config', 'workflow.defaultBranch', 'master')
        self.assertEqual(self.push('master'), 1)

    def test_unknown_default_fails_closed(self):
        self.git('symbolic-ref', '--delete', 'refs/remotes/origin/HEAD')
        self.assertEqual(self.push('feature'), 1)

    def test_install_idempotent_and_custom_hook_preserved(self):
        spec = importlib.util.spec_from_file_location('installer', ROOT / 'git/install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with patch.object(Path, 'home', return_value=self.root), patch.object(sys, 'argv', ['install', '--root', str(self.repos)]):
            installer.main()
            installer.main()
            includes = self.git('config', '--global', '--get-all', 'include.path').splitlines()
            self.assertEqual(len(includes), 1)
            self.assertEqual(self.git('config', '--get', 'pull.ff'), 'only')
            hook = self.repo / '.git/hooks/pre-push'
            self.assertEqual(hook.read_bytes(), (ROOT / 'git/pre-push').read_bytes())
            hook.write_text('#!/bin/sh\nexit 0\n')
            installer.main()
            self.assertEqual(hook.read_text(), '#!/bin/sh\nexit 0\n')


if __name__ == '__main__':
    unittest.main()
