# Inventory Refactor Plan

## Goal

Separate host attributes from execution-target groups so the inventory can express:

- roles or responsibilities via groups
- host capabilities and platform via host variables

## Current Problems

- `ubuntu_knode` and `ubuntu_cuda` mix OS and GPU capability in one group name.
- `mac_llm` and `mac_infra` mix OS and host purpose in one group name.
- Several playbooks infer Linux or macOS behavior from those group names instead of explicit host attributes.

## Refactor Direction

1. Add explicit host attributes:
   - `host_os: linux|macos|haos`
   - `has_gpu: true|false`
   - `power_control: wol|macos_sleep|none`
2. Keep role-based groups:
   - `nomad_server`
   - `prometheus_server`
   - `grafana_server`
   - `prometheus_node_exporter_targets`
3. Introduce capability/platform groups for playbook targeting:
   - `linux`
   - `macos`
   - `gpu_hosts`
   - `power_managed`
4. Update playbooks and templates to target the new groups and use host vars for behavior selection.

## Implementation Steps

1. Update `inventories/hosts.example.yml`
2. Update `inventories/production/hosts.yml`
3. Replace direct references to `ubuntu_knode`, `ubuntu_cuda`, `mac_llm`, and `mac_infra`
4. Make Home Assistant generation rely on `power_managed` and `host_os`/`power_control`
5. Run syntax validation on the affected playbooks

## Expected Outcome

- Inventory names represent stable target sets.
- OS/GPU/power behavior is explicit on each host.
- Adding a new Linux GPU host no longer requires inventing another composite group name.
