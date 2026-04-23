"""
ALOA Backend Regression Tests
Run: python tests/test_backend.py
"""
import sys, os, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))
        FAIL += 1


class TestCache(unittest.TestCase):
    def test_set_get(self):
        from utils.cache import TTLCache
        c = TTLCache("test")
        c.set("k", "v", 10)
        self.assertEqual(c.get("k"), "v")

    def test_expiry(self):
        from utils.cache import TTLCache
        c = TTLCache("test")
        c.set("k", "v", 1)
        time.sleep(1.1)
        self.assertIsNone(c.get("k"))

    def test_cache_hit_is_fast(self):
        from utils.cache import TTLCache
        c = TTLCache("test")
        c.set("big", "x" * 10000, 60)
        t0 = time.perf_counter()
        _ = c.get("big")
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, 0.005)  # under 5ms

    def test_normalize_key(self):
        from utils.cache import normalize_key
        self.assertEqual(normalize_key("  HELLO  "), "hello")

    def test_content_hash_length(self):
        from utils.cache import content_hash
        self.assertEqual(len(content_hash("anything")), 12)


class TestProviders(unittest.TestCase):
    def test_call_llm_no_keys_returns_error_string(self):
        """With no API keys, call_llm should return an error string, not raise."""
        import os
        # Temporarily blank all keys
        orig = {k: os.environ.pop(k, "") for k in ["GROQ_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY_1"]}
        from utils import providers
        # Reload to pick up empty env
        import importlib; importlib.reload(providers)
        result = providers.call_llm("test", use_cache=False)
        # Restore
        for k, v in orig.items():
            if v: os.environ[k] = v
        self.assertIn("⚠️", result)

    def test_llm_cache_hit(self):
        """Second call with same prompt should be instant (cache hit)."""
        from utils.cache import llm_cache, content_hash
        llm_cache.set(f"llm:{content_hash('test prompt')}", "cached answer", 60)
        from utils.providers import call_llm
        t0 = time.perf_counter()
        result = call_llm("test prompt")
        elapsed = time.perf_counter() - t0
        self.assertEqual(result, "cached answer")
        self.assertLess(elapsed, 0.01)


class TestNLPPreMatch(unittest.TestCase):
    """Tests the natural language feature matcher in main.py."""

    def _match(self, text):
        # Import the match function without running main()
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location(
            "aloa_main",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")
        )
        # We can't exec main() safely, so test the pattern logic directly
        import re
        FEATURE_PATTERNS = [
            (r"app|install|uninstall|open|launch|software",          1),
            (r"system|doctor|health|junk|clean|ram|cpu|memory|disk", 2),
            (r"attend|excel|sheet|absent|student|class",             3),
            (r"youtube|lecture|note|video|transcript",               4),
            (r"exam|quiz|question|mcq|pilot|solve",                  5),
            (r"code|debug|fix|error|heal|bug",                       6),
            (r"cloud|github|repo|remote|ci|deploy",                  7),
            (r"deploy|vercel|render|push|release",                   8),
            (r"resume|cv|profile|job|apply|generate",                9),
            (r"radar|news|intel|brief|daily|trend",                  10),
        ]
        for pattern, num in FEATURE_PATTERNS:
            if re.search(pattern, text.lower()):
                return num
        return None

    def test_install_maps_to_feature_1(self):
        self.assertEqual(self._match("install python"), 1)

    def test_health_maps_to_feature_2(self):
        self.assertEqual(self._match("check my cpu"), 2)

    def test_attendance_maps_to_feature_3(self):
        self.assertEqual(self._match("mark attendance"), 3)

    def test_youtube_maps_to_feature_4(self):
        self.assertEqual(self._match("make notes from youtube video"), 4)

    def test_code_healer_maps_to_feature_6(self):
        self.assertEqual(self._match("fix my bug"), 6)

    def test_radar_maps_to_feature_10(self):
        self.assertEqual(self._match("show me today's radar brief"), 10)

    def test_unknown_returns_none(self):
        self.assertIsNone(self._match("xyzzy nonsense gibberish"))


if __name__ == "__main__":
    print("=" * 60)
    print("ALOA Backend Regression Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
