# Proxmox container management with Ansible Semaphore

This directory provides public-safe automation for:

- read-only Proxmox and LXC inventory reporting;
- creating and powering explicitly selected LXC containers;
- applying a small Debian/Ubuntu baseline over SSH;
- read-only firewall, listener and routing audits.

It deliberately does **not** commit production inventory, addresses, VMIDs,
credentials, firewall rules or Twingate policy. Those values belong in Ansible
Semaphore.

## Safety model

- Proxmox API secrets are read only from controller environment variables.
- Lifecycle modules use `no_log: true`.
- TLS certificate verification defaults to enabled.
- Disruptive power operations require target-bound confirmation text.
- Proxmox lifecycle operations are skipped in check mode because the pinned
  module cannot reliably predict them.
- Container configuration uses `serial: 1` by default.
- Firewall automation is audit-only. See `docs/firewall-policy.md` before adding
  any deployment role.

## Repository layout

```text
proxmox/
├── ansible.cfg
├── requirements.yml
├── requirements.txt
├── inventories/example/
├── group_vars/
├── playbooks/
│   ├── inventory_audit.yml
│   ├── firewall_audit.yml
│   ├── configure.yml
│   ├── site.yml
│   ├── lxc_create.yml
│   └── lxc_power.yml
└── roles/
    ├── proxmox_lxc/
    ├── linux_baseline/
    └── firewall_audit/
```

## Controller requirements

The Semaphore runner currently targets the following compatible versions:

- Ansible Core 2.14.x
- `community.general` 6.6.2
- `ansible.posix` 1.5.4
- `proxmoxer` 1.2 or newer
- `requests` 2.x

Install dependencies in the Python environment used by Semaphore:

```bash
ansible-galaxy collection install -r proxmox/requirements.yml
python3 -m pip install -r proxmox/requirements.txt
```

`community.general` 6.6.2 predates Proxmox VE 9. Test lifecycle operations in a
non-production pool before treating create or power automation as production
ready.

## Semaphore configuration

Create separate Semaphore objects instead of placing production values in Git.

### 1. Repository

Add the clean GitHub repository URL. Do not embed a token in the URL.

### 2. Key Store

Store:

- the SSH private key used for the Proxmox host and managed containers;
- the become password only if passwordless constrained sudo is unavailable.

Do not place key paths or private key material in inventory variables.

### 3. Production inventory

Create a Semaphore inventory with these groups:

```yaml
all:
  children:
    proxmox_hosts:
      hosts:
        pve-production:
          ansible_host: "<proxmox-management-address>"
          ansible_port: "<management-ssh-port>"
          ansible_user: "<automation-user>"
    managed_lxc:
      hosts:
        service-one:
          ansible_host: "<container-address>"
          ansible_user: "<automation-user>"
        worker-one:
          ansible_host: "<container-address>"
          ansible_user: "<automation-user>"
```

The real inventory must remain in Semaphore. The checked-in example uses IANA
documentation addresses and must never be used as production inventory.

### 4. Protected environment

Set these environment variables in Semaphore:

```text
ANSIBLE_CONFIG=<checkout>/proxmox/ansible.cfg
PROXMOX_API_HOST=<bare-api-hostname-or-address>
PROXMOX_URL=https://<api-hostname-or-address>:8006
PROXMOX_API_USER=<account-with-realm>
PROXMOX_API_TOKEN_ID=<token-name>
PROXMOX_API_TOKEN_SECRET=<token-secret>
```

The lifecycle module requires both the API user and token name. The dynamic
inventory example uses the full `PROXMOX_URL`; lifecycle playbooks use the bare
`PROXMOX_API_HOST`.

Install the private CA's public certificate in the Semaphore runner when the
Proxmox API does not use a publicly trusted certificate. Do not permanently set
`validate_certs: false`.

### 5. Task templates

Create separate templates and permissions:

| Template | Playbook | Recommended mode |
|---|---|---|
| Inventory audit | `proxmox/playbooks/inventory_audit.yml` | Routine, read-only |
| Firewall audit | `proxmox/playbooks/firewall_audit.yml` | Routine, read-only |
| Container baseline check | `proxmox/playbooks/configure.yml` | `--check --diff` |
| Container baseline apply | `proxmox/playbooks/configure.yml` | Manual, limited group |
| LXC create | `proxmox/playbooks/lxc_create.yml` | Manual approval |
| LXC power | `proxmox/playbooks/lxc_power.yml` | Manual approval |

Keep lifecycle permissions separate from routine configuration and audit.

## Lifecycle input

Pass `proxmox_lxc_instances` through a protected Semaphore survey or inventory
variable. Example values below are placeholders only:

```yaml
proxmox_lxc_instances:
  - vmid: 9001
    node: pve-node-placeholder
    hostname: lxc-placeholder
    ostemplate: local:vztmpl/debian-placeholder.tar.zst
    storage: local-lvm
    disk: local-lvm:8
    cores: 2
    memory: 1024
    swap: 512
    onboot: true
    unprivileged: true
    netif:
      net0: name=eth0,bridge=vmbr0,ip=dhcp,type=veth
    tags:
      - ansible_managed
```

If container creation needs an initial SSH public key, inject `pubkey` through a
protected Semaphore value. Never commit a container password.

### Create

Run `lxc_create.yml`. Check mode prints the plan but intentionally does not call
the Proxmox module.

### Power

Set `proxmox_power_state` to `started`, `stopped` or `restarted`.

Starting does not require confirmation. Stopping and restarting require:

```text
POWER-STOPPED:9001,9002
POWER-RESTARTED:9001,9002
```

in `proxmox_power_confirmation`. The VMID list and order must exactly match the
selected `proxmox_lxc_instances`, so a confirmation cannot be reused after the
target list changes.

Container deletion is intentionally outside this suite. Proxmox deletion also
removes related ACL and firewall entries, so it requires a separately reviewed
break-glass workflow rather than the routine Semaphore lifecycle role.

## Container baseline

`configure.yml` currently supports Debian-family containers and:

- installs a small package baseline;
- configures the Brisbane timezone;
- changes one container at a time.

It intentionally does not manage users, SSH keys, sudoers or `sshd_config`.
Those controls need a separately reviewed access-management design to avoid
locking out Semaphore.

Run the check template first:

```bash
ANSIBLE_CONFIG="$PWD/proxmox/ansible.cfg" \
ansible-playbook -i <inventory> proxmox/playbooks/configure.yml \
  --limit <one-test-container> --check --diff
```

## Firewall audit

`firewall_audit.yml` collects declared/effective firewall state, routes and
listeners without changing them. It runs read-only commands even under
`--check`, while reporting no changed state.

Audit logs contain production addresses, routes, listeners and firewall rules.
Restrict Semaphore job-log access and retention even though the repository
itself contains no production values.

The audit does not prove Internet isolation by itself. Review upstream router
port forwarding, DMZ and UPnP/NAT-PMP state, public IPv6, and Twingate Resources,
groups and policies. See `docs/firewall-policy.md`.

## Local validation

From the repository root:

```bash
export ANSIBLE_CONFIG="$PWD/proxmox/ansible.cfg"

ansible --version
ansible-config dump --only-changed
ansible-galaxy collection list community.general ansible.posix
python3 -c 'import proxmoxer, requests; print(proxmoxer.__version__, requests.__version__)'

ansible-inventory -i proxmox/inventories/example/hosts.yml --graph

for playbook in proxmox/playbooks/*.yml; do
  ansible-playbook -i proxmox/inventories/example/hosts.yml \
    "$playbook" --syntax-check
 done
```

The lifecycle syntax checks require placeholder environment values because the
role validates API inputs at runtime. Syntax checking does not call the API.

## Values that must never be committed

- production IP addresses, hostnames, VMIDs and network ranges;
- Proxmox API user, token ID or token secret;
- SSH private keys, passwords or Vault passwords;
- real Twingate networks, Resources or policy exports;
- Discord/webhook URLs and application credentials;
- copied production firewall files or full unredacted audit output.
