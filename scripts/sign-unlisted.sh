#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${AMO_JWT_ISSUER:-}" || -z "${AMO_JWT_SECRET:-}" ]]; then
  echo "AMO_JWT_ISSUER and AMO_JWT_SECRET must be set in the environment." >&2
  exit 2
fi

if ! command -v web-ext >/dev/null 2>&1; then
  echo "web-ext is required. Install it using Mozilla's documented method before signing." >&2
  exit 3
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/validate.py
node --check popup.js
node --check options.js

exec web-ext sign \
  --source-dir "$ROOT" \
  --artifacts-dir "$ROOT/web-ext-artifacts" \
  --channel unlisted \
  --api-key "$AMO_JWT_ISSUER" \
  --api-secret "$AMO_JWT_SECRET"
