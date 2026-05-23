#!/usr/bin/env bash
set -euo pipefail

echo "Running quality gate checks..."

UI_ROOT="apps/ui/src"
echo "1) Blocking frontend token storage in localStorage..."
if rg -n 'localStorage\.(getItem|setItem|removeItem)\("ai_platform_token"\)' "$UI_ROOT"; then
  echo "Found forbidden token storage in localStorage."
  exit 1
fi

echo "2) Blocking silent catches..."
if rg -n 'catch\s*\{\s*\}' "$UI_ROOT" apps/api packages; then
  echo "Found silent catch blocks."
  exit 1
fi

echo "3) Blocking console logging in frontend source..."
if rg -n 'console\.(log|error|warn|debug)' "$UI_ROOT"; then
  echo "Found forbidden console logging."
  exit 1
fi

echo "4) Blocking explicit any in frontend TypeScript..."
if rg -n ':\s*any\b|<\s*any\s*>|as\s+any\b' "$UI_ROOT" --glob '*.ts' --glob '*.tsx'; then
  echo "Found forbidden any usage."
  exit 1
fi

echo "Quality gate passed."
