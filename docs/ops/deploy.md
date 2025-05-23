# Deployment Guide

## Hot-fix via systemd tarball

For quick hot-fixes, you can deploy using the systemd tarball:

1. Create a tarball with the updated systemd unit files:
   ```bash
   tar czf /tmp/emaillm_systemd.tgz -C /tmp emaillm_systemd/
   ```

2. Copy to the VPS:
   ```bash
   scp /tmp/emaillm_systemd.tgz ubuntu@emaillm.com:/tmp/
   ```

3. Install and restart the service:
   ```bash
   ssh ubuntu@emaillm.com '
     set -euo pipefail
     cd /tmp
     rm -rf emaillm_systemd
     tar xzf emaillm_systemd.tgz
     sudo install -m 644 emaillm_systemd/emaillm.service /etc/systemd/system/emaillm.service
     sudo mkdir -p /etc/systemd/system/emaillm.service.d
     sudo install -m 644 emaillm_systemd/emaillm.service.d/env.conf /etc/systemd/system/emaillm.service.d/env.conf
     sudo systemctl daemon-reload
     sudo systemctl restart emaillm
     sudo systemctl is-active --quiet emaillm && echo "✅ service running"
   '
   ```

## Standard Deployment

[Add standard deployment instructions here]
