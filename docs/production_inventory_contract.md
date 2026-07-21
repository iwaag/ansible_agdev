# Production inventory contract 1.0

Production inventory composition is owned by `nctl`. Ansible owns the actuation inputs in
`vars/deployment_profiles.yml` and consumes the generated inventory; nintent owns desired-state
records and exposes them through GraphQL.

## Generation flow

Run from the parent `pj-clusterintent` checkout:

```bash
NAUTOBOT_TOKEN=... uv run --project nctl nctl render production \
  --config nctl.toml \
  --out ansible_agdev/inventories/generated
```

From this directory, `make production-inventory` runs the equivalent command. The full
`make pipeline` order is bootstrap inventory, nodeutils collect/ingest, then production render.
The bootstrap stage runs `nctl render hosts-intent --out inventories/generated`; it does not
run a Nautobot export Job or download a JobResult file through Ansible.

`nctl` reads `vars/deployment_profiles.yml` directly, fetches desired and actual state from
Nautobot, validates a staged inventory with `ansible-inventory --list`, writes the immutable
`production.reports/<generation_id>.json` report, and atomically replaces `production.yml`.
The old Ansible→Nautobot canonical-JSON/digest byte transport, sync/export Jobs, and profile
projection no longer exist.

## Ownership

- `vars/deployment_profiles.yml`: Ansible-owned profile-to-group and placement-config schema.
  It contains no secrets.
- Desired nodes, operational configs, service placements, and endpoints: nintent ledger records.
- Actual device facts: Nautobot records populated from nodeutils.
- Composition, profile validation, platform policy, drift/skipped reporting, and artifact
  validation: `nctl_core.production`.
- Host actuation and role defaults: Ansible.

The profile digest remains in schema 1.0 output as local provenance calculated by `nctl`; it is
not a cross-process authentication or byte-contract field.

## Inventory shape

The generated YAML keeps the established schema metadata under `all.vars` (bumped to `"3.0"` by
`devdocs/small/fix_sshkey/plan.md` Step 4 -- see below):

```yaml
all:
  vars:
    nintent_inventory_schema_version: "3.0"
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
```

Service groups are derived from active placements and their deployment profiles. Host connection,
platform, power, traceability, skip, and drift rules are implemented and tested in nctl. See the
nctl production modules and tests for the executable contract.

## SSH trust host variables (schema 3.0)

Every `ssh_hosts` member also carries two controller-generated variables, derived only from the
node's immutable DesiredNode UUID -- never from `ansible_host`, a slug, an IP, or a MAC address:

```yaml
nctl_ssh_host_key_alias: nctl-node-<DesiredNode UUID>
ansible_ssh_common_args: >-
  -o HostKeyAlias=nctl-node-<DesiredNode UUID>
  -o UserKnownHostsFile=<nctl's configured [ssh].known_hosts_file>
  -o StrictHostKeyChecking=yes
  -o CheckHostIP=no
  -o UpdateHostKeys=no
```

This makes SSH host-key trust follow the node's stable identity across mDNS, `.home.arpa`, a
reserved/static IP, or a Tailscale address -- the same alias/args nctl's bootstrap
`hosts_intent.yml` emits for the same node, byte-identical even when `ansible_host` differs. See
`nctl/README.md`'s "SSH trust configuration" section and `nctl ssh enroll --help` for how the
managed known_hosts file referenced by `UserKnownHostsFile` is populated; this document does not
duplicate that lifecycle.

## Operational boundary

The bootstrap `hosts_intent.yml` remains separate, is rendered by nctl from desired state, and is
used for collection before a production inventory exists. Operational playbooks use
`inventories/generated/production.yml` through `ansible.cfg`.

After changing `vars/deployment_profiles.yml`, rerun `nctl render production`; no profile sync
step is required. A render failure leaves the previous installed production inventory unchanged.
