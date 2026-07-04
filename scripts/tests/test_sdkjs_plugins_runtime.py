import importlib.util
import sys
import tempfile
import types
import unittest
import warnings
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def load_base_module():
  sys.modules["config"] = types.SimpleNamespace(option=lambda name: "")
  spec = importlib.util.spec_from_file_location("base", ROOT_DIR / "scripts" / "base.py")
  module = importlib.util.module_from_spec(spec)
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    spec.loader.exec_module(module)
  return module


base = load_base_module()


class SdkjsPluginsRuntimePatchTest(unittest.TestCase):
  def test_rewrites_legacy_unload_cleanup_to_pagehide(self):
    self.assertTrue(hasattr(base, "patch_sdkjs_plugins_runtime_content"))

    content = (
      'b.Asc.plugin.detachEditorEvent=function(c){delete b.Asc.plugin["event_"+c]};'
      'b.onunload=function(){b.addEventListener?\n'
      'b.removeEventListener("message",q,!1):b.detachEvent("onmessage",q)}})(window,void 0);'
    )

    patched = base.patch_sdkjs_plugins_runtime_content(content)

    self.assertNotIn("b.onunload=function", patched)
    self.assertIn('b.addEventListener("pagehide"', patched)
    self.assertIn('b.removeEventListener("message",q,!1)', patched)
    self.assertIn('b.attachEvent("onunload"', patched)
    self.assertIn('b.detachEvent("onmessage",q)', patched)

  def test_runtime_patch_is_idempotent(self):
    self.assertTrue(hasattr(base, "patch_sdkjs_plugins_runtime_content"))

    content = (
      'b.onunload=function(){b.addEventListener?'
      'b.removeEventListener("message",q,!1):b.detachEvent("onmessage",q)}})(window,void 0);'
    )

    patched_once = base.patch_sdkjs_plugins_runtime_content(content)
    patched_twice = base.patch_sdkjs_plugins_runtime_content(patched_once)

    self.assertEqual(patched_once, patched_twice)

  def test_runtime_file_patch_updates_downloaded_plugins_js(self):
    self.assertTrue(hasattr(base, "patch_sdkjs_plugins_runtime_file"))

    content = (
      'b.onunload=function(){b.addEventListener?'
      'b.removeEventListener("message",q,!1):b.detachEvent("onmessage",q)}})(window,void 0);'
    )

    with tempfile.TemporaryDirectory() as temp_dir:
      plugins_js = Path(temp_dir) / "plugins.js"
      plugins_js.write_text(content)

      base.patch_sdkjs_plugins_runtime_file(str(plugins_js))

      patched = plugins_js.read_text()
      self.assertNotIn("b.onunload=function", patched)
      self.assertIn('b.addEventListener("pagehide"', patched)


if __name__ == "__main__":
  unittest.main()
