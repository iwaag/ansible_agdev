# Ansible Project

Operational usage lives here. Initial SSH, inventory, and Vault setup is documented in `README_ADMIN.md`.
The minimal webhook server lives in `api/`. See `api/README.md`.

## Playbooks

Render the nintent mDNS bootstrap inventory from Nautobot desired state:

```bash
NAUTOBOT_TOKEN=your-nautobot-api-token \
uv run --project ../nctl nctl render hosts-intent \
  --config ../nctl.toml --out inventories/generated
```

The generated bootstrap inventory is written to:

```text
inventories/generated/hosts_intent.yml
```

This file is intentionally generated and ignored by Git. The collection stage
selects it explicitly with `-i inventories/generated/hosts_intent.yml`. The
`ansible.cfg` default inventory points at the generated production inventory
`inventories/generated/production.yml`, which operational playbooks use. Run
`make pipeline` (nctl bootstrap render, nodeutils collect/ingest, nctl production render)
before using operational commands on a fresh checkout.

Allow the default user to suspend a host without a sudo password:

```bash
ansible-playbook playbooks/power/configure_suspend_sudo.yml --limit <host_or_group>
```

Suspend Linux hosts immediately:

```bash
ansible-playbook playbooks/power/suspend_hosts.yml --limit <host_or_group>
```

Allow the default user to put a macOS host to sleep without a sudo password:

```bash
ansible-playbook playbooks/power/configure_suspend_mac.yml --limit <host_or_group>
```

Put macOS hosts to sleep immediately:

```bash
ansible-playbook playbooks/power/sleep_macos_hosts.yml --limit <host_or_group>
```

Enable Wake-on-LAN on Linux targets:

```bash
ansible-playbook playbooks/power/enable_wake_on_lan.yml --limit <host_or_group>
```

Apply the Linux worker baseline setup:

```bash
ansible-playbook playbooks/bootstrap/linux_initial_setup.yml --limit <host_or_group>
```

Install Prometheus from the upstream release archive:

```bash
ansible-playbook playbooks/monitoring/setup_prometheus.yml --limit <host_or_group>
```

Install node exporter on selected hosts and refresh Prometheus targets:

```bash
ansible-playbook playbooks/monitoring/setup_node_exporter.yml --limit <host_or_group_or_group_union>
```

Install Grafana and provision the Prometheus data source:

```bash
ansible-playbook playbooks/monitoring/setup_grafana.yml --limit <host_or_group>
```

Install and configure a Nomad server on Ubuntu:

```bash
ansible-playbook playbooks/nomad/setup_nomad_server.yml --limit <host_or_group>
```

Install and configure a Nomad client on Ubuntu:

```bash
ansible-playbook playbooks/nomad/setup_nomad_client.yml --limit <host_or_group>
```

Install and configure a Nomad client on macOS (`raw_exec` only):

```bash
ansible-playbook playbooks/nomad/setup_nomad_client_macos.yml --limit <host_or_group>
```

Install uv on Linux and macOS hosts:

```bash
ansible-playbook playbooks/bootstrap/setup_uv.yml --limit <host_or_group>
```

Install Git on Linux hosts:

```bash
ansible-playbook playbooks/bootstrap/setup_git.yml --limit <host_or_group>
```

Install and configure dnsmasq on Linux hosts:

```bash
ansible-playbook playbooks/bootstrap/setup_dnsmasq.yml --limit <host_or_group>
```

Deploy a pre-rendered dnsmasq configuration to dnsmasq servers:

```bash
ansible-playbook playbooks/dnsmasq/deploy_dnsmasq_records.yml \
  -e dnsmasq_records_src=/absolute/path/to/dnsmasq-records.conf
```

Clone nodeutils on each selected host and write a local inventory report:

```bash
ansible-playbook playbooks/nautobot/run_nodeutils_collect.yml --limit <host_or_group>
```

Collection, report-cache installation, Nautobot Job triggering/polling, and verification are
sequenced by `nctl`, not Ansible. From the parent `pj-clusterintent` checkout:

```bash
NAUTOBOT_TOKEN=your-nautobot-api-token \
uv run --project nctl nctl reconcile --config nctl.toml --yes
```

`ansible_agdev/Makefile`'s `pipeline` target runs the equivalent command. Run
`run_nodeutils_collect.yml` directly (previous section) only for diagnostics; it writes the local
report but does not submit anything to Nautobot.

Clone a Git repository and run a one-line command inside it:

```bash
ansible-playbook playbooks/bootstrap/clone_git_and_run.yml \
  -e target_hosts=<host_or_group> \
  -e git_clone_run_repo=https://github.com/example/repo.git \
  -e 'git_clone_run_command=./run.sh'
```

Schedule a macOS host to wake shortly:

```bash
ansible-playbook playbooks/power/wake_hosts.yml --limit <host_or_group>
```

Send a Wake-on-LAN magic packet from the control node to Linux targets:

```bash
ansible-playbook playbooks/power/wake_linux_hosts.yml --limit <host_or_group>
```

Generate Home Assistant `command_line` power switches from inventory:

```bash
ansible-playbook playbooks/power/generate_home_assistant_power_switches.yml \
  -e home_assistant_webhook_base_url=http://YOUR_API_HOST:8000 \
  -e home_assistant_webhook_token=YOUR_WEBHOOK_TOKEN
```

Generate and deploy the Home Assistant package to `haos_server`:

```bash
ansible-playbook playbooks/power/deploy_home_assistant_power_switches.yml \
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
- `configure_suspend_mac.yml` targets `macos:&power_managed` and allows `/usr/bin/pmset sleepnow` and `/usr/bin/pmset schedule wake *`.
- `sleep_macos_hosts.yml` expects the macOS sudoers rule from `configure_suspend_mac.yml` to already be installed.
- `enable_wake_on_lan.yml` targets `linux:&power_managed`.
- `linux_initial_setup.yml` targets `linux:&power_managed` and uses the generated `is_laptop` host variable to apply the laptop-specific power profile.
- `setup_prometheus.yml` installs Prometheus from GitHub releases, runs it as `default_user`, and ignores the LXC provisioning step.
- `setup_node_exporter.yml` installs the Debian/Ubuntu `prometheus-node-exporter` package on `prometheus_node_exporter_targets` and refreshes Prometheus scrape targets from inventory groups.
- `setup_grafana.yml` installs Grafana from the official apt repository on `grafana_server` and provisions a Prometheus data source that points at the first host in `prometheus_server`.
- `setup_nomad_server.yml` installs Nomad from the official HashiCorp apt repository on `nomad_server`, configures a single-node server, and keeps `advertise` and `server_join.retry_join` configurable for later multi-node expansion.
- `setup_nomad_client.yml` installs Nomad from the official HashiCorp apt repository on `nomad_client`, points clients at the inventory's `nomad_server` hosts by default, and exposes `node_class`, `meta`, and static `host_volume` settings through variables.
- `setup_nomad_client_macos.yml` installs Nomad via Homebrew on `nomad_client:&macos`, runs it as a system `launchd` daemon, and enables only the `raw_exec` task driver by default.
- `setup_nomad_client_macos.yml` expects Homebrew to already be installed on the target Mac and uses the host's `network_interface` inventory value, typically `en0`.
- `setup_uv.yml` installs the pinned uv release from GitHub release archives into `/usr/local/bin` on Linux hosts. On Apple Silicon macOS hosts, it installs uv with Homebrew from `/opt/homebrew/bin/brew`.
- `setup_git.yml` installs the distro Git package on Linux hosts. Override `git_client_packages` to install related packages such as `git-lfs`.
- `setup_dnsmasq.yml` installs the distro `dnsmasq` package on `dnsmasq_server` hosts and writes `/etc/dnsmasq.d/ansible.conf`. Override `dnsmasq_listen_addresses`, `dnsmasq_interfaces`, `dnsmasq_upstream_servers`, and `dnsmasq_local_domain` to fit the network. Direct record and DHCP list variables remain available for non-nctl use, but the normal source of truth for DNS records, DHCP reservations, and DHCP ranges is the rendered artifact deployed by `playbooks/dnsmasq/deploy_dnsmasq_records.yml`. When `dnsmasq_port` is `53`, the role disables the `systemd-resolved` DNS stub listener if `systemd-resolved.service` exists, so dnsmasq can bind the DNS port. It does not rewrite `/etc/resolv.conf`; check the target host's resolver configuration after changing local DNS ownership.
- `playbooks/dnsmasq/deploy_dnsmasq_records.yml` is deploy-only: it requires `dnsmasq_records_src` to be an absolute path to a pre-rendered configuration on the controller, validates the file with `dnsmasq --test`, and installs it on `dnsmasq_server` hosts as `/etc/dnsmasq.d/nintent-records.conf`. The file can contain DNS records, DHCP reservations, and `dhcp-range=` lines; keep `/etc/dnsmasq.d/ansible.conf` for dnsmasq service settings. Rendering and Nautobot reads belong to `nctl`, so this playbook requires no Nautobot URL, token, Job polling, or File Proxy access.
- `nctl render hosts-intent` reads desired nodes through GraphQL, validates a staged schema `3.0` inventory with `ansible-inventory --list`, and atomically replaces `inventories/generated/hosts_intent.yml`, preserving the previous file if validation fails. This generated inventory is the mDNS-only bootstrap inventory for name-reserved nodes; it carries no service groups or desired `host_os`, and is not the detailed canonical inventory. `make bootstrap-inventory` invokes this command directly; no Nautobot export Job or File Proxy is involved.
- `nctl render production` reads `vars/deployment_profiles.yml` directly, joins it with desired and actual state, validates a staged schema `1.0` inventory with `ansible-inventory --list`, and atomically installs `inventories/generated/production.yml` plus its generation-addressed report. No Nautobot export/sync Job, projection, canonical-JSON transport, or File Proxy is involved. `make production-inventory` invokes this command directly for diagnostics/manual recovery; the normal path is `make pipeline` (`nctl reconcile --yes`), which regenerates production inventory itself on every apply round.
- `run_nodeutils_collect.yml` targets `ssh_hosts` by default, installs Git on Linux hosts, installs uv on Linux/macOS, clones `nodeutils_repo` into `nodeutils_checkout_dir` (`/opt/nodeutils` by default), forcibly refreshes that checkout, runs `uv sync --frozen`, and writes `nodeutils_output_path` (`/var/lib/nodeutils/inventory.json` by default). Override `nodeutils_repo`, `nodeutils_version`, `nodeutils_checkout_dir`, or `nodeutils_collect_args` when needed. `nctl reconcile` invokes this playbook itself against a private operation-scoped inventory; run it directly only for diagnostics, since doing so does not submit anything to Nautobot.
- Collection sequencing, the Nautobot report cache, `Ingest Nodeutils Inventory` Job triggering/polling, and post-ingest verification all live in `nctl reconcile` (`nctl_core.observation`), not in an Ansible playbook. Ansible has no task that calls `/api/extras/jobs/` or reads a Nautobot token; `vars/nautobot.yml` and the `nautobot_url`/`nautobot_token` vault variables described in `README_ADMIN.md` are unused by any playbook in this repository and are kept only as reference for `NAUTOBOT_URL`/`NAUTOBOT_TOKEN`, which `nctl` itself reads from the environment.
- `clone_git_and_run.yml` clones or updates `git_clone_run_repo` into `git_clone_run_dest` (`/tmp/ansible-git-clone-run` by default) and runs `git_clone_run_command` from that directory. Override `git_clone_run_version` to pin a branch, tag, or commit.
- `wake_hosts.yml` targets `macos:&power_managed` and schedules `pmset` wake two seconds ahead on the selected host.
- `wake_linux_hosts.yml` uses each selected Linux host's `mac_address` and sends to `255.255.255.255:9`.
- `generate_home_assistant_power_switches.yml` renders `generated/home_assistant/ansible_power_switches.yaml` for `power_managed` hosts, split into Linux and macOS by the `linux`/`macos` selector groups. State is derived from pinging `local_ip`, `local_dns_hostname`, or `mdns_hostname`, Linux power on uses `POST /webhook/wake/linux`, macOS power on uses `POST /webhook/wake/macos`, Linux power off uses `POST /webhook/suspend/linux`, and macOS power off uses `POST /webhook/sleep/macos`.
- `deploy_home_assistant_power_switches.yml` renders the same package locally and copies it to `/config/packages/ansible_power_switches.yaml` on hosts in `haos_server`.
- The default inventory is configured in `ansible.cfg` and points at the generated production inventory `inventories/generated/production.yml`. The bootstrap/collection stage selects `inventories/generated/hosts_intent.yml` explicitly, so production and bootstrap never share an ambiguous default.
