# Developer Notes

## Production inventory contract

The service-placement cutover contract is documented in
`docs/production_inventory_contract.md`. The Ansible-owned mapping is
`vars/deployment_profiles.yml`; it must contain no secrets.

Verify Ansible's canonical JSON bytes and the current map before changing a
profile:

```bash
ansible-playbook playbooks/verify_deployment_profiles_contract.yml
```

Profile changes are breaking contract changes during the current cutover. Keep
the nintent contract fixtures and the audited role/default table in sync.

After editing `vars/deployment_profiles.yml`, push the map into nintent's
read-only projection so the Quick Service Placement UI sees the new profiles and
config schemas. It uses the same canonical JSON + digest contract as the export:

```bash
ansible-playbook playbooks/sync_nintent_deployment_profiles.yml
```

Ansible stays the authoritative owner; the projection is advisory, and production
export still revalidates the map at export time.

## Adding A Prometheus Exporter

This repository is set up so exporter installation and Prometheus target registration stay loosely coupled.

Use this pattern when adding a new exporter:

1. Create a dedicated role under `roles/` for the exporter installation.
2. Create a dedicated playbook under `playbooks/` that applies that role to a target inventory group.
3. Add a target group in the inventory for hosts that should run that exporter.
4. Register the exporter in the Prometheus role by adding a new item to `prometheus_inventory_jobs`.

Current example:

- `roles/prometheus_node_exporter/` installs `prometheus-node-exporter`
- `playbooks/setup_node_exporter.yml` applies that role
- `prometheus_node_exporter_targets` defines which hosts expose port `9100`
- `roles/prometheus_server/defaults/main.yml` maps that group to the `node_exporter` scrape job

## Why This Structure

This keeps each concern separate:

- exporter installation logic lives in its own role
- target selection lives in inventory
- Prometheus scrape registration lives in one place

This makes it easy to add more exporters later without rewriting the Prometheus playbook.

## Example For A New Exporter

If you want to add `process_exporter`, follow the same structure:

1. Add `roles/prometheus_process_exporter/`
2. Add `playbooks/setup_process_exporter.yml`
3. Add an inventory group such as `prometheus_process_exporter_targets`
4. Add a Prometheus inventory job like this:

```yaml
prometheus_inventory_jobs:
  - job_name: node_exporter
    groups:
      - prometheus_node_exporter_targets
    port: 9100
    hostvar: ansible_host

  - job_name: process_exporter
    groups:
      - prometheus_process_exporter_targets
    port: 9256
    hostvar: ansible_host
```

## Implementation Rules

- Keep one exporter per role.
- Keep one setup playbook per exporter.
- Prefer inventory groups over hard-coded host lists.
- Prefer extending `prometheus_inventory_jobs` over editing the Prometheus template for each new exporter.
- Use `ansible_host` as the default scrape address unless you have a clear reason to use another host variable.
- If an exporter needs custom labels, metrics path, or scheme, add them in the corresponding `prometheus_inventory_jobs` entry.

## Operational Notes

- `playbooks/setup_prometheus.yml` installs and configures the Prometheus server.
- `playbooks/setup_node_exporter.yml` installs node exporter and then refreshes Prometheus configuration on the Prometheus server.
- When using `--limit`, make sure the Prometheus server is still included if you expect scrape targets to be refreshed.

## nintent dnsmasq Consumption

`playbooks/deploy_nintent_dnsmasq_records.yml` consumes nintent dnsmasq export schema `3.0`.
The deployed `/etc/dnsmasq.d/nintent-records.conf` is intentionally a single generated
artifact that can contain DNS records, DHCP reservations, and DHCP ranges.

Keep `/etc/dnsmasq.d/ansible.conf` focused on dnsmasq service settings such as port,
listen addresses, interfaces, upstream resolvers, and local zones. The direct
`dnsmasq_dhcp_ranges`, `dnsmasq_dhcp_hosts`, and static record variables in the role
are still useful for non-nintent deployments, but they should not be the normal source
of truth once `DesiredIPRange` and `DesiredEndpoint.ip_policy` export are enabled.
