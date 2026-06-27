# Production inventory contract 1.0

This document freezes the inputs and outputs audited before the service
placement cutover. It is an executable contract together with
`vars/deployment_profiles.yml`, nintent's
`production_inventory_contract.py`, and their fixtures. Pre-redesign formats
are not accepted.

## Static group audit

| Group | Classification | Contract source | Disposition |
| --- | --- | --- | --- |
| `ssh_hosts` | bootstrap/production execution index | eligible DesiredNode plus stage-specific checks | keep; never a service declaration |
| `linux` | observed selector | nodeutils `facts.system == Linux` | generate from actual state |
| `macos` | observed selector | nodeutils `facts.system == Darwin` | generate from actual state |
| `haos` | declared selector | OperationalConfig `declared_host_os == haos` | add as declared selector |
| `power_managed` | desired operational policy | `power_control != none` | generate from OperationalConfig |
| `dnsmasq_server` | service placement | profile `dnsmasq` | generate from active placements |
| `prometheus_server` | service placement | profile `prometheus` | generate from active placements |
| `grafana_server` | service placement | profile `grafana` | generate from active placements |
| `nomad_server` | service placement | profile `nomad_server` | generate from active placements |
| `nomad_client` | service placement | profile `nomad_client` | generate from active placements |
| `haos_server` | service placement | profile `home_assistant` | generate from active placements |
| `prometheus_node_exporter_targets` | service placement | profile `prometheus_node_exporter` | generate from active placements |
| `gpu_hosts` | obsolete | none; no current playbook consumer | remove at cutover |
| `nautobot_server` | obsolete example-only group | none; no current playbook consumer | remove at cutover |

`all` and `localhost` are Ansible mechanics and are not placement groups.
`dnsmasq_server` and `nautobot_server` occur in the old broad example even
when absent from the hand-maintained production inventory; that example was
included in this audit.

## Host-variable audit

Only variables with a current consumer or an explicit operational contract are
projected. Variables gathered live by Ansible (`ansible_system`,
`ansible_architecture`, `ansible_distribution_release`, and similar) remain
Ansible facts and are not production inventory exports.

| Variable | Consumer | Authority | Kind |
| --- | --- | --- | --- |
| `host_os` | power-switch generation and OS selector checks | normalized nodeutils `facts.system`; `declared_host_os` only for HAOS | actual/explicit declared |
| `local_ip` | connection selection, Nomad advertise, power-switch generation | nodeutils `facts.network.primary_ip_address`; declared HAOS local endpoint only | actual/explicit declared |
| `mac_address` | WOL and power-switch generation | nodeutils `facts.network.primary_mac_address` | actual |
| `network_interface` | Nomad client and WOL-related execution | nodeutils `facts.network.primary_interface.name` | actual |
| `connection_path` | `group_vars/all` connection selection | OperationalConfig | desired operational |
| `local_dns_hostname` | local connection fallback | selected local endpoint `dns_name` | desired operational |
| `mdns_hostname` | local connection fallback/bootstrap | selected local endpoint `mdns_name` | desired operational |
| `tailscale_ip` | Tailscale connection | selected Tailscale endpoint `ip_address` | desired operational |
| `ansible_port` | SSH transport | OperationalConfig | desired operational |
| `power_control` | wake/sleep validation and generation | OperationalConfig | desired operational |
| `is_laptop` | laptop policy | OperationalConfig | desired operational |
| `ansible_user` | all SSH playbooks | shared `default_user` group variable | Ansible-owned shared policy |
| `ansible_host` | Ansible transport and cross-host role lookups | deterministic connection expression in `group_vars/all` | derived connection value |
| `has_gpu` | none | old static inventory | remove; do not export |
| `package_manager` | none | none | forbidden; roles use live facts and role logic |

Traceability variables are `nintent_desired_node_id`,
`nintent_operational_config_id`, `nautobot_device_id`, and
`nintent_active_placement_ids`. They are identifiers, not configuration.

## Deployment-profile audit

The only runtime profile map is `vars/deployment_profiles.yml`. Profile keys,
groups, config schema versions, config keys, Ansible variable names, JSON
types, list item types, and requiredness form a closed schema. Unknown keys and
objects fail validation. Profiles may have an empty config schema when group
membership alone is the service contract.

The exposed values were checked against current role defaults and templates:

| Profile | Role/default consumer | Exposed placement configuration |
| --- | --- | --- |
| `dnsmasq` | `dnsmasq_server` defaults and `ansible.conf.j2` | bind behavior, cache size, DHCP enable/authority, interfaces, listen addresses, local domain, upstream servers |
| `grafana` | `grafana_server` defaults and `prometheus-datasource.yml.j2` | datasource enable/name/default, Prometheus scheme/port |
| `home_assistant` | HAOS deployment play | none in schema 1; group membership only |
| `nomad_client` | Linux/macOS client defaults and `nomad.hcl.j2`/plist | region, datacenter, node class, raw-exec flag |
| `nomad_server` | server defaults and `nomad.hcl.j2` | region, datacenter, bootstrap count, retry-join list |
| `prometheus` | server defaults and `prometheus.yml.j2`/service template | listen address and retention time |
| `prometheus_node_exporter` | node-exporter role | none in schema 1; group membership only |

Package names, repository URLs, install paths, service names, file modes,
binary versions, generated DNS record collections, secrets, and values derived
from other inventory hosts remain role/playbook owned. They are deliberately
not placement configuration.

## Profile Job-input bytes

The export playbook passes only the value below `deployment_profiles`, not the
YAML wrapper. Canonical JSON is exactly Python:

```python
json.dumps(
    value,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
)
```

It is UTF-8 with no BOM and no trailing newline. Every mapping key must be a
string. The digest is lowercase SHA-256 of those exact bytes. The Job parses
the JSON, serializes it again, requires exact string equality, and then checks
the supplied digest. `playbooks/verify_deployment_profiles_contract.yml`
proves Ansible produces the same fixture bytes and digest as Python.

## Qualified YAML references

A DesiredNode reference is one non-empty globally unique `slug` string.

A DesiredService reference is an object with exactly these non-empty fields:

```yaml
intent_source: infrastructure
catalog_namespace: default
catalog_metadata_name: dnsmasq
service_type: service
```

`intent_source` is the globally unique IntentSource slug. The complete tuple
matches the existing DesiredService database uniqueness constraint.

After selecting a node, a DesiredEndpoint reference is an object with exactly:

```yaml
name: primary
endpoint_type: primary
```

It matches the existing `(desired_node, name, endpoint_type)` constraint.
Zero matches is `missing_reference`; more than one is
`ambiguous_reference`. Selecting the first query result is forbidden.

## Connection contract

For `connection_path=local`, `ansible_host` resolves in this order:

1. actual `local_ip` (or the declared HAOS endpoint IP),
2. selected local endpoint `dns_name` as `local_dns_hostname`,
3. selected local endpoint `mdns_name` as `mdns_hostname`,
4. `inventory_hostname`.

For `connection_path=tailscale`, the selected Tailscale endpoint must contain a
valid IP and it is exported as both `tailscale_ip` and the resolved
`ansible_host`. There is no fallback. Endpoint IP prefixes are normalized to
host addresses. All hosts receive `ansible_user: "{{ default_user }}"` from
generated `group_vars/all`; it is never duplicated in host vars.

## Actual-state and platform contract

Actual data is fresh when `collected_at >= generated_at - 72 hours`; equality
is fresh. Missing, invalid, and older timestamps produce respectively
`missing_actual_data`, `invalid_actual_timestamp`, and `stale_actual_data` host
skip reasons. The fixed 72-hour schema 1.0 window matches the existing nauto
ingest default.

Observed OS normalization is closed: `Linux -> linux` and `Darwin -> macos`.
Required nodes compare the normalized observed value with `expected_host_os`
and record `desired_actual_os_mismatch` drift, but export the observed value.
Declared nodes support only `haos`. Valid power combinations are:

| Platform | Allowed `power_control` |
| --- | --- |
| Linux | `none`, `wol` |
| macOS | `none`, `macos_sleep` |
| HAOS | `none` |

## Production YAML schema 1.0

The YAML document contains only Ansible inventory data. Metadata is under
`all.vars` so `ansible-inventory` can validate the complete artifact:

```yaml
all:
  vars:
    nintent_inventory_schema_version: "1.0"
    nintent_generation_id: "<uuid>"
    nintent_generated_at: "<RFC3339 UTC>"
    nintent_report_path: "production.reports/<generation_id>.json"
    nintent_deployment_profile_digest: "<64 lowercase hex>"
  children:
    ssh_hosts:
      hosts: {}
    linux:
      hosts: {}
    macos:
      hosts: {}
    haos:
      hosts: {}
    power_managed:
      hosts: {}
    <audited service group>:
      hosts: {}
```

Inventory hostnames, group names, variable names, placement processing, and
JSON/YAML mapping keys are sorted lexically before rendering. A host is defined
once under `ssh_hosts`; selector/service group members use empty mappings.
Given the same explicit generation metadata, source records, actual records,
and profile payload, rendering is byte-stable.

## Companion report schema 1.0

The immutable UTF-8 JSON report uses this exact top-level key set:

```text
schema_version, generation_id, generated_at, report_path,
deployment_profile_digest, summary, hosts, skipped, drift, errors
```

`summary` contains integer `eligible`, `included`, `skipped`, `placements`,
`active_placements`, and `inactive_placements` counts. `hosts`, `skipped`,
`drift`, and `errors` are arrays sorted by inventory hostname, code, and stable
object ID. Each skipped entry has `inventory_hostname`, `desired_node_id`,
`code`, and `detail`. Each drift entry has the same identity fields plus
`expected` and `observed`. Global validation produces no new artifacts.

Global error codes are:

- `invalid_profile_json`, `noncanonical_profile_json`,
  `invalid_profile_digest`, `profile_digest_mismatch`;
- `invalid_profile_map`, `invalid_profile`, `unknown_profile`,
  `unsupported_profile_schema`, `unsupported_config_schema`,
  `unknown_config_key`, `missing_required_config`,
  `invalid_profile_value_type`, `duplicate_variable_assignment`;
- `missing_reference`, `ambiguous_reference`, `endpoint_node_mismatch`;
- `missing_operational_config`, `invalid_actual_state_policy`,
  `invalid_connection_path`, `unresolved_connection_path`,
  `invalid_platform_power`, `conflicting_host_variable`,
  `duplicate_inventory_hostname`.

Host-skip codes are `missing_actual_data`, `invalid_actual_timestamp`,
`stale_actual_data`, `missing_required_actual_fact`, `missing_realized_device`,
`unsupported_actual_type`, and `unsupported_observed_host_os`. A placement on a
skipped host is counted as inactive and never creates group membership.
