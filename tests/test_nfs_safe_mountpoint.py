"""Exercise NFS role guards with real Ansible and scratch files only."""

from __future__ import annotations

import shutil
import subprocess
import getpass
import grp
import os
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1]


def _ansible() -> str:
    binary = shutil.which("ansible-playbook")
    if not binary:
        pytest.skip("ansible-playbook is not installed")
    return binary


def _run(tmp_path: Path, tasks: list[dict], vars_: dict) -> subprocess.CompletedProcess:
    play = [{"hosts": "localhost", "connection": "local", "gather_facts": False,
             "vars": vars_, "tasks": tasks}]
    playbook = tmp_path / "play.yml"
    playbook.write_text(yaml.safe_dump(play), encoding="utf-8")
    return subprocess.run([_ansible(), "-i", "localhost,", str(playbook)],
                          capture_output=True, text=True, timeout=20)


def test_linux_role_skips_directory_task_for_nfs_mountinfo_entry(tmp_path):
    mount_path = tmp_path / "hung-share"
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(f"41 30 0:40 / {mount_path} rw - nfs4 server:/share rw\n", encoding="utf-8")
    tasks = yaml.safe_load((ROOT / "roles/nfs_client/tasks/linux.yml").read_text(encoding="utf-8"))
    selected = [task for task in tasks if task["name"] in {
        "Read Linux mount table before touching mountpoint paths",
        "Record which requested paths are already mounted as NFS",
        "Ensure each mount point exists",
    }]
    selected[0]["ansible.builtin.slurp"]["src"] = str(mountinfo)
    result = _run(tmp_path, selected, {"nfs_client_mounts": [
        {"instance_name": "share", "nfs_client_path": str(mount_path)},
    ]})
    assert result.returncode == 0, result.stdout + result.stderr
    assert not mount_path.exists(), "the role must not call file: state=directory on an existing NFS mount"
    assert "skipping" in result.stdout.lower()


def test_macos_nfs_conf_setting_preserves_other_keys_and_is_idempotent(tmp_path):
    nfs_conf = tmp_path / "nfs.conf"
    nfs_conf.write_text("# local setting\nnfs.client.mount_timeout = 25\nother.setting = yes\n", encoding="utf-8")
    tasks = yaml.safe_load((ROOT / "roles/nfs_server/tasks/macos.yml").read_text(encoding="utf-8"))
    task = next(item for item in tasks if item["name"] ==
                "Declare the macOS reserved-port policy while preserving other nfs.conf settings")
    task["ansible.builtin.lineinfile"]["path"] = str(nfs_conf)
    vars_ = {"nfs_server_mount_require_resv_port": False,
             "nfs_server_macos_config_owner": getpass.getuser(),
             "nfs_server_macos_config_group": grp.getgrgid(os.getgid()).gr_name}
    first = _run(tmp_path, [task], vars_)
    assert first.returncode == 0, first.stdout + first.stderr
    expected = "# local setting\nnfs.client.mount_timeout = 25\nother.setting = yes\nnfs.server.mount.require_resv_port = 0\n"
    assert nfs_conf.read_text(encoding="utf-8") == expected
    second = _run(tmp_path, [task], vars_)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "changed=0" in second.stdout
    assert nfs_conf.read_text(encoding="utf-8") == expected
