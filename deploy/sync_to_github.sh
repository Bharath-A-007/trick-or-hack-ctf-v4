#!/usr/bin/env bash
# Safely sync local Trick or Hack changes to your existing GitHub repo,
# without ever committing the live database or secrets.
set -e

echo "== Trick or Hack: GitHub Sync =="

# 1. Make sure .gitignore protects live data before anything else
if [ ! -f .gitignore ]; then
  echo "Creating .gitignore..."
fi
cat > .gitignore << 'EOF'
instance/
*.db
*.db-wal
*.db-shm
attachments/*
!attachments/.gitkeep
venv/
__pycache__/
*.pyc
.DS_Store
.env
server.log
EOF
mkdir -p attachments && touch attachments/.gitkeep

# 2. Show what changed before committing anything
echo ""
echo "--- git status ---"
git status --short

read -p "Continue and commit these changes? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted. No changes committed."
  exit 0
fi

# 3. Stage and commit
git add .
COMMIT_MSG=${1:-"v2: multi-member teams, anti-cheat lockouts, riddle hints, Halloween theme, credits"}
git commit -m "$COMMIT_MSG" || echo "Nothing new to commit."

# 4. Push
CURRENT_BRANCH=$(git branch --show-current)
echo "Pushing to origin/$CURRENT_BRANCH ..."
git push origin "$CURRENT_BRANCH"

echo ""
echo "== Done. =="
echo "On the COLLEGE SERVER, apply the update safely with:"
echo "   cd /opt/trickorhack/platform"
echo "   git pull origin $CURRENT_BRANCH"
echo "   source venv/bin/activate && pip install -r requirements.txt"
echo "   python migrate_v1_to_v2.py instance/toh_v1_backup.db   # only if upgrading from v1"
echo "   sudo systemctl restart toh"
echo "   sudo systemctl restart witchs_ledger"
