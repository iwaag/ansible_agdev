"""nfs_server role: real-ansible proof that each OS's guard runs before any mutation.

The backing-directory task must not run ahead of the OS-specific refusal
(unprivileged Linux container / non-root macOS) that is supposed to gate it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROLE = Path(__file__).parents[1] / "roles/nfs_server"


def _skip_unless_ansible_playbook() -> str:
    path = shutil.which("ansible-playbook")
    if path is None:
        pytest.skip("ansible-playbook is not installed")
    return path


def _export(backing_path: Path) -> list[dict[str, object]]:
    return [
        {
            "instance_name": "example",
            "nfs_server_path": str(backing_path),
            "nfs_server_clients": ["127.0.0.1"],
            "nfs_server_anon_uid": 1000,
            "nfs_server_anon_gid": 1000,
        }
    ]


def _prepare_role_tasks(tmp_path: Path) -> Path:
    """Copy the role's tasks, substituting the Linux uid_map read so it never
    depends on a real /proc (this test machine may not be Linux at all)."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for name in ("main.yml", "linux.yml", "macos.yml"):
        content = yaml.safe_load((ROLE / "tasks" / name).read_text())
        if name == "linux.yml":
            for task in content:
                slurp = task.get("ansible.builtin.slurp")
                if slurp and slurp.get("src") == "/proc/self/uid_map":
                    task["fixture_slurp"] = task.pop("ansible.builtin.slurp")
        (tasks_dir / name).write_text(yaml.safe_dump(content))
    library = tmp_path / "library"
    library.mkdir()
    (library / "fixture_slurp.py").write_text(
        "from ansible.module_utils.basic import AnsibleModule\n"
        "import base64\n"
        "m = AnsibleModule(argument_spec=dict(src=dict(required=True)))\n"
        # root mapped to an unprivileged uid: the Linux guard must refuse.
        "m.exit_json(content=base64.b64encode(b'0 1000 1\\n').decode(), encoding='base64',\n"
        "             source=m.params['src'])\n"
    )
    return tasks_dir / "main.yml"


def _run_role(tmp_path: Path, ansible_facts: dict[str, str], backing_path: Path, env: dict[str, str] | None = None):
    playbook_binary = _skip_unless_ansible_playbook()
    main_tasks = _prepare_role_tasks(tmp_path)
    play: dict[str, object] = {
        "hosts": "localhost",
        "connection": "local",
        "gather_facts": False,
        "vars": {
            "ansible_facts": ansible_facts,
            "nfs_server_exports": _export(backing_path),
        },
        "tasks": [{"name": "run the role's tasks", "ansible.builtin.include_tasks": str(main_tasks)}],
    }
    if env:
        play["environment"] = env
    fixture = tmp_path / "play.yml"
    fixture.write_text(yaml.safe_dump([play]))
    return subprocess.run(
        [playbook_binary, "-i", "localhost,", str(fixture)],
        text=True,
        capture_output=True,
    )


def test_linux_unprivileged_container_refusal_runs_before_backing_directory_is_created(tmp_path):
    backing = tmp_path / "target" / "share"
    result = _run_role(tmp_path, {"system": "Linux", "os_family": "Debian"}, backing)
    assert result.returncode != 0, result.stdout
    assert "unprivileged uid" in result.stdout
    assert not backing.exists(), "the backing directory must not exist once the Linux guard has refused"


def test_macos_root_refusal_runs_before_backing_directory_is_created(tmp_path):
    backing = tmp_path / "target" / "share"
    fake_id = tmp_path / "id"
    fake_id.write_text("#!/bin/sh\necho 501\n")
    fake_id.chmod(0o700)
    result = _run_role(
        tmp_path,
        {"system": "Darwin"},
        backing,
        env={"PATH": f"{tmp_path}:{os.environ['PATH']}"},
    )
    assert result.returncode != 0, result.stdout
    assert "did not escalate to root" in result.stdout
    assert not backing.exists(), "the backing directory must not exist once the macOS guard has refused"
