"""Exercise roles/nfs_client/tasks/macos.yml against scratch files, then
parse the result with the real macOS getfsent(3) (via a DYLD_INSERT_LIBRARIES
interposer redirecting /etc/fstab) so the macOS parser itself is the check,
not just the file text (project_migration p6 ex1): macOS's own "/- -static"
map drops an fstab entry carrying a trailing comment, so the fix moves the
"# nintent:<instance>" marker onto its own line above a comment-free entry.

Run with: python3 -m unittest roles.nfs_client.tests.test_nfs_client_macos_fstab
(from the ansible_agdev directory), or directly:
  python3 roles/nfs_client/tests/test_nfs_client_macos_fstab.py

Darwin-only (getfsent(3) and the macOS task file do not exist elsewhere) and
skipped when the local toolchain (cc) or ansible-playbook is unavailable.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(__file__)
_ROLE_ROOT = os.path.dirname(_HERE)
_ROLES_DIR = os.path.dirname(_ROLE_ROOT)
_ANSIBLE_AGDEV_DIR = os.path.dirname(_ROLES_DIR)
_GETFSENT_SRC = os.path.join(_HERE, "getfsent_fstab")

_MOUNT = {
    "instance_name": "agshare-client-agstudio",
    "server": "192.168.0.100",
    "export": "/opt/nfs/agshare",
    "path": "/Volumes/agshare",
}
_ENTRY_NO_COMMENT = (
    f"{_MOUNT['server']}:{_MOUNT['export']} {_MOUNT['path']} nfs "
    "rw,resvport,hard,vers=3 0 0"
)
_MARKER_LINE = f"# nintent:{_MOUNT['instance_name']}"
_LEGACY_ENTRY_WITH_TRAILING_MARKER = f"{_ENTRY_NO_COMMENT} {_MARKER_LINE}"

_PLAYBOOK_TEMPLATE = """
- hosts: localhost
  connection: local
  gather_facts: true
  vars:
    nfs_client_macos_fstab: "{fstab}"
    nfs_client_macos_master: "{master}"
    nfs_client_macos_map_legacy: "{legacy_map}"
    nfs_client_mounts: {mounts}
  tasks:
    - import_role:
        name: nfs_client
        tasks_from: macos
"""


def _mounts_yaml(active):
    if not active:
        return "[]"
    rows = []
    for m in active:
        rows.append(
            "[{instance_name: %s, nfs_client_server: %s, nfs_client_export: %s, "
            "nfs_client_path: %s}]" % (m["instance_name"], m["server"], m["export"], m["path"])
        )
    return "[" + ", ".join(r[1:-1] for r in rows) + "]"


def _have(cmd):
    return shutil.which(cmd) is not None


@unittest.skipUnless(sys.platform == "darwin", "getfsent(3) and the macOS task file are Darwin-only")
@unittest.skipUnless(_have("cc"), "no C compiler available to build the getfsent harness")
@unittest.skipUnless(_have("ansible-playbook"), "ansible-playbook not available")
class NfsClientMacosFstabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp(prefix="nfs_client_macos_fstab_test_")
        cls.prog = os.path.join(cls.work, "getfsent_prog")
        cls.dylib = os.path.join(cls.work, "libinterpose.dylib")
        subprocess.run(
            ["cc", os.path.join(_GETFSENT_SRC, "prog.c"), "-o", cls.prog],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["cc", "-dynamiclib", os.path.join(_GETFSENT_SRC, "interpose.c"), "-o", cls.dylib],
            check=True, capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix="nfs_client_scratch_", dir=self.work)
        self.fstab = os.path.join(self.scratch, "fstab")
        self.master = os.path.join(self.scratch, "auto_master")
        self.legacy_map = os.path.join(self.scratch, "auto_nintent")
        # The role's absent-state lineinfile task on nfs_client_macos_master
        # requires the file to exist; the legacy map is only ever removed if
        # present, so it is left absent.
        open(self.master, "w").close()
        # Stub out "automount -cv" (the role's reload handler): it reloads
        # the real host's automounter from the real /etc/auto_master and
        # /etc/fstab, which this test never touches and must not reload.
        self.bindir = os.path.join(self.scratch, "bin")
        os.mkdir(self.bindir)
        automount_stub = os.path.join(self.bindir, "automount")
        with open(automount_stub, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(automount_stub, 0o755)

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _run_playbook(self, active_mounts):
        playbook = _PLAYBOOK_TEMPLATE.format(
            fstab=self.fstab,
            master=self.master,
            legacy_map=self.legacy_map,
            mounts=_mounts_yaml(active_mounts),
        )
        playbook_path = os.path.join(self.scratch, "play.yml")
        with open(playbook_path, "w", encoding="utf-8") as fh:
            fh.write(playbook)
        env = dict(os.environ)
        env["PATH"] = self.bindir + ":" + env.get("PATH", "")
        result = subprocess.run(
            ["ansible-playbook", "-i", "localhost,", playbook_path],
            cwd=_ANSIBLE_AGDEV_DIR,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"ansible-playbook failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        return result

    def _fstab_lines(self):
        with open(self.fstab, encoding="utf-8") as fh:
            return [line.rstrip("\n") for line in fh if line.strip()]

    def _getfsent_entries(self):
        env = dict(os.environ)
        env["DYLD_INSERT_LIBRARIES"] = self.dylib
        env["FSTAB_REDIRECT_SRC"] = "/etc/fstab"
        env["FSTAB_REDIRECT_TARGET"] = self.fstab
        result = subprocess.run([self.prog], env=env, capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        entries = [l for l in lines if l.startswith("ENTRY ")]
        count = int(lines[-1].split("=", 1)[1])
        self.assertEqual(len(entries), count)
        return entries

    def test_new_placement_is_marker_line_above_comment_free_entry(self):
        self._run_playbook([_MOUNT])
        lines = self._fstab_lines()
        self.assertIn(_MARKER_LINE, lines)
        self.assertIn(_ENTRY_NO_COMMENT, lines)
        marker_at = lines.index(_MARKER_LINE)
        self.assertEqual(lines[marker_at + 1], _ENTRY_NO_COMMENT)

    def test_getfsent_parses_the_new_form(self):
        self._run_playbook([_MOUNT])
        entries = self._getfsent_entries()
        nfs_entries = [e for e in entries if _MOUNT["server"] in e]
        self.assertEqual(len(nfs_entries), 1, entries)
        self.assertIn(f"spec=[{_MOUNT['server']}:{_MOUNT['export']}]", nfs_entries[0])
        self.assertIn(f"file=[{_MOUNT['path']}]", nfs_entries[0])

    def test_getfsent_drops_the_legacy_trailing_marker_form(self):
        # Pre-seed the pre-fix form directly (what a real host still carries
        # until migrated): the stock parser silently drops it.
        with open(self.fstab, "w", encoding="utf-8") as fh:
            fh.write(_LEGACY_ENTRY_WITH_TRAILING_MARKER + "\n")
        entries = self._getfsent_entries()
        nfs_entries = [e for e in entries if _MOUNT["server"] in e]
        self.assertEqual(nfs_entries, [])

    def test_migrates_legacy_form_to_marker_above_entry(self):
        with open(self.fstab, "w", encoding="utf-8") as fh:
            fh.write(_LEGACY_ENTRY_WITH_TRAILING_MARKER + "\n")
        self._run_playbook([_MOUNT])
        lines = self._fstab_lines()
        self.assertNotIn(_LEGACY_ENTRY_WITH_TRAILING_MARKER, lines)
        self.assertIn(_MARKER_LINE, lines)
        self.assertIn(_ENTRY_NO_COMMENT, lines)
        self.assertEqual(lines[lines.index(_MARKER_LINE) + 1], _ENTRY_NO_COMMENT)
        entries = self._getfsent_entries()
        self.assertEqual(len([e for e in entries if _MOUNT["server"] in e]), 1, entries)

    def test_rerun_is_idempotent_one_marker_one_entry(self):
        self._run_playbook([_MOUNT])
        self._run_playbook([_MOUNT])
        lines = self._fstab_lines()
        self.assertEqual(lines.count(_MARKER_LINE), 1)
        self.assertEqual(lines.count(_ENTRY_NO_COMMENT), 1)

    def test_removing_the_placement_removes_both_lines(self):
        self._run_playbook([_MOUNT])
        self._run_playbook([])
        lines = self._fstab_lines()
        self.assertNotIn(_MARKER_LINE, lines)
        self.assertNotIn(_ENTRY_NO_COMMENT, lines)

    def test_unmarked_lines_are_left_alone(self):
        unrelated = "/dev/disk1s2 /Volumes/Other apfs rw 0 0"
        with open(self.fstab, "w", encoding="utf-8") as fh:
            fh.write(unrelated + "\n")
        self._run_playbook([_MOUNT])
        self._run_playbook([])  # placement removed again; unrelated line must survive
        lines = self._fstab_lines()
        self.assertIn(unrelated, lines)


if __name__ == "__main__":
    unittest.main()
