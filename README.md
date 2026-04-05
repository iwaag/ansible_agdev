# Ansible Project

Operational usage lives here. Initial SSH, inventory, and Vault setup is documented in `README_ADMIN.md`.
The minimal webhook server lives in `api/`. See `api/README.md`.

## Playbooks

Allow the default user to suspend a host without a sudo password:

```bash
ansible-playbook playbooks/configure_suspend_sudo.yml --limit <host_or_group>
```

Suspend Linux hosts immediately:

```bash
ansible-playbook playbooks/suspend_hosts.yml --limit <host_or_group>
```

Allow the default user to put a macOS host to sleep without a sudo password:

```bash
ansible-playbook playbooks/configure_suspend_mac.yml --limit <host_or_group>
```

Put macOS hosts to sleep immediately:

```bash
ansible-playbook playbooks/sleep_macos_hosts.yml --limit <host_or_group>
```

Enable Wake-on-LAN on Linux targets:

```bash
ansible-playbook playbooks/enable_wake_on_lan.yml --limit <host_or_group>
```

Send a Wake-on-LAN magic packet from the control node:

```bash
ansible-playbook playbooks/wake_hosts.yml --limit <host_or_group>
```

## Notes

- `suspend_hosts.yml` expects the Linux sudoers rule from `configure_suspend_sudo.yml` to already be installed.
- `configure_suspend_mac.yml` is intended for the `mac_llm` and `mac_infra` groups and allows `/usr/bin/pmset sleepnow`.
- `sleep_macos_hosts.yml` expects the macOS sudoers rule from `configure_suspend_mac.yml` to already be installed.
- `enable_wake_on_lan.yml` is intended for the `ubuntu_knode` and `ubuntu_cuda` groups.
- `wake_hosts.yml` uses each selected host's `mac_address` and sends to `255.255.255.255:9`.
- The default inventory is configured in `ansible.cfg`.
