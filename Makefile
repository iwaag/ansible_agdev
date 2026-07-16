# nintent-driven inventory and deployment pipeline.
#
# Override the playbook runner or pass extra args, for example:
#   make pipeline ANSIBLE_PLAYBOOK="ansible-playbook -v"
ANSIBLE_PLAYBOOK ?= ansible-playbook
NCTL ?= uv run --project ../nctl nctl
PLAYBOOKS := playbooks
BOOTSTRAP_INVENTORY := inventories/generated/hosts_intent.yml

.PHONY: pipeline bootstrap-inventory collect-ingest production-inventory

# Full refresh: reach reserved-name nodes with the bootstrap inventory, collect
# and ingest actual facts, then compose the production inventory from desired
# intent joined with actual facts.
pipeline: bootstrap-inventory collect-ingest production-inventory

bootstrap-inventory:
	$(NCTL) render hosts-intent --config ../nctl.toml --out inventories/generated

# The collection stage runs against the freshly generated bootstrap inventory,
# not the default production inventory, because production is built afterwards.
collect-ingest:
	$(ANSIBLE_PLAYBOOK) -i $(BOOTSTRAP_INVENTORY) $(PLAYBOOKS)/collect_nodeutils_and_ingest_nautobot.yml

production-inventory:
	$(NCTL) render production --config ../nctl.toml --out inventories/generated
