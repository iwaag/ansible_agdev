# Host Setup Verification Guide

Use this checklist on each host after applying `playbooks/linux_initial_setup.yml`.

## Linux

### Linux laptop

Run the following on the host:

```bash
systemctl is-enabled ansible-rfkill-block.service
systemctl status ansible-rfkill-block.service --no-pager
rfkill list
grep -E '^IdleAction=' /etc/systemd/logind.conf.d/80-ansible-idle-action.conf
systemctl is-enabled tlp.service
systemctl status tlp.service --no-pager
grep -E '^(HandleLidSwitch|HandleLidSwitchDocked)=' /etc/systemd/logind.conf.d/80-ansible-lid-switch.conf
cat /sys/power/mem_sleep
systemctl status ansible-mem-sleep-default.service --no-pager
systemctl status ansible-setterm-blank.service --no-pager
TERM=linux setterm --blank < /dev/tty1
apt-config dump | grep -E 'APT::Periodic::(Update-Package-Lists|Unattended-Upgrade)'
unattended-upgrade --dry-run --debug
needrestart -b
```

Checks:

- `rfkill list` should show `Wireless LAN` and `Bluetooth` as `Soft blocked: yes`.
- `/etc/systemd/logind.conf.d/80-ansible-idle-action.conf` should contain `IdleAction=ignore`.
- `tlp.service` should be `enabled` and `active`.
- `/etc/systemd/logind.conf.d/80-ansible-lid-switch.conf` should contain `HandleLidSwitch=ignore` and `HandleLidSwitchDocked=ignore`.
- `cat /sys/power/mem_sleep` should show `[s2idle]` on systems that support `s2idle`.
- `ansible-mem-sleep-default.service` should not be in a failed state. On systems without `s2idle` support, only verify the `cat /sys/power/mem_sleep` output.
- `ansible-setterm-blank.service` should not be in a failed state.
- `TERM=linux setterm --blank < /dev/tty1` should report `1`.
- `apt-config dump` should show periodic update and unattended upgrade enabled.
- `unattended-upgrade --dry-run --debug` should complete without fatal errors.
- `needrestart -b` should confirm that services are not being restarted automatically.

### Linux desktop or server

Run the following on the host:

```bash
systemctl is-enabled ansible-rfkill-block.service
systemctl status ansible-rfkill-block.service --no-pager
rfkill list
grep -E '^IdleAction=' /etc/systemd/logind.conf.d/80-ansible-idle-action.conf
systemctl status suspend.target --no-pager
apt-config dump | grep -E 'APT::Periodic::(Update-Package-Lists|Unattended-Upgrade)'
unattended-upgrade --dry-run --debug
needrestart -b
```

Checks:

- `ansible-rfkill-block.service` should be `enabled`.
- `rfkill list` should show `Wireless LAN` and `Bluetooth` blocked if those adapters are meant to stay disabled.
- `/etc/systemd/logind.conf.d/80-ansible-idle-action.conf` should contain `IdleAction=ignore`.
- `suspend.target` should not be masked.
- `apt-config dump` should show periodic update and unattended upgrade enabled.
- `unattended-upgrade --dry-run --debug` should complete without fatal errors.
- `needrestart -b` should confirm that services are not being restarted automatically.

## macOS

coming soon
