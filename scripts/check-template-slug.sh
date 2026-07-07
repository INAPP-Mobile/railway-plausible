#!/bin/bash
# Check template slug validity
SLUG="$1"
if [ -z "$SLUG" ]; then
  echo "Usage: check-template-slug.sh <slug>"
  exit 1
fi
if [[ ! "$SLUG" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
  echo "FAIL: slug '$SLUG' does not match expected pattern (lowercase alphanumeric and hyphens)"
  exit 1
fi
if [ ${#SLUG} -lt 3 ] || [ ${#SLUG} -gt 64 ]; then
  echo "FAIL: slug '$SLUG' length out of range (min=3, max=64)"
  exit 1
fi
echo "OK: slug '$SLUG' is valid"
exit 0
