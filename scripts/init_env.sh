#!/usr/bin/env bash
#
# Create ./.env from .env.example with every CHANGE_ME replaced by a freshly generated
# secret (DJANGO_SECRET_KEY gets a long key satisfying the stage/prod length guard; the
# rest get random passwords). Comment lines are left untouched.
#
# An existing .env is NEVER modified — the script just reports and exits, so it is safe
# to re-run. Used by `make init`.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
    echo ".env already exists — left untouched."
    exit 0
fi

if ! command -v openssl >/dev/null 2>&1; then
    echo "ERROR: openssl is required to generate secrets but was not found on PATH." >&2
    exit 1
fi

generated=()
while IFS= read -r line; do
    case "$line" in
        \#*) ;; # keep commented examples (e.g. the DB_BACKUP block) as-is
        *CHANGE_ME*)
            var="${line%%=*}"
            case "$var" in
                DJANGO_SECRET_KEY) secret="$(openssl rand -hex 64)" ;;
                *)                 secret="$(openssl rand -hex 16)" ;;
            esac
            line="${line//CHANGE_ME/$secret}"
            generated+=("$var")
            ;;
    esac
    printf '%s\n' "$line"
done <.env.example >.env

echo "Created .env from .env.example. Generated secrets for:"
for var in "${generated[@]}"; do
    echo "  - $var"
done
