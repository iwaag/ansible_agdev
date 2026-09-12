"""Run retirement's real task ordering against a disposable systemd boundary."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


@pytest.mark.parametrize("scenario", ["stopped", "absent", "stop_error", "bus_error", "lingering"])
def test_retirement_checks_stop_and_process_state(tmp_path, scenario):
    source = Path(__file__).parents[1] / "playbooks/agent/retire_agag_agent.yml"
    play = yaml.safe_load(source.read_text())[0]
    play["gather_facts"] = False
    play["connection"] = "local"
    play["environment"] = {"PATH": f"{tmp_path}:{os.environ['PATH']}"}
    play["vars"].update({
        "ansible_facts": {"env": {"HOME": str(tmp_path)}},
        "ansible_python_interpreter": sys.executable,
        "remove_checkout": True,
    })
    # Only the systemd module boundary is substituted; conditions, commands,
    # assertions, and filesystem operations run through real Ansible.
    for task in play["tasks"]:
        if "ansible.builtin.systemd_service" in task:
            task["fixture_systemd"] = task.pop("ansible.builtin.systemd_service")
    fixture = tmp_path / "retire.yml"
    fixture.write_text(yaml.safe_dump([play]))
    library = tmp_path / "library"
    library.mkdir()
    (library / "fixture_systemd.py").write_text(
        "from ansible.module_utils.basic import AnsibleModule\n"
        "m = AnsibleModule(argument_spec=dict(name=dict(), state=dict(), "
        "enabled=dict(type='bool'), scope=dict(), daemon_reload=dict(type='bool')))\n"
        f"scenario = {scenario!r}\n"
        "if m.params.get('state') == 'stopped' and scenario == 'stop_error':\n"
        "    m.fail_json(msg='fixture stop failed')\n"
        "m.exit_json(changed=True)\n"
    )
    systemctl = tmp_path / "systemctl"
    systemctl.write_text(
        f"#!{sys.executable}\nimport sys\nscenario = {scenario!r}\n"
        "if scenario == 'bus_error':\n"
        "    print('Failed to connect to bus', file=sys.stderr); sys.exit(1)\n"
        "if '--value' in sys.argv:\n"
        "    print('not-found' if scenario == 'absent' else 'loaded')\n"
        "else:\n"
        "    print('LoadState=not-found')\n"
        "    print('ActiveState=active' if scenario == 'lingering' else 'ActiveState=inactive')\n"
        "    print('MainPID=123' if scenario == 'lingering' else 'MainPID=0')\n"
        "sys.exit(4 if scenario == 'absent' else 0)\n"
    )
    systemctl.chmod(0o700)
    unit = tmp_path / ".config/systemd/user/agag-demo.service"
    unit.parent.mkdir(parents=True)
    if scenario != "absent":
        unit.write_text("fixture-owned unit")
    checkout = tmp_path / "demo"
    checkout.mkdir()
    (checkout / "record").write_text("fixture-owned record")
    result = subprocess.run(
        ["ansible-playbook", "-i", "localhost,", str(fixture), "-e",
         json.dumps({"target": "localhost", "agag_agent_agent": "demo"})],
        cwd=tmp_path, text=True, capture_output=True,
        env={**os.environ, "ANSIBLE_LIBRARY": str(library)},
    )
    if scenario in ("stopped", "absent"):
        assert result.returncode == 0, result.stdout + result.stderr
        assert not unit.exists()
        assert not checkout.exists()
    else:
        assert result.returncode != 0, result.stdout
        assert checkout.exists(), "failed retirement must not delete the checkout"
        if scenario != "lingering":
            assert unit.exists(), "failed inspection/stop must not remove the unit"
        expected = {"stop_error": "fixture stop failed", "bus_error": "Failed to connect to bus",
                    "lingering": "Listener retirement did not stop the unit"}[scenario]
        assert expected in result.stdout + result.stderr
