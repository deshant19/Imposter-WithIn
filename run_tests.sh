#!/usr/bin/env bash
# =============================================================================
# run_tests.sh — Imposter Within Test Suite Runner
# =============================================================================
# Usage:
#   ./run_tests.sh              # Run all tests (backend + frontend)
#   ./run_tests.sh --backend    # Backend tests only
#   ./run_tests.sh --frontend   # Frontend tests only
#   ./run_tests.sh --unit       # Backend unit tests only (fast)
#   ./run_tests.sh --coverage   # Full run with HTML coverage reports
#   ./run_tests.sh --watch      # Frontend tests in watch mode
#   ./run_tests.sh --ci         # CI mode: fail-fast, no watch
# =============================================================================

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# ── Flags ────────────────────────────────────────────────────────────────────
RUN_BACKEND=true
RUN_FRONTEND=true
COVERAGE=false
WATCH=false
CI_MODE=false
UNIT_ONLY=false

for arg in "$@"; do
  case $arg in
    --backend)   RUN_FRONTEND=false ;;
    --frontend)  RUN_BACKEND=false ;;
    --unit)      RUN_FRONTEND=false; UNIT_ONLY=true ;;
    --coverage)  COVERAGE=true ;;
    --watch)     RUN_BACKEND=false; WATCH=true ;;
    --ci)        CI_MODE=true ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
log()     { echo -e "${CYAN}[TEST]${RESET} $*"; }
success() { echo -e "${GREEN}[PASS]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo -e "${RED}[FAIL]${RESET} $*"; }
banner()  { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════════${RESET}"; \
            echo -e "${BOLD}${CYAN}  $*${RESET}"; \
            echo -e "${BOLD}${CYAN}══════════════════════════════════════════════${RESET}\n"; }

BACKEND_EXIT=0
FRONTEND_EXIT=0

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND TESTS
# ─────────────────────────────────────────────────────────────────────────────

run_backend() {
  banner "🐍 Backend Tests (pytest)"

  cd "$BACKEND_DIR"

  # ── Environment setup ────────────────────────────────────────────────────
  log "Checking Python environment..."

  if ! command -v python3 &>/dev/null; then
    error "python3 not found. Install Python 3.9+ first."
    return 1
  fi

  PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  log "Python version: $PYTHON_VERSION"

  # Create virtual env if not present
  if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
  fi

  # Activate venv
  source venv/bin/activate

  # Install / upgrade test deps
  log "Installing test dependencies..."
  pip install -q -r requirements-test.txt

  # Ensure data dir exists
  mkdir -p data
  touch data/rooms.json || true
  echo '{}' > data/rooms.json

  # ── Run tests ────────────────────────────────────────────────────────────
  if [ "$UNIT_ONLY" = true ]; then
    log "Running unit tests only (test_game_logic.py)..."
    PYTEST_ARGS="tests/test_game_logic.py -v --tb=short"
  elif [ "$COVERAGE" = true ]; then
    log "Running tests with coverage..."
    PYTEST_ARGS="tests/ --cov=main --cov-report=term-missing --cov-report=html:coverage_html -v"
  elif [ "$CI_MODE" = true ]; then
    log "Running tests in CI mode (fail-fast)..."
    PYTEST_ARGS="tests/ -x --tb=short -q"
  else
    log "Running all backend tests..."
    PYTEST_ARGS="tests/ -v --tb=short"
  fi

  # shellcheck disable=SC2086
  if python3 -m pytest $PYTEST_ARGS; then
    success "All backend tests passed ✓"
    BACKEND_EXIT=0
  else
    error "Some backend tests failed ✗"
    BACKEND_EXIT=1
  fi

  deactivate
  cd "$SCRIPT_DIR"
}

# ─────────────────────────────────────────────────────────────────────────────
# FRONTEND TESTS
# ─────────────────────────────────────────────────────────────────────────────

run_frontend() {
  banner "⚛️  Frontend Tests (Jest + RTL)"

  cd "$FRONTEND_DIR"

  # ── Environment setup ────────────────────────────────────────────────────
  log "Checking Node.js environment..."

  if ! command -v node &>/dev/null; then
    error "Node.js not found. Install Node.js 18+ first."
    return 1
  fi

  NODE_VERSION=$(node --version)
  log "Node version: $NODE_VERSION"

  if ! command -v npm &>/dev/null; then
    error "npm not found."
    return 1
  fi

  # Install if node_modules missing
  if [ ! -d "node_modules" ]; then
    log "Installing frontend dependencies (this may take a minute)..."
    npm install --silent
  fi

  # ── Run tests ────────────────────────────────────────────────────────────
  if [ "$WATCH" = true ]; then
    log "Starting tests in watch mode..."
    npm test -- --watchAll

  elif [ "$COVERAGE" = true ]; then
    log "Running frontend tests with coverage..."
    if CI=true npm test -- --coverage --watchAll=false; then
      success "All frontend tests passed ✓"
      FRONTEND_EXIT=0
    else
      error "Some frontend tests failed ✗"
      FRONTEND_EXIT=1
    fi

  elif [ "$CI_MODE" = true ]; then
    log "Running frontend tests in CI mode..."
    if CI=true npm test -- --watchAll=false --forceExit; then
      success "All frontend tests passed ✓"
      FRONTEND_EXIT=0
    else
      error "Some frontend tests failed ✗"
      FRONTEND_EXIT=1
    fi

  else
    log "Running frontend tests..."
    if CI=true npm test -- --watchAll=false; then
      success "All frontend tests passed ✓"
      FRONTEND_EXIT=0
    else
      error "Some frontend tests failed ✗"
      FRONTEND_EXIT=1
    fi
  fi

  cd "$SCRIPT_DIR"
}

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print_summary() {
  banner "📊 Test Summary"

  if [ "$RUN_BACKEND" = true ]; then
    if [ "$BACKEND_EXIT" -eq 0 ]; then
      success "Backend  : PASSED"
    else
      error   "Backend  : FAILED"
    fi
  fi

  if [ "$RUN_FRONTEND" = true ]; then
    if [ "$FRONTEND_EXIT" -eq 0 ]; then
      success "Frontend : PASSED"
    else
      error   "Frontend : FAILED"
    fi
  fi

  if [ "$COVERAGE" = true ]; then
    echo ""
    log "Coverage reports:"
    [ "$RUN_BACKEND"  = true ] && log "  Backend  → backend/coverage_html/index.html"
    [ "$RUN_FRONTEND" = true ] && log "  Frontend → frontend/coverage/lcov-report/index.html"
  fi

  echo ""
  TOTAL_EXIT=$((BACKEND_EXIT + FRONTEND_EXIT))
  if [ "$TOTAL_EXIT" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 All tests passed!${RESET}"
  else
    echo -e "${RED}${BOLD}❌ Some tests failed. See output above.${RESET}"
  fi
  echo ""
  return $TOTAL_EXIT
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}🕵️  Imposter Within — Test Suite${RESET}"
echo -e "    $(date)"
echo ""

[ "$RUN_BACKEND"  = true ] && run_backend  || true
[ "$RUN_FRONTEND" = true ] && run_frontend || true

print_summary
