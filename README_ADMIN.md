# Ansible Project Admin Guide

## SSH key setup

Generate the control-node SSH key used by Ansible:

```bash
./scripts/generate_ansible_ssh_key.sh
```

This creates:

- `~/.ssh/ansible_key`
- `~/.ssh/ansible_key.pub`

The default Ansible config uses this key with `private_key_file = ~/.ssh/ansible_key`.

## SSH key distribution

Install the public key on each target host:

```bash
ssh-copy-id -i ~/.ssh/ansible_key.pub <user>@<host>
```

Example:

```bash
ssh-copy-id -i ~/.ssh/ansible_key.pub username@192.168.1.20
```

Test SSH access after distribution:

```bash
ssh -i ~/.ssh/ansible_key <user>@<host>
```

## Vault setup

Create the local Vault password file outside the repository:

```bash
mkdir -p ~/.ansible
chmod 700 ~/.ansible
printf '%s\n' 'YOUR_VAULT_PASSWORD' > ~/.ansible/vault_pass.txt
chmod 600 ~/.ansible/vault_pass.txt
```

Create the encrypted variable file from the example:

```bash
cp inventories/production/group_vars/all/vault.example.yml inventories/production/group_vars/all/vault.yml
ansible-vault encrypt inventories/production/group_vars/all/vault.yml
```

The plain variables in `inventories/production/group_vars/all/main.yml` expose:

- `default_user`
- `ansible_become_password`

The encrypted `vault.yml` should define:

- `vault_default_user`
- `vault_ansible_become_password`

Example:

```yaml
vault_default_user: your-login-user
vault_ansible_become_password: your-sudo-password
```

## Host inventory notes

The default inventory path is:

```text
inventories/production/hosts.yml
```

Each host entry can include:

- `ansible_user`
- `local_ip`
- `tailscale_ip`
- `mac_address`
- `network_interface`

Wake-on-LAN related playbooks depend on:

- `mac_address`
- `network_interface`

The example inventory is:

```text
inventories/hosts.example.yml
```
