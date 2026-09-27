"""Safety checks: the diagnostic must not signal a reused or exited PID."""
import importlib.util
from pathlib import Path
import signal
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'watch_cs2', Path(__file__).with_name('watch-cs2-memory.py'))
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class SignalSafetyTests(unittest.TestCase):
    def test_reused_pid_is_preserved(self):
        with patch.object(watch, 'games', return_value={123: 'new'}), \
                patch.object(watch.os, 'kill') as kill:
            watch.stop({123: 'old'}, signal.SIGTERM)
            kill.assert_not_called()

    def test_matching_identity_is_signalled(self):
        with patch.object(watch, 'games', return_value={123: 'same'}), \
                patch.object(watch.os, 'kill') as kill:
            watch.stop({123: 'same'}, signal.SIGTERM)
            kill.assert_called_once_with(123, signal.SIGTERM)

    def test_exited_process_is_ignored(self):
        with patch.object(watch, 'games', return_value={}), \
                patch.object(watch.os, 'kill') as kill:
            watch.stop({123: 'old'}, signal.SIGKILL)
            kill.assert_not_called()

    def test_exit_between_check_and_signal_is_ignored(self):
        with patch.object(watch, 'games', return_value={123: 'same'}), \
                patch.object(watch.os, 'kill', side_effect=ProcessLookupError):
            watch.stop({123: 'same'}, signal.SIGTERM)


if __name__ == '__main__':
    unittest.main()
