#!/usr/bin/env bash
# Sync GitHub mirror's main branch with Azure DevOps (origin) main, for both submodules.
# Safe to run: github/main has no unique commits in either repo (pure fast-forward).
set -euo pipefail

REPOS=(
  "/Users/abadr/Documents/Laplace/Projects/odoo19/addons_lp_ecommerce"
  "/Users/abadr/Documents/Laplace/Projects/odoo19/next_ecommerce"
)

for repo in "${REPOS[@]}"; do
  echo "=== $repo ==="
  cd "$repo"

  git fetch origin main
  git fetch github main

  # Bail out if github has commits origin doesn't (would need a non-ff push / force)
  unique_to_github=$(git rev-list --count origin/main..github/main)
  if [ "$unique_to_github" != "0" ]; then
    echo "ABORT: github/main has $unique_to_github commit(s) not on origin/main (azure)."
    echo "Resolve manually before syncing (would require a force push)."
    exit 1
  fi

  # Note: we push the fetched origin/main ref directly, so the local checked-out
  # main branch / working tree (which may have unrelated uncommitted edits) is
  # never touched by this script.

  echo "Fast-forwarding github/main -> origin/main"
  git push github origin/main:main
  echo "Done: $repo"
  echo
done
