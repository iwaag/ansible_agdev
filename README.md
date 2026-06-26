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

Install and configure a Nomad server on Ubuntu:

```bash
ansible-playbook playbooks/setup_nomad_server.yml --limit <host_or_group>
```

Install and configure a Nomad client on Ubuntu:

```bash
ansible-playbook playbooks/setup_nomad_client.yml --limit <host_or_group>
```

Install and configure a Nomad client on macOS (`raw_exec` only):

```bash
ansible-playbook playbooks/setup_nomad_client_macos.yml --limit <host_or_group>
```

Install uv on Linux and macOS hosts:

```bash
ansible-playbook playbooks/setup_uv.yml --limit <host_or_group>
```

Install Git on Linux hosts:

```bash
ansible-playbook playbooks/setup_git.yml --limit <host_or_group>
```

Install and configure dnsmasq on Linux hosts:

```bash
ansible-playbook playbooks/setup_dnsmasq.yml --limit <host_or_group>
```

Export nintent dnsmasq records and DHCP ranges from Nautobot and deploy them to dnsmasq servers:

```bash
NAUTOBOT_URL=https://nautobot.example.local \
NAUTOBOT_TOKEN=your-nautobot-api-token \
ansible-playbook playbooks/deploy_nintent_dnsmasq_records.yml
```

Clone nodeutils on each selected host and write a local inventory report:

```bash
ansible-playbook playbooks/run_nodeutils_collect.yml --limit <host_or_group>
```

Collect nodeutils reports, copy them to the Nautobot server, and run the Nautobot ingest Job:

```bash
NAUTOBOT_URL=https://nautobot.example.local \
NAUTOBOT_TOKEN=your-nautobot-api-token \
ansible-playbook playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

Install Nautobot Ansible dynamic inventory support on the control node:

```bash
ansible-playbook playbooks/setup_nautobot_ansible_inventory.yml
```

Pin or upgrade the collection if needed:

```bash
ansible-playbook playbooks/setup_nautobot_ansible_inventory.yml \
  -e nautobot_ansible_collection_version='==5.16.2'

ansible-playbook playbooks/setup_nautobot_ansible_inventory.yml \
  -e nautobot_ansible_collection_upgrade=true
```

Clone a Git repository and run a one-line command inside it:

```bash
ansible-playbook playbooks/clone_git_and_run.yml \
  -e target_hosts=<host_or_group> \
  -e git_clone_run_repo=https://github.com/example/repo.git \
  -e 'git_clone_run_command=./run.sh'
```

Schedule a macOS host to wake shortly:

```bash
ansible-playbook playbooks/wake_hosts.yml --limit <host_or_group>
```

Send a Wake-on-LAN magic packet from the control node to Linux targets:

```bash
ansible-playbook playbooks/wake_linux_hosts.yml --limit <host_or_group>
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
- `configure_suspend_mac.yml` is intended for the `mac_llm` and `mac_infra` groups and allows `/usr/bin/pmset sleepnow` and `/usr/bin/pmset schedule wake *`.
- `sleep_macos_hosts.yml` expects the macOS sudoers rule from `configure_suspend_mac.yml` to already be installed.
- `enable_wake_on_lan.yml` is intended for the `ubuntu_knode` and `ubuntu_cuda` groups.
- `linux_initial_setup.yml` is intended for the `ubuntu_knode` and `ubuntu_cuda` groups and uses `is_laptop: true` on hosts that should receive the laptop-specific power profile.
- `setup_prometheus.yml` installs Prometheus from GitHub releases, runs it as `default_user`, and ignores the LXC provisioning step.
- `setup_node_exporter.yml` installs the Debian/Ubuntu `prometheus-node-exporter` package on `prometheus_node_exporter_targets` and refreshes Prometheus scrape targets from inventory groups.
- `setup_grafana.yml` installs Grafana from the official apt repository on `grafana_server` and provisions a Prometheus data source that points at the first host in `prometheus_server`.
- `setup_nomad_server.yml` installs Nomad from the official HashiCorp apt repository on `nomad_server`, configures a single-node server, and keeps `advertise` and `server_join.retry_join` configurable for later multi-node expansion.
- `setup_nomad_client.yml` installs Nomad from the official HashiCorp apt repository on `nomad_client`, points clients at the inventory's `nomad_server` hosts by default, and exposes `node_class`, `meta`, and static `host_volume` settings through variables.
- `setup_nomad_client_macos.yml` installs Nomad via Homebrew on `nomad_client:&macos`, runs it as a system `launchd` daemon, and enables only the `raw_exec` task driver by default.
- `setup_nomad_client_macos.yml` expects Homebrew to already be installed on the target Mac and uses the host's `network_interface` inventory value, typically `en0`.
- `setup_uv.yml` installs the pinned uv release from GitHub release archives into `/usr/local/bin` on Linux hosts. On Apple Silicon macOS hosts, it installs uv with Homebrew from `/opt/homebrew/bin/brew`.
- `setup_git.yml` installs the distro Git package on Linux hosts. Override `git_client_packages` to install related packages such as `git-lfs`.
- `setup_dnsmasq.yml` installs the distro `dnsmasq` package on `dnsmasq_server` hosts and writes `/etc/dnsmasq.d/ansible.conf`. Override `dnsmasq_listen_addresses`, `dnsmasq_interfaces`, `dnsmasq_upstream_servers`, and `dnsmasq_local_domain` to fit the network. Direct record and DHCP list variables remain available for non-nintent use, but once `DesiredIPRange` export is enabled the normal source of truth for DNS records, DHCP reservations, and DHCP ranges is the nintent artifact deployed by `deploy_nintent_dnsmasq_records.yml`. When `dnsmasq_port` is `53`, the role disables the `systemd-resolved` DNS stub listener if `systemd-resolved.service` exists, so dnsmasq can bind the DNS port. It does not rewrite `/etc/resolv.conf`; check the target host's resolver configuration after changing local DNS ownership.
- `deploy_nintent_dnsmasq_records.yml` runs nintent's Nautobot `Export dnsmasq Records` Job, downloads the generated schema `3.0` `dnsmasq-records.conf` JobResult file, and deploys it to `dnsmasq_server` hosts as `/etc/dnsmasq.d/nintent-records.conf`. The file can contain DNS records, DHCP reservations, and `dhcp-range=` lines from `DesiredIPRange`; keep `/etc/dnsmasq.d/ansible.conf` for dnsmasq service settings. Nautobot connection defaults are centralized in `vars/nautobot.yml`; set `nautobot_url` and `nautobot_token` through extra vars, `NAUTOBOT_URL`/`NAUTOBOT_TOKEN`, or Vault. The Nautobot token must be able to run the Job and view/download File Proxy objects.
- `run_nodeutils_collect.yml` installs Git on Linux hosts, installs uv on Linux/macOS, clones `nodeutils_repo` into `nodeutils_checkout_dir` (`/opt/nodeutils` by default), runs `uv sync --frozen`, and writes `nodeutils_output_path` (`/var/lib/nodeutils/inventory.json` by default). Override `nodeutils_repo`, `nodeutils_version`, `nodeutils_checkout_dir`, or `nodeutils_collect_args` when needed.
- `collect_nodeutils_and_ingest_nautobot.yml` runs `run_nodeutils_collect.yml`, fetches reports to `nodeutils_report_local_dir` (`/tmp/ansible-nodeutils-reports` by default), copies them to `nautobot_nodeutils_report_dir` (`/var/tmp/nodeutils-reports` by default) on `nautobot_server_group` (`nautobot_server` by default), and runs the Nautobot `Ingest Nodeutils Inventory` Job by API. It defaults to `nautobot_ingest_dry_run=true`; set `-e nautobot_ingest_dry_run=false` to commit changes after reviewing Job logs. Nautobot connection defaults are centralized in `vars/nautobot.yml`; set `nautobot_url` and `nautobot_token` through extra vars, `NAUTOBOT_URL`/`NAUTOBOT_TOKEN`, or Vault.
- `setup_nautobot_ansible_inventory.yml` installs the `networktocode.nautobot` collection and `pynautobot>=2.0.0` on the Ansible control node for the Nautobot dynamic inventory plugin. The collection is pinned to `==5.16.2` by default because `networktocode.nautobot` 6.x requires ansible-core 2.18 or newer. Override `nautobot_ansible_collection_version` to pin a different collection version, `nautobot_ansible_collection_upgrade=true` to upgrade, or `nautobot_ansible_pip_extra_args` if the control node's Python packaging policy requires different pip flags.
- `clone_git_and_run.yml` clones or updates `git_clone_run_repo` into `git_clone_run_dest` (`/tmp/ansible-git-clone-run` by default) and runs `git_clone_run_command` from that directory. Override `git_clone_run_version` to pin a branch, tag, or commit.
- `wake_hosts.yml` is intended for the `mac_llm` and `mac_infra` groups and schedules `pmset` wake two seconds ahead on the selected host.
- `wake_linux_hosts.yml` uses each selected Linux host's `mac_address` and sends to `255.255.255.255:9`.
- `generate_home_assistant_power_switches.yml` renders `generated/home_assistant/ansible_power_switches.yaml` for hosts in `ubuntu_knode`, `ubuntu_cuda`, `mac_llm`, and `mac_infra`. State is derived from pinging `local_ip`, `local_dns_hostname`, or `mdns_hostname`, Linux power on uses `POST /webhook/wake/linux`, macOS power on uses `POST /webhook/wake/macos`, Linux power off uses `POST /webhook/suspend/linux`, and macOS power off uses `POST /webhook/sleep/macos`.
- `deploy_home_assistant_power_switches.yml` renders the same package locally and copies it to `/config/packages/ansible_power_switches.yaml` on hosts in `haos_server`.
- The default inventory is configured in `ansible.cfg`.
