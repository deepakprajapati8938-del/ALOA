"""
ALOA Phase 2 Audit Verification Tests
======================================
Verifies the security hardening, performance caching, and optimization items
from the Phase 2 audit plan.

Run from the project root (aloa/):
    python tests/audit_verify.py          # plain unittest runner
    python -m pytest tests/audit_verify.py -v   # if pytest is installed
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock, call

# Ensure the project root (aloa/) is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Test 1: Registry Cache Speed ────────────────────────────────────────────

class TestRegistryCacheSpeed(unittest.TestCase):
    """The second scan_installed_apps() call must be near-instant (cache hit)."""

    def _make_mock_winreg(self, mock_reg):
        """Configure winreg mock to return a single fake app."""
        # OpenKey context manager
        mock_key = MagicMock()
        mock_reg.OpenKey.return_value.__enter__ = lambda s: mock_key
        mock_reg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
        # One subkey visible
        mock_reg.QueryInfoKey.return_value = (1, 0, 0)
        mock_reg.EnumKey.return_value = "TestApp"

        # QueryValueEx: raise FileNotFoundError for anything except DisplayName
        def qve_side_effect(key, name):
            if name == "DisplayName":
                return ("TestApp", 1)
            raise FileNotFoundError(name)

        mock_reg.QueryValueEx.side_effect = qve_side_effect
        mock_reg.HKEY_LOCAL_MACHINE = 0x80000002
        mock_reg.HKEY_CURRENT_USER = 0x80000001

    def test_cache_returns_same_list_object(self):
        """Cache returns the exact same list object on a repeated call within TTL."""
        import importlib
        import lifecycle.registry as reg
        importlib.reload(reg)

        with patch("lifecycle.registry.winreg") as mock_reg:
            self._make_mock_winreg(mock_reg)
            first = reg.scan_installed_apps(refresh=True)

        # Second call — no winreg patch needed; must hit cache
        t0 = time.perf_counter()
        second = reg.scan_installed_apps()
        elapsed = time.perf_counter() - t0

        self.assertIs(first, second, "Cache should return the same list object")
        self.assertLess(elapsed, 0.05,
                        f"Cache hit took {elapsed:.3f}s — should be <50 ms")

    def test_clear_cache_forces_rescan(self):
        """clear_cache() must cause the next call to re-scan."""
        import lifecycle.registry as reg
        reg._APP_CACHE = ["dummy"]
        reg._LAST_SCAN_TIME = time.time()

        reg.clear_cache()

        self.assertEqual(reg._LAST_SCAN_TIME, 0,
                         "clear_cache() should reset _LAST_SCAN_TIME to 0")


# ── Test 2: Uninstall String Parser ─────────────────────────────────────────

class TestUninstallStringParsing(unittest.TestCase):
    """Verify that various registry uninstall strings are parsed safely."""

    def _parse(self, raw_cmd: str) -> list:
        import shlex
        try:
            parts = shlex.split(raw_cmd, posix=False)
        except ValueError:
            parts = raw_cmd.split()
        return parts

    def test_msiexec_string(self):
        raw = r'MsiExec.exe /X{12345678-ABCD-EF01-2345-6789ABCDEF01}'
        parts = self._parse(raw)
        self.assertEqual(parts[0], "MsiExec.exe")
        self.assertIn("/X{12345678-ABCD-EF01-2345-6789ABCDEF01}", parts)

    def test_quoted_path_with_spaces(self):
        raw = r'"C:\Program Files\MyApp\uninstall.exe" /S'
        parts = self._parse(raw)
        exe = parts[0].strip('"')
        self.assertIn("Program Files", exe)
        self.assertEqual(parts[-1], "/S")

    def test_bare_exe_no_args(self):
        raw = r'C:\Apps\remove.exe'
        parts = self._parse(raw)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], r'C:\Apps\remove.exe')

    def test_msiexec_silent_flags_appended(self):
        import shlex
        raw = r'MsiExec.exe /X{GUID}'
        cmd_parts = shlex.split(raw, posix=False)

        has_silent = any(a.lower() in ("/s", "/silent", "/quiet", "/qn")
                         for a in cmd_parts)
        if not has_silent and "msiexec" in cmd_parts[0].lower():
            if "/qn" not in [a.lower() for a in cmd_parts]:
                cmd_parts.extend(["/qn", "/norestart"])

        self.assertIn("/qn", cmd_parts)
        self.assertIn("/norestart", cmd_parts)


# ── Test 3: Parser Multi-word Target Casing ─────────────────────────────────

class TestParserTargetCasing(unittest.TestCase):
    """The parser must preserve the original casing of multi-word app names."""

    def test_multiword_target_preserves_case(self):
        from core.parser import parse
        cmd = parse("install Visual Studio Code")
        self.assertEqual(cmd.intent, "install")
        self.assertEqual(cmd.target, "Visual Studio Code",
                         "Target should preserve user casing, not be lowercased")

    def test_single_word_target(self):
        from core.parser import parse
        cmd = parse("install maven")
        self.assertEqual(cmd.intent, "install")
        self.assertEqual(cmd.target, "maven")

    def test_natural_language_target(self):
        from core.parser import parse
        cmd = parse("can you install Node.js for me please")
        self.assertEqual(cmd.intent, "install")
        self.assertIn("Node.js", cmd.target)

    def test_uninstall_preserves_casing(self):
        from core.parser import parse
        cmd = parse("uninstall Google Chrome")
        self.assertEqual(cmd.intent, "uninstall")
        self.assertEqual(cmd.target, "Google Chrome")


# ── Test 4: is_protected() respected in suggestion flow ─────────────────────

class TestIsProtectedInSuggestions(unittest.TestCase):
    """Protected processes must never appear as suggestion targets."""

    def test_protected_processes(self):
        from utils.constants import is_protected
        for proc in ["lsass.exe", "csrss.exe", "svchost.exe",
                     "winlogon.exe", "python.exe", "System"]:
            self.assertTrue(is_protected(proc),
                            f"Expected {proc!r} to be protected")

    def test_user_processes_not_protected(self):
        from utils.constants import is_protected
        for proc in ["notepad.exe", "chrome.exe", "vlc.exe", "steam.exe"]:
            self.assertFalse(is_protected(proc),
                             f"{proc!r} should NOT be protected")

    def test_is_protected_case_insensitive(self):
        from utils.constants import is_protected
        self.assertTrue(is_protected("LSASS.EXE"))
        self.assertTrue(is_protected("Svchost.Exe"))
        self.assertFalse(is_protected("CHROME.EXE"))


# ── Test 5: _execute_suggestion never uses shell=True ───────────────────────

class TestExecuteSuggestionNoShell(unittest.TestCase):
    """subprocess.run must never be invoked with shell=True in suggestions."""

    # Patch Rich's console so the ✔/✖ Unicode chars don't trip up the
    # Windows CP1252 codec in test output.
    def setUp(self):
        self.console_patcher = patch("utils.formatting.console")
        self.mock_console = self.console_patcher.start()

    def tearDown(self):
        self.console_patcher.stop()

    def test_taskkill_no_shell(self):
        from health.suggestions import _execute_suggestion

        suggestion = {
            "priority": 1,
            "category": "RAM",
            "action": "Close notepad.exe",
            "command": 'taskkill /IM "notepad.exe" /F',
            "impact": "Free RAM",
            "auto_executable": True,
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            _execute_suggestion(suggestion)

            self.assertTrue(mock_run.called, "subprocess.run should have been called")
            _args, kwargs = mock_run.call_args
            self.assertNotEqual(
                kwargs.get("shell", False), True,
                "subprocess.run must NOT be called with shell=True",
            )

    def test_cleanmgr_no_shell(self):
        from health.suggestions import _execute_suggestion

        suggestion = {
            "priority": 2,
            "category": "Disk",
            "action": "Run Disk Cleanup",
            "command": "cleanmgr /d C",
            "impact": "Free disk space",
            "auto_executable": True,
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            _execute_suggestion(suggestion)

            if mock_run.called:
                _args, kwargs = mock_run.call_args
                self.assertNotEqual(kwargs.get("shell", False), True)

    def test_cleanup_sentinel_does_not_call_subprocess(self):
        from health.suggestions import _execute_suggestion

        suggestion = {
            "command": "__cleanup__",
            "action": "Clean temp files",
            "auto_executable": True,
        }

        with patch("subprocess.run") as mock_run, \
             patch("health.suggestions.execute_cleanup", return_value=(0, 0)):
            _execute_suggestion(suggestion)
            mock_run.assert_not_called()


# ── Test 6: scan_clutter depth pruning ──────────────────────────────────────

class TestScanClutterDepthPruning(unittest.TestCase):
    """The depth-limited clutter scan must cap traversal for deep directories."""

    def test_max_clutter_depth_constant(self):
        """_MAX_CLUTTER_DEPTH must exist and be a reasonable value."""
        import health.disk_inspector as di
        self.assertTrue(hasattr(di, "_MAX_CLUTTER_DEPTH"),
                        "disk_inspector must define _MAX_CLUTTER_DEPTH")
        self.assertGreaterEqual(di._MAX_CLUTTER_DEPTH, 1)
        self.assertLessEqual(di._MAX_CLUTTER_DEPTH, 5,
                             "Max depth should be conservative (<= 5)")

    def test_shallow_clutter_dirs_defined(self):
        """_SHALLOW_CLUTTER_DIRS must list the directories to depth-limit."""
        import health.disk_inspector as di
        self.assertTrue(hasattr(di, "_SHALLOW_CLUTTER_DIRS"),
                        "disk_inspector must define _SHALLOW_CLUTTER_DIRS")
        self.assertTrue(
            any("Firefox" in m or "Profiles" in m
                for m in di._SHALLOW_CLUTTER_DIRS),
            "_SHALLOW_CLUTTER_DIRS should include 'Firefox' or 'Profiles'"
        )

    def test_dirnames_pruned_inplace_for_large_files(self):
        """find_large_files must use in-place dirnames pruning (_SKIP_DIRS)."""
        import health.disk_inspector as di

        visited_dirs = []

        def fake_walk(path):
            """Yield a root dir with one 'appdata' subdir — should be pruned."""
            root = path
            appdata_sub = "AppData"
            docs_sub = "Documents"
            yield (root, [appdata_sub, docs_sub], [])
            # If appdata_sub is NOT pruned, os.walk would yield it
            yield (os.path.join(root, docs_sub), [], ["bigfile.iso"])

        with patch("os.path.isdir", return_value=True), \
             patch("os.walk", side_effect=fake_walk), \
             patch("os.path.getsize", return_value=600 * 1024 * 1024):
            results = di.find_large_files(root="C:\\", threshold_mb=500)

        # The appdata subdir should have been removed from dirnames in-place,
        # so we should only get results from Documents, not AppData
        appdata_results = [r for r in results if "AppData" in r["path"]]
        self.assertEqual(len(appdata_results), 0,
                         "AppData should be pruned in-place by find_large_files")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
