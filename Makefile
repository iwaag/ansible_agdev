# nintent-driven inventory and deployment pipeline.
#
# Override the playbook runner or pass extra args, for example:
#   make pipeline ANSIBLE_PLAYBOOK="ansible-playbook -v"
ANSIBLE_PLAYBOOK ?= ansible-playbook
PLAYBOOKS := playbooks
BOOTSTRAP_INVENTORY := inventories/generated/hosts_intent.yml

.PHONY: pipeline bootstrap-inventory collect-ingest production-inventory verify-profiles

# Full refresh: reach reserved-name nodes with the bootstrap inventory, collect
# and ingest actual facts, then compose the production inventory from desired
# intent joined with actual facts.
pipeline: bootstrap-inventory collect-ingest production-inventory

bootstrap-inventory:
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOKS)/export_nintent_hosts_intent.yml

# The collection stage runs against the freshly generated bootstrap inventory,
# not the default production inventory, because production is built afterwards.
collect-ingest:
	$(ANSIBLE_PLAYBOOK) -i $(BOOTSTRAP_INVENTORY) $(PLAYBOOKS)/collect_nodeutils_and_ingest_nautobot.yml

production-inventory:
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOKS)/export_nintent_production.yml

verify-profiles:
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOKS)/verify_deployment_profiles_contract.yml
