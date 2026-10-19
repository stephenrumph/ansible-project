# ansible-project

A public-safe Ansible project for managing servers. Checked-in hostnames, DNS
names and addresses are documentation placeholders only; production inventory
and credentials belong in Ansible Semaphore.

## Proxmox automation

The `proxmox/` directory contains the Proxmox LXC lifecycle, Linux baseline and
read-only firewall-audit suite. Start with `proxmox/README.md` for Semaphore
Inventory, Key Store, protected Environment and task-template setup.

The suite does not commit production addresses, VMIDs, API credentials, SSH
keys, firewall policy or Twingate configuration. Firewall deployment and
container deletion are deliberately excluded from routine automation.
