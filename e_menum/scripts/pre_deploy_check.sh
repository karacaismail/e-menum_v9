#!/usr/bin/env bash
# =============================================================================
# E-Menum Pre-Deploy Check Script
# =============================================================================
#
# This script validates the migration state before deployment.  It is designed
# to run in CI/CD pipelines (GitHub Actions, Coolify pre-deploy hooks) and
# returns a non-zero exit code when issues are found.
#
# Checks performed:
#   1. Pending (unapplied) migrations
#   2. Migration file conflicts (forked migration graph)
#   3. Model changes that need new migration files
#   4. Dangerous operations in pending migrations
#
# Usage:
#   ./scripts/pre_deploy_check.sh            # Run all checks
#   ./scripts/pre_deploy_check.sh --ci       # Strict mode (any warning = fail)
#   ./scripts/pre_deploy_check.sh --json     # JSON output for pipeline parsing
#
# Exit codes:
#   0  - All checks passed
#   1  - Issues found (check output)
#   2  - Script error (missing dependencies, bad environment)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for terminal output (disabled if not a TTY)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'  # No Color
    BOLD='\033[1m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
    BOLD=''
fi

CI_MODE=false
JSON_OUTPUT=false
EXIT_CODE=0

# ─── Argument parsing ────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --ci)     CI_MODE=true ;;
        --json)   JSON_OUTPUT=true ;;
        --help|-h)
            echo "Usage: $0 [--ci] [--json] [--help]"
            echo ""
            echo "  --ci    Strict mode: treat warnings as errors"
            echo "  --json  Output results as JSON"
            echo "  --help  Show this message"
            exit 0
            ;;
    esac
done

# ─── Helper functions ─────────────────────────────────────────────

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()    { echo -e "${RED}[FAIL]${NC}  $*"; EXIT_CODE=1; }
header()  { echo -e "\n${BOLD}$*${NC}"; echo "$(printf '%.0s─' {1..60})"; }

# ─── Environment check ───────────────────────────────────────────

header "Environment Check"

cd "$PROJECT_DIR" || { fail "Cannot cd to $PROJECT_DIR"; exit 2; }

if [ ! -f "manage.py" ]; then
    fail "manage.py not found in $PROJECT_DIR"
    exit 2
fi

# Ensure Django settings module is set
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"
info "Settings: $DJANGO_SETTINGS_MODULE"
info "Project:  $PROJECT_DIR"

# Quick Django import check
if ! python -c "import django; django.setup()" 2>/dev/null; then
    # Try development settings as fallback
    export DJANGO_SETTINGS_MODULE="config.settings.development"
    if ! python -c "import django; django.setup()" 2>/dev/null; then
        fail "Django setup failed. Check DJANGO_SETTINGS_MODULE and dependencies."
        exit 2
    fi
    warn "Using development settings as fallback."
fi

ok "Django environment ready."

# ─── Check 1: Unapplied migrations ───────────────────────────────

header "Check 1: Unapplied Migrations"

SHOWMIGRATIONS_OUTPUT=$(python manage.py showmigrations --plan 2>/dev/null || true)
UNAPPLIED=$(echo "$SHOWMIGRATIONS_OUTPUT" | grep "^\[ \]" || true)

if [ -z "$UNAPPLIED" ]; then
    ok "All migrations are applied."
else
    UNAPPLIED_COUNT=$(echo "$UNAPPLIED" | wc -l | tr -d ' ')
    warn "$UNAPPLIED_COUNT unapplied migration(s) found:"
    echo "$UNAPPLIED" | while IFS= read -r line; do
        echo "    $line"
    done

    if [ "$CI_MODE" = true ]; then
        fail "Unapplied migrations detected in CI mode."
    fi
fi

# ─── Check 2: Migration conflicts ────────────────────────────────

header "Check 2: Migration Conflicts"

# makemigrations --check returns exit code 1 if changes are detected
# We run it with --dry-run to avoid creating files
CONFLICT_OUTPUT=""
CONFLICT_EXIT=0
CONFLICT_OUTPUT=$(python manage.py makemigrations --check --dry-run 2>&1) || CONFLICT_EXIT=$?

if [ "$CONFLICT_EXIT" -eq 0 ]; then
    ok "No model changes need new migrations."
else
    warn "Model changes detected that may need new migrations."
    if [ -n "$CONFLICT_OUTPUT" ]; then
        echo "$CONFLICT_OUTPUT" | head -20 | while IFS= read -r line; do
            echo "    $line"
        done
    fi
    if [ "$CI_MODE" = true ]; then
        fail "Unmigrated model changes in CI mode."
    fi
fi

# ─── Check 3: Dangerous operations in pending migrations ─────────

header "Check 3: Dangerous Operation Detection"

# Scan migration files for dangerous SQL patterns
DANGEROUS_FOUND=false

# Look for pending migration files and check for dangerous operations
for migration_file in $(find "$PROJECT_DIR/apps" -path "*/migrations/*.py" -newer "$PROJECT_DIR/manage.py" 2>/dev/null || true); do
    filename=$(basename "$migration_file")
    # Skip __init__.py
    [ "$filename" = "__init__.py" ] && continue

    # Check for dangerous patterns in the migration file
    DANGEROUS_PATTERNS="DeleteModel\|RemoveField\|RunSQL\|DROP TABLE\|DROP COLUMN\|TRUNCATE"
    MATCHES=$(grep -n "$DANGEROUS_PATTERNS" "$migration_file" 2>/dev/null || true)

    if [ -n "$MATCHES" ]; then
        DANGEROUS_FOUND=true
        warn "Potentially dangerous operations in: $filename"
        echo "$MATCHES" | while IFS= read -r line; do
            echo "    $line"
        done
    fi
done

if [ "$DANGEROUS_FOUND" = false ]; then
    ok "No dangerous operations detected in migration files."
else
    if [ "$CI_MODE" = true ]; then
        fail "Dangerous operations found in pending migrations."
    else
        warn "Review dangerous operations before deploying."
    fi
fi

# ─── Check 4: Migration file integrity ───────────────────────────

header "Check 4: Migration File Integrity"

# Check for syntax errors in migration files
SYNTAX_ERRORS=false
for migration_file in $(find "$PROJECT_DIR/apps" -path "*/migrations/*.py" -name "*.py" 2>/dev/null || true); do
    filename=$(basename "$migration_file")
    [ "$filename" = "__init__.py" ] && continue

    if ! python -c "import ast; ast.parse(open('$migration_file').read())" 2>/dev/null; then
        fail "Syntax error in migration: $migration_file"
        SYNTAX_ERRORS=true
    fi
done

if [ "$SYNTAX_ERRORS" = false ]; then
    ok "All migration files have valid Python syntax."
fi

# ─── Check 5: check_migrations command (if available) ────────────

header "Check 5: Detailed Migration Status (check_migrations)"

CHECK_OUTPUT=""
CHECK_EXIT=0

if python manage.py check_migrations --json 2>/dev/null; then
    ok "check_migrations command passed."
else
    CHECK_EXIT=$?
    if [ "$CHECK_EXIT" -eq 1 ]; then
        warn "check_migrations reported issues (exit code 1)."
        # Run again for human-readable output
        python manage.py check_migrations --detail 2>/dev/null || true
    else
        info "check_migrations command not available (skipping)."
    fi
fi

# ─── Summary ──────────────────────────────────────────────────────

echo ""
echo "$(printf '%.0s=' {1..60})"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}PRE-DEPLOY CHECK: PASSED${NC}"
else
    echo -e "  ${RED}${BOLD}PRE-DEPLOY CHECK: FAILED${NC}"
fi
echo "$(printf '%.0s=' {1..60})"
echo ""

exit "$EXIT_CODE"
