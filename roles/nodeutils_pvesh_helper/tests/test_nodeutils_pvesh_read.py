"""Stdlib-only unit tests for roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read.

Run with: python3 -m unittest roles.nodeutils_pvesh_helper.tests.test_nodeutils_pvesh_read
(from the ansible_agdev directory), or directly:
  python3 roles/nodeutils_pvesh_helper/tests/test_nodeutils_pvesh_read.py
"""
import importlib.machinery
import importlib.util
import os
import unittest

_HELPER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "files", "nodeutils-pvesh-read"
)

_loader = importlib.machinery.SourceFileLoader("nodeutils_pvesh_read", _HELPER_PATH)
_spec = importlib.util.spec_from_loader("nodeutils_pvesh_read", _loader)
helper = importlib.util.module_from_spec(_spec)
_loader.exec_module(helper)


ACCEPTED_PATHS = [
    "/cluster/status",
    "/cluster/resources",
    "/nodes",
    "/nodes/aghub/qemu",
    "/nodes/aghub/lxc",
    "/nodes/aghub/storage",
    "/nodes/aghub/network",
    "/nodes/aghub/qemu/100/config",
    "/nodes/aghub/lxc/9999/config",
    "/nodes/aghub/qemu/100/agent/network-get-interfaces",
    "/nodes/pve-node-1/qemu/1/config",
    "/nodes/aghub/storage/local/content",
    "/nodes/aghub/storage/local-lvm/content",
    "/nodes/aghub/storage/local_lvm/content",
]

REJECTED_PATHS = [
    "",
    "/",
    "/cluster",
    "/cluster/status/",
    "/cluster/status/../../etc/passwd",
    "/nodes/../etc/passwd/qemu",
    "/nodes/aghub/qemu\n/etc/passwd",
    "/nodes/aghub/qemu ; rm -rf /",
    "/nodes/aghub/qemu`id`",
    "/nodes/aghub/qemu$(id)",
    "/nodes/aghub/qemu/0/config",  # vmid must be positive, no leading zero digit rule (0 rejected)
    "/nodes/aghub/qemu/-1/config",
    "/nodes/aghub/qemu/01/config",
    "/nodes/a ghub/qemu",
    "/nodes/aghub/qemu?extra=1",
    "/nodes/aghub/qemu/100/config --delete",
    "/cluster/status --output-format json; pvesh get /access/users",
    "/access/users",
    "/nodes/aghub/qemu/100/status/start",
    "-e",
    "--help",
    # storage-content negative cases: traversal, query strings, whitespace, shell syntax,
    # extra path segments, invalid storage identifiers, and any write/status verb or path.
    "/nodes/aghub/storage/local/content/",
    "/nodes/aghub/storage/../../etc/passwd/content",
    "/nodes/aghub/storage/local/content?extra=1",
    "/nodes/aghub/storage/local /content",
    "/nodes/aghub/storage/local/content; rm -rf /",
    "/nodes/aghub/storage/local/content`id`",
    "/nodes/aghub/storage/local/content$(id)",
    "/nodes/aghub/storage//content",
    "/nodes/aghub/storage/local!/content",
    "/nodes/aghub/storage/local/content/extra",
    "/nodes/aghub/storage/local/content/100",
    "/nodes/aghub/storage/local/status",
    "/nodes/aghub/storage/local/content/100/download",
]

# Tier B / domain_contract: validate_path is the authoritative allowlist boundary.  These rows
# vary argv cardinality and endpoint syntax, asserting the canonical path or stable diagnostic.
# Exec construction and the real privileged-helper boundary are intentionally covered separately.
VALIDATE_PATH_CASES = [
    (f"accepted-{index:02d}", ["prog", path], path, None)
    for index, path in enumerate(ACCEPTED_PATHS, start=1)
] + [
    (f"rejected-{index:02d}", ["prog", path], None, "rejected API path")
    for index, path in enumerate(REJECTED_PATHS, start=1)
] + [
    ("extra-argument-rejected", ["prog", "/cluster/status", "/cluster/resources"], None, "expected exactly one API path argument"),
    ("missing-argument-rejected", ["prog"], None, "expected exactly one API path argument"),
    ("empty-argument-rejected", ["prog", ""], None, "rejected API path"),
]


class ValidatePathTests(unittest.TestCase):
    def test_validate_path_contract(self):
        for case_id, argv, expected_path, expected_error in VALIDATE_PATH_CASES:
            with self.subTest(case_id=case_id):
                if expected_error is None:
                    self.assertEqual(helper.validate_path(argv), expected_path)
                else:
                    with self.assertRaisesRegex(SystemExit, expected_error):
                        helper.validate_path(argv)


class MainExecTests(unittest.TestCase):
    def test_executed_argv_is_exact_pvesh_get_call(self):
        captured = {}

        def fake_execve(path, argv, env):
            captured["path"] = path
            captured["argv"] = argv
            captured["env"] = env

        original_execve = helper.os.execve
        helper.os.execve = fake_execve
        try:
            helper.main(["prog", "/cluster/status"])
        finally:
            helper.os.execve = original_execve

        self.assertEqual(captured["path"], "/usr/bin/pvesh")
        self.assertEqual(
            captured["argv"],
            ["/usr/bin/pvesh", "get", "/cluster/status", "--output-format", "json"],
        )

    def test_rejected_path_never_reaches_exec(self):
        calls = []
        original_execve = helper.os.execve
        helper.os.execve = lambda *a, **k: calls.append((a, k))
        try:
            with self.assertRaises(SystemExit):
                helper.main(["prog", "/access/users"])
        finally:
            helper.os.execve = original_execve
        self.assertEqual(calls, [])

    def test_no_shell_invocation_is_possible(self):
        # The helper never imports subprocess/os.system/popen and only calls os.execve.
        with open(_HELPER_PATH, encoding="utf-8") as fh:
            source = fh.read()
        for forbidden in ("subprocess", "os.system", "os.popen", "shell=True"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
