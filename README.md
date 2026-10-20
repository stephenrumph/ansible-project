# ansible-project

Public-safe Ansible playbooks for server maintenance.

## Public repository boundary

Do not commit production hostnames, addresses, SSH users, private keys,
passwords, Vault files, API tokens, management networks, or firewall exports.
The checked-in `inventories/example/` inventory deliberately contains no hosts.

Store all real inventory, SSH credentials, become credentials, secrets and
environment values in Ansible Semaphore:

- **Inventory**: production groups and host details.
- **Key Store**: SSH private key and optional become credential.
- **Environment**: runtime variables and service credentials.
- **Vault password**: Semaphore only, never Git.

Install collections in the Semaphore execution environment before running:

```sh
ansible-galaxy collection install -r collections/requirements.yml
```

Use the Semaphore-managed inventory when applying a playbook. The repository's
example inventory is for syntax checks and documentation only.

## Validation

```sh
ansible-galaxy collection install -r collections/requirements.yml
ansible-playbook -i inventories/example/linux.ini playbooks/Linux/get-info.yaml --syntax-check
ansible-playbook -i inventories/example/linux.ini playbooks/Linux/update-apt.yaml --syntax-check
ansible-playbook -i inventories/example/linux.ini playbooks/Windows/install-xammp.yaml --syntax-check
ansible-playbook -i inventories/example/linux.ini playbooks/Windows/sanity-check.yaml --syntax-check
ansible-lint playbooks
yamllint -c .yamllint .
python scripts/check_public_safety.py
```