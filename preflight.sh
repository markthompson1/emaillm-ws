#!/bin/zsh

# === WindSurf PRE-FLIGHT (zsh) ===
set -e

# 1) virtual-env
which python | grep -q '.venv' && echo '✅ .venv is active' \
  || { echo '❌ .venv not active'; exit 1; }

# 2) secrets (direnv OR .env)
[[ -f .envrc ]] && eval "$(direnv export zsh)" || true
[[ -f .env   ]] && export $(grep -v '^#' .env | xargs) || true

for V in OPENAI_API_KEY SENDGRID_KEY REDIS_URL; do
  if [[ -z ${(P)V} ]]; then
    echo "❌ Missing $V"; exit 1
  else
    echo "✅ $V is set"
  fi
done

# 3) git hygiene
git diff --quiet || { echo '❌ Uncommitted changes'; exit 1; }
if [[ -n $(git ls-files --others --exclude-standard) ]]; then
  echo '❌ Untracked files present:'
  git ls-files --others --exclude-standard
  exit 1
fi
echo '✅ git tree clean'

git pull --ff-only && echo '✅ up-to-date on $(git rev-parse --abbrev-ref HEAD)'

# 4) deps
pip install -q -r requirements.txt && echo '✅ requirements satisfied'

# 5) tests
pytest -q && echo '✅ all tests green'

echo '🎉 PRE-FLIGHT OK — WindSurf may proceed'
# ==================================
