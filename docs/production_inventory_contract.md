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

The generated YAML keeps the established schema 1.0 metadata under `all.vars`:

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
```

Service groups are derived from active placements and their deployment profiles. Host connection,
platform, power, traceability, skip, and drift rules are implemented and tested in nctl. See the
nctl production modules and tests for the executable contract.

## Operational boundary

The bootstrap `hosts_intent.yml` remains separate and is used for collection before a production
inventory exists. Operational playbooks use `inventories/generated/production.yml` through
`ansible.cfg`.

After changing `vars/deployment_profiles.yml`, rerun `nctl render production`; no profile sync
step is required. A render failure leaves the previous installed production inventory unchanged.
