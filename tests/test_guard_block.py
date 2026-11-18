"""A message that is not a hybrid command is not worked on.

The plugin used to skip messages carrying a guard marker set by guard-plugin, but no plugin
in the fleet ever produced that marker (guard-plugin only looks itself up and never writes
it), so the check was removed as obsolete behavior, not as a regression.
"""
import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

# the Cat services need these to build their singletons at import time
os.environ.setdefault("CAT_CRYPTO_SALT", "testsalt")
os.environ.setdefault("CAT_CRYPTO_KEY", "testkey")

PLUGIN_DIR = Path(__file__).resolve().parents[1]
FAST_REPLY = None


def _load():
    global FAST_REPLY
    from cat.looking_glass.mad_hatter.plugin import Plugin

    # the loader derives the module path from the plugin path, so it must be relative to an importable root
    sys.path.insert(0, str(PLUGIN_DIR.parent))
    cwd = os.getcwd()
    os.chdir(PLUGIN_DIR.parent)
    try:
        plugin = Plugin(PLUGIN_DIR.name)
        plugin._load_decorated_functions()
    finally:
        os.chdir(cwd)
    FAST_REPLY, = [h.function for h in plugin.hooks if h.name == "agent_fast_reply"]


class GuardBlockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _load()

    def test_a_plain_message_is_not_worked_on(self):
        # no guard marker exists on the working memory, and the message is not a plugin command
        cat = mock.Mock()
        cat.working_memory = mock.Mock(spec=["user_message", "context_memories"])
        cat.working_memory.user_message = SimpleNamespace(text="hello there")
        cat.working_memory.context_memories = []
        self.assertIsNone(asyncio.run(FAST_REPLY(cat)))
        self.assertEqual(cat.mock_calls, [], "nothing of the Cat is used")

    def test_every_file_passes_the_security_scan(self):
        from cat.looking_glass.mad_hatter.plugin_extractor import PluginExtractor

        self.assertTrue(PluginExtractor._is_safe_plugin(str(PLUGIN_DIR)))


if __name__ == "__main__":
    unittest.main()
