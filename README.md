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

Apply the Linux worker baseline setup:

```bash
ansible-playbook playbooks/linux_initial_setup.yml --limit <host_or_group>
```

Install Prometheus from the upstream release archive:

```bash
ansible-playbook playbooks/setup_prometheus.yml --limit <host_or_group>
```

Install node exporter on selected hosts and refresh Prometheus targets:

```bash
ansible-playbook playbooks/setup_node_exporter.yml --limit <host_or_group_or_group_union>
```

Install Grafana and provision the Prometheus data source:

```bash
ansible-playbook playbooks/setup_grafana.yml --limit <host_or_group>
```

Send a Wake-on-LAN magic packet from the control node:

```bash
ansible-playbook playbooks/wake_hosts.yml --limit <host_or_group>
```

Generate Home Assistant `command_line` power switches from inventory:

```bash
ansible-playbook playbooks/generate_home_assistant_power_switches.yml \
  -e home_assistant_webhook_base_url=http://YOUR_API_HOST:8000 \
  -e home_assistant_webhook_token=YOUR_WEBHOOK_TOKEN
```

Generate and deploy the Home Assistant package to `haos_server`:

```bash
ansible-playbook playbooks/deploy_home_assistant_power_switches.yml \
  -e home_assistant_webhook_base_url=http://YOUR_API_HOST:8000 \
  -e home_assistant_webhook_token=YOUR_WEBHOOK_TOKEN
```

## Home Assistant

To load the deployed package from `/config/packages/ansible_power_switches.yaml`, enable packages in Home Assistant's `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

If `homeassistant:` already exists, add only the `packages:` line under it.

After deploying or updating the package:

1. In Developer Tools, run the `command_line.reload` action to reload `command_line` entities.
2. If this is the first time you enabled packages or the first time Home Assistant sees this YAML, restart Home Assistant once.

The generated file defines `command_line` switches, so the entities should appear after the reload or restart.

## Notes

- `suspend_hosts.yml` expects the Linux sudoers rule from `configure_suspend_sudo.yml` to already be installed.
- `configure_suspend_mac.yml` is intended for the `mac_llm` and `mac_infra` groups and allows `/usr/bin/pmset sleepnow`.
- `sleep_macos_hosts.yml` expects the macOS sudoers rule from `configure_suspend_mac.yml` to already be installed.
- `enable_wake_on_lan.yml` is intended for the `ubuntu_knode` and `ubuntu_cuda` groups.
- `linux_initial_setup.yml` is intended for the `ubuntu_knode` and `ubuntu_cuda` groups and uses `is_laptop: true` on hosts that should receive the laptop-specific power profile.
- `setup_prometheus.yml` installs Prometheus from GitHub releases, runs it as `default_user`, and ignores the LXC provisioning step.
- `setup_node_exporter.yml` installs the Debian/Ubuntu `prometheus-node-exporter` package on `prometheus_node_exporter_targets` and refreshes Prometheus scrape targets from inventory groups.
- `setup_grafana.yml` installs Grafana from the official apt repository on `grafana_server` and provisions a Prometheus data source that points at the first host in `prometheus_server`.
- `wake_hosts.yml` uses each selected host's `mac_address` and sends to `255.255.255.255:9`.
- `generate_home_assistant_power_switches.yml` renders `generated/home_assistant/ansible_power_switches.yaml` for hosts in `ubuntu_knode`, `ubuntu_cuda`, `mac_llm`, and `mac_infra`. State is derived from `local_ip` ping, power on uses `POST /webhook/wake`, Linux power off uses `POST /webhook/suspend/linux`, and macOS power off uses `POST /webhook/sleep/macos`.
- `deploy_home_assistant_power_switches.yml` renders the same package locally and copies it to `/config/packages/ansible_power_switches.yaml` on hosts in `haos_server`.
- The default inventory is configured in `ansible.cfg`.
