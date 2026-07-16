# nintent-driven inventory and deployment pipeline.
#
# Override the playbook runner or pass extra args, for example:
#   make pipeline NCTL="uv run --project ../nctl nctl -v"
NCTL ?= uv run --project ../nctl nctl

.PHONY: pipeline bootstrap-inventory production-inventory

# Full refresh: drift -> plan -> execute (collect, ingest, ledger links, service
# actuation) -> re-observe -> converge, as one bounded nctl operation. This is
# the canonical entry point; bootstrap-inventory and production-inventory below
# remain only for diagnostics and manual recovery, since `nctl reconcile` already
# regenerates both from a private operation-scoped inventory as part of its run.
pipeline:
	$(NCTL) reconcile --config ../nctl.toml --yes

# Diagnostics/manual recovery only: nctl reconcile renders its own scoped
# bootstrap inventory internally and does not read or write this file.
bootstrap-inventory:
	$(NCTL) render hosts-intent --config ../nctl.toml --out inventories/generated

# Diagnostics/manual recovery only: nctl reconcile regenerates the full
# production inventory itself on every apply round.
production-inventory:
	$(NCTL) render production --config ../nctl.toml --out inventories/generated
