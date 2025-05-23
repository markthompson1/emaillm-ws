#!/usr/bin/env bash
set -euo pipefail

echo -e "\n🔒 logging into VPS…"
ssh ubuntu@emaillm.com -tt <<'EOF'
sudo -i <<'INNER'
set -euo pipefail
cd /srv/emaillm-ws

echo -e "\n🌀 on commit: $(git rev-parse --short HEAD)"
echo "   expecting 37600f7 (last-known-good)…"

# reinstall deps
./.venv/bin/pip install -q -r requirements.txt
echo "✅ dependencies ok"

# quick pytest
./.venv/bin/python -m pytest -q
echo "✅ tests pass"

# restart
systemctl restart emaillm
sleep 3
systemctl is-active --quiet emaillm && echo "✅ service running"

# local webhook smoke-test
RES=$(
  curl -s -o /tmp/resp.json -w "%{http_code}" \
       -F from="Me <me@example.com>" \
       -F to="mark@thompson.one" \
       -F subject="ping" \
       -F text="hello" \
       http://127.0.0.1:8000/webhook/inbound
)
echo "HTTP $RES – response body:"
cat /tmp/resp.json && echo

INNER
EOF
