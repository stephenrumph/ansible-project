# Firewall policy and rollout

This repository intentionally contains **audit automation only**. It does not
apply Proxmox host, guest-edge, router, or Twingate firewall changes.

Firewall changes can sever the only management path to the Proxmox host. Before
any deployment automation is added:

1. Confirm physical console or equivalent break-glass access.
2. Identify the source address actually seen from Semaphore and Twingate.
3. Save the declared and effective firewall state.
4. Add a narrow temporary management allow before adding restrictive rules.
5. Compile the candidate and inspect rule ordering.
6. Keep the existing session open and verify a second independent connection.
7. Change one guest at a time, then re-run the complete audit.

## Interpretation rules

- RFC1918 addressing is not proof of Internet isolation. Router forwards, DMZ,
  UPnP/NAT-PMP, public IPv6, VPN routes and Twingate Resources must be checked.
- A listener on `0.0.0.0` is not automatically public; it is reachable only from
  networks permitted by routing and firewall policy.
- Proxmox host input policy does not automatically filter bridged LXC traffic.
- LXC `firewall=1` is intent, not proof. Confirm a compiled and runtime chain.
- Keep reverse-proxy, DNS, management, model API and analysis workloads in
  separate policy groups with explicit consumers.

Do not commit production firewall files, addresses, VMIDs, Twingate networks or
source ranges. Store those in the Semaphore Inventory or protected Environment.
